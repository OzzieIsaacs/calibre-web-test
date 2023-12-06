#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import time
import os

from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup, debug_startup
from helper_func import save_logfiles, add_dependency, remove_dependency
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


RESOURCES = {'ports': 1}

PORTS = ['8083']


class TestMergeBooksList(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, port=PORTS[0], env={"APP_MODE": "test"})
            time.sleep(3)
            cls.goto_page("nav_new")
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

    def test_delete_book(self):
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        details = self.get_book_details(4)
        # add folder to folder
        book_path1 = os.path.join(TEST_DB, details['author'][0], details['title'][:36] + ' (4)')
        sub_folder = os.path.join(book_path1, 'new_subfolder')
        os.mkdir(sub_folder)
        bl = self.get_books_list(1)
        bl['search'].clear()
        bl['search'].send_keys("Very long")
        bl['search'].send_keys(Keys.RETURN)
        time.sleep(1)
        bl = self.get_books_list(-1)
        # delete book, -> denied because of additional folder
        bl['table'][0]['Delete']['element'].click()
        time.sleep(1)
        confirm = self.check_element_on_page((By.ID, "delete_confirm"))
        self.assertTrue(confirm)
        confirm.click()
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))

        os.rmdir(sub_folder)
        self.assertTrue(os.path.isdir(book_path1))
        self.assertEqual(0, len([name for name in os.listdir(book_path1) if os.path.isfile(name)]))
        self.get_book_details(4)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))

        # change permission of folder -> delete denied because of access rights
        book_path = os.path.join(TEST_DB, 'John Doe', 'Buuko (7)')
        os.chmod(book_path, 0o400)
        bl = self.get_books_list(1)
        bl['search'].clear()
        bl['search'].send_keys("Buuko")
        bl['search'].send_keys(Keys.RETURN)
        time.sleep(1)
        bl = self.get_books_list(-1)

        bl['table'][0]['Delete']['element'].click()
        time.sleep(1)
        confirm = self.check_element_on_page((By.ID, "delete_confirm"))
        self.assertTrue(confirm)
        confirm.click()
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        os.chmod(book_path, 0o775)
        self.goto_page("nav_new")
        books_after = self.get_books_displayed()
        self.assertEqual(len(books[1]) - 1, len(books_after[1]))

    # select book on page 1, select book on page 2, -> button accessible, go to different page and return -> books selected
    # select book on page 1, select book on page 2 -> press unselect, both books unselected
    # select book on page 1, select book on page 2 -> merge -> abort, everything like before
    # select book on page 1, select book on page 2 -> merge -> one book less, both formats available
    def test_book_merge(self):
        bl = self.get_books_list(1)
        # select one book on page one -> button greyed
        bl['table'][0]['selector']['element'].click()
        self.assertTrue("disabled" in self.check_element_on_page((By.ID, "merge_books")).get_attribute("class"))
        # select two books on page one -> button accessible
        bl['table'][2]['selector']['element'].click()
        self.assertFalse("disabled" in self.check_element_on_page((By.ID, "merge_books")).get_attribute("class"))
        # Click unselect books -> no book selected, merge button greyed out
        bl['remove-btn'].click()
        bl = self.get_books_list(-1)
        self.assertFalse(bl['table'][0]['selector']['element'].is_selected())
        self.assertFalse(bl['table'][2]['selector']['element'].is_selected())
        self.assertTrue("disabled" in self.check_element_on_page((By.ID, "merge_books")).get_attribute("class"))
        # select book on page 1, select book on page 2, check merge button clickable
        bl['table'][0]['selector']['element'].click()
        bl['pagination']['›']['link'].click()
        bl = self.get_books_list(-1)
        bl['table'][0]['selector']['element'].click()
        self.assertFalse("disabled" in self.check_element_on_page((By.ID, "merge_books")).get_attribute("class"))
        # change page, books stay selected
        bl['pagination']['‹']['link'].click()
        bl = self.get_books_list(-1)
        self.assertTrue(bl['table'][0]['selector']['element'].is_selected())
        # click unselect, both books (on both pages) are unselected
        bl['remove-btn'].click()
        bl = self.get_books_list(-1)
        self.assertFalse(bl['table'][0]['selector']['element'].is_selected())
        bl['pagination']['›']['link'].click()
        bl = self.get_books_list(-1)
        self.assertFalse(bl['table'][0]['selector']['element'].is_selected())
        # select 2 books and click merge and abort, check both books still selected
        bl['table'][0]['selector']['element'].click()
        bl['pagination']['‹']['link'].click()
        bl = self.get_books_list(-1)
        bl['table'][0]['selector']['element'].click()
        bl['merge-btn'].click()
        time.sleep(1)
        self.check_element_on_page((By.ID, "merge_abort")).click()
        bl = self.get_books_list(-1)
        self.assertTrue(bl['table'][0]['selector']['element'].is_selected())
        bl['pagination']['›']['link'].click()
        bl = self.get_books_list(-1)
        self.assertTrue(bl['table'][0]['selector']['element'].is_selected())
        bl['merge-btn'].click()
        time.sleep(1)
        self.check_element_on_page((By.ID, "merge_confirm")).click()
        time.sleep(1)
        bl = self.get_books_list(-1)
        self.assertEqual(1, len(bl['pagination']))
        self.assertEqual(10, len(bl['table']))
        merged_book = self.get_book_details(1)
        self.assertEqual("Der Buchtitel", merged_book['title'])
        self.assertEqual(4, len(merged_book['author']))
        self.assertEqual(2, len(merged_book['download']))

