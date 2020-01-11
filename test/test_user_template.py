#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import shutil
from ui_helper import ui_class
from subproc_wrapper import process_open
from testconfig import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME

from parameterized import parameterized_class

'''@parameterized_class([
   { "py_version": u'/usr/bin/python'},
   { "py_version": u'/usr/bin/python3'},
],names=('Python27','Python36'))'''
class test_user_template(unittest.TestCase, ui_class):
    p=None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH,'app.db'))
        except:
            pass
        shutil.rmtree(TEST_DB,ignore_errors=True)
        shutil.copytree('./Calibre_db', TEST_DB)
        try:
            cls.p = process_open([cls.py_version, os.path.join(CALIBRE_WEB_PATH,u'cps.py')],(1))

            # create a new Firefox session
            cls.driver = webdriver.Firefox()
            # time.sleep(15)
            cls.driver.implicitly_wait(BOOT_TIME)
            print('Calibre-web started')

            cls.driver.maximize_window()

            # navigate to the application home page
            cls.driver.get("http://127.0.0.1:8083")

            # Wait for config screen to show up
            cls.fill_initial_config({'config_calibre_dir':TEST_DB})

            # wait for cw to reboot
            time.sleep(BOOT_TIME)

            # Wait for config screen with login button to show up
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.NAME, "login")))
            login_button = cls.driver.find_element_by_name("login")
            login_button.click()

            # login
            cls.login("admin", "admin123")
        except:
            cls.driver.quit()
            cls.p.kill()


    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        cls.p.kill()

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin','admin123')

    def test_random_user_template(self):
        self.fill_view_config({'show_32':0})
        self.goto_page('create_user')
        self.create_user('random',{'password':'1234','email':'a5@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_32':1})
        self.logout()
        self.login('random','1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('random',{'delete':1})

    def test_recent_user_template(self):
        self.fill_view_config({'show_512':0})
        self.goto_page('create_user')
        self.create_user('recent',{'password':'1234','email':'a4@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_512':1})
        self.logout()
        self.login('recent','1234')
        self.assertFalse(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('recent',{'delete':1})

    def test_hot_user_template(self):
        self.fill_view_config({'show_16':0})
        self.goto_page('create_user')
        self.create_user('hot',{'password':'1234','email':'a2@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_16':1})
        self.logout()
        self.login('hot','1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('hot',{'delete':1})

    def test_best_user_template(self):
        self.fill_view_config({'show_128':0})
        self.goto_page('create_user')
        self.create_user('best',{'password':'1234','email':'a1@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_128': 1})
        self.logout()
        self.login('best','1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('best',{'delete':1})

    def test_language_user_template(self):
        self.fill_view_config({'show_2':0})
        self.goto_page('create_user')
        self.create_user('lang',{'password':'1234','email':'a6@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_2': 1})
        self.logout()
        self.login('lang','1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('lang',{'delete':1})

    def test_series_user_template(self):
        self.fill_view_config({'show_4':0})
        self.goto_page('create_user')
        self.create_user('series',{'password':'1234','email':'a7@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_4': 1})
        self.logout()
        self.login('series','1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('series',{'delete':1})

    def test_category_user_template(self):
        self.fill_view_config({'show_8':0})
        self.goto_page('create_user')
        self.create_user('cat',{'password':'1234','email':'a8@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_8':1})
        self.logout()
        self.login('cat','1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('cat',{'delete':1})

    def test_publisher_user_template(self):
        self.fill_view_config({'show_4096':0})
        self.goto_page('create_user')
        self.create_user('pub',{'password':'1234','email':'a9@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_4096':1})
        self.logout()
        self.login('pub','1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_publisher")))
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('pub',{'delete':1})

    def test_author_user_template(self):
        self.fill_view_config({'show_64':0})
        self.goto_page('create_user')
        self.create_user('author',{'password':'1234','email':'a9@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_64':1})
        self.logout()
        self.login('author','1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('author',{'delete':1})

    def test_read_user_template(self):
        self.fill_view_config({'show_256': 0 })
        self.goto_page('create_user')
        self.create_user('read',{'password':'1234','email':'aa@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'show_256' : 1})
        self.logout()
        self.login('read','1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_read")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('read',{'delete':1})

    def test_detail_random_user_template(self):
        self.fill_view_config({'Show_detail_random':0})
        self.goto_page('create_user')
        self.create_user('drand',{'password':'1234','email':'ab@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_view_config({'Show_detail_random':1})
        self.logout()
        self.login('drand','1234')
        self.assertTrue(self.check_element_on_page((By.ID, "nav_new")))
        # self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        self.goto_page("nav_new")
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in category section
        list_element = self.goto_page("nav_cat")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books shown in series section
        list_element = self.goto_page("nav_serie")
        list_element[0].click()
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
        # check random books not shown in best rated section
        self.goto_page("nav_rated")
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in read section
        self.goto_page("nav_read")
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in unread section
        self.goto_page("nav_unread")
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))
        # check random books not shown in sorted section
        self.logout()
        self.login('admin','admin123')
        # delete user
        self.edit_user('drand',{'delete':1})

    @unittest.skip("Not Implemented")
    def test_ui_language_settings(self):
        pass

    @unittest.skip("Not Implemented")
    def test_limit_book_languages(self):
        pass

    @unittest.skip("Not Implemented")
    def test_mature_content_settings(self):
        pass

