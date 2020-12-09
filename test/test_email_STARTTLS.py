#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import time

from helper_email_convert import AIOSMTPServer
import helper_email_convert
from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME
# from parameterized import parameterized_class
from helper_func import startup, wait_Email_received
from helper_func import save_logfiles


@unittest.skipIf(helper_email_convert.is_calibre_not_present(),"Skipping convert, calibre not found")
class TestSTARTTLS(unittest.TestCase, ui_class):
    p = None
    driver = None
    email_server = None

    @classmethod
    def setUpClass(cls):
        # start email server
        cls.email_server = AIOSMTPServer(
            hostname='127.0.0.1',
            port=1026,
            only_ssl=False,
            startSSL=True,
            certfile='files/server.crt',
            keyfile='files/server.key',
            timeout=10
        )
        cls.email_server.start()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB,
                                          'config_converterpath': helper_email_convert.calibre_path(),
                                          'config_ebookconverter': 'converter2'})

            cls.edit_user('admin', {'email': 'a5@b.com','kindle_mail': 'a1@b.com'})
            cls.setup_server(True, {'mail_server': '127.0.0.1', 'mail_port': '1026',
                                    'mail_use_ssl': 'SSL/TLS', 'mail_login': 'name@host.com', 'mail_password':'10234',
                                    'mail_from': 'name@host.com'})
        except:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        cls.email_server.stop()
        time.sleep(2)
        save_logfiles(cls.__name__)

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


    def test_STARTTLS_resend_password(self):
        self.create_user('paswd_resend', {'password': '123', 'email': 'a@b.com', 'edit_role': 1})
        self.setup_server(False, {'mail_use_ssl': 'STARTTLS'})
        self.assertTrue(self.edit_user(u'paswd_resend', { 'resend_password': 1}))
        self.edit_user('paswd_resend', element={})
        password_link = self.check_element_on_page((By.ID, "resend_password")).find_elements_by_tag_name("a")[0].get_attribute('href')
        user_id = password_link[password_link.rfind("/")+1:]
        self.logout()
        self.assertTrue(wait_Email_received(self.email_server.handler.check_email_received))
        user, passw = self.email_server.handler.extract_register_info()
        self.email_server.handler.reset_email_received()
        self.assertTrue(self.login(user, passw))
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('admin','admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.setup_server(False, {'mail_server': 'mail.example.org'})
        # check button disappears
        self.edit_user('paswd_resend', element={})
        self.assertFalse(self.check_element_on_page((By.ID, "resend_password")))
        self.driver.get('http://127.0.0.1:8083/admin/user/99')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.driver.get(password_link)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.driver.get(password_link[:password_link.rfind("/")] + '/99')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.edit_user('paswd_resend', {'delete': 1})
        self.setup_server(False, {'mail_server': '127.0.0.1'})
