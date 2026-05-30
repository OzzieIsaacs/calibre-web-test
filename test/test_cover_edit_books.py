#!/usr/bin/env python
# -*- coding: utf-8 -*-


from base_test import ParallelTestCase, acquire_resource, release_resource
import os
import time

from selenium.webdriver.common.by import By
from config_test import base_path
from helper_func import startup
from helper_proxy import Proxy, val
from diffimg import diff
from io import BytesIO


class TestCoverEditBooks(ParallelTestCase):


    proxy = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            cls.port = acquire_resource("port")
            cls.proxy = Proxy(cls.port)
            cls.proxy.start()
            pem_file = os.path.join(os.path.expanduser('~'), '.mitmproxy', 'mitmproxy-ca-cert.pem')
            my_env = os.environ.copy()
            my_env["http_proxy"] = f'http://localhost:{cls.port}'
            my_env["https_proxy"] = f'http://localhost:{cls.port}'
            my_env["REQUESTS_CA_BUNDLE"] = pem_file
            my_env["APP_MODE"] = "test"
            my_env["CALIBRE_PORT"] = cls.worker_port
            startup(cls, cls.py_version,
                    {'config_calibre_dir': cls.temp_dir, 'config_uploading': 1},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env=my_env,
                    lib_dest=cls.temp_dir,
                    parameter=["-l"])
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        '''cls.driver.get("http://127.0.0.1:" + cls.worker_port)
        cls.stop_calibre_web()
        cls.driver.quit()
        cls.proxy.stop_proxy()
        cls.p.terminate()'''
        release_resource("port", cls.port)
        super().tearDownClass()

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
        # check spaces in request are stripped
        self.edit_book(content={'cover_url': u' https://api.github.com/repos/janeczku/calibre-web/cover/test.jpg '})
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
