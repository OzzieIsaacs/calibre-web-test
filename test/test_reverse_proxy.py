# -*- coding: utf-8 -*-

from base_test import ParallelTestCase, acquire_resource, release_resource
import time
import re
import socket
import requests
from requests.exceptions import RequestException

from selenium.webdriver.common.by import By
from helper_reverse_proxy import Reverse_Proxy
from helper_func import get_Host_IP, startup, wait_for_reboot


class TestReverseProxy(ParallelTestCase):

    proxy = None
    host = None
    proxy_login_header = "X-LOGIN"
    proxy_secret_header = "X-PROXY-SECRET"
    proxy_secret_value = "proxy-shared-secret"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.port = acquire_resource("port")
        try:
            cls.host = get_Host_IP()
            host = 'http://' + cls.host
            host_port = host + ':' + cls.worker_port
            cls.proxy = Reverse_Proxy(sitename=host_port, port=cls.port)
            cls.proxy.start()
            cls.trusted_proxy_ip = cls.host
            cls.log_class("Starting Reverse Proxy Flask server")

            startup(cls, cls.py_version, {'config_calibre_dir':cls.temp_dir}, host=host,
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir,
                    parameter=["-i", cls.host])

            time.sleep(3)
            cls.driver.get(f'http://127.0.0.1:{cls.port}/cw')
            cls.login('admin', 'admin123')
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.proxy.stop()
        cls.driver.get(f'http://{cls.host}:{cls.worker_port}')
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        release_resource("port", cls.port)
        super().tearDownClass(no=True)

    # Verifies that navigation to the about page works through the reverse proxy path.
    def test_reverse_about(self):
        self.assertTrue(self.goto_page('nav_about'))

    def setUp(self):
        self.proxy.set_upstream_headers({})

    def tearDown(self):
        self.proxy.set_upstream_headers({})
        super().tearDown()

    def _configure_reverse_proxy_login(self, use_shared_secret=False, trusted_proxy_ips=None):
        config = {
            'config_allow_reverse_proxy_header_login': 1,
            'config_reverse_proxy_login_header_name': self.proxy_login_header,
            'config_reverse_proxy_trusted_ips': trusted_proxy_ips or self.trusted_proxy_ip,
            'config_reverse_proxy_use_shared_secret': 1 if use_shared_secret else 0,
        }
        if use_shared_secret:
            config.update({
                'config_reverse_proxy_login_secret_header_name': self.proxy_secret_header,
                'config_reverse_proxy_login_header_secret_e': self.proxy_secret_value,
            })
        self.fill_basic_config(config)
        wait_for_reboot(self.host + ":" + self.worker_port)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # self._wait_http_ready()

    def _proxy_get(self, path="/", headers=None):
        return requests.get(f"http://127.0.0.1:{self.port}/cw{path}", headers=headers or {}, allow_redirects=False)

    def _direct_get(self, path="/", headers=None):
        return requests.get(f"http://{self.trusted_proxy_ip}:{self.worker_port}{path}",
                            headers=headers or {}, allow_redirects=False)

    def _wait_http_ready(self, timeout=15):
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = self._proxy_get("/login")
                if resp.status_code in (200, 302):
                    return
            except RequestException:
                pass
            time.sleep(0.5)
        self.fail("Calibre-Web did not become ready in time after config update")

    def _assert_login_page(self, response):
        self.assertIn(response.status_code, (200, 302))
        if response.status_code == 302:
            self.assertIn("/login", response.headers.get("Location", ""))
        else:
            self.assertIn("Calibre-Web | Login", response.text)

    def _assert_admin_authenticated(self, response):
        self.assertEqual(200, response.status_code)
        self.assertNotIn("Calibre-Web | Login", response.text)
        self.assertIn("kindle_mail", response.text)

    # Ensures proxy header authentication succeeds for a trusted proxy and existing user.
    def test_proxy_auth_01_trusted_proxy_valid_user_header(self):
        self._configure_reverse_proxy_login()
        self.proxy.set_auth_header(self.proxy_login_header, "admin")
        resp = self._proxy_get("/me")
        self._assert_admin_authenticated(resp)

    # Ensures direct access with a spoofed auth header is denied when request source is untrusted.
    def test_proxy_auth_02_direct_access_header_denied(self):
        self._configure_reverse_proxy_login(trusted_proxy_ips="127.0.0.1")
        resp = self._direct_get("/", headers={self.proxy_login_header: "admin"})
        self._assert_login_page(resp)

    # Ensures unknown users are rejected even when the request comes from a trusted proxy.
    def test_proxy_auth_03_trusted_proxy_unknown_user_denied(self):
        self._configure_reverse_proxy_login()
        self.proxy.set_auth_header(self.proxy_login_header, "does-not-exist")
        resp = self._proxy_get("/")
        self._assert_login_page(resp)

    # Ensures shared-secret checks are skipped when the shared-secret feature is disabled.
    def test_proxy_auth_04_shared_secret_disabled_does_not_block_login(self):
        self._configure_reverse_proxy_login(use_shared_secret=False)
        self.proxy.set_auth_header(self.proxy_login_header, "admin")
        resp = self._proxy_get("/me")
        self._assert_admin_authenticated(resp)

    # Ensures login is denied if shared-secret mode is enabled but the secret header is missing.
    def test_proxy_auth_05_shared_secret_enabled_missing_secret_denied(self):
        self._configure_reverse_proxy_login(use_shared_secret=True)
        self.proxy.set_auth_header(self.proxy_login_header, "admin")
        resp = self._proxy_get("/")
        self._assert_login_page(resp)

    # Ensures login is denied if shared-secret mode is enabled and the provided secret is wrong.
    def test_proxy_auth_06_shared_secret_enabled_wrong_secret_denied(self):
        self._configure_reverse_proxy_login(use_shared_secret=True)
        self.proxy.set_auth_header(self.proxy_login_header, "admin")
        self.proxy.set_secret_header(self.proxy_secret_header, "wrong-secret")
        resp = self._proxy_get("/")
        self._assert_login_page(resp)

    # Ensures login succeeds when shared-secret mode is enabled and the correct secret is provided.
    def test_proxy_auth_07_shared_secret_enabled_correct_secret_allows_login(self):
        self._configure_reverse_proxy_login(use_shared_secret=True)
        self.proxy.set_auth_header(self.proxy_login_header, "admin")
        self.proxy.set_secret_header(self.proxy_secret_header, self.proxy_secret_value)
        resp = self._proxy_get("/me")
        self._assert_admin_authenticated(resp)

    # Ensures direct requests remain denied even with correct user and secret headers.
    def test_proxy_auth_08_direct_access_with_secret_still_denied(self):
        self._configure_reverse_proxy_login(use_shared_secret=True, trusted_proxy_ips="127.0.0.1")
        resp = self._direct_get("/", headers={
            self.proxy_login_header: "admin",
            self.proxy_secret_header: self.proxy_secret_value,
        })
        self._assert_login_page(resp)

    # Verifies standard logout and login error/success flow through the reverse proxy.
    def test_logout(self):
        self.logout()
        self.assertTrue(self.check_element_on_page((By.ID,"username")))
        self.login("adm", "admi")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.login("admin", "admin123")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    # Verifies core navigation targets remain reachable behind the reverse proxy.
    def test_move_page(self):
        self.assertTrue(self.goto_page("admin_setup"))
        self.assertTrue(self.goto_page("view_config"))
        self.assertTrue(self.goto_page("logviewer"))
        self.assertTrue(self.goto_page("adv_search"))
        self.assertTrue(self.goto_page("mail_server"))

    # Verifies login redirect handling with multiple next-parameter variants behind proxy prefix.
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
