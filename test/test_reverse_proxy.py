#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase
import time
from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup, debug_startup
from helper_func import save_logfiles
from selenium.webdriver.common.by import By
from helper_reverse_proxy import Reverse_Proxy
from helper_func import get_Host_IP
import requests
import re
import socket

RESOURCES = {'ports': 2}

PORTS = ['8083', '8080']
INDEX = ""

from flask import Flask, request, Response
import requests

# app = Flask(__name__)

'''host = 'http://' + get_Host_IP()
host_port = host + ':' + PORTS[0]
# The server you want to proxy to
TARGET_URL = host_port    # change this to your backend URL


@app.route("/cw", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.route("/cw/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def reverse_proxy(path):
    # Build the target URL (strip "/cw")
    url = f"{TARGET_URL}/{path}"

    # Forward the incoming request to the target server
    resp = requests.request(
        method=request.method,
        url=url,
        headers={key: value for key, value in request.headers if key.lower() != "host"},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=True,
        params=request.args
    )

    # Remove hop-by-hop headers
    excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
    headers = [
        (name, value) for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    return Response(resp.content, resp.status_code, headers)'''


#if __name__ == "__main__":
#    app.run(port=8080, debug=True, use_reloader=False)
#    time.sleep(1)

'''host = 'http://' + get_Host_IP()
host_port = host + ':' + PORTS[0]
test_proxy = Reverse_Proxy(sitename=host_port)
test_proxy.start()

time.sleep(10)'''

class TestReverseProxy(TestCase, ui_class):
    p = None
    driver = None
    proxy = None

    @classmethod
    def setUpClass(cls):
        try:
            host = 'http://' + get_Host_IP()
            host_port = host + ':' + PORTS[0]
            cls.proxy = Reverse_Proxy(sitename=host_port)
            cls.proxy.start()
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB}, host=host, 
                    port=PORTS[0], index=INDEX, parameter=["-i", get_Host_IP()], env={"APP_MODE": "test"})

            time.sleep(3)
            cls.driver.get('http://127.0.0.1:{}/cw'.format(PORTS[1]))
            cls.login('admin', 'admin123')
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.proxy.stop()
        cls.driver.get('http://' + get_Host_IP() + ':' + PORTS[0])
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_reverse_about(self):
        self.assertTrue(self.goto_page('nav_about'))

    def test_logout(self):
        self.logout()
        self.assertTrue(self.check_element_on_page((By.ID,"username")))
        self.login("adm", "admi")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.login("admin", "admin123")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_move_page(self):
        self.assertTrue(self.goto_page("admin_setup"))
        self.assertTrue(self.goto_page("view_config"))
        self.assertTrue(self.goto_page("logviewer"))
        self.assertTrue(self.goto_page("adv_search"))
        self.assertTrue(self.goto_page("mail_server"))

    def test_next(self):
        self.logout()
        self.driver.get("http://127.0.0.1:" + PORTS[1] + "/cw/me")
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "kindle_mail")))
        # no next parameter
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[1] + "/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[1] + "/cw/login", data=payload)
        self.assertEqual(200, page.status_code)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get("http://127.0.0.1:" + PORTS[1] + "/cw/logout")
        login_page = r.get("http://127.0.0.1:" + PORTS[1] + "/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "http:///example.com", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[1] + "/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get("http://127.0.0.1:" + PORTS[1] + "/cw/logout")
        login_page = r.get("http://127.0.0.1:" + PORTS[1] + "/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "https:///example.com", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[1] + "/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get("http://127.0.0.1:" + PORTS[1] + "/cw/logout")
        login_page = r.get("http://127.0.0.1:" + PORTS[1] + "/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "https:///example.com/test", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[1] + "/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get("http://127.0.0.1:" + PORTS[1] + "/cw/logout")
        # with proxy this is an invalid path
        login_page = r.get("http://127.0.0.1:" + PORTS[1] + "/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "/admin/1", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[1] + "/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get("http://127.0.0.1:" + PORTS[1] + "/cw/logout")
        login_page = r.get("http://127.0.0.1:" + PORTS[1] + "/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "../stats", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[1] + "/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get("http://127.0.0.1:" + PORTS[1] + "/cw/logout")
        login_page = r.get("http://127.0.0.1:" + PORTS[1] + "/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "ftp://" + socket.gethostname() + "/cw/admin/view", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[1] + "/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get("http://127.0.0.1:" + PORTS[1] + "/cw/logout")
        login_page = r.get("http://127.0.0.1:" + PORTS[1] + "/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "ftp://" + socket.gethostname() + "/admin/view", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[1] + "/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get("http://127.0.0.1:" + PORTS[1] + "/cw/logout")
        login_page = r.get("http://127.0.0.1:" + PORTS[1] + "/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "http://" + socket.gethostname() + "/cw/admin/view", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[1] + "/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get("http://127.0.0.1:" + PORTS[1] + "/cw/logout")
        r.close()



