#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
import os
import sys
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import shutil
from ui_helper import ui_class
from subproc_wrapper import process_open
from testconfig import CALIBRE_WEB_PATH, TEST_DB
from email_convert_helper import Gevent_SMPTPServer, CredentialValidator
import email_convert_helper
from parameterized import parameterized_class

@parameterized_class([
   { "py_version": u'python','LOG_LEVEL':'DEBUG'},
   { "py_version": u'python3','LOG_LEVEL':'DEBUG'},
],names=('Python27','Python36'))
@unittest.skipIf(email_convert_helper.is_calibre_not_present(),"Skipping convert, calibre not found")
class test_SSL(unittest.TestCase, ui_class):
    p=None
    driver = None
    email_server = None
    # py_version = 'python3'
    # LOG_LEVEL = 'DEBUG'

    @classmethod
    def setUpClass(cls):
        print('test_SSL')
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH,'app.db'))
        except:
            pass
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log'))
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log.1'))
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log.2'))
        except:
            pass
        shutil.rmtree(TEST_DB,ignore_errors=True)
        shutil.copytree('./Calibre_db', TEST_DB)
        cls.p = process_open([cls.py_version, os.path.join(CALIBRE_WEB_PATH,u'cps.py')],(1), sout=None)

        # start email server
        cls.email_server = Gevent_SMPTPServer(
            ('127.0.0.1', 1027),
            only_ssl=True,
            certfile='SSL/ssl.crt',
            keyfile='SSL/ssl.key',
            credential_validator=CredentialValidator(),
            timeout = 10
        )
        cls.email_server.start()

        # create a new Firefox session
        cls.driver = webdriver.Firefox()
        # time.sleep(15)
        cls.driver.implicitly_wait(5)
        print('Calibre-web started')

        cls.driver.maximize_window()

        # navigate to the application home page
        cls.driver.get("http://127.0.0.1:8083")

        # INFO: Crash on python3 and DEBUG output, where normal start works in python3
        # Wait for config screen to show up
        cls.fill_initial_config({'config_calibre_dir':TEST_DB, 'config_converterpath':email_convert_helper.calibre_path(),
                                 'config_ebookconverter':'converter2', 'config_log_level':cls.LOG_LEVEL})

        # wait for cw to reboot
        time.sleep(5)

        # Wait for config screen with login button to show up
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.NAME, "login")))
        login_button = cls.driver.find_element_by_name("login")
        login_button.click()

        # login
        cls.login("admin", "admin123")
        cls.edit_user('admin', {'email': 'a5@b.com','kindle_mail': 'a1@b.com'})
        cls.setup_server(False, {'mail_server':'127.0.0.1', 'mail_port':'1027',
                            'mail_use_ssl':'SSL/TLS','mail_login':'name@host.com','mail_password':'10234',
                            'mail_from':'name@host.com'})


    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        cls.email_server.stop()
        time.sleep(2)


    # start sending e-mail
    # check email received
    def test_SSL_only(self):
        task_len = len(self.check_tasks())
        self.setup_server(False, {'mail_use_ssl': 'SSL/TLS'})
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


    # check behavior for failed server setup (STARTTLS)
    def test_SSL_STARTTLS_setup_error(self):
        task_len = len(self.check_tasks())
        self.setup_server(False, {'mail_use_ssl':'STARTTLS'})
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

    # check behavior for failed server setup (NonSSL)
    def test_SSL_None_setup_error(self):
        task_len = len(self.check_tasks())
        self.setup_server(False, {'mail_use_ssl':'None'})
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
        self.assertEqual('Failed', ret[-1]['result'])

    # check if email traffic is logged to logfile
    def test_SSL_logging_email(self):
        self.setup_server(True, {'mail_use_ssl': 'SSL/TLS'})
        time.sleep(2)
        with open(os.path.join(CALIBRE_WEB_PATH,'calibre-web.log'),'r') as logfile:
            data = logfile.read()
        self.assertTrue(len(re.findall('Subject: Calibre-Web test e-mail',data)),"Email logging not working")

