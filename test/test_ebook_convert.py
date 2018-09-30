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

'''
use secure-smtp
'''

class test_convert_email(unittest.TestCase, ui_class):
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
        cls.login("admin", "admin123")
        # ToDo: set converter to calibre-convert, setup email server


    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin','admin123')

    # Set excecutable to wrong exe and start convert
    # set excecutable not existing and start convert
    # set excecutable non excecutable and start convert
    def test_convert_wrong_excecutable(self):
        pass

    # deactivate converter and check send to kindle and convert are not visible anymore
    def test_convert_deactivate(self):
        pass

    # set parameters for convert and start conversion
    def test_convert_parameter(self):
        pass

    # convert everything to everything
    # start conversion of azw3 -> mobi
    # start conversion of mobi -> azw3
    # start conversion of epub -> pdf
    # start conversion of epub -> txt
    # start conversion of epub -> fb2
    # start conversion of epub -> lit
    # start conversion of epub -> html
    # start conversion of epub -> rtf
    # start conversion of epub -> odt
    # create user
    # logout
    # check conversion result for non admin user -> nothing visible
    # start conversion for non admin user
    # check conversion result for non admin user -> own conversion visible without username
    # logout
    # login as admin
    # check conversion result conversion of other user visible
    def test_convert_only(self):
        pass

    # start conversion of epub -> mobi
    # wait for finished
    # start sending e-mail
    # check email received
    def test_email_only(self):
        pass

    # press send to kindle for not converted book
    # wait for finished
    # check email received
    def test_convert_email(self):
        pass

    # check visiblility kindle button for user with not set kindle-email
    def test_kindle_send_not_configured(self):
        pass

    # check behavior for failed email (size)
    # conversion okay, email failed
    def test_email_failed(self):
        pass

    # check conversion and email started and conversion failes
    def test_convert_failed_and_email(self):
        pass

    # check behavior for failed server setup (non-SSL)
    def test_smtp_setup_error(self):
        pass

    # check behavior for failed server setup (SSL)
    def test_SSL_smtp_setup_error(self):
        pass

    # check behavior for failed server setup (STARTTLS)
    def test_STARTTLS_smtp_setup_error(self):
        pass

