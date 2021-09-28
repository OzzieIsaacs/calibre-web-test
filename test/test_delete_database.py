#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase
import time
from helper_ui import ui_class
from config_test import TEST_DB
# from parameterized import parameterized_class
from helper_func import startup, debug_startup
from helper_func import save_logfiles
from selenium.webdriver.common.by import By

class TestDeleteDatabase(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB})
            time.sleep(3)
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

    def test_delete_books_in_database(self):
        self.delete_book(1)
        self.delete_book(3)
        self.delete_book(4)
        self.delete_book(5)
        self.delete_book(7)
        self.delete_book(8)
        bl = self.get_books_list(1)
        bl['table'][4]['Delete']['element'].click()
        time.sleep(1)
        self.check_element_on_page((By.ID, "delete_confirm")).click()
        time.sleep(1)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "merge_books")))
        bl = self.get_books_list(-1)
        self.assertEqual(4, len(bl['table']))
        self.delete_book(10)
        self.delete_book(11)
        self.delete_book(12)
        # Check if users table is working
        self.goto_page('admin_setup')
        self.check_element_on_page((By.ID, "admin_user_table")).click()
        self.assertEqual(1, len(self.get_user_table(-1)['table']))

        self.delete_book(13)
        books = self.get_books_displayed()
        self.assertEqual(0, len(books[0]))
        self.assertEqual(0, len(books[1]))
        self.assertEqual(len(self.adv_search({'book_title': 'book10'})), 0)
        self.assertEqual(len(self.search('book10')), 0)
        list_element = self.goto_page("nav_serie")
        self.assertEqual(0, len(list_element))
        list_element = self.goto_page("nav_author")
        self.assertEqual(0, len(list_element))
        list_element = self.goto_page("nav_lang")
        self.assertEqual(0, len(list_element))
        list_element = self.goto_page("nav_publisher")
        self.assertEqual(0, len(list_element))
        list_element = self.goto_page("nav_cat")
        self.assertEqual(0, len(list_element))
        bl = self.get_books_list(1)
        self.assertEqual(1, len(bl['table']))
        self.assertEqual("", bl['table'][0]['selector']['text'])
