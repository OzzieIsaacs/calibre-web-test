#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import time
import re
import shutil
from ui_helper import ui_class
from subproc_wrapper import process_open
from testconfig import CALIBRE_WEB_PATH, TEST_DB

class test_login(unittest.TestCase, ui_class):
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
        cls.p = process_open([u"python", os.path.join(CALIBRE_WEB_PATH,u'cps.py')],(1))

        # create a new Firefox session
        cls.driver = webdriver.Firefox()
        # time.sleep(15)
        cls.driver.implicitly_wait(5)
        print('Calibre-web started')

        cls.driver.maximize_window()

        # navigate to the application home page
        cls.driver.get("http://127.0.0.1:8083")

        # Wait for config screen to show up
        cls.fill_initial_config({'config_calibre_dir':TEST_DB})

        # wait for cw to reboot
        time.sleep(5)

        # Wait for config screen with login button to show up
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.NAME, "login")))
        login_button = cls.driver.find_element_by_name("login")
        login_button.click()


    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()

    def tearDown(self):
        if self.check_user_logged_in('', True):
            self.logout()

    def fail_access_page(self, page):
        try:
            self.driver.get(page)
        except WebDriverException as e:
            return re.findall('Reached error page: about:neterror?e=connectionFailure', e.msg)
        if self.driver.title == u'500 Internal server error':
            return True
        elif self.driver.title == u'403 Forbidden':
            return True
        elif self.driver.title == u'404 Not Found':
            return True
        else:
            return False

    # try to access all pages without login
    def test_login_protected(self):
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/config"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/user"))
        # self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/user/1"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/user/resetpassword/1"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/book"))
        # self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/book/1"))
        '''self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/upload"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/convert"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/convert/1"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/view"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/config"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/viewconfig"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/user/new"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin/mailsettings"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/ajax/emailstat"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/ajax/editdomain"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/ajax/deletedomain"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/ajax/domainlist"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/ajax/toggleread"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/ajax/bookmark/1/1"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/get_authors_json"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/get_tags_json"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/get_languages_json"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/get_series_json"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/get_matching_tags"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/get_update_status"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/get_updater_status"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/tasks"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/stats"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/page"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/book"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/book/1"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/newest"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/newest/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/newest/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/newest/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/oldest"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/oldest/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/oldest/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/a-z"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/a-z/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/a-z/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/hot"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/hot/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/hot/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/rated"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/rated/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/rated/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/discover"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/discover/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/discover/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/author"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/author/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/author/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/series"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/series/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/series/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/language"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/language/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/language/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/category"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/category/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/books/category/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/unreadbooks"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/unreadbooks/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/unreadbooks/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/readbooks"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/readbooks/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/readbooks/page/2"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/delete"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/delete/1"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/delete/1/EPUB"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/gdrive"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/gdrive/authenticate"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/gdrive/callback"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/gdrive/watch"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/gdrive/watch/subscribe"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/gdrive/watch/revoke"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/gdrive/watch/callback"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/shutdown"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/update"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/search"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/advanced_search"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/cover"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/cover/213"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/show/1/epub"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/read/1/epub"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/download/1/epub"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/download/1/epub/name"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/register"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/logout"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/remote_login"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/verify/34898295"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/ajax/verify_token"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/send/66"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/shelf/add"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/shelf/add/1/1"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/shelf/massadd"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/shelf/remove"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/shelf/remove/1/1"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/shelf/create"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/shelf/delete"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/shelf/delete/1"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/shelf/1"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/shelf/order/1"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/me"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/admin"))
        self.assertTrue(self.fail_access_page("http://127.0.0.1:8083/"))'''

    # login with admin
    # create new user, leave passwort empty
    # logout
    # try to login
    # logout
    def test_login_empty_password(self):
        self.driver.get("http://127.0.0.1:8083/login")
        self.login('admin','admin123')
        self.create_user('epass',{'email':'a5@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID,'flash_alert')))
        self.create_user('epass', {'email': 'a5@b.com', 'password':'1', 'passwd_role':1})
        self.assertTrue(self.check_element_on_page((By.ID,'flash_success')))
        self.logout()
        self.assertTrue(self.login('epass','1'))
        self.change_visibility_me({'password':''})
        self.assertTrue(self.check_element_on_page((By.ID,'flash_success')))
        self.logout()
        self.assertFalse(self.login('epass',''))
        self.assertTrue(self.login('epass', '1'))
        self.logout()

    # login with admin
    # create new user (Capital letters), passwort with ß and unicode and spaces within
    # logout
    # try login with username lowercase letters and correct password
    # logout
    # try login with username lowercase letters and password with capital letters
    # logout
    def test_login_capital_letters_user_unicode_password_passwort(self):
        self.driver.get("http://127.0.0.1:8083/login")
        self.login('admin','admin123')
        self.create_user('KaPiTaL',{'password':u'Kß ü执','email':'a@b.com'})
        self.logout()
        self.assertTrue(self.login('KAPITAL',u'Kß ü执'))
        self.logout()
        self.assertTrue(self.login('kapital',u'Kß ü执'))
        self.logout()
        self.assertFalse(self.login('KaPiTaL',u'kß ü执'))

    # login with admin
    # create new user (unicode characters), passwort with spaces at begining
    # logout
    # try login with username and correct password
    # logout
    # try login with username and password without space at beginning
    def test_login_unicode_user_space_end_passwort(self):
        self.driver.get("http://127.0.0.1:8083/login")
        self.login('admin','admin123')
        self.create_user(u'Kß ü执',{'password':' space', 'email':'a1@b.com'})
        self.logout()
        self.assertTrue(self.login(u'Kß ü执',' space'))
        self.logout()
        self.assertFalse(self.login(u'Kß ü执','space'))


    # login with admin
    # create new user (spaces within), passwort with space at end
    # logout
    # try login with username and correct password
    # logout
    # try login with username without space and correct password without space at end
    # try login with username with space and password without space at end
    def test_login_user_with_space_passwort_end_space(self):
        self.driver.get("http://127.0.0.1:8083/login")
        self.login('admin','admin123')
        self.create_user('Klaus peter',{'password':'space ','email':'a2@b.com'})
        self.logout()
        self.assertTrue(self.login('Klaus peter','space '))
        self.logout()
        self.assertFalse(self.login('Klauspeter','space'))
        self.logout()
        self.assertFalse(self.login('Klaus peter','space'))

    # login with admin
    # create new user as admin user
    # logout
    # try login with username and correct password
    # logout
    # delete original admin user
    # logout
    # try login with orig admin
    # rename user to admin
    # logout
    # ToDo: for real check restart has to be performed
    def test_login_delete_admin(self):
        self.driver.get("http://127.0.0.1:8083/login")
        self.login('admin','admin123')
        self.create_user('admin2',{'password':'admin2', 'admin_role':1 ,'email':'a3@b.com'})
        self.logout()
        self.assertTrue(self.login('admin2','admin2'))
        self.edit_user('admin',{'delete':1})
        self.logout()
        self.assertFalse(self.login('admin','admin123'))
        self.login('admin2','admin2')
        self.create_user('admin',{'password':'admin123', 'admin_role':1,'email':'a4@b.com'})
        self.logout()


