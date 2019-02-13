#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import shutil
from ui_helper import ui_class
from subproc_wrapper import process_open
from testconfig import CALIBRE_WEB_PATH, TEST_DB
import requests

'''
opds feed tests

'''


class test_opds_feed(unittest.TestCase, ui_class):
    p=None
    driver = None

    @classmethod
    def setUpClass(cls):

        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH,'app.db'))
        except:
            pass
        shutil.rmtree(TEST_DB,ignore_errors=True)
        shutil.copytree('./Calibre_db', TEST_DB)
        cls.p = process_open([u"python", os.path.join(CALIBRE_WEB_PATH,u'cps.py')],(1))

        # create a new Firefox session
        cls.driver = webdriver.Firefox()

        cls.driver.implicitly_wait(5)
        print('Calibre-web started')

        cls.driver.maximize_window()

        # navigate to the application home page
        cls.driver.get("http://127.0.0.1:8083")

        # Wait for config screen to show up
        cls.fill_initial_config({'config_calibre_dir':TEST_DB})

        # wait for cw to reboot
        time.sleep(5)

        # Wait for config screen with login button to show up
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.NAME, "login")))
        login_button = cls.driver.find_element_by_name("login")
        login_button.click()

        # login
        # cls.login("admin", "admin123")


    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()

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
        r = requests.get('http://127.0.0.1:8083'+elements['Category list']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Hot Books']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['New Books']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Public Shelves']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Publishers']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Random Books']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Series list']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Unread Books']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Read Books']['link'], auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Your Shelves']['link'], auth=('admin', 'admin123'))
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
        r = requests.get('http://127.0.0.1:8083'+elements['Category list']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Hot Books']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['New Books']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Public Shelves']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Publishers']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Random Books']['link'])
        self.assertEqual(200, r.status_code)
        r = requests.get('http://127.0.0.1:8083'+elements['Series list']['link'])
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
