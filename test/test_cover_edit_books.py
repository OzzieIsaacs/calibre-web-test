#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import os
import time
# import requests

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB, base_path
from helper_func import startup
from helper_proxy import Proxy, val
from helper_func import save_logfiles
from diffimg import diff
from io import BytesIO


class TestCoverEditBooks(TestCase, ui_class):
    p = None
    driver = None
    proxy = None

    @classmethod
    def setUpClass(cls):

        try:
            cls.proxy = Proxy()
            cls.proxy.start()
            pem_file = os.path.join(os.path.expanduser('~'), '.mitmproxy', 'mitmproxy-ca-cert.pem')
            my_env = os.environ.copy()
            my_env["http_proxy"] = 'http://localhost:8080'
            my_env["https_proxy"] = 'http://localhost:8080'
            my_env["REQUESTS_CA_BUNDLE"] = pem_file
            my_env["APP_MODE"] = "test"
            # my_env["LANG"] = 'de_DE.UTF-8'
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_uploading': 1}, env=my_env,
                    parameter=["-l"])
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

    def check_invalid_cover(self, invalid_cover):
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        element = self.check_element_on_page((By.ID, "btn-upload-cover"))
        element.send_keys(invalid_cover)
        self.check_element_on_page((By.ID, "submit")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))

    def test_upload_jpg(self):
        val.set_type(['HTTPError'])
        self.get_book_details(8)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jpg'})
        self.assertTrue("Error Downloading Cover" in self.check_element_on_page((By.ID, "flash_danger")).text)
        val.set_type(['ConnectionError'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jpg'})
        self.assertTrue("Error Downloading Cover" in self.check_element_on_page((By.ID, "flash_danger")).text)
        original = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jpg'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_danger')))
        jpg = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreaterEqual(diff(BytesIO(original), BytesIO(jpg), delete_diff_file=True), 0.03)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.webp'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_danger')))
        web = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreater(diff(BytesIO(web), BytesIO(jpg), delete_diff_file=True), 0.005)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.png'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_danger')))
        png = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreater(diff(BytesIO(web), BytesIO(png), delete_diff_file=True), 0.01)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.bmp'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_danger')))
        bmp = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreater(diff(BytesIO(bmp), BytesIO(png), delete_diff_file=True), 0.006)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jol'})
        # Check if file content is detected correct
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_danger')), "BMP file is not detected")
        bmp2 = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertAlmostEqual(diff(BytesIO(bmp), BytesIO(bmp2), delete_diff_file=True), 0.0, delta=0.0001)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.brk'})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(
            content={'cover_url': u'https://api.github.com/repos/janeczku/calibre-web/cover/test.jpg?size=500'})
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_danger')))
        last = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertAlmostEqual(diff(BytesIO(last), BytesIO(jpg), delete_diff_file=True), 0.0, delta=0.0001,
                               msg="Browser-Cache Problem: Old Cover is displayed instead of New Cover")

    def test_invalid_jpg_hdd(self):
        invalid_cover = os.path.join(base_path, 'files', 'invalid.jpg')
        with open(invalid_cover, 'wb') as file_out:
            file_out.write(os.urandom(124))
        self.check_invalid_cover(invalid_cover)
        # check empty file
        open(invalid_cover, 'wb').close()
        self.check_invalid_cover(invalid_cover)
        os.unlink(invalid_cover)
