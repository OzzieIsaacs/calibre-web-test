#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase
import time

from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup, save_logfiles, read_metadata_epub

RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""

class TestDownloadMetadata(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB},
                    port=PORTS[0],
                    index=INDEX, env={"APP_MODE": "test"})
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:" + PORTS[0])
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_download_check_metadata(self):
        # no calibre download
        code, content = self.download_book(10, "admin", "admin123")
        self.assertEqual(200, code)
        test = read_metadata_epub(content)

        # code, content = self.download_book(1, "admin", "admin123")
        # self.assertEqual(200, code)
