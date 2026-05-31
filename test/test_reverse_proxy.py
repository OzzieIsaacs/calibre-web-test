# -*- coding: utf-8 -*-

from base_test import ParallelTestCase, acquire_resource, release_resource
import time
import re
import socket
import requests
import datetime

from selenium.webdriver.common.by import By
from helper_reverse_proxy import Reverse_Proxy
from helper_func import get_Host_IP
from helper_func import startup


class TestReverseProxy(ParallelTestCase):


    proxy = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.port = acquire_resource("port")
        try:
            host = 'http://' + get_Host_IP()
            host_port = host + ':' + cls.worker_port
            cls.proxy = Reverse_Proxy(sitename=host_port, port=cls.port)
            cls.proxy.start()
            now = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} Starting Flask server")

            startup(cls, cls.py_version, {'config_calibre_dir':cls.temp_dir}, host=host,
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir,
                    parameter=["-i", get_Host_IP()])

            time.sleep(3)
            cls.driver.get(f'http://127.0.0.1:{cls.port}/cw')
            cls.login('admin', 'admin123')
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.proxy.stop()
        cls.driver.get(f'http://{get_Host_IP()}:{cls.worker_port}')
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        release_resource("port", cls.port)
        super().tearDownClass(no=True)

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
        self.driver.get(f"http://127.0.0.1:{self.port}/cw/me")
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "kindle_mail")))
        # no next parameter
        r = requests.session()
        login_page = r.get(f"http://127.0.0.1:{self.port}/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", "csrf_token": token.group(1)}
        page = r.post(f"http://127.0.0.1:{self.port}/cw/login", data=payload)
        self.assertEqual(200, page.status_code)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get(f"http://127.0.0.1:{self.port}/cw/logout")
        login_page = r.get(f"http://127.0.0.1:{self.port}/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "http:///example.com", "csrf_token": token.group(1)}
        page = r.post(f"http://127.0.0.1:{self.port}/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get(f"http://127.0.0.1:{self.port}/cw/logout")
        login_page = r.get(f"http://127.0.0.1:{self.port}/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "https:///example.com", "csrf_token": token.group(1)}
        page = r.post(f"http://127.0.0.1:{self.port}/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get(f"http://127.0.0.1:{self.port}/cw/logout")
        login_page = r.get(f"http://127.0.0.1:{self.port}/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "https:///example.com/test", "csrf_token": token.group(1)}
        page = r.post(f"http://127.0.0.1:{self.port}/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get(f"http://127.0.0.1:{self.port}/cw/logout")
        # with proxy this is an invalid path
        login_page = r.get(f"http://127.0.0.1:{self.port}/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "/admin/1", "csrf_token": token.group(1)}
        page = r.post(f"http://127.0.0.1:{self.port}/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get(f"http://127.0.0.1:{self.port}/cw/logout")
        login_page = r.get(f"http://127.0.0.1:{self.port}/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "../stats", "csrf_token": token.group(1)}
        page = r.post(f"http://127.0.0.1:{self.port}/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get(f"http://127.0.0.1:{self.port}/cw/logout")
        login_page = r.get(f"http://127.0.0.1:{self.port}/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "ftp://" + socket.gethostname() + "/cw/admin/view", "csrf_token": token.group(1)}
        page = r.post(f"http://127.0.0.1:{self.port}/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get(f"http://127.0.0.1:{self.port}/cw/logout")
        login_page = r.get(f"http://127.0.0.1:{self.port}/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "ftp://" + socket.gethostname() + "/admin/view", "csrf_token": token.group(1)}
        page = r.post(f"http://127.0.0.1:{self.port}/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get(f"http://127.0.0.1:{self.port}/cw/logout")
        login_page = r.get(f"http://127.0.0.1:{self.port}/cw/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "http://" + socket.gethostname() + "/cw/admin/view", "csrf_token": token.group(1)}
        page = r.post(f"http://127.0.0.1:{self.port}/cw/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.get(f"http://127.0.0.1:{self.port}/cw/logout")
        r.close()



