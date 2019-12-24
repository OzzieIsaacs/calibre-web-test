#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
import os
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import shutil
from ui_helper import ui_class
from subproc_wrapper import process_open
from testconfig import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME
from email_convert_helper import Gevent_SMPTPServer, CredentialValidator
import email_convert_helper
from parameterized import parameterized_class
from func_helper import startup

@parameterized_class([
   { "py_version": u'/usr/bin/python'},
   { "py_version": u'/usr/bin/python3'},
],names=('Python27','Python36'))
@unittest.skipIf(email_convert_helper.is_calibre_not_present(),"Skipping convert, calibre not found")
class test_STARTTLS(unittest.TestCase, ui_class):
    p=None
    driver = None
    email_server = None

    @classmethod
    def setUpClass(cls):
        print('test_STARTTLS')
        # start email server
        cls.email_server = Gevent_SMPTPServer(
            ('127.0.0.1', 1026),
            only_ssl=False,
            certfile='SSL/ssl.crt',
            keyfile='SSL/ssl.key',
            credential_validator=CredentialValidator(),
            timeout=10
        )
        cls.email_server.start()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,
                                          'config_converterpath':email_convert_helper.calibre_path(),
                                          'config_ebookconverter':'converter2'})

            cls.edit_user('admin', {'email': 'a5@b.com','kindle_mail': 'a1@b.com'})
            cls.setup_server(True, {'mail_server':'127.0.0.1', 'mail_port':'1026',
                                'mail_use_ssl':'SSL/TLS','mail_login':'name@host.com','mail_password':'10234',
                                'mail_from':'name@host.com'})
        except:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.kill()
        cls.email_server.stop()
        time.sleep(2)

    # start sending e-mail
    # check email received
    def test_STARTTLS(self):
        task_len = len(self.check_tasks())
        self.setup_server(False, {'mail_use_ssl': 'STARTTLS'})
        details = self.get_book_details(7)
        details['kindlebtn'].click()
        conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        self.assertTrue(conv)
        conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 10:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Finished')


    # check behavior for failed server setup (SSL)
    def test_STARTTLS_SSL_setup_error(self):
        task_len = len(self.check_tasks())
        self.setup_server(False, {'mail_use_ssl':'SSL/TLS'})
        details = self.get_book_details(7)
        details['kindlebtn'].click()
        conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        self.assertTrue(conv)
        conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 10:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Failed')
