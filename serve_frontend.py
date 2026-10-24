"""Local entry point. Cloud uses api/index.py and the separate durable worker."""
import argparse
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from dotenv import load_dotenv
from src.http_app import handle

load_dotenv(Path(__file__).resolve().parent/'.env')


class Handler(BaseHTTPRequestHandler):
    def dispatch(self):
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<=size<=16384:
                self.send_error(413); return
        except ValueError:
            self.send_error(400); return
        status,body,headers=handle(self.command,self.path,self.headers,self.rfile.read(size) if size else b'')
        self.send_response(status)
        for key,value in headers.items(): self.send_header(key,value)
        self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    do_GET=dispatch
    do_POST=dispatch


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=int(os.getenv('PORT','4173')))
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--no-worker',action='store_true')
    args=parser.parse_args()
    if args.host not in {'127.0.0.1','localhost'} and not os.getenv('STUDIO_USERS_JSON'):
        raise SystemExit('Configure STUDIO_USERS_JSON before exposing the server.')
    worker=None if args.no_worker else subprocess.Popen([sys.executable,str(Path(__file__).with_name('worker.py'))])
    try:
        print(f'Video Data Agent: http://{args.host}:{args.port}',flush=True)
        ThreadingHTTPServer((args.host,args.port),Handler).serve_forever()
    finally:
        if worker:
            worker.terminate()
            try: worker.wait(timeout=10)
            except subprocess.TimeoutExpired: worker.kill(); worker.wait()
