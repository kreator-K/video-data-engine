"""Durable admission, worker leases and immutable evidence. SQLite local, Postgres cloud."""
import hashlib
import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


class AdmissionError(ValueError):
    pass


class JobStore:
    def __init__(self, path=None, database_url=None):
        self.url = database_url if database_url is not None else (None if path is not None else (os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')))
        if self.url:
            parts=urlsplit(self.url)
            self.url=urlunsplit(parts._replace(query=urlencode([(k,v) for k,v in parse_qsl(parts.query) if k not in {'supa','pgbouncer','connection_limit','pool_timeout'}])))
        self.path = Path(path or os.getenv('JOB_DATABASE_PATH', 'data/jobs.sqlite3'))
        if not self.url:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection(write=True) as db:
            if self.url:
                db.execute('CREATE SCHEMA IF NOT EXISTS studio_private')
                db.execute('REVOKE ALL ON SCHEMA studio_private FROM PUBLIC')
            binary = 'BYTEA' if self.url else 'BLOB'
            db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, owner TEXT NOT NULL, status TEXT NOT NULL, created DOUBLE PRECISION NOT NULL, completed DOUBLE PRECISION, lease DOUBLE PRECISION NOT NULL DEFAULT 0, request TEXT NOT NULL, report TEXT, message TEXT NOT NULL, sources TEXT NOT NULL DEFAULT \'[]\', worker TEXT)')
            db.execute(f'CREATE TABLE IF NOT EXISTS images (digest TEXT PRIMARY KEY, content {binary} NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS job_images (job_id TEXT NOT NULL, digest TEXT NOT NULL, PRIMARY KEY(job_id,digest))')
            db.execute('CREATE INDEX IF NOT EXISTS jobs_owner_created ON jobs(owner, created)')
            if self.url:
                for table in ('jobs','images','job_images'):
                    db.execute('ALTER TABLE '+table+' ENABLE ROW LEVEL SECURITY')

    @contextmanager
    def connection(self, write=False):
        if self.url:
            import psycopg
            from psycopg.rows import dict_row
            db = psycopg.connect(self.url, row_factory=dict_row, connect_timeout=10, prepare_threshold=None)
            db.execute('SET search_path TO studio_private')
            db.execute("SET statement_timeout TO '15s'")
            class Adapter:
                def execute(self, sql, args=()):
                    return db.execute(sql.replace('?', '%s'), args)
            conn = Adapter()
            try:
                if write:
                    db.execute('SELECT pg_advisory_xact_lock(726518903)')
                yield conn
                db.commit()
            except BaseException:
                db.rollback(); raise
            finally:
                db.close()
        else:
            db = sqlite3.connect(self.path, timeout=15)
            db.row_factory = sqlite3.Row
            try:
                db.execute('PRAGMA busy_timeout=15000')
                if write:
                    db.execute('BEGIN IMMEDIATE')
                yield db
                db.commit()
            except BaseException:
                db.rollback(); raise
            finally:
                db.close()

    def submit(self, owner, query, refs, source_limit=10):
        now = time.time()
        request = json.dumps({'query': query.strip(), 'reference_urls': list(dict.fromkeys(refs)), 'source_limit': source_limit}, sort_keys=True)
        with self.connection(write=True) as db:
            active = db.execute("SELECT * FROM jobs WHERE status IN ('queued','running') ORDER BY created").fetchall()
            for job in active:
                if job['owner'] == owner and job['request'] == request:
                    return job['id']
            if len(active) >= int(os.getenv('MAX_PENDING_JOBS', '4')):
                raise AdmissionError('The studio is busy. Please try again later.')
            if any(j['owner'] == owner for j in active):
                raise AdmissionError('Your analysis is already running. Please wait for it to finish.')
            count = db.execute('SELECT COUNT(*) AS n FROM jobs WHERE owner=? AND created>?', (owner, now - 86400)).fetchone()['n']
            total = db.execute('SELECT COUNT(*) AS n FROM jobs WHERE created>?', (now - 86400,)).fetchone()['n']
            if count >= int(os.getenv('MAX_DAILY_JOBS_PER_USER', '3')) or total >= int(os.getenv('MAX_DAILY_JOBS', '10')):
                raise AdmissionError('The daily analysis limit has been reached.')
            jid = uuid.uuid4().hex
            db.execute('INSERT INTO jobs(id,owner,status,created,request,message) VALUES (?,?,?,?,?,?)', (jid, owner, 'queued', now, request, 'Waiting to begin analysis.'))
            return jid

    def claim(self, worker):
        now = time.time()
        with self.connection(write=True) as db:
            # A database lease coordinates every web/worker process, not just one thread.
            if db.execute("SELECT id FROM jobs WHERE status='running' AND lease>?", (now,)).fetchone():
                return None
            job = db.execute("SELECT * FROM jobs WHERE status='queued' OR (status='running' AND lease<=?) ORDER BY created LIMIT 1", (now,)).fetchone()
            if not job:
                return None
            db.execute("UPDATE jobs SET status='running',worker=?,lease=?,message=? WHERE id=?", (worker, now + 90, 'Preparing analysis.', job['id']))
            return self.internal(job['id'], db)

    def internal(self, jid, db=None):
        if db is None:
            with self.connection() as conn:
                return self.internal(jid, conn)
        row = db.execute('SELECT * FROM jobs WHERE id=?', (jid,)).fetchone()
        if not row:
            return None
        result = dict(row)
        for key in ('request', 'sources', 'report'):
            result[key] = json.loads(result[key]) if result[key] else None
        return result

    def update(self, jid, worker, *, message=None, sources=None, report=None, status=None):
        with self.connection(write=True) as db:
            job = db.execute('SELECT worker,status,lease FROM jobs WHERE id=?', (jid,)).fetchone()
            if not job or job['worker'] != worker or job['status'] != 'running' or job['lease']<=time.time():
                raise RuntimeError('Worker lease no longer owned')
            columns, args = ['lease=?'], [time.time()+90]
            for key, value in [('message',message),('sources',sources),('report',report),('status',status)]:
                if value is not None:
                    columns.append(key+'=?'); args.append(json.dumps(value) if key in {'sources','report'} else value)
            if status in {'completed','failed','cancelled'}:
                columns.append('completed=?'); args.append(time.time())
            db.execute('UPDATE jobs SET '+','.join(columns)+' WHERE id=?', (*args,jid))

    def public(self, jid, owner):
        job = self.internal(jid)
        if not job or job['owner'] != owner:
            return None
        result = {k: job[k] for k in ('id','status','message')}
        result['created_at'] = job['created']
        if job['completed']:
            result['completed_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(job['completed']))
        if job['status']=='completed' and job['report']:
            result['analysis'] = job['report']
        return result

    def history(self, owner):
        with self.connection() as db:
            rows = db.execute("SELECT id,request,completed FROM jobs WHERE owner=? AND status='completed' ORDER BY completed DESC", (owner,)).fetchall()
        return [{'id': r['id'], 'title': json.loads(r['request'])['query'], 'status':'completed', 'completed_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(r['completed']))} for r in rows]

    def image(self, content, jid):
        if not content.startswith(b'\xff\xd8') or len(content)>4*1024*1024:
            raise ValueError('Invalid evidence image')
        digest = hashlib.sha256(content).hexdigest()
        with self.connection(write=True) as db:
            existing=db.execute('SELECT digest FROM images WHERE digest=?',(digest,)).fetchone()
            if not existing:
                used=db.execute('SELECT COALESCE(SUM(length(content)),0) AS n FROM images').fetchone()['n']
                if used+len(content)>int(os.getenv('MAX_EVIDENCE_STORAGE_BYTES',str(200*1024*1024))):
                    raise AdmissionError('Evidence storage limit reached.')
            db.execute('INSERT INTO images(digest,content) VALUES (?,?) ON CONFLICT(digest) DO NOTHING', (digest, content))
            db.execute('INSERT INTO job_images(job_id,digest) VALUES (?,?) ON CONFLICT(job_id,digest) DO NOTHING', (jid,digest))
        return '/api/evidence/'+digest+'.jpg'

    def get_image(self, digest, owner):
        with self.connection() as db:
            row = db.execute('SELECT images.content FROM images JOIN job_images ON images.digest=job_images.digest JOIN jobs ON jobs.id=job_images.job_id WHERE images.digest=? AND jobs.owner=? AND jobs.status=\'completed\' LIMIT 1', (digest,owner)).fetchone()
        return bytes(row['content']) if row else None
