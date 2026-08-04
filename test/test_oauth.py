#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base_test import ParallelTestCase

from selenium.webdriver.common.by import By
from helper_func import startup, wait_for_reboot


class TestOAuthLogin(ParallelTestCase):

    kobo_adress = None
    dependency = ["flask-dance", "sqlalchemy-utils"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir':cls.temp_dir},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir)
        except Exception as e:
            cls.log_class('setup failed')
            cls.driver.quit()
            cls.p.terminate()

    def test_visible_oauth(self):
        # set to default
        self.fill_basic_config({'config_login_type':'Use OAuth'})
        wait_for_reboot(f"http://127.0.0.1:{self.worker_port}")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # enable github oauth
        self.fill_basic_config({'config_1_oauth_client_id': '1234','config_1_oauth_client_secret':'5678' })
        wait_for_reboot(f"http://127.0.0.1:{self.worker_port}")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # check link button visible
        self.goto_page('user_setup')
        self.assertTrue(self.check_element_on_page((By.ID, "config_1_oauth")))
        self.navigate_to_user("admin")
        self.assertTrue(self.check_element_on_page((By.ID, "name")))
        self.assertFalse(self.check_element_on_page((By.ID, "config_1_oauth")))
        # logout
        self.logout()
        # check github button visible, google invisible
        self.assertTrue(self.check_element_on_page((By.CLASS_NAME, "github")))
        self.assertFalse(self.check_element_on_page((By.CLASS_NAME, "google")))
        # login
        self.login('admin','admin123')
        # enable additionally google oauth
        self.fill_basic_config({'config_2_oauth_client_id': '1234', 'config_2_oauth_client_secret': '5678'})
        wait_for_reboot(f"http://127.0.0.1:{self.worker_port}")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
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
        wait_for_reboot(f"http://127.0.0.1:{self.worker_port}")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # Check google link button invisible
        self.goto_page('user_setup')
        self.assertTrue(self.check_element_on_page((By.ID, "config_2_oauth")))
        # deactivate both oauths again
        self.fill_basic_config({'config_2_oauth_client_id': '','config_2_oauth_client_secret':'' })
        wait_for_reboot(f"http://127.0.0.1:{self.worker_port}")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # open settings
        self.driver.find_elements(By.CLASS_NAME, "accordion-toggle")[3].click()
        # check all 4 fields are empty
        self.assertEqual('', self.check_element_on_page((By.ID, "config_1_oauth_client_id")).get_attribute('value'))
        self.assertEqual('', self.check_element_on_page((By.ID, "config_1_oauth_client_secret")).get_attribute('value'))
        self.assertEqual('', self.check_element_on_page((By.ID, "config_2_oauth_client_id")).get_attribute('value'))
        self.assertEqual('', self.check_element_on_page((By.ID, "config_2_oauth_client_secret")).get_attribute('value'))


    def test_oauth_about(self):
        self.assertTrue(self.goto_page('nav_about'))
