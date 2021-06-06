from flask import Flask, request, Response, redirect
import requests
import re
import logging
from multiprocessing import Process
# import time

SITE_NAME = None # 'http://192.168.188.57:8083'
SERVER_PATH = None # "/cw"
SCHEME = None # "http"

app = Flask(__name__)
log =logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def set_header():
    headers = {
        'Host': SITE_NAME
    }
    return headers

def parse_headers(header):
    req_header = {}
    for line in header.environ:
        if line.startswith('HTTP_'):
            req_header[line[5:]] = header.environ[line]
        if line.startswith('CONTENT_TYPE'):
            req_header[line] = header.environ[line]

    return req_header

@app.route('/')
def index():
    return 'Flask is running!'\

@app.route('/<path:p>',methods=['GET','POST',"DELETE"])
def proxy(p):
    if not request.full_path.startswith(SERVER_PATH):
        return "", 502
    path = request.full_path[len(SERVER_PATH):]

    req_header = parse_headers(request.headers)
    req_header['X-Script-Name'] = SERVER_PATH
    req_header['X-Scheme'] = SCHEME
    req_header['X-Forwarded-For'] = request.host

    url = re.sub('^http(s)?://', '', SITE_NAME)

    req_header['X-Forwarded-Host'] = url # "192.168.188.57:8083"

    if request.method=='GET':
        resp = requests.get(f'{SITE_NAME}{path}', headers=merge_two_dicts(req_header, set_header()), verify=False, allow_redirects=False)
    elif request.method=='POST':
        # todo: Handle fileupload
        post_body = request.form.to_dict()
        resp = requests.post(f'{SITE_NAME}{path}', data=post_body, headers=merge_two_dicts(req_header, set_header()), verify=False, allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
    if 'Location' in resp.headers:
        headers.append(('Location', resp.headers['Location'].replace(SITE_NAME, req_header['HOST'])))
    if (resp.status_code > 300 and resp.status_code < 304) or (resp.status_code > 304 and resp.status_code < 400):
        path = re.sub('^' + SITE_NAME, '', resp.headers['Location'])
        response = redirect(path, resp.status_code)
        for el in headers:
            if el[0] not in ["Content-Type", "Content-Length", "Location"]:
                response.headers[el[0]] = el[1]
    else:
        response = Response(resp.content, resp.status_code, headers)
    return response

class Reverse_Proxy():
    def __init__(self, port=8080, path="/cw", scheme="http", sitename="http://10.10.10.10:8083"):
        global SERVER_PATH, SCHEME, SITE_NAME
        SERVER_PATH = path
        SCHEME = scheme
        SITE_NAME = sitename
        self.port=port
        self.server=None
    def start(self):
        self.server = Process(target=app.run, kwargs={'debug': False, 'use_reloader': False,'port': self.port})
        self.server.start()

    def stop(self):
        self.server.terminate()
        self.server.join()