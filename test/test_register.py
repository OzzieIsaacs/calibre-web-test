#!/usr/bin/env python
# -*- coding: utf-8 -*-

from email_convert_helper import Gevent_SMPTPServer, CredentialValidator
# import email_convert_helper
from testconfig import TEST_DB
from func_helper import startup, wait_Email_received
from parameterized import parameterized_class
import unittest
from ui_helper import ui_class


'''@parameterized_class([
   { "py_version": u'/usr/bin/python'},
   { "py_version": u'/usr/bin/python3'},
],names=('Python27','Python36'))'''
class test_register(unittest.TestCase, ui_class):
    p=None
    driver = None
    # py_version = u'/usr/bin/python3'

    @classmethod
    def setUpClass(cls):
        cls.email_server = Gevent_SMPTPServer(
            ('127.0.0.1', 1025),
            only_ssl=False,
            credential_validator=CredentialValidator(),
            timeout=10
        )
        cls.email_server.start()

        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,
                                          'config_public_reg': 1})
            cls.edit_user('admin', {'email': 'a5@b.com','kindle_mail': 'a1@b.com'})
            cls.setup_server(False, {'mail_server':'127.0.0.1', 'mail_port':'1025',
                                'mail_use_ssl':'None','mail_login':'name@host.com','mail_password':'10234',
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

    def tearDown(self):
        self.email_server.reset_email_received()
        if self.check_user_logged_in('admin'):
            self.logout()

    # no emailserver configure, email server not reachable
    def test_register_no_server(self):
        if not self.check_user_logged_in('admin', True):
            self.login('admin', 'admin123')
        self.setup_server(False, {'mail_server':'mail.example.org'})
        self.logout()
        self.assertEqual(u'flash_alert',self.register(u'noserver','alo@de.org'))
        self.goto_page('unlogged_login')
        self.login('admin', 'admin123')
        self.setup_server(False, {'mail_server': '127.0.0.1'})

    @unittest.skip("Not Implemented")
    def test_limit_domain(self):
        pass

    @unittest.skip("Not Implemented")
    def test_limit_domain(self):
        pass

    # register user, extract password, login, check rights
    def test_registering_user(self):
        if self.check_user_logged_in('admin',True):
            self.logout()
        self.assertEqual(u'flash_success',self.register(u'u1','huj@de.de'))
        self.assertTrue(wait_Email_received(self.email_server.check_email_received))
        user, passw = self.email_server.extract_register_info()
        self.email_server.reset_email_received()
        self.assertTrue(self.login(user, passw))
        self.logout()
        self.assertEqual(u'flash_success',self.register(u'ü执1',u'huij@de.de'))
        self.assertTrue(wait_Email_received(self.email_server.check_email_received))
        user, passw = self.email_server.extract_register_info()
        self.assertTrue(self.login(user, passw))
        self.logout()

    # double username, emailadress, capital letters, lowercase characters
    def test_registering_user_fail(self):
        if self.check_user_logged_in('admin',True):
            self.logout()
        self.email_server.reset_email_received()
        self.assertEqual(u'flash_success',self.register(u'udouble','huj@de.com'))
        self.assertTrue(wait_Email_received(self.email_server.check_email_received))
        self.email_server.reset_email_received()
        self.assertEqual(u'flash_alert',self.register(u'udouble','huj@de.cem'))
        self.email_server.reset_email_received()
        self.assertEqual(u'flash_alert',self.register(u'udoubl','huj@de.com'))
        self.email_server.reset_email_received()
        self.assertEqual(u'flash_alert',self.register(u'UdoUble','huo@de.com'))
        self.email_server.reset_email_received()
        self.assertEqual(u'flash_alert',self.register(u'UdoUble','huJ@dE.com'))
        self.email_server.reset_email_received()
        self.assertEqual(u'flash_alert',self.register(u'UdoUble','huJ@de'))

    # user registers, user changes password, user forgets password, admin resents password for user
    def test_user_change_password(self):
        if self.check_user_logged_in('admin',True):
            self.logout()
        self.goto_page('unlogged_login')
        self.login('admin','admin123')
        self.fill_view_config({'passwd_role': 1})
        self.logout()
        self.assertEqual(u'flash_success',self.register(u'upasswd','passwd@de.com'))
        self.assertTrue(wait_Email_received(self.email_server.check_email_received))
        user, passw = self.email_server.extract_register_info()
        self.email_server.reset_email_received()
        self.assertTrue(self.login(user, passw))
        self.assertTrue(self.change_current_user_password('new_passwd'))
        self.logout()
        self.assertTrue(self.login(user, 'new_passwd'))
        self.logout()
        self.assertTrue(self.forgot_password(u'upasswd'))
        self.assertTrue(wait_Email_received(self.email_server.check_email_received))
        user, passw = self.email_server.extract_register_info()
        self.email_server.reset_email_received()
        self.assertTrue(self.login(user, passw))
        self.logout()
        # admin resents password
        self.login('admin', 'admin123')
        self.assertTrue(self.edit_user(u'upasswd', { 'resend_password':1}))
        self.logout()
        self.assertTrue(wait_Email_received(self.email_server.check_email_received))
        user, passw = self.email_server.extract_register_info()
        self.email_server.reset_email_received()
        self.assertTrue(self.login(user, passw))
        self.logout()
