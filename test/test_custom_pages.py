#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import time
import psutil
from unittest import skip
from selenium.webdriver.common.by import By

from helper_ui import ui_class
from config_test import TEST_DB, BOOT_TIME, CALIBRE_WEB_PATH
from helper_func import startup
from helper_func import save_logfiles


class TestCustomPages(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, env={"APP_MODE": "test"})
            cls.login("admin", "admin123")
        except Exception:
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

    def test_create_top_page(self):
        self.goto_page('pages_config')
        new_page_button = self.check_element_on_page((By.ID, "new_page"))
        self.assertTrue(new_page_button)
        # create new page
        new_page_button.click()
        title_input = self.check_element_on_page((By.ID, "title"))
        name_input = self.check_element_on_page((By.ID, "name"))
        content_input = self.check_element_on_page((By.ID, "content"))
        position_input = self.check_element_on_page((By.ID, "position"))
        self.assertTrue(title_input)
        self.assertTrue(name_input)
        self.assertTrue(content_input)
        self.assertTrue(position_input)
        title_input.text = "Test Title"
        name_input.text = "Test Top"
        content_input.text = "## Test Heading\n\nTest Content"
        position_input.value = "1"
        submit_button = self.check_element_on_page((By.ID, "page_submit"))
        self.assertTrue(submit_button)
        # submit new page
        submit_button.click()
        # check it was created
        test_page = self.check_element_on_page((By.ID, "nav_Test Top"))
        self.assertTrue(test_page)
        side_nav = self.check_element_on_page((By.ID, "scnd-nav"))
        self.assertTrue(side_nav)
        children = side_nav.find_elements(By.XPATH, "*")
        self.assertEqual(children[0].id, "nav_Test Top")

    def test_create_bottom_page(self):
        self.goto_page('pages_config')
        new_page_button = self.check_element_on_page((By.ID, "new_page"))
        self.assertTrue(new_page_button)
        # create new page
        new_page_button.click()
        title_input = self.check_element_on_page((By.ID, "title"))
        name_input = self.check_element_on_page((By.ID, "name"))
        content_input = self.check_element_on_page((By.ID, "content"))
        position_input = self.check_element_on_page((By.ID, "position"))
        self.assertTrue(title_input)
        self.assertTrue(name_input)
        self.assertTrue(content_input)
        self.assertTrue(position_input)
        title_input.text = "Test Title"
        name_input.text = "Test Bottom"
        content_input.text = "## Test Heading\n\nTest Content"
        position_input.value = "0"
        submit_button = self.check_element_on_page((By.ID, "page_submit"))
        self.assertTrue(submit_button)
        # submit new page
        submit_button.click()
        # check it was created
        test_page = self.check_element_on_page((By.ID, "nav_Test Bottom"))
        self.assertTrue(test_page)
        side_nav = self.check_element_on_page((By.ID, "scnd-nav"))
        self.assertTrue(side_nav)
        children = side_nav.find_elements(By.XPATH, "*")
        self.assertEqual(children[-1].id, "nav_Test Bottom")