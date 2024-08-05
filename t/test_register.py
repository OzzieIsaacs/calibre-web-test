#!/usr/bin/env python
# -*- coding: utf-8 -*-

from helper_email_convert import AIOSMTPServer
from selenium.webdriver.common.by import By
from config_test import TEST_DB
from helper_func import startup, wait_Email_received
# from parameterized import parameterized_class
import unittest
import re
from helper_ui import ui_class
import time
from helper_func import save_logfiles
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestRegister(unittest.TestCase, ui_class):
    p = None
    driver = None
    # py_version = u'/usr/bin/python3'

    @classmethod
    def setUpClass(cls):
        cls.email_server = AIOSMTPServer(
            hostname='127.0.0.1',port=1025,
            only_ssl=False,
            timeout=10
        )
        cls.email_server.start()

        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,
                                          'config_public_reg': 1}, env={"APP_MODE": "test"})
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
            cls.edit_user('admin', {'email': 'a5@b.com','kindle_mail': 'a1@b.com'})
            cls.setup_server(False, {'mail_server':'127.0.0.1', 'mail_port':'1025',
                                'mail_use_ssl':'None','mail_login':'name@host.com','mail_password_e':'10234',
                                'mail_from':'name@host.com'})

        except Exception as e:
            print(e)
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.login('admin', 'admin123')
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        cls.email_server.stop()
        save_logfiles(cls, cls.__name__)

    def tearDown(self):
        self.email_server.handler.reset_email_received()
        if self.check_user_logged_in('admin'):
            self.logout()

    # no emailserver configure, email server not reachable
    def test_register_no_server(self):
        if not self.check_user_logged_in('admin', True):
            self.login('admin', 'admin123')
            self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.setup_server(False, {'mail_server':'mail.example.org'})
        self.logout()
        self.assertEqual(u'flash_danger', self.register(u'noserver', 'alo@de.org'))
        self.goto_page('unlogged_login')
        self.login('admin', 'admin123')
        self.setup_server(False, {'mail_server': '127.0.0.1'})

    def test_limit_domain(self):
        if not self.check_user_logged_in('admin', True):
            self.login('admin', 'admin123')
            self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('mail_server')
        a_domains = self.list_domains(allow=True)
        self.assertEqual(a_domains[0]['domain'],'*.*')
        self.delete_domains(a_domains[0]['id'], accept=False, allow=True)
        a_domains = self.list_domains(allow=True)
        self.assertEqual(a_domains[0]['domain'], '*.*')
        self.delete_domains(a_domains[0]['id'], accept=True, allow=True)
        a_domains = self.list_domains(allow=True)
        self.assertEqual(a_domains[0]['domain'], '*.*')
        self.edit_domains(a_domains[0]['id'], '*.com', accept=False, allow=True)
        a_domains = self.list_domains(allow=True)
        self.assertEqual(a_domains[0]['domain'], '*.*')
        self.edit_domains(a_domains[0]['id'], '*.com', accept=True, allow=True)
        a_domains = self.list_domains(allow=True)
        self.assertEqual(a_domains[0]['domain'], '*.com')
        self.logout()
        self.assertEqual(self.register('nocom', 'alfa@com.de'), 'flash_danger')
        self.assertEqual(self.register('nocom', 'alfa@com.com'),'flash_success')
        self.login('admin','admin123')
        self.goto_page('mail_server')
        d_domains = self.list_domains(allow=False)
        self.assertEqual(len(d_domains), 0)
        self.add_domains('dod@google.com', allow=False)
        d_domains = self.list_domains(allow=False)
        self.assertEqual(d_domains[0]['domain'], 'dod@google.com')
        self.delete_domains(d_domains[0]['id'], accept=False, allow=True)
        d_domains = self.list_domains(allow=False)
        self.assertEqual(d_domains[0]['domain'], 'dod@google.com')
        self.delete_domains(d_domains[0]['id'], accept=True, allow=True)
        d_domains = self.list_domains(allow=False)
        self.assertEqual(len(d_domains), 0)
        self.add_domains('dod@g?ogle.com', allow=False)
        d_domains = self.list_domains(allow=False)
        self.assertEqual(d_domains[0]['domain'], 'dod@g?ogle.com')
        self.edit_domains(d_domains[0]['id'], '*dod@g?ogle.c*', accept=True, allow=True)
        d_domains = self.list_domains(allow=False)
        self.assertEqual(d_domains[0]['domain'], '*dod@g?ogle.c*')
        self.logout()
        self.assertEqual(self.register('nocom1', 'a.dod@google.com'),'flash_danger')
        self.assertEqual(self.register('nocom2', 'doda@google.cum'), 'flash_danger')
        self.assertEqual(self.register('nocom3', 'dod@koogle.com'), 'flash_success')
        #cleanup
        self.login('admin','admin123')
        self.goto_page('mail_server')
        d_domains = self.list_domains(allow=False)
        self.delete_domains(d_domains[0]['id'], accept=True, allow=False)
        a_domains = self.list_domains(allow=True)
        self.delete_domains(a_domains[0]['id'], accept=True, allow=True)


    # register user, extract password, login, check rights
    def test_registering_user(self):
        if self.check_user_logged_in('admin', True):
            self.logout()
        self.assertEqual(u'flash_success',self.register(u'u1', 'huj@de.de'))
        self.assertTrue(wait_Email_received(self.email_server.handler.check_email_received))
        user, passw = self.email_server.handler.extract_register_info()
        self.email_server.handler.reset_email_received()
        self.assertTrue(self.login(user, passw))
        self.logout()
        self.assertEqual(u'flash_success',self.register(u'ü执1', u'huij@de.de'))
        self.assertTrue(wait_Email_received(self.email_server.handler.check_email_received))
        user, passw = self.email_server.handler.extract_register_info()
        self.assertTrue(self.login(user, passw))
        self.logout()
        self.assertEqual(u'flash_danger',self.register(u'guest','hufdj@de.de'))
        self.assertEqual(u'flash_danger', self.register(u' guest ', 'hufdj@de.de'))

    # double username, emailadress, capital letters, lowercase characters
    def test_registering_user_fail(self):
        if self.check_user_logged_in('admin',True):
            self.logout()
        self.email_server.handler.reset_email_received()
        self.assertEqual(u'flash_success',self.register(u'udouble', 'huj@de.com'))
        self.assertTrue(wait_Email_received(self.email_server.handler.check_email_received))
        self.email_server.handler.reset_email_received()
        self.assertEqual(u'flash_danger',self.register(u'udouble', 'huj@de.cem'))
        self.email_server.handler.reset_email_received()
        self.assertEqual(u'flash_danger',self.register(u'udoubl', 'huj@de.com'))
        self.email_server.handler.reset_email_received()
        self.assertEqual(u'flash_danger',self.register(u'UdoUble', 'huo@de.com'))
        self.email_server.handler.reset_email_received()
        self.assertEqual(u'flash_danger',self.register(u'UdoUble', 'huJ@dE.com'))
        self.email_server.handler.reset_email_received()
        self.assertEqual(u'flash_danger',self.register(u'UdoUble', 'huJ@de'))

    # user registers, user changes password, user forgets password, admin resents password for user
    def test_user_change_password(self):
        if self.check_user_logged_in('admin',True):
            self.logout()
        self.goto_page('unlogged_login')
        self.login('admin','admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'passwd_role': 1})
        self.logout()
        self.assertEqual(u'flash_success',self.register(u'upasswd', 'passwd@de.com'))
        self.assertTrue(wait_Email_received(self.email_server.handler.check_email_received))
        user, passw = self.email_server.handler.extract_register_info()
        self.email_server.handler.reset_email_received()
        self.assertTrue(self.login(user, passw))
        self.assertTrue(self.change_current_user_password('new_passwd123AbC*!'))
        self.logout()
        self.assertTrue(self.login(user, 'new_passwd123AbC*!'))
        self.logout()
        self.assertTrue(self.forgot_password(u'upasswd'))
        self.assertTrue(wait_Email_received(self.email_server.handler.check_email_received))
        user, passw = self.email_server.handler.extract_register_info()
        self.email_server.handler.reset_email_received()
        self.assertTrue(self.login(user, passw))
        self.logout()
        # admin resents password
        self.login('admin', 'admin123')
        self.assertTrue(self.edit_user(u'upasswd', { 'resend_password': 1}))
        self.logout()
        self.assertTrue(wait_Email_received(self.email_server.handler.check_email_received))
        user, passw = self.email_server.handler.extract_register_info()
        self.email_server.handler.reset_email_received()
        self.assertTrue(self.login(user, passw))
        self.logout()

    def test_forgot_password(self):
        if not self.check_user_logged_in('admin', True):
            self.login('admin', 'admin123')
            self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.email_server.handler.reset_email_received()
        self.create_user('forget', {'passwd_role': 0, 'password': '123AbC*!', 'email': 'alfa@b.com'})
        self.logout()
        self.assertTrue(self.forgot_password('forget'))
        time.sleep(3)
        __, passw = self.email_server.handler.extract_register_info()
        self.email_server.handler.reset_email_received()
        self.login('forget', passw)
        time.sleep(1)
        self.assertTrue(self.check_user_logged_in('forget', noCompare=True))
        self.assertFalse(self.forgot_password('forgot'))

    # register user, extract password, login, check rights
    def test_registering_only_email(self):
        if not self.check_user_logged_in('admin',True):
            self.login('admin', 'admin123')
            self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_register_email': 1})
        self.logout()
        self.assertEqual(u'flash_success', self.register(u'', 'hujh@de.de'))
        self.assertTrue(wait_Email_received(self.email_server.handler.check_email_received))
        user, passw = self.email_server.handler.extract_register_info()
        self.assertEqual('hujh@de.de', user)
        self.email_server.handler.reset_email_received()
        self.assertTrue(self.login(user, passw))
        self.logout()
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_register_email': 0})
        self.logout()

    def test_illegal_email(self):
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'name': 'user0 negativ', 'email': '1234', "csrf_token": token.group(1)}
        resp = r.post('http://127.0.0.1:8083/register', data=payload)
        self.assertTrue("flash_danger" in resp.text)
        payload = {'email': '1234@gr.de', "csrf_token": token.group(1)}
        resp = r.post('http://127.0.0.1:8083/register', data=payload)
        self.assertTrue("flash_danger" in resp.text)
        payload = {'name': 'user0 negativ', "csrf_token": token.group(1)}
        resp = r.post('http://127.0.0.1:8083/register', data=payload)
        self.assertTrue("flash_danger" in resp.text)
        payload = {'name': '/etc/./passwd', 'email': '/etc/./passwd', "csrf_token": token.group(1)}
        resp = r.post('http://127.0.0.1:8083/register', data=payload)
        self.assertTrue("flash_danger" in resp.text)
        payload = {"name": "abc123@mycom.com'\"[]()", 'email': "abc123@mycom.com'\"[]()", "csrf_token": token.group(1)}
        resp = r.post('http://127.0.0.1:8083/register', data=payload)
        self.assertTrue("flash_danger" in resp.text)
        payload = {"name": "abc123@mycom.com anD 1028=1028", 'email': "abc123@mycom.com anD 1028=1028", "csrf_token": token.group(1)}
        resp = r.post('http://127.0.0.1:8083/register', data=payload)
        self.assertTrue("flash_danger" in resp.text)
        payload = {"name": "abc123@myc@om.com", 'email': "abc123@myc@om.com", "csrf_token": token.group(1)}
        resp = r.post('http://127.0.0.1:8083/register', data=payload)
        self.assertTrue("flash_danger" in resp.text)
        payload = {"name": "1234456", 'email': "1@2.3", "csrf_token": token.group(1)}
        resp = r.post('http://127.0.0.1:8083/register', data=payload)
        self.assertTrue("flash_success" in resp.text)
        payload = {"name": "9dsfaf", 'email': "ü执1@ü执1.3", "csrf_token": token.group(1)}
        resp = r.post('http://127.0.0.1:8083/register', data=payload)
        self.assertTrue("flash_success" in resp.text)



