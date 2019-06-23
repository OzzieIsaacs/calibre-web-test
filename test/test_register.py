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

'''
use mitmproxy
use secure smtp
'''

class test_register(unittest.TestCase, ui_class):
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
        # time.sleep(15)
        cls.driver.implicitly_wait(BOOT_TIME)
        print('Calibre-web started')

        cls.driver.maximize_window()

        # navigate to the application home page
        cls.driver.get("http://127.0.0.1:8083")

        # Wait for config screen to show up
        cls.fill_initial_config({'config_calibre_dir':TEST_DB})

        # wait for cw to reboot
        time.sleep(BOOT_TIME)

        # Wait for config screen with login button to show up
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.NAME, "login")))
        login_button = cls.driver.find_element_by_name("login")
        login_button.click()

        # login
        cls.login("admin", "admin123")


    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()

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
