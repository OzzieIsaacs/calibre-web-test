# -*- coding: utf-8 -*-

import unittest
import os

from selenium.webdriver.common.by import By
from helper_func import save_logfiles
from helper_db import change_book_path
from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup, debug_startup


RESOURCES = {'ports': 1}

PORTS = ['8083']


class TestBookDatabase(unittest.TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, port=PORTS[0], env={"APP_MODE": "test"})

        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):        
        cls.driver.get("http://127.0.0.1:" + PORTS[0])
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_invalid_book_path(self):
        change_book_path(os.path.join(TEST_DB, "metadata.db"), 10)
        self.restart_calibre_web()
        self.delete_book(10)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertTrue(10, len(books[1]))

