#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import time
import requests

from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup
from helper_func import save_logfiles


class TestReconnect(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, parameter=["-r"])
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_reconnect_endpoint(self):
        resp = requests.get('http://127.0.0.1:8083/reconnect')
        self.assertEqual(200, resp.status_code)
        self.assertDictEqual({}, resp.json())
