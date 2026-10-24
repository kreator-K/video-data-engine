"""Vercel Python HTTP function. Paid processing runs only in the worker daemon."""
from http.server import BaseHTTPRequestHandler
from src.http_app import handle

class handler(BaseHTTPRequestHandler):
    def dispatch(self):
        try: size=int(self.headers.get('Content-Length','0'))
        except ValueError:
            self.send_error(400); return
        if not 0<=size<=16384:
            self.send_error(413); return
        status,body,headers=handle(self.command,self.path,self.headers,self.rfile.read(size) if size else b'')
        self.send_response(status)
        for key,value in headers.items(): self.send_header(key,value)
        self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    do_GET=dispatch
    do_POST=dispatch
