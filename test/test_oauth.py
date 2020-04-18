# -*- coding: utf-8 -*-

import unittest
import time
from helper_ui import ui_class
from testconfig import TEST_DB, BOOT_TIME
from helper_func import startup, debug_startup, add_dependency, remove_dependency
from selenium.webdriver.common.by import By

class test_OAuth_login(unittest.TestCase, ui_class):

    p=None
    driver = None
    kobo_adress = None
    dep_line = ["flask-dance", "sqlalchemy-utils"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dep_line, cls.__name__)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB}, env=None)
        except Exception as e:
            cls.driver.quit()
            cls.p.terminate()

    @classmethod
    def tearDownClass(cls):
        cls.stop_calibre_web()
        cls.p.terminate()
        cls.driver.quit()
        # close the browser window and stop calibre-web
        remove_dependency(cls.dep_line)


    def test_visible_oauth(self):
        # set to default
        self.fill_basic_config({'config_login_type':'Use OAuth'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # enable github oauth
        self.fill_basic_config({'config_1_oauth_client_id': '1234','config_1_oauth_client_secret':'5678' })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # check link button visible
        self.goto_page('user_setup')
        self.assertTrue(self.check_element_on_page((By.ID, "config_1_oauth")))
        # logout
        self.logout()
        # check github button visible, google invisible
        self.assertTrue(self.check_element_on_page((By.CLASS_NAME, "github")))
        self.assertFalse(self.check_element_on_page((By.CLASS_NAME, "google")))
        # login
        self.login('admin','admin123')
        # enable additionally google oauth
        self.fill_basic_config({'config_2_oauth_client_id': '1234', 'config_2_oauth_client_secret': '5678'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # Check link button visible
        self.goto_page('user_setup')
        self.assertTrue(self.check_element_on_page((By.ID, "config_2_oauth")))
        # logout
        self.logout()
        # check both logos visible
        self.assertTrue(self.check_element_on_page((By.CLASS_NAME, "github")))
        self.assertTrue(self.check_element_on_page((By.CLASS_NAME, "google")))
        # login
        self.login('admin', 'admin123')
        self.fill_basic_config({'config_1_oauth_client_id': '','config_1_oauth_client_secret':'' })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # Check google link button invisible
        self.goto_page('user_setup')
        self.assertTrue(self.check_element_on_page((By.ID, "config_2_oauth")))
        # deactivate both oauths again
        self.fill_basic_config({'config_2_oauth_client_id': '','config_2_oauth_client_secret':'' })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # open settings
        self.driver.find_elements_by_class_name("accordion-toggle")[3].click()
        # check all 4 fields are empty
        self.assertEqual('', self.check_element_on_page((By.ID, "config_1_oauth_client_id")).get_attribute('value'))
        self.assertEqual('', self.check_element_on_page((By.ID, "config_1_oauth_client_secret")).get_attribute('value'))
        self.assertEqual('', self.check_element_on_page((By.ID, "config_2_oauth_client_id")).get_attribute('value'))
        self.assertEqual('', self.check_element_on_page((By.ID, "config_2_oauth_client_secret")).get_attribute('value'))


    def test_oauth_about(self):
        self.assertTrue(self.goto_page('nav_about'))

