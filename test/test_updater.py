#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import shutil
from ui_helper import ui_class
from testconfig import TEST_DB
from func_helper import startup
from parameterized import parameterized_class

'''
use mitmproxy
Test update add updateerrors
'''
'''@parameterized_class([
   { "py_version": u'/usr/bin/python'},
   { "py_version": u'/usr/bin/python3'}]
    ,names=('Python27','Python36'))'''
class test_updater(unittest.TestCase, ui_class):
    p=None
    driver = None

    @classmethod
    def setUpClass(cls):
        startup(cls, cls.py_version,{'config_calibre_dir':TEST_DB})

    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        cls.p.kill()

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin','admin123')

    @unittest.skip("Not Implemented")
    def test_updater(self):
        self.assertIsNone('Not Implemented')