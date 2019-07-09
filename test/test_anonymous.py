#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
#from selenium import webdriver
#import os
from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC
#import time
#import shutil
from ui_helper import ui_class
#from subproc_wrapper import process_open
from testconfig import TEST_DB
from func_helper import startup
from parameterized import parameterized_class
import sys

'''
guest user support test
'''


@parameterized_class([
   { "py_version": u'python'},
   { "py_version": u'python3'},
],names=('Python27','Python36'))
class test_anonymous(unittest.TestCase, ui_class):
    p=None
    driver = None
    py_version = 'python'

    @classmethod
    def setUpClass(cls):
        startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_anonbrowse': 1})

    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.check_element_on_page((By.ID, "top_user")).click()
            self.login('admin','admin123')

    def test_guest_about(self):
        self.logout()
        self.assertFalse(self.goto_page('nav_about'))

    # Checks if random book section is available in all sidebar menus
    def test_guest_random_books_available(self):
        self.edit_user('Guest',{'show_512':1, 'show_128':1, 'show_2': 1, 'show_64':1,
                                'show_16': 1, 'show_4': 1, 'show_4096': 1, 'show_8': 1, 'show_32':1})
        self.logout()
        # check random books shown in new section
        self.goto_page('nav_new')
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # check random books shown in category section
        list_element = self.goto_page('nav_cat')
        self.assertIsNotNone(list_element)
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # check random books shown in series section
        list_element = self.goto_page('nav_serie')
        self.assertIsNotNone(list_element)
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # check random books NOT shown in author section
        list_element = self.goto_page('nav_author')
        self.assertIsNotNone(list_element)
        list_element[0].click()
        self.driver.implicitly_wait(5)
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))

        # check random books shown in language section
        list_element = self.goto_page('nav_lang')
        self.assertIsNotNone(list_element)
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # check random books shown in hot section
        list_element = self.goto_page('nav_author')
        self.assertIsNotNone(list_element)
        self.goto_page('nav_hot')
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # check random books shown in publisher section
        list_element = self.goto_page('nav_publisher')
        self.assertIsNotNone(list_element)
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # Check random menu is in sidebar
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.edit_user('Guest',{'show_32':0, 'show_512':0, 'show_128':0, 'show_2': 0,
                                'show_16': 0, 'show_4': 0, 'show_4096': 0, 'show_8': 0, 'show_64':0})


    # checks if admin can configure sidebar for random view
    def test_guest_visibility_sidebar(self):
        self.edit_user('Guest',{'show_32':0, 'show_512':1, 'show_128':1, 'show_2': 1,
                                'show_16': 1, 'show_4': 1, 'show_4096': 1, 'show_8': 1, 'show_64':1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_new")
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in category section
        list_element = self.goto_page("nav_cat")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books shown in series section
        list_element = self.goto_page("nav_serie")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in author section
        list_element = self.goto_page("nav_author")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in publisher section
        list_element = self.goto_page("nav_publisher")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in language section
        list_element = self.goto_page("nav_lang")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in hot section
        self.goto_page("nav_hot")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in best rated section
        self.goto_page("nav_rated")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in sorted section
        '''self.driver.find_element_by_id("nav_sort").click()
        self.goto_page("nav_sort_old")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_sort_new")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_sort_asc")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_sort_desc")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))'''

        # Go to admin section and reenable show random view
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.edit_user('Guest', {'show_32': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        list_element = self.goto_page("nav_cat")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books shown in series section
        list_element = self.goto_page("nav_serie")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in author section
        list_element = self.goto_page("nav_author")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in publisher section
        list_element = self.goto_page("nav_publisher")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in language section
        list_element = self.goto_page("nav_lang")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in hot section
        self.goto_page("nav_hot")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in best rated section
        self.goto_page("nav_rated")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in sorted section
        '''self.driver.find_element_by_id("nav_sort").click()
        self.goto_page("nav_sort_old")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_sort_new")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_sort_asc")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_sort_desc")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))'''
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.edit_user('Guest',{'show_32':0, 'show_512':0, 'show_128':0, 'show_2': 0,
                                'show_16': 0, 'show_4': 0, 'show_4096': 0, 'show_8': 0, 'show_64':0})


    # Test if user can change visibility of sidebar view sorted
    '''def test_guest_change_visibility_sorted(self):
        self.edit_user('Guest',{'show_sorted':1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.edit_user('Guest',{'show_sorted': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertFalse(self.check_element_on_page((By.ID, "nav_sort")))'''


    # Test if user can change visibility of sidebar view best rated books
    def test_guest_change_visibility_rated(self):
        self.edit_user('Guest',{'show_128':1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.edit_user('Guest',{'show_128': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rated")))

    # Test if user can change visibility of sidebar view read and unread books
    def test_guest_visibility_read(self):
        self.goto_page('admin_setup')
        user = self.driver.find_elements_by_xpath("//table[@id='table_user']/tbody/tr/td/a")
        for ele in user:
            if ele.text == 'Guest':
                ele.click()
                self.assertFalse(self.check_element_on_page((By.ID, "show_256")))

    # checks if admin can change user language
    def test_guest_change_visibility_language(self):
        self.edit_user('Guest', {'show_2': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.edit_user('Guest',{'show_2': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertFalse(self.check_element_on_page((By.ID, "nav_lang")))

    # checks if admin can change hot books
    def test_guest_change_visibility_hot(self):
        self.edit_user('Guest', {'show_16': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.edit_user('Guest',{'show_16': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertFalse(self.check_element_on_page((By.ID, "nav_hot")))

    # checks if admin can change series
    def test_guest_change_visibility_series(self):
        self.edit_user('Guest', {'show_4': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.edit_user('Guest', {'show_4': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertFalse(self.check_element_on_page((By.ID, "nav_serie")))

    # checks if admin can change publisher
    def test_guest_change_visibility_publisher(self):
        self.edit_user('Guest', {'show_4096': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.edit_user('Guest',{'show_4096': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertFalse(self.check_element_on_page((By.ID, "nav_publisher")))

    # checks if admin can change categories
    def test_guest_change_visibility_category(self):
        self.edit_user('Guest', {'show_8': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.edit_user('Guest', {'show_8': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # Category not visible
        self.logout()
        self.assertFalse(self.check_element_on_page((By.ID, "nav_cat")))

