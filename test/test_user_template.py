#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium.webdriver.common.by import By
import time
from helper_ui import ui_class, RESTRICT_TAG_TEMPLATE, RESTRICT_COL_TEMPLATE
from config_test import TEST_DB
from helper_func import startup
from helper_func import save_logfiles


class TestUserTemplate(unittest.TestCase, ui_class):
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

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin', 'admin123')

    def test_random_user_template(self):
        self.fill_view_config({'show_32': 0})
        self.goto_page('create_user')
        self.create_user('random', {'password': '1234', 'email': 'a5@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_32': 1})
        self.logout()
        self.login('random', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('random', {'delete': 1})

    def test_recent_user_template(self):
        self.fill_view_config({'show_4': 0, 'show_8': 0, 'show_16': 0, 'show_32': 0, 'show_64': 0, 'show_128': 0,
                               'show_256': 0, 'show_4096': 0, 'show_8192': 0, 'show_131072': 0,
                               'show_16384': 0, 'show_32768': 0, 'show_2': 0, 'show_65536': 0
                               })
        self.goto_page('create_user')
        self.create_user('recent', {'password': '1234', 'email': 'a4@b.com'})
        self.fill_view_config({'show_4': 1, 'show_8': 1, 'show_16': 1, 'show_32': 1, 'show_64': 1, 'show_128': 1,
                               'show_256': 1, 'show_4096': 1, 'show_8192': 1, 'show_65536': 1,
                               'show_16384': 1, 'show_32768': 1, 'show_2': 1, 'show_131072': 1,
                               })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('recent', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_download")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_read")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_author")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_format")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('recent', {'delete': 1})

    def test_hot_user_template(self):
        self.fill_view_config({'show_16': 0})
        self.goto_page('create_user')
        self.create_user('hot', {'password': '1234','email': 'a2@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_16': 1})
        self.logout()
        self.login('hot', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('hot', {'delete': 1})

    def test_best_user_template(self):
        self.fill_view_config({'show_128': 0})
        self.goto_page('create_user')
        self.create_user('best', {'password': '1234', 'email': 'a1@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_128': 1})
        self.logout()
        self.login('best', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('best', {'delete': 1})

    def test_language_user_template(self):
        self.fill_view_config({'show_2': 0})
        self.goto_page('create_user')
        self.create_user('lang', {'password': '1234', 'email': 'a6@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_2': 1})
        self.logout()
        self.login('lang', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('lang', {'delete': 1})

    def test_series_user_template(self):
        self.fill_view_config({'show_4': 0})
        self.goto_page('create_user')
        self.create_user('series', {'password': '1234','email': 'a7@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_4': 1})
        self.logout()
        self.login('series', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('series', {'delete': 1})

    def test_category_user_template(self):
        self.fill_view_config({'show_8': 0})
        self.goto_page('create_user')
        self.create_user('cat', {'password': '1234','email': 'a8@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_8': 1})
        self.logout()
        self.login('cat', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('cat', {'delete': 1})

    def test_publisher_user_template(self):
        self.fill_view_config({'show_4096': 0})
        self.goto_page('create_user')
        self.create_user('pub',{'password': '1234', 'email': 'a9@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_4096': 1})
        self.logout()
        self.login('pub', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('pub', {'delete': 1})

    def test_format_user_template(self):
        self.fill_view_config({'show_16384': 0})
        self.goto_page('create_user')
        self.create_user('format', {'password': '1234','email': 'a10@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_16384': 1})
        self.logout()
        self.login('format', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('format', {'delete': 1})

    def test_archived_format_template(self):
        self.fill_view_config({'show_32768': 0})
        self.goto_page('create_user')
        self.create_user('format', {'password': '1234','email': 'a10@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_32768': 1})
        self.logout()
        self.login('format', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('format', {'delete': 1})


    def test_author_user_template(self):
        self.fill_view_config({'show_64': 0})
        self.goto_page('create_user')
        self.create_user('author', {'password': '1234','email': 'a9@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_64': 1})
        self.logout()
        self.login('author', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('author', {'delete': 1})

    def test_read_user_template(self):
        self.fill_view_config({'show_256': 0})
        self.goto_page('create_user')
        self.create_user('read', {'password': '1234','email': 'aa@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_256': 1})
        self.logout()
        self.login('read', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_read")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('read',{'delete':1})

    def test_download_user_template(self):
        self.fill_view_config({'show_65536': 0})
        self.goto_page('create_user')
        self.create_user('download', {'password': '1234','email': 'aaa@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_65536': 1})
        self.logout()
        self.login('download', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('download', {'delete': 1})

    def test_list_user_template(self):
        self.fill_view_config({'show_131072': 0})
        self.goto_page('create_user')
        self.create_user('list', {'password': '1234','email': 'aaa@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_131072': 1})
        self.logout()
        self.login('list', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_list")))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('list', {'delete': 1})

    def test_detail_random_user_template(self):
        self.fill_view_config({'Show_detail_random':0})
        self.goto_page('create_user')
        self.create_user('drand', {'password': '1234','email': 'ab@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'Show_detail_random': 1})
        self.logout()
        self.login('drand', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_download")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_list")))
        self.goto_page("nav_new")
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in category section
        list_element = self.goto_page("nav_cat")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books shown in series section
        self.goto_page("nav_serie")
        list_element = self.get_series_books_displayed()
        self.assertIsNotNone(list_element)
        list_element[0]['ele'].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in author section
        list_element = self.goto_page("nav_author")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in language section
        list_element = self.goto_page("nav_lang")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in publisher section
        list_element = self.goto_page("nav_publisher")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in hot section
        self.goto_page("nav_hot")
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in hot section
        self.goto_page("nav_download")
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in best rated section
        self.goto_page("nav_rated")
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in read section
        self.goto_page("nav_read")
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in unread section
        self.goto_page("nav_unread")
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books shown in format section
        list_element = self.goto_page("nav_format")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books shown in archived section
        list_element = self.goto_page("nav_archived")
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check about page visible and libs section not visible
        self.assertTrue(self.goto_page('nav_about'))
        self.assertFalse(self.check_element_on_page((By.ID, 'libs')))
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('drand', {'delete': 1})

    def test_ui_language_settings(self):
        self.edit_user('admin', {'locale': 'Deutsch'})
        self.goto_page('user_setup')
        username = self.check_element_on_page((By.XPATH, '//label[@for="name"]'))
        self.assertEqual(username.text, 'Benutzername')
        self.change_visibility_me({'locale': 'English'})
        self.goto_page('user_setup')
        username = self.check_element_on_page((By.XPATH, '//label[@for="name"]'))
        self.assertEqual(username.text, 'Username')

    def test_limit_book_languages(self):
        self.edit_user('admin',{'default_language': 'Norwegian Bokmål'})
        self.goto_page("nav_hot")
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 0)
        self.assertIn(int(books[0][0]['id']), (8, 12, 13))
        self.assertIn(int(books[0][1]['id']), (8, 12, 13))
        self.assertIn(int(books[0][2]['id']), (8, 12, 13))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_lang")))
        self.goto_page("nav_unread")
        books = self.get_books_displayed()
        self.assertEqual(int(books[1][0]['id']), 13)
        self.assertEqual(int(books[1][1]['id']), 12)
        self.assertEqual(int(books[1][2]['id']), 8)
        self.assertIn(int(books[0][0]['id']), (8, 12, 13))
        self.assertIn(int(books[0][1]['id']), (8, 12, 13))
        self.assertIn(int(books[0][2]['id']), (8, 12, 13))
        tags = self.driver.find_elements_by_tag_name('h2')
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[1].text, 'Unread Books (3)')
        # find 2 h2

    def test_allow_tag_restriction(self):
        restricts = self.list_restrictions(RESTRICT_TAG_TEMPLATE)
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('Gênot', allow=True)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)

        self.goto_page('create_user')
        self.create_user('allowtag', {'password': '1234', 'email': 'abb@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 11)
        self.logout()
        self.login('allowtag', '1234')
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 4)
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('allowtag', {'delete': 1})
        self.list_restrictions(RESTRICT_TAG_TEMPLATE)
        self.delete_restrictions('a0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        close.click()
        time.sleep(2)

    def test_deny_tag_restriction(self):
        restricts = self.list_restrictions(RESTRICT_TAG_TEMPLATE)
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('Gênot', allow=False)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)

        self.goto_page('create_user')
        self.create_user('denytag', {'password': '1234', 'email': 'aba@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 11)
        self.logout()
        self.login('denytag', '1234')
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 7)

        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('denytag', {'delete': 1})
        self.list_restrictions(RESTRICT_TAG_TEMPLATE)
        self.delete_restrictions('d0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        close.click()
        time.sleep(2)

    def test_allow_column_restriction(self):
        self.fill_view_config({'config_restricted_column': "Custom Text 人物 *'()&"})
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": 'test'})
        self.edit_book(11, custom_content={"Custom Text 人物 *'()&": 'test'})
        self.edit_book(1, custom_content={"Custom Text 人物 *'()&": 'test'})
        self.edit_book(9, custom_content={"Custom Text 人物 *'()&": 'test'})

        restricts = self.list_restrictions(RESTRICT_COL_TEMPLATE)
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('test', allow=True)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)

        self.goto_page('create_user')
        self.create_user('allowcolum', {'password': '1234', 'email': 'abc@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 11)
        self.logout()
        self.login('allowcolum', '1234')
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 4)

        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('allowcolum', {'delete': 1})
        self.list_restrictions(RESTRICT_COL_TEMPLATE)
        self.delete_restrictions('a0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        close.click()
        time.sleep(2)
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(11, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(8, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(3, custom_content={"Custom Text 人物 *'()&": ''})
        self.fill_view_config({'config_restricted_column': "None"})

    def test_deny_column_restriction(self):
        self.fill_view_config({'config_restricted_column': "Custom Text 人物 *'()&"})
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": 'deny'})
        self.edit_book(11, custom_content={"Custom Text 人物 *'()&": 'deny'})
        self.edit_book(1, custom_content={"Custom Text 人物 *'()&": 'deny'})
        self.edit_book(9, custom_content={"Custom Text 人物 *'()&": 'deny'})
        restricts = self.list_restrictions(RESTRICT_COL_TEMPLATE)
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('deny', allow=False)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)

        self.goto_page('create_user')
        self.create_user('denycolum', {'password': '1234', 'email': 'abd@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 11)
        self.logout()
        self.login('denycolum', '1234')
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 7)
        self.logout()
        self.login('admin', 'admin123')
        # delete user
        self.edit_user('denycolum', {'delete': 1})
        self.list_restrictions(RESTRICT_COL_TEMPLATE)
        self.delete_restrictions('d0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        close.click()
        time.sleep(2)
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(11, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(8, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(3, custom_content={"Custom Text 人物 *'()&": ''})
        self.fill_view_config({'config_restricted_column': "None"})
