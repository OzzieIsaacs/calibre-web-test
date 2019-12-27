#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from ui_helper import ui_class
from testconfig import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME
import requests
from func_helper import startup
from parameterized import parameterized_class
'''
opds feed tests
'''

'''@parameterized_class([
   { "py_version": u'/usr/bin/python'},
   { "py_version": u'/usr/bin/python3'},
],names=('Python27','Python36'))'''
class test_opds_feed(unittest.TestCase, ui_class):
    p=None
    driver = None

    @classmethod
    def setUpClass(cls):
        startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB}, login=False)

    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.kill()

    def test_opds(self):
        r = requests.get('http://127.0.0.1:8083/opds')
        self.assertEqual(401,r.status_code)
        r = requests.get('http://127.0.0.1:8083/opds', auth=('admin', '123'))
        self.assertEqual(401,r.status_code)
        r = requests.get('http://127.0.0.1:8083/opds', auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        elements = self.get_opds_index(r.text)
        r = requests.get('http://127.0.0.1:8083'+elements['Authors']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Best rated Books']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Categories']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Hot Books']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Recently added Books']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Public Shelves']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Publishers']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Random Books']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Series']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Unread Books']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Read Books']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Your Shelves']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Languages']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['File formats']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)

    def test_opds_guest_user(self):
        self.login("admin", "admin123")
        self.fill_basic_config({'config_anonbrowse': 1})
        r = requests.get('http://127.0.0.1:8083/opds')
        self.assertEqual(200, r.status_code)
        elements = self.get_opds_index(r.text)
        r = requests.get('http://127.0.0.1:8083'+elements['Authors']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Best rated Books']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Categories']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Hot Books']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Recently added Books']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Public Shelves']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Publishers']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Random Books']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Series']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Languages']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['File formats']['link'])
        self.assertEqual(200, r.status_code)
        self.assertFalse('Your Shelves' in elements)
        self.assertFalse('Read Books' in elements)
        self.assertFalse('Unread Books' in elements)
        self.fill_basic_config({'config_anonbrowse': 0})

    @unittest.skip("Not Implemented")
    def test_opds_search(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_shelf_access(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_non_admin(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_random(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_cover(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_download_book(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_read_unread(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_hot(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_language(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_series(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_calibre_companion(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_publisher(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_author(self):
        self.assertIsNone('Not Implemented')

    @unittest.skip("Not Implemented")
    def test_opds_paging(self):
        self.assertIsNone('Not Implemented')
