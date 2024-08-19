#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from selenium.webdriver.common.by import By
from config_test import TEST_DB, BOOT_TIME, CALIBRE_WEB_PATH
from helper_func import startup
import unittest
import time
from helper_ui import ui_class
from helper_func import save_logfiles, add_hidden_dependency, remove_dependency
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from helper_redis import Redis as redis_server

RESOURCES = {'ports': 1}

PORTS = ['8083',"1029"]
INDEX = ""


class TestSecurity(unittest.TestCase, ui_class):
    p = None
    driver = None
    hidden_dependencys = ["redis"]

    @classmethod
    def setUpClass(cls):
        add_hidden_dependency(cls.hidden_dependencys, cls.__name__)
        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB}, port=PORTS[0],
                    index=INDEX, env={"APP_MODE": "test"})
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        except Exception as e:
            print(e)
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        remove_dependency(cls.hidden_dependencys)
        cls.driver.get("http://127.0.0.1:" + PORTS[0])
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_opds_limit(self):
        # request several times the same endpoint within one minute,
        for i in range (1, 4):
            r = requests.get('http://127.0.0.1:{}/opds'.format(PORTS[0]), auth=('admin', '122'))
            self.assertEqual(401, r.status_code)
        # after x tries get 429 ?
        r = requests.get('http://127.0.0.1:{}/opds'.format(PORTS[0]), auth=('admin', '122'))
        self.assertEqual(429, r.status_code)
        # try to login with right credentials -> not working
        r = requests.get('http://127.0.0.1:{}/opds'.format(PORTS[0]), auth=('admin', 'admin123'))
        self.assertEqual(429, r.status_code)
        # wait one minute try to login with wrong credentials
        time.sleep(61)
        r = requests.get('http://127.0.0.1:{}/opds'.format(PORTS[0]), auth=('admin', '122'))
        self.assertEqual(401, r.status_code)
        # login with right credentials
        r = requests.get('http://127.0.0.1:{}/opds'.format(PORTS[0]), auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        # switch of limit, logout
        self.fill_basic_config({"config_ratelimiter":0})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        # try to login with wrong credentials several times, every time 401,
        for i in range (1, 5):
            r = requests.get('http://127.0.0.1:{}/opds'.format(PORTS[0]), auth=('admin', '122'))
            self.assertEqual(401, r.status_code)
        # try to login with right credentials working instantaneously
        r = requests.get('http://127.0.0.1:{}/opds'.format(PORTS[0]), auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        # switch on limit, logout
        self.login('admin', 'admin123')
        self.fill_basic_config({"config_ratelimiter": 1})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_redis_backend(self):
        self.restart_calibre_web()
        time.sleep(3)
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, 'calibre-web.log'), 'r') as logfile:
            data = logfile.readlines()
        self.assertTrue(any('Using the in-memory storage for tracking rate limits' in line for line in data[-15:]))
        server = redis_server()
        server.start()
        self.fill_basic_config({"config_limiter_uri": "redis://localhost:6379"})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page("nav_new")
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, 'calibre-web.log'), 'r') as logfile:
            data = logfile.readlines()
        self.assertFalse(any('Using the in-memory storage for tracking rate limits' in line for line in data[-15:]))
        self.fill_basic_config({"config_limiter_uri": ""})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        server.stop()

    def test_login_limit(self):
        self.create_user('second_user', {'password': '123AbC*!', 'email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.logout()
        # request several times the same endpoint within one minute,
        for i in range(1, 4):
            self.login("admin", "123")
            error = self.check_element_on_page((By.ID, "flash_danger"))
            self.assertTrue(error)
            self.assertTrue("Username" in error.text)
        # after x tries get 429 ?
        self.login("admin", "123")
        error = self.check_element_on_page((By.ID, "flash_danger"))
        self.assertTrue(error)
        self.assertTrue("wait" in error.text)
        # try to login with right credentials -> not working
        self.login("admin", "admin123")
        error = self.check_element_on_page((By.ID, "flash_danger"))
        self.assertTrue(error)
        self.assertTrue("wait" in error.text)
        # try to log in as differnt user, should work
        self.assertTrue(self.login("second_user", '123AbC*!'))
        self.logout()
        # wait one minute try to login with wrong credentials -> 401 wrong login name
        time.sleep(61)
        # login with right credentials
        self.login("admin", "admin123")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # switch of limit, logout
        self.fill_basic_config({"config_ratelimiter":0})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        # try to login with wrong credentials several times, every time wrong login name
        for i in range(1, 4):
            self.login("admin", "123")
            error = self.check_element_on_page((By.ID, "flash_danger"))
            self.assertTrue(error)
            self.assertTrue("Username" in error.text)
        # try to login with right credentials working instantaneously
        self.login("admin", "admin123")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('second_user', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # switch on limit
        self.fill_basic_config({"config_ratelimiter":1})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_register_limit(self):
        self.edit_user('admin', {'email': 'a5@b.com', 'kindle_mail': 'a1@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.setup_server(False, {'mail_server': '127.0.0.1', 'mail_port': PORTS[1],
                                 'mail_use_ssl': 'None', 'mail_login': 'name@host.com', 'mail_password_e': '10234',
                                 'mail_from': 'name@host.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_public_reg': 1})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        # request several times the same endpoint within one minute,
        # request several times the same endpoint within one minute, with different emails from same ip address
        for i in range(1, 4):
            self.assertEqual(u'flash_success', self.register('lulu{}'.format(i), 'hujh{}@de.de'.format(i)))
        # after x tries get 429
        self.assertEqual(u'flash_danger', self.register('lulu99', 'hujhgh@de.de'))
        # try to register another e-mail address, not working
        self.assertEqual(u'flash_danger', self.register('lulu990', 'hujhgh@de.de'))
        # wait one minute
        time.sleep(61)
        # try to register another address, working
        self.assertEqual(u'flash_success', self.register('lulu990', 'hujhgh@de.de'))
        # switch of limit, logout
        self.login("admin", "admin123")
        self.fill_basic_config({"config_ratelimiter":0})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        # try to register several times -> working all the time
        for i in range(1, 5):
            self.assertEqual(u'flash_success', self.register('luhulu{}'.format(i), 'hufjh{}@de.de'.format(i)))
        # switch on limit, logout
        self.login("admin", "admin123")
        self.fill_basic_config({"config_ratelimiter":1, 'config_public_reg':0})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_password_strength(self):
        # switch off, try empty password, not working
        self.fill_basic_config({"config_password_policy":0})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_user('test_pol_off',
                         {'email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.fill_basic_config({"config_password_policy": 1, "config_password_number": 0, "config_password_lower": 0,
                                "config_password_upper": 0, "config_password_special": 0,
                                "config_password_character": 0, "config_password_min_length": 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.fill_basic_config({"config_password_policy": 1, "config_password_number": 0, "config_password_lower": 0,
                                "config_password_upper": 0, "config_password_special": 0,
                                "config_password_character": 0, "config_password_min_length": 41})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.fill_basic_config({"config_password_policy": 1, "config_password_number": 0, "config_password_lower": 0,
                                "config_password_upper": 0, "config_password_special": 0,
                                "config_password_character": 0, "config_password_min_length": 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # only min length
        self.create_user('test_min_length',
                         {'password': 'a','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('test_min_length', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({"config_password_min_length": 4})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_user('test_min_length',
                         {'password': 'abc','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.create_user('test_min_length',
                         {'password': 'abcd','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('test_min_length', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # only number
        self.fill_basic_config({"config_password_number": 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_user('test_number',
                         {'password': 'abcd','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.create_user('test_number',
                         {'password': 'ab1d','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('test_number', {'delete': 1})
        # only lowercase letters
        self.fill_basic_config({"config_password_number": 0, "config_password_lower": 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_user('test_lower',
                         {'password': 'ABCE','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.create_user('test_lower',
                         {'password': 'PQWe','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('test_lower', {'delete': 1})
        # only uppercase letters
        self.fill_basic_config({"config_password_upper": 1, "config_password_lower": 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_user('test_upper',
                         {'password': 'abcd','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.create_user('test_upper',
                         {'password': 'aDer','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('test_upper', {'delete': 1})
        # only special letters
        self.fill_basic_config({"config_password_upper": 0, "config_password_special": 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_user('test_special',
                         {'password': 'abcd','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.create_user('test_special',
                         {'password': 'a￥er','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('test_special', {'delete': 1})
        # everything
        self.fill_basic_config({"config_password_number": 1, "config_password_lower": 1,
                                "config_password_upper": 1, "config_password_special": 1,
                                "config_password_min_length": 6})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_user('test_all',
                         {'password': 'aBe!f','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.create_user('test_all',
                         {'password': 'ave!fb','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.create_user('test_all',
                         {'password': 'aVeffb','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.create_user('test_all',
                         {'password': 'aV!f1b','email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com',
                          "passwd_role": 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login("test_all", "aV!f1b")
        self.change_visibility_me({"password": "aBe!f"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.change_visibility_me({"password": "ave!fb"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.change_visibility_me({"password": "aVef1b"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.change_visibility_me({"password": "aV!f1C"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login("admin", "admin123")
        self.edit_user('test_all', {"password": "aBe!f"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.edit_user('test_all', {"password": "ave!fb"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.edit_user('test_all', {"password": "aVef1b"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.edit_user('test_all', {"password": "aV!f1D"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('test_all', {'delete': 1})
        self.fill_basic_config({"config_password_min_length": 8})

