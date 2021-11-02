# -*- coding: utf-8 -*-

import unittest
import time
from selenium.webdriver.common.by import By

from helper_func import save_logfiles
from helper_ui import ui_class
from config_test import TEST_DB
# from parameterized import parameterized_class
from helper_func import startup, debug_startup


class TestCalibreWebListOrders(unittest.TestCase, ui_class):

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
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_series_sort(self):
        self.goto_page('nav_serie')
        list = self.check_element_on_page((By.ID, "list-button"))
        self.assertTrue(list)
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")
        self.check_element_on_page((By.ID, "asc")).click()
        time.sleep(1)
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")
        self.check_element_on_page((By.ID, "desc")).click()
        time.sleep(1)
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Loko")
        self.assertEqual(list_element[1]['title'], "Djüngel")
        self.driver.refresh()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Loko")
        self.assertEqual(list_element[1]['title'], "Djüngel")
        self.check_element_on_page((By.ID, "list-button")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Loko")
        self.assertEqual(list_element[1]['title'], "Djüngel")
        grid = self.check_element_on_page((By.ID, "grid-button"))
        self.assertTrue(grid)
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Loko")
        self.assertEqual(list_element[1]['title'], "Djüngel")
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")
        self.driver.refresh()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")
        self.check_element_on_page((By.ID, "desc")).click()
        self.check_element_on_page((By.ID, "grid-button")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Loko")
        self.assertEqual(list_element[1]['title'], "Djüngel")
        self.check_element_on_page((By.ID, "desc")).click()
        time.sleep(1)
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Loko")
        self.assertEqual(list_element[1]['title'], "Djüngel")
        self.check_element_on_page((By.ID, "asc")).click()
        time.sleep(1)
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")

    def test_author_sort(self):
        self.goto_page('nav_author')
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Leo Baskerville")
        self.assertEqual(list_element[10]['title'], "Liu Yang")
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Leo Baskerville")
        self.assertEqual(list_element[10]['title'], "Liu Yang")
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Liu Yang")
        self.assertEqual(list_element[10]['title'], "Leo Baskerville")
        self.driver.refresh()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Liu Yang")
        self.assertEqual(list_element[10]['title'], "Leo Baskerville")
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Liu Yang")
        self.assertEqual(list_element[10]['title'], "Leo Baskerville")
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Leo Baskerville")
        self.assertEqual(list_element[10]['title'], "Liu Yang")
        self.check_element_on_page((By.ID, "sort_name")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Baskerville, Leo")
        self.assertEqual(list_element[10]['title'], "Yang, Liu")
        self.driver.refresh()   # sort_name is not saved
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Leo Baskerville")
        self.assertEqual(list_element[10]['title'], "Liu Yang")
        self.check_element_on_page((By.XPATH, "//button[contains(text(), 'L')]")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Sigurd Lindgren")
        self.assertEqual(list_element[1]['title'], "Asterix Lionherd")
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Asterix Lionherd")
        self.assertEqual(list_element[1]['title'], "Sigurd Lindgren")
        self.assertEqual(len(list_element),2)
        self.check_element_on_page((By.XPATH, "//button[contains(text(), 'D')]")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "John Döe")
        self.assertEqual(len(list_element), 1)
        self.check_element_on_page((By.ID, "all")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Liu Yang")
        self.assertEqual(list_element[10]['title'], "Leo Baskerville")
        self.assertEqual(len(list_element), 11)