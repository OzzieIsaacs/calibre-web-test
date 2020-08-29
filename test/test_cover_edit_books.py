#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import os
import time
import requests

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB
# from parameterized import parameterized_class
from helper_func import startup, debug_startup, add_dependency, remove_dependency
from helper_proxy import Proxy, val


class TestCoverEditBooks(TestCase, ui_class):
    p = None
    driver = None
    dependencys = ['Pillow']

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependencys, cls.__name__)

        try:
            cls.proxy = Proxy()
            cls.proxy.start()
            pem_file = os.path.join(os.path.expanduser('~'), '.mitmproxy', 'mitmproxy-ca-cert.pem')
            my_env = os.environ.copy()
            my_env["http_proxy"] = 'http://127.0.0.1:8080'
            my_env["https_proxy"] = 'https://127.0.0.1:8080'
            my_env["REQUESTS_CA_BUNDLE"] = pem_file
            # my_env["LANG"] = 'de_DE.UTF-8'
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, env=my_env)
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()


    @classmethod
    def tearDownClass(cls):
        remove_dependency(cls.dependencys)
        cls.stop_calibre_web()
        cls.driver.quit()
        cls.proxy.stop_proxy()
        cls.p.terminate()

    def test_upload_jpg(self):
        val.set_type(['HTTPError'])
        self.get_book_details(8)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jpg'})
        self.assertTrue("Error Downloading Cover" in self.check_element_on_page((By.ID, "flash_alert")).text)
        val.set_type(['ConnectionError'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jpg'})
        self.assertTrue("Error Downloading Cover" in self.check_element_on_page((By.ID, "flash_alert")).text)
        #val.set_type(['GeneralError'])
        #self.check_element_on_page((By.ID, "edit_book")).click()
        #self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jpg'})
        #self.assertTrue("Error Downloading Cover" in self.check_element_on_page((By.ID, "flash_alert")).text)
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jpg'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_alert')))
        resp = r.get('http://127.0.0.1:8083/cover/8')
        self.assertAlmostEqual(15938, int(resp.headers['Content-Length']), delta=300)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.webp'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_alert')))
        resp = r.get('http://127.0.0.1:8083/cover/8')
        self.assertAlmostEqual(17420, int(resp.headers['Content-Length']), delta=300)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.png'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_alert')))
        resp = r.get('http://127.0.0.1:8083/cover/8')
        self.assertAlmostEqual(20317, int(resp.headers['Content-Length']), delta=300)
        r.close()
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.bmp'})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_alert')))
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jol'})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_alert')))
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.brk'})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_alert')))
        self.assertTrue(False, "Browser-Cache Problem: Old Cover is displayed instead of New Cover")
