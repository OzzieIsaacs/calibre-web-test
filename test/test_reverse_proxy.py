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


RESOURCES = {'ports': 2}

PORTS = ['8083', '8080']
INDEX = ""


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



