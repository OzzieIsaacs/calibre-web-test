#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium.webdriver.common.by import By
from config_test import TEST_DB
from helper_func import startup
import unittest
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
        cls.login('admin', 'admin123')
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_opds_limit(self):
        # request several times the same endpoint within one minute,
        # after x tries get 429 ?
        # try to login with right credentials -> not working
        # wait one minute try to login with wrong credentials
        # login with right credentials
        # switch of limit, logout
        # try to login with wrong credentials several times, every time 401,
        # try to login with right credentials working instantaneously
        # switch on limit, logout
        for i in range (1, 10):
            r = requests.get('http://127.0.0.1:8083/opds', auth=('admin', '122'))
            self.assertEqual(401, r.status_code)

    def test_login_limit(self):
        # request several times the same endpoint within one minute,
        # after x tries get 429 ?
        # try to login with right credentials -> not working
        # wait one minute try to login with wrong credentials -> 401 wrong login name
        # login with right credentials
        # switch of limit, logout
        # try to login with wrong credentials several times, every time wrong login name
        # try to login with right credentials working instantaneously
        # switch on limit, logout
        pass

    def test_register_limit(self):
        # request several times the same endpoint within one minute, with different emails from same ip address
        # after x tries get 429
        # try to register another e-mail address, not working
        # wait one minute
        # try to register another address, working
        # switch of limit, logout
        # try to register several times -> working all the time
        # switch on limit, logout
        pass

    def test_kobo_limit(self):
        pass
        # activate kobo login for user admin
        # request several times the same endpoint with different hashes within one minute, from same ip address
        # after x tries get 429
        # try to use working endpoint not working
        # wait one minute
        # access wrong endpoint again -> error 401
        # access right endpoint -> working
        # switch of limit, logout
        # request several times the same endpoint with different hashes within one minute, from same ip address -> working all the time
        # switch on limit, logout
        pass

    def test_password_strength(self):
        pass
        # switch off, try empty password
        # only min length
        # only number
        # only lowercase letters
        # only uppercase letters
        # only special letters
        # everything
