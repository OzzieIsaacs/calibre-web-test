#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import os
import time
import requests

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup, debug_startup, add_dependency, remove_dependency
from helper_proxy import Proxy, val
from helper_func import save_logfiles
from diffimg import diff

class TestCoverEditBooks(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):

        try:
            cls.proxy = Proxy()
            cls.proxy.start()
            pem_file = os.path.join(os.path.expanduser('~'), '.mitmproxy', 'mitmproxy-ca-cert.pem')
            my_env = os.environ.copy()
            my_env["http_proxy"] = 'http://localhost:8080'
            my_env["https_proxy"] = 'https://localhost:8080'
            my_env["REQUESTS_CA_BUNDLE"] = pem_file
            # my_env["LANG"] = 'de_DE.UTF-8'
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_uploading': 1}, env=my_env)
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()


    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        cls.driver.quit()
        cls.proxy.stop_proxy()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

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
        #r = requests.session()
        #payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        #r.post('http://127.0.0.1:8083/login', data=payload)
        self.save_cover_screenshot('original.png')
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jpg'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_alert')))
        self.save_cover_screenshot('jpg.png')
        self.assertGreater(diff('original.png', 'jpg.png', delete_diff_file=True), 0.03)
        os.unlink('original.png')
        #resp = r.get('http://127.0.0.1:8083/cover/8')
        #self.assertAlmostEqual(15938, int(resp.headers['Content-Length']), delta=300)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.webp'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_alert')))
        # resp = r.get('http://127.0.0.1:8083/cover/8')
        self.save_cover_screenshot('web.png')
        self.assertGreater(diff('web.png', 'jpg.png', delete_diff_file=True), 0.005)
        # self.assertAlmostEqual(17420, int(resp.headers['Content-Length']), delta=300)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.png'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_alert')))
        #resp = r.get('http://127.0.0.1:8083/cover/8')
        #self.assertAlmostEqual(20317, int(resp.headers['Content-Length']), delta=300)
        #r.close()
        self.save_cover_screenshot('png.png')
        self.assertGreater(diff('web.png', 'png.png', delete_diff_file=True), 0.01)
        os.unlink('web.png')
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.bmp'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_alert')))
        self.save_cover_screenshot('bmp.png')
        self.assertGreater(diff('bmp.png', 'png.png', delete_diff_file=True), 0.006)
        os.unlink('png.png')
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jol'})
        # Check if file content is detected correct
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_alert')), "BMP file is not detected")
        self.save_cover_screenshot('bmp2.png')
        self.assertAlmostEqual(diff('bmp.png', 'bmp2.png', delete_diff_file=True), 0.0, delta=0.0001)
        os.unlink('bmp2.png')
        os.unlink('bmp.png')
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.brk'})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_alert')))
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jpg?size=500'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_alert')))
        self.save_cover_screenshot('last.png')
        self.assertAlmostEqual(diff('last.png', 'jpg.png', delete_diff_file=True), 0.0, delta=0.0001,
                               msg="Browser-Cache Problem: Old Cover is displayed instead of New Cover")
        os.unlink('last.png')
        os.unlink('jpg.png')
        os.unlink('page.png')
