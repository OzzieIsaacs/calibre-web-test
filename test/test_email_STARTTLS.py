#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import time
import re
import requests
import socket

from helper_email_convert import AIOSMTPServer
import helper_email_convert
from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME
# from parameterized import parameterized_class
from helper_func import startup, wait_Email_received
from helper_func import save_logfiles


RESOURCES = {'ports': 2}

PORTS = ['8083', '1026']
INDEX = ""


@unittest.skipIf(helper_email_convert.is_calibre_not_present(),"Skipping convert, calibre not found")
class TestSTARTTLS(unittest.TestCase, ui_class):
    p = None
    driver = None
    email_server = None

    @classmethod
    def setUpClass(cls):
        # start email server
        cls.email_server = AIOSMTPServer(
            hostname=socket.gethostname(),
            port=int(PORTS[1]),
            only_ssl=False,
            startSSL=True,
            certfile='files/server.crt',
            keyfile='files/server.key',
            timeout=10
        )
        cls.email_server.start()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB,
                                          'config_binariesdir': helper_email_convert.calibre_path()},
                    port=PORTS[0], index=INDEX, env={"APP_MODE": "test"})

            cls.edit_user('admin', {'email': 'a5@b.com','kindle_mail': 'a1@b.com'})
            cls.setup_server(True, {'mail_server': socket.gethostname(), 'mail_port': PORTS[1],
                                    'mail_use_ssl': 'SSL/TLS', 'mail_login': 'name@host.com', 'mail_password_e':'10234',
                                    'mail_from': 'name@host.com'})
        except:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:" + PORTS[0])
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        cls.email_server.stop()
        time.sleep(2)
        save_logfiles(cls, cls.__name__)

    # start sending e-mail
    # check email received
    def test_STARTTLS(self):
        tasks = self.check_tasks()
        self.setup_server(False, {'mail_use_ssl': 'STARTTLS'})
        # self.goto_page('mail_server')
        password = self.check_element_on_page((By.ID, "mail_password_e"))
        self.assertEqual("", password.text)
        details = self.get_book_details(7)
        details['kindlebtn'].click()
        conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        self.assertTrue(conv)
        conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        task_len, ret = self.wait_tasks(tasks, 1)
        #i = 0
        #while i < 10:
        #    time.sleep(2)
        #    task_len, ret = self.check_tasks(tasks)
        #    if task_len == 1:
        #        if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
        #            break
        #    i += 1
        self.assertEqual(ret[-1]['result'], 'Finished')


    # check behavior for failed server setup (SSL)
    def test_STARTTLS_SSL_setup_error(self):
        tasks = self.check_tasks()
        self.setup_server(False, {'mail_use_ssl':'SSL/TLS'})
        details = self.get_book_details(7)
        details['kindlebtn'].click()
        conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        self.assertTrue(conv)
        conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        task_len, ret = self.wait_tasks(tasks, 1)
        #i = 0
        #while i < 10:
        #    time.sleep(2)
        #    task_len, ret = self.check_tasks(tasks)
        #    if task_len == 1:
        #        if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
        #            break
        #    i += 1
        self.assertEqual(ret[-1]['result'], 'Failed')


    def test_STARTTLS_resend_password(self):
        self.create_user('paswd_resend', {'password': '123AbC*!', 'email': 'a@b.com', 'edit_role': 1})
        self.setup_server(False, {'mail_use_ssl': 'STARTTLS'})
        self.assertTrue(self.edit_user(u'paswd_resend', { 'resend_password': 1}))
        self.edit_user('paswd_resend', element={})
        password_link = self.check_element_on_page((By.ID, "resend_password")).get_attribute('data-action')
        # user_id = password_link[password_link.rfind("/")+1:]
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
        self.driver.get('http://127.0.0.1:{}/admin/user/99'.format(PORTS[0]))
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        r = requests.session()
        login_page = r.get('http://127.0.0.1:{}/login'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': "admin", 'password': "admin123", 'submit': "", 'next': "/", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:{}/login'.format(PORTS[0]), data=payload)
        link = r.get('http://127.0.0.1:{}/admin/view'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', link.text)
        payload = {"csrf_token": token.group(1)}
        request = r.post('http://127.0.0.1:{}'.format(PORTS[0]) + password_link, data=payload)
        # self.driver.get(password_link)
        self.assertTrue("flash_danger" in request.text)
        #self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        request = r.post('http://127.0.0.1:{}'.format(PORTS[0]) + password_link[:password_link.rfind("/")] + '/99', data=payload)
        # self.driver.get()
        self.assertTrue("flash_danger" in request.text)
        r.close()
        # self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.edit_user('paswd_resend', {'delete': 1})
        self.setup_server(False, {'mail_server': '127.0.0.1'})
