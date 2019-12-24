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
from testconfig import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME
from func_helper import startup
from parameterized import parameterized_class
'''
use mitmproxy
use secure smtp
'''

@parameterized_class([
   { "py_version": u'/usr/bin/python'},
   { "py_version": u'/usr/bin/python3'},
],names=('Python27','Python36'))
class test_register(unittest.TestCase, ui_class):
    p=None
    driver = None

    @classmethod
    def setUpClass(cls):
        startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB})

    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.kill()

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin','admin123')

    # no emailserver configure, email server not reachable
    @unittest.skip("Not Implemented")
    def test_registering_user(self):
        self.assertIsNone('Not Implemented')

    # no emailadress during register double username, emailadress, capital letters, lowercase characters
    @unittest.skip("Not Implemented")
    def test_registering_user_fail(self):
        self.assertIsNone('Not Implemented')

    # no emailadress during register double username, emailadress, capital letters, lowercase characters
    @unittest.skip("Not Implemented")
    def test_login_with_password(self):
        self.assertIsNone('Not Implemented')

    # admin resends password
    @unittest.skip("Not Implemented")
    def test_resend_password(self):
        self.assertIsNone('Not Implemented')

    # admin resends password
    @unittest.skip("Not Implemented")
    def user_change_password(self):
        self.assertIsNone('Not Implemented')
