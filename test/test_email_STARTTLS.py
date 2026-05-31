#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from base_test import ParallelTestCase, acquire_resource, release_resource
import time
import re
import requests
import socket
import datetime
import os

from helper_email_convert import AIOSMTPServer
import helper_email_convert
from config_test import base_path
from selenium.webdriver.common.by import By
from helper_func import startup, wait_Email_received


@unittest.skipIf(helper_email_convert.is_calibre_not_present(),"Skipping convert, calibre not found")
class TestSTARTTLS(ParallelTestCase):


    email_server = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # start email server
        cls.port = acquire_resource("port")
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} starting E-Mail Server")
        cls.email_server = AIOSMTPServer(
            hostname=socket.gethostname(),
            port=int(cls.port),
            only_ssl=False,
            startSSL=True,
            certfile=os.path.join(base_path,'files','server.crt'),
            keyfile=os.path.join(base_path,'files', 'server.key'),
            timeout=10
        )
        cls.email_server.start()

        try:
            startup(cls, cls.py_version, {'config_calibre_dir': cls.temp_dir,
                                          'config_binariesdir': helper_email_convert.calibre_path()},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir)
            cls.edit_user('admin', {'email': 'a5@b.com','kindle_mail': 'a1@b.com'})
            cls.setup_server(True, {'mail_server': socket.gethostname(), 'mail_port': cls.port,
                                    'mail_use_ssl': 'SSL/TLS', 'mail_login': 'name@host.com', 'mail_password_e':'10234',
                                    'mail_from': 'name@host.com'})
        except:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.email_server.stop()
        release_resource("port", cls.port)
        super().tearDownClass()

    # start sending e-mail
    # check email received
    def test_STARTTLS(self):
        self.setup_server(False, {'mail_use_ssl': 'STARTTLS'})
        password = self.check_element_on_page((By.ID, "mail_password_e"))
        self.assertEqual("", password.text)
        time.sleep(2)
        tasks = self.check_tasks()
        details = self.get_book_details(7)
        details['kindlebtn'].click()
        conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        self.assertTrue(conv)
        conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        task_len, ret = self.wait_tasks(tasks, 1)
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
        self.driver.get('http://127.0.0.1:{}/admin/user/99'.format(self.worker_port))
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        r = requests.session()
        login_page = r.get('http://127.0.0.1:{}/login'.format(self.worker_port))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': "admin", 'password': "admin123", 'submit': "", 'next': "/", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:{}/login'.format(self.worker_port), data=payload)
        link = r.get('http://127.0.0.1:{}/admin/view'.format(self.worker_port))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', link.text)
        payload = {"csrf_token": token.group(1)}
        request = r.post('http://127.0.0.1:{}'.format(self.worker_port) + password_link, data=payload)
        # self.driver.get(password_link)
        self.assertTrue("flash_danger" in request.text)
        #self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        request = r.post('http://127.0.0.1:{}'.format(self.worker_port) + password_link[:password_link.rfind("/")] + '/99', data=payload)
        # self.driver.get()
        self.assertTrue("flash_danger" in request.text)
        r.close()
        # self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.edit_user('paswd_resend', {'delete': 1})
        self.setup_server(False, {'mail_server': '127.0.0.1'})
