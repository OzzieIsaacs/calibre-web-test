#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase
import time
from helper_ui import ui_class
from config_test import TEST_DB
# from parameterized import parameterized_class
from helper_func import startup, debug_startup
from helper_func import save_logfiles


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
        self.delete_book(9)
        self.delete_book(10)
        self.delete_book(11)
        self.delete_book(12)
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
