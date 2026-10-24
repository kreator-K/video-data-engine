"""Authenticated HTTP boundary shared by local server and Vercel function."""
import base64
import hashlib
import hmac
import json
import logging
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

from src.job_store import JobStore, AdmissionError
from src.presentation import safe_url, video_key

ROOT=Path(__file__).resolve().parents[1]


def credentials(headers):
    users = json.loads(os.getenv('STUDIO_USERS_JSON','{}'))
    production = os.getenv('STUDIO_ENV')=='production' or bool(os.getenv('VERCEL'))
    if not users:
        return None if production else 'local-owner'
    try:
        scheme, encoded = headers.get('Authorization','').split(' ',1)
        if scheme.lower()!='basic': return None
        user,password=base64.b64decode(encoded,validate=True).decode().split(':',1)
        expected=users.get(user)
        if expected and hmac.compare_digest(password.encode(),expected.encode()):
            return hashlib.sha256(user.encode()).hexdigest()
    except (ValueError, UnicodeError): pass
    return None


def handle(method,path,headers,body=b'',store=None):
    """Return status, bytes and headers; no framework or orchestration dependency."""
    def response(status,data,mime='application/json',extra=None):
        data=json.dumps(data).encode() if mime=='application/json' else data
        return status,data,{'Content-Type':mime,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
            'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",**(extra or {})}
    production = os.getenv('STUDIO_ENV')=='production' or bool(os.getenv('VERCEL'))
    try:
        if not production and urlsplit('http://'+headers.get('Host','')).hostname not in {'127.0.0.1','localhost','::1'}:
            return response(403,{'error':'Local host required.'})
        owner = credentials(headers)
        if not owner:
            return response(401,{'error':'Sign in to the studio.'},extra={'WWW-Authenticate':'Basic realm="Creative Intelligence", charset="UTF-8"'})
        if production and not (os.getenv('DATABASE_URL') or os.getenv('POSTGRES_URL')):
            return response(503,{'error':'The studio is not configured yet.'})
        if method=='POST':
            origin=headers.get('Origin')
            expected=os.getenv('STUDIO_ORIGIN')
            host=headers.get('Host','')
            if origin and origin != (expected or (('https://' if production else 'http://')+host)):
                return response(403,{'error':'Origin not allowed.'})
            # Reject form/no-cors requests. Native CLI may omit Origin but must send JSON.
            if headers.get('Content-Type','').split(';')[0]!='application/json':
                return response(415,{'error':'JSON content is required.'})
        path=urlsplit(path).path
        store=store or JobStore()
        if method=='GET' and path=='/api/analyses':
            return response(200,{'analyses':store.history(owner),'capabilities':{'discovery':True,'live_analysis':True,'cached_analysis':True}})
        match=re.fullmatch(r'/api/(searches|analyses)/([a-f0-9]{32})',path)
        if method=='GET' and match:
            job=store.public(match[2],owner)
            if not job: return response(404,{'error':'Analysis not found.'})
            if match[1]=='analyses':
                if job['status']!='completed': return response(409,{'error':'Analysis is not completed.'})
                return response(200,{'analysis':job['analysis']})
            return response(200,job)
        image=re.fullmatch(r'/api/evidence/([a-f0-9]{64})\.jpg',path)
        if method=='GET' and image:
            data=store.get_image(image[1],owner)
            return response(200,data,'image/jpeg') if data else response(404,{'error':'Evidence not found.'})
        if method=='POST' and path=='/api/searches':
            if len(body)>16384: return response(413,{'error':'Request is too large.'})
            try:
                request=json.loads(body)
                query,refs=request['query'],request.get('reference_urls',[])
                limit=request.get('source_limit',10)
                if type(limit) is not int or not 1<=limit<=10:raise ValueError()
                if not isinstance(query,str) or not 1<=len(query.strip())<=1000 or not isinstance(refs,list) or len(refs)>10 or any(not safe_url(u) or not re.fullmatch(r'[A-Za-z0-9_-]{11}',video_key(u)) for u in refs):
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                return response(400,{'error':'Enter a topic and up to 10 valid YouTube video URLs.'})
            try:
                canonical_refs=['https://www.youtube.com/watch?v='+video_key(u) for u in refs]
                jid=store.submit(owner,query,canonical_refs,source_limit=limit)
                return response(202,{'id':jid})
            except AdmissionError as error:
                return response(429,{'error':str(error)})
        static={'/':('index.html','text/html'),'/index.html':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/analytics.mjs':('analytics.mjs','text/javascript'),'/styles.css':('styles.css','text/css')}
        if method=='GET' and path in static:
            filename,mime=static[path]
            return response(200,(ROOT/'frontend'/filename).read_bytes(),mime)
        if method=='GET' and path=='/data/design-preview.json' and not production:
            return response(200,(ROOT/'frontend/data/design-preview.json').read_bytes(),'application/octet-stream')
        return response(404,{'error':'Not found.'})
    except Exception:
        logging.exception('HTTP operation failed')
        return response(503,{'error':'The studio is temporarily unavailable. Please try again.'})
