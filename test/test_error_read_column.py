# -*- coding: utf-8 -*-

import unittest
import os

from selenium.webdriver.common.by import By
from helper_func import save_logfiles
import time
import requests
from helper_db import delete_cust_class
from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup, debug_startup
from helper_ui import RESTRICT_COL_USER

class TestErrorReadColumn(unittest.TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB})

        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        pass
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_invalid_custom_read_column(self):
        self.fill_view_config({'config_read_column': "Custom Bool 1 Ä"})
        self.get_book_details(10)
        self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        delete_cust_class(os.path.join(TEST_DB, "metadata.db"), 3)
        self.restart_calibre_web()
        self.goto_page("nav_read")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.goto_page("nav_new")
        self.goto_page("nav_unread")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.adv_search({"read_status": "Yes"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.adv_search({"read_status": "No"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.get_book_details(5)
        self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.get_book_details(5)
        self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.fill_view_config({'config_read_column': ""})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))

    def test_invalid_custom_column(self):
        self.fill_view_config({'config_restricted_column': "Custom Text 人物 *'()&"})
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": 'test'})
        restricts = self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('test', allow=False)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        delete_cust_class(os.path.join(TEST_DB, "metadata.db"), 10)
        self.restart_calibre_web()
        self.goto_page("nav_read")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.goto_page("nav_new")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.goto_page("nav_lang")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.fill_view_config({'config_restricted_column': "None"})
