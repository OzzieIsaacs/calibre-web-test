#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium.webdriver.common.by import By
from config_test import TEST_DB, BOOT_TIME
from helper_func import startup
import unittest
import time
from helper_ui import ui_class
from helper_func import save_logfiles
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestSecurity(unittest.TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB}, env={"APP_MODE": "test"})
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        except Exception as e:
            print(e)
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_opds_limit(self):
        # request several times the same endpoint within one minute,
        for i in range (1, 4):
            r = requests.get('http://127.0.0.1:8083/opds', auth=('admin', '122'))
            self.assertEqual(401, r.status_code)
        # after x tries get 429 ?
        r = requests.get('http://127.0.0.1:8083/opds', auth=('admin', '122'))
        self.assertEqual(429, r.status_code)
        # try to login with right credentials -> not working
        r = requests.get('http://127.0.0.1:8083/opds', auth=('admin', 'admin123'))
        self.assertEqual(429, r.status_code)
        # wait one minute try to login with wrong credentials
        time.sleep(61)
        r = requests.get('http://127.0.0.1:8083/opds', auth=('admin', '122'))
        self.assertEqual(401, r.status_code)
        # login with right credentials
        r = requests.get('http://127.0.0.1:8083/opds', auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        # switch of limit, logout
        self.fill_basic_config({"config_ratelimiter":0})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        # try to login with wrong credentials several times, every time 401,
        for i in range (1, 5):
            r = requests.get('http://127.0.0.1:8083/opds', auth=('admin', '122'))
            self.assertEqual(401, r.status_code)
        # try to login with right credentials working instantaneously
        r = requests.get('http://127.0.0.1:8083/opds', auth=('admin', 'admin123'))
        self.assertEqual(200, r.status_code)
        # switch on limit, logout
        self.login('admin', 'admin123')
        self.fill_basic_config({"config_ratelimiter": 1})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_login_limit(self):
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
        # switch on limit
        self.fill_basic_config({"config_ratelimiter":1})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_register_limit(self):
        self.edit_user('admin', {'email': 'a5@b.com', 'kindle_mail': 'a1@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.setup_server(False, {'mail_server': '127.0.0.1', 'mail_port': '1025',
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
        pass
        # switch off, try empty password
        # only min length
        # only number
        # only lowercase letters
        # only uppercase letters
        # only special letters
        # everything
