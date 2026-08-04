from flask import Flask, request, Response, redirect
import requests
import re
import logging
from werkzeug.serving import make_server
# from multiprocessing import Process
import threading

SITE_NAME = None # 'http://192.168.188.57:8083'
SERVER_PATH = None # "/cw"
SCHEME = None # "http"
UPSTREAM_HEADERS = {}

app = Flask(__name__)
log =logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


def _forward_request(method, url, req_header, post_body=None):
    try:
        if method == 'GET':
            return requests.get(url, headers=merge_two_dicts(req_header, set_header()),
                                verify=False, allow_redirects=False, timeout=2)
        if method == 'POST':
            return requests.post(url, data=post_body, headers=merge_two_dicts(req_header, set_header()),
                                 verify=False, allow_redirects=False, timeout=2)
    except requests.exceptions.RequestException:
        return None
    return None

def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z

def set_header():
    headers = {
        'HOST': re.sub('^http(s)?://', '', SITE_NAME)
    }
    return headers


def _normalize_header_name(name):
    return "-".join(part.capitalize() for part in name.split("-"))


def _strip_header_case_insensitive(headers, header_name):
    remove_keys = [key for key in headers if key.lower() == header_name.lower()]
    for key in remove_keys:
        del headers[key]


def set_upstream_headers(headers=None):
    global UPSTREAM_HEADERS
    UPSTREAM_HEADERS = dict(headers or {})


def update_upstream_headers(req_header):
    for header_name, header_value in UPSTREAM_HEADERS.items():
        _strip_header_case_insensitive(req_header, header_name)
        if header_value is not None:
            req_header[_normalize_header_name(header_name)] = header_value

def parse_headers(header):
    req_header = {}
    for line in header.environ:
        if line.startswith('HTTP_'):
            req_header[line[5:].replace('_', '-')] = header.environ[line]
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
    path = request.full_path[len(SERVER_PATH):] # .strip("?")

    req_header = parse_headers(request.headers)
    req_header['X-Script-Name'] = SERVER_PATH
    req_header['X-Scheme'] = SCHEME
    req_header['X-Forwarded-For'] = request.host

    url = re.sub('^http(s)?://', '', SITE_NAME)

    req_header['X-Forwarded-Host'] = url # "192.168.188.57:8083"
    update_upstream_headers(req_header)

    resp = None
    if request.method == 'GET':
        resp = _forward_request('GET', f'{SITE_NAME}{path}', req_header)
    elif request.method == 'POST':
        # todo: Handle fileupload
        post_body = request.form.to_dict()
        resp = _forward_request('POST', f'{SITE_NAME}{path}', req_header, post_body)
    if resp is None:
        return "", 502

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


class Reverse_Proxy(threading.Thread):
    def __init__(self, port=8080, path="/cw", scheme="http", sitename="http://10.10.10.10:8083"):
        threading.Thread.__init__(self)
        global SERVER_PATH, SCHEME, SITE_NAME
        SERVER_PATH = path
        SCHEME = scheme
        SITE_NAME = sitename
        self.port=port
        self.server = make_server("127.0.0.1",  self.port, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.daemon = True

    def run(self):
        # print("Starting Flask server...")
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()

    def set_auth_header(self, header_name, header_value):
        headers = dict(UPSTREAM_HEADERS)
        if header_name:
            headers[header_name] = header_value
        set_upstream_headers(headers)

    def clear_auth_header(self, header_name):
        headers = dict(UPSTREAM_HEADERS)
        headers.pop(header_name, None)
        set_upstream_headers(headers)

    def set_secret_header(self, header_name, header_value):
        headers = dict(UPSTREAM_HEADERS)
        if header_name:
            headers[header_name] = header_value
        set_upstream_headers(headers)

    def clear_secret_header(self, header_name):
        headers = dict(UPSTREAM_HEADERS)
        headers.pop(header_name, None)
        set_upstream_headers(headers)

    def set_upstream_headers(self, headers=None):
        set_upstream_headers(headers)