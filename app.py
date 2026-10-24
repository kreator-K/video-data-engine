"""WSGI adapter for the supervised Vercel container runtime."""
from src.http_app import handle


def application(environ,start_response):
    from http import HTTPStatus
    try: size=int(environ.get('CONTENT_LENGTH') or '0')
    except ValueError: size=-1
    if not 0<=size<=16384:
        start_response('413 Payload Too Large',[('Content-Type','application/json')]); return [b'{"error":"Request too large."}']
    headers={key[5:].replace('_','-').title():value for key,value in environ.items() if key.startswith('HTTP_')}
    if environ.get('CONTENT_TYPE'): headers['Content-Type']=environ['CONTENT_TYPE']
    status,body,response_headers=handle(environ['REQUEST_METHOD'],environ['PATH_INFO'],headers,environ['wsgi.input'].read(size) if size else b'')
    start_response(f'{status} {HTTPStatus(status).phrase}',list(response_headers.items())+[('Content-Length',str(len(body)))])
    return [body]
