#!/usr/bin/env python
# -*- coding: utf-8 -*-

from helper_email_convert import AIOSMTPServer
import helper_email_convert
import unittest
import os
import re
import sys
from selenium.webdriver.common.by import By
import time
from helper_ui import ui_class
from testconfig import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME

from parameterized import parameterized_class
from helper_func import startup

'''@parameterized_class([
   { "py_version": u'/usr/bin/python','LOG_LEVEL':'DEBUG'},
   { "py_version": u'/usr/bin/python3','LOG_LEVEL':'DEBUG'},
],names=('Python27','Python36'))'''
@unittest.skipIf(helper_email_convert.is_calibre_not_present(),"Skipping convert, calibre not found")
class test_SSL(unittest.TestCase, ui_class):
    p=None
    driver = None
    email_server = None
    # py_version = 'python3'
    LOG_LEVEL = 'DEBUG'

    @classmethod
    def setUpClass(cls):

        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log'))
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log.1'))
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log.2'))
        except:
            pass

        # start email server
        cls.email_server = AIOSMTPServer(
            hostname='127.0.0.1',port=1027,
            only_ssl=True,
            certfile='SSL/ssl.crt',
            keyfile='SSL/ssl.key',
            timeout = 10
        )

        cls.email_server.start()

        startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,
                                      'config_converterpath':helper_email_convert.calibre_path(),
                                      'config_ebookconverter':'converter2',
                                      'config_log_level':cls.LOG_LEVEL})

        cls.edit_user('admin', {'email': 'a5@b.com','kindle_mail': 'a1@b.com'})
        cls.setup_server(False, {'mail_server':'127.0.0.1', 'mail_port':'1027',
                            'mail_use_ssl':'SSL/TLS','mail_login':'name@host.com','mail_password':'10234',
                            'mail_from':'name@host.com'})


    @classmethod
    def tearDownClass(cls):
        cls.stop_calibre_web()
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
    @unittest.skipIf(sys.version_info < (3, 7), "AsyncIO has no ssl handshake timeout")
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
    @unittest.skipIf(sys.version_info < (3, 7), "AsyncIO has no ssl handshake timeout")
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
        time.sleep(5)
        with open(os.path.join(CALIBRE_WEB_PATH,'calibre-web.log'),'r') as logfile:
            data = logfile.read()
        self.assertTrue(len(re.findall('Subject: Calibre-Web test e-mail',data)),"Email logging not working")

