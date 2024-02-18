#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from unittest import skip
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import re
from helper_ui import ui_class
from config_test import TEST_DB, CALIBRE_WEB_PATH, BOOT_TIME
from helper_func import startup, check_response_language_header, curl_available, digest_login
import requests
import os
import time
from helper_func import save_logfiles
import socket


RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


class TestLogin(unittest.TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, login=False, index=INDEX, env={"APP_MODE": "test"})
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:" + PORTS[0] + "/login")
        cls.login('admin', 'admin123')
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        try:
            os.unlink(os.path.join(CALIBRE_WEB_PATH + INDEX, 'cps', 'static', 'robots.txt'))
        except:
            pass
        save_logfiles(cls, cls.__name__)

    def tearDown(self):
        if self.check_user_logged_in('', True):
            self.logout()

    def fail_access_page(self, page):
        try:
            self.driver.get(page)
        except WebDriverException as e:
            return re.findall('Reached error page: about:neterror?e=connectionFailure', e.msg)
        if self.driver.title == u'500 Internal server error':
            return 2
        elif self.driver.title == u'Calibre-Web | HTTP Error (Error 403)':
            return 2
        elif self.driver.title == u'Calibre-Web | HTTP Error (Error 404)':
            return 2
        elif self.driver.title == u'Calibre-Web | HTTP Error (Error 405)':
            return 2
        elif self.driver.title == u'Calibre-Web | Login' or self.driver.title == u'Calibre-Web | login':
            return 1
        else:
            return 0

    # try to access all pages without login
    def test_login_protected(self):
        host = "http://127.0.0.1:" + PORTS[0]
        self.assertEqual(self.fail_access_page(host + "/config"), 2)
        self.assertEqual(self.fail_access_page(host + "/books"), 2)
        self.assertEqual(self.fail_access_page(host + "/admin/user"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/user/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/user/resetpassword/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/book"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/book/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/upload"), 2)
        self.assertEqual(self.fail_access_page(host + "/admin/convert"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/convert/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/view"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/config"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/viewconfig"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/user/new"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/mailsettings"), 1)
        self.assertEqual(self.fail_access_page(host + "/ajax/emailstat"), 1)
        self.assertEqual(self.fail_access_page(host + "/ajax/editdomain"), 1)
        self.assertEqual(self.fail_access_page(host + "/ajax/deletedomain"), 1)
        self.assertEqual(self.fail_access_page(host + "/ajax/domainlist"), 1)
        self.assertEqual(self.fail_access_page(host + "/ajax/toggleread"), 1)
        self.assertEqual(self.fail_access_page(host + "/ajax/bookmark/1/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/get_authors_json"), 1)
        self.assertEqual(self.fail_access_page(host + "/get_tags_json"), 1)
        self.assertEqual(self.fail_access_page(host + "/get_languages_json"), 1)
        self.assertEqual(self.fail_access_page(host + "/get_series_json"), 1)
        self.assertEqual(self.fail_access_page(host + "/get_matching_tags"), 1)
        self.assertEqual(self.fail_access_page(host + "/get_update_status"), 1)
        self.assertEqual(self.fail_access_page(host + "/get_updater_status"), 1)
        self.assertEqual(self.fail_access_page(host + "/tasks"), 1)
        self.assertEqual(self.fail_access_page(host + "/stats"), 1)
        self.assertEqual(self.fail_access_page(host + "/page"), 2)
        self.assertEqual(self.fail_access_page(host + "/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/book"), 2)
        self.assertEqual(self.fail_access_page(host + "/book/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/newest"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/newest/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/newest/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/newest/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/oldest"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/oldest/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/oldest/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/a-z"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/a-z/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/a-z/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/hot"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/hot/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/hot/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/rated"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/rated/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/rated/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/discover"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/discover/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/discover/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/author"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/author/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/author/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/series"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/series/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/series/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/language"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/language/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/language/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/category"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/category/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/books/category/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/unreadbooks"), 2)
        self.assertEqual(self.fail_access_page(host + "/unreadbooks/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/unreadbooks/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/readbooks"), 2)
        self.assertEqual(self.fail_access_page(host + "/readbooks/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/readbooks/page/2"), 1)
        self.assertEqual(self.fail_access_page(host + "/delete"), 2)
        self.assertEqual(self.fail_access_page(host + "/delete/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/delete/1/EPUB"), 1)
        self.assertEqual(self.fail_access_page(host + "/gdrive"), 2)
        self.assertEqual(self.fail_access_page(host + "/gdrive/authenticate"), 1)
        self.assertEqual(self.fail_access_page(host + "/gdrive/callback"), 2)
        self.assertEqual(self.fail_access_page(host + "/gdrive/watch"), 1)
        self.assertEqual(self.fail_access_page(host + "/gdrive/watch/subscribe"), 1)
        self.assertEqual(self.fail_access_page(host + "/gdrive/watch/revoke"), 1)
        # self.assertEqual(self.fail_access_page(host + "/gdrive/watch/callback"),0)
        self.assertEqual(self.fail_access_page(host + "/shutdown"), 2)
        self.assertEqual(self.fail_access_page(host + "/update"), 2)
        self.assertEqual(self.fail_access_page(host + "/search"), 1)
        self.assertEqual(self.fail_access_page(host + "/advsearch"), 1)
        self.assertEqual(self.fail_access_page(host + "/cover"), 2)
        self.assertEqual(self.fail_access_page(host + "/cover/213"), 1)
        self.assertEqual(self.fail_access_page(host + "/show/1/epub"), 1)
        self.assertEqual(self.fail_access_page(host + "/read/1/epub"), 1)
        self.assertEqual(self.fail_access_page(host + "/download/1/epub"), 1)
        # important this endpoint has to exist, otherwise Kobo download will fail
        self.assertEqual(self.fail_access_page(host + "/download/1/epub/name"), 1)
        self.assertEqual(self.fail_access_page(host + "/register"), 2)
        self.assertEqual(self.fail_access_page(host + "/logout"), 1)
        self.assertEqual(self.fail_access_page(host + "/remote_login"), 2)
        self.assertEqual(self.fail_access_page(host + "/verify/34898295"), 2)
        self.assertEqual(self.fail_access_page(host + "/ajax/verify_token"), 1)
        self.assertEqual(self.fail_access_page(host + "/send/66"), 1)
        self.assertEqual(self.fail_access_page(host + "/shelf/add"), 1)
        self.assertEqual(self.fail_access_page(host + "/shelf/add/1/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/shelf/massadd"), 1)
        self.assertEqual(self.fail_access_page(host + "/shelf/remove"), 1)
        self.assertEqual(self.fail_access_page(host + "/shelf/remove/1/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/shelf/create"), 1)
        self.assertEqual(self.fail_access_page(host + "/shelf/delete"), 1)
        self.assertEqual(self.fail_access_page(host + "/shelf/delete/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/shelf/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/shelf/order/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/me"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin"), 1)
        self.assertEqual(self.fail_access_page(host + "/"), 1)
        self.assertEqual(self.fail_access_page(host + "/import_ldap_users"), 2)
        self.assertEqual(self.fail_access_page(host + "/admin/logdownload/1"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/debug"), 1)
        self.assertEqual(self.fail_access_page(host + "/ajax/log/0"), 1)
        self.assertEqual(self.fail_access_page(host + "/admin/resetpassword/0"), 1)

    # login with admin
    # create new user, leave password empty
    # logout
    # try to login
    # logout
    def test_login_empty_password(self):
        self.driver.get("http://127.0.0.1:" + PORTS[0] + "/login")
        self.login('admin', 'admin123')
        self.create_user('epass', {'email': 'a5@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))
        self.create_user('epass', {'email': 'a5@b.com', 'password': '123AbC*!', 'passwd_role': 1})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        self.logout()
        self.assertTrue(self.login('epass', '123AbC*!'))
        self.change_visibility_me({'password': ''})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        self.logout()
        self.assertFalse(self.login('epass', ''))
        self.assertTrue(self.login('epass', '123AbC*!'))
        self.logout()

    # login with admin
    # create new user (Capital letters), password with ß and unicode and spaces within
    # logout
    # try login with username lowercase letters and correct password
    # logout
    # try login with username lowercase letters and password with capital letters
    # logout
    def test_login_capital_letters_user_unicode_password(self):
        self.driver.get("http://127.0.0.1:" + PORTS[0] + "/login")
        self.login('admin', 'admin123')
        self.create_user('KaPiTaL', {'password': u'Kß ü执123AbC*!', 'email': 'a@b.com'})
        self.logout()
        self.assertTrue(self.login('KAPITAL', u'Kß ü执123AbC*!'))
        self.logout()
        self.assertTrue(self.login('kapital', u'Kß ü执123AbC*!'))
        self.logout()
        self.assertFalse(self.login('KaPiTaL', u'kß ü执123AbC*!'))

    # login with admin
    # create new user (unicode characters), password with spaces at beginning
    # logout
    # try login with username and correct password
    # logout
    # try login with username and password without space at beginning
    def test_login_unicode_user_space_end_password(self):
        self.driver.get("http://127.0.0.1:" + PORTS[0] + "/login")
        self.login('admin', 'admin123')
        self.create_user(u'Kß ü执', {'password': ' space123AbC*!', 'email': 'a1@b.com'})
        self.logout()
        self.assertTrue(self.login(u'Kß ü执', ' space123AbC*!'))
        self.logout()
        self.assertFalse(self.login(u'Kß ü执', 'space123AbC*!'))

    # login with admin
    # create new user (spaces within), password with space at end
    # logout
    # try login with username and correct password
    # logout
    # try login with username without space and correct password without space at end
    # try login with username with space and password without space at end
    def test_login_user_with_space_password_end_space(self):
        self.driver.get("http://127.0.0.1:" + PORTS[0] + "/login")
        self.login('admin', 'admin123')
        self.create_user('Klaus peter', {'password': '123AbC*!space ', 'email': 'a2@b.com'})
        self.logout()
        self.assertTrue(self.login('Klaus peter', '123AbC*!space '))
        self.logout()
        self.assertFalse(self.login('Klauspeter', '123AbC*!space'))
        self.logout()
        self.assertFalse(self.login('Klaus peter', '123AbC*!space'))

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
        self.driver.get("http://127.0.0.1:" + PORTS[0] + "/login")
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_password_policy': 0})
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_user('admin2', {'password': '123AbC*!', 'admin_role': 1, 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertTrue(self.login('admin2', '123AbC*!'))
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('admin', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertFalse(self.login('admin', 'admin123'))
        self.login('admin2', '123AbC*!')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_user('admin', {'password': 'admin123', 'admin_role': 1, 'email': 'a4@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('admin', 'admin123')
        self.edit_user('admin2', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('admin', {'admin_role': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.edit_user('admin', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.fill_basic_config({'config_password_policy':1})
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()

    def test_password_policy(self):
        self.driver.get("http://127.0.0.1:" + PORTS[0] + "/login")
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # number of chars to less
        self.create_user('passwd_user', {'password': '1235lP+', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        # no lowercase
        self.create_user('passwd_user', {'password': '123456P+', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        # no uppercase
        self.create_user('passwd_user', {'password': '123456l+', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        # no specialchar
        self.create_user('passwd_user', {'password': '123456lP', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        # no number
        self.create_user('passwd_user', {'password': 'accHUlP+#', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        # no policy
        self.fill_basic_config({'config_password_policy': 0})
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_user('no_user', {'password': '1', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user("no_user", {'delete': 1})
        # no policy
        self.fill_basic_config({'config_password_policy': 1, 'config_password_number': 0})
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # no number
        self.create_user('number_user', {'password': 'accHUlP+#', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user("number_user", {'delete': 1})

        self.fill_basic_config({ 'config_password_number': 1, 'config_password_lower': 0})
        # no lowercase
        self.create_user('lower_user', {'password': '123456P+', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user("lower_user", {'delete': 1})
        time.sleep(1)

        self.fill_basic_config({'config_password_lower': 1, 'config_password_upper': 0})
        # no uppercase
        self.create_user('upper_user', {'password': '123456l+', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user("upper_user", {'delete': 1})
        time.sleep(1)

        self.fill_basic_config({ 'config_password_upper': 1, 'config_password_special': 0})
        # no specialchar
        self.create_user('special_user', {'password': '123456lP', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user("special_user", {'delete': 1})
        time.sleep(1)

        self.fill_basic_config({'config_password_special': 1, 'config_password_min_length': 5})
        # shorter length password
        self.create_user('short_user', {'password': '45lP+', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user("short_user", {'delete': 1})
        time.sleep(1)
        self.create_user('short_user', {'password': '5lP+', 'email': 'a3@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))

        self.fill_basic_config({'config_password_special': 1, 'config_password_min_length': 8})
        self.logout()


    @unittest.skipIf(not curl_available, "Skipping language detection, pycurl not available")
    def test_login_locale_select(self):
        # this one should work and throw not an error 500
        url = "http://127.0.0.1:" + PORTS[0] + "/login"
        self.assertTrue(check_response_language_header(url,
                                                       ['Accept-Language: de-de;q=0.9,en;q=0.7,*;q=0.8'],
                                                       200,
                                                       '<label for="username">Benutzername</label>'),
                        'Locale detect with "-" failed')
        self.assertTrue(check_response_language_header(url,
                                                       ['Accept-Language: *;q=0.9,de;q=0.7,en;q=0.8'],
                                                       200,
                                                       '<label for="username">Username</label>'),
                        'Locale detect with different q failed')
        self.assertTrue(check_response_language_header(url,
                                                       ['Accept-Language: zh_cn;q=0.9,de;q=0.8,en;q=0.7'],
                                                       200,
                                                       '<label for="username">用户名</label>'))
        self.assertTrue(check_response_language_header(url,
                                                       ['Accept-Language: xx'],
                                                       200,
                                                       '<label for="username">Username</label>'),
                        'Locale detect with unknown locale failed')
        self.assertTrue(check_response_language_header(url,
                                                       ['Accept-Language: *'],
                                                       200,
                                                       '<label for="username">Username</label>'),
                        'Locale detect with only "*" failed')

    # Check that digest Authentication header doesn't crash the application
    @unittest.skipIf(not curl_available, "Skipping auth_login, pycurl not available")
    def test_digest_login(self):
        url =  "http://127.0.0.1:" + PORTS[0] + "/login"
        self.assertTrue(digest_login(url, 200))

    # Check proxy login
    def test_proxy_login(self):
        self.driver.get("http://127.0.0.1:" + PORTS[0] + "/login")
        self.login('admin', 'admin123')
        self.fill_basic_config({'config_allow_reverse_proxy_header_login': 1 })
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # login not possible with empty header or with "X-LOGIN" header
        r = requests.session()
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("Calibre-Web | Login" in resp.text)
        r.headers['X-LOGIN'] = "X-Logo"
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("Calibre-Web | Login" in resp.text)
        r.close()
        # set 'config_reverse_proxy_login_header_name': "X-LOGIN"
        self.fill_basic_config({'config_reverse_proxy_login_header_name': "X-LOGIN" })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        r = requests.session()
        r.headers['X-LOGIN'] = ""
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("Calibre-Web | Login" in resp.text)
        # login with X-LOGIN wrong user -> no login
        r.headers['X-LOGIN'] = "admini"
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("Calibre-Web | Login" in resp.text)

        # login with X-LoGiN -> login
        r.headers['X-LoGiN'] = "admin"
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse("Calibre-Web | Login" in resp.text)
        r.close()

        # login with X-LoGiN -> login
        r = requests.session()
        r.headers['X-LoGiN'] = "admin"
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse("Calibre-Web | Login" in resp.text)
        r.close()

        # login with X-LOGIN -> login
        r = requests.session()
        r.headers['X-LOGIN'] = "admin"
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse("Calibre-Web | Login" in resp.text)
        r.close()
        self.assertTrue(self.login('admin', 'admin123'))
        self.fill_basic_config({'config_anonbrowse': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        r = requests.session()
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("Guest" in resp.text)
        r.close()
        r = requests.session()
        r.headers['X-LoGiN'] = "admin"
        resp = r.get("http://127.0.0.1:8083/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('class="hidden-sm">Admin</span>' in resp.text)
        r.close()
        # ToDo: Additional test with reverse proxy
        self.assertTrue(self.login('admin', 'admin123'))
        self.fill_basic_config({'config_allow_reverse_proxy_header_login': 0, 'config_anonbrowse': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()

    def test_proxy_login_opds(self):
        self.driver.get("http://127.0.0.1:" + PORTS[0] + "/login")
        self.login('admin', 'admin123')
        self.fill_basic_config({'config_allow_reverse_proxy_header_login': 1 })
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # login not possible to access opds with empty header
        r = requests.session()
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/opds")
        self.assertEqual(resp.status_code, 401)
        self.fill_basic_config({'config_reverse_proxy_login_header_name': "X-LOGIN" })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        r.headers['X-LoGiN'] = "admin"
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/opds")
        self.assertEqual(resp.status_code, 200)
        r.close()
        self.assertTrue(self.login('admin', 'admin123'))
        self.fill_basic_config({'config_allow_reverse_proxy_header_login': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()

    def test_proxy_login_multi_user(self):
        self.driver.get("http://127.0.0.1:" + PORTS[0] + "/login")
        self.login('admin', 'admin123')
        self.create_user('new_user1', {'password': '123AbC*!', 'email': 'a123@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_allow_reverse_proxy_header_login': 1,
                                'config_reverse_proxy_login_header_name': "X-LOGIN" })
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        # login not possible with empty header or with "X-LOGIN" header
        r = requests.session()
        r.headers['X-LOGIN'] = "admin"
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/me")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse("Calibre-Web | Login" in resp.text)
        self.assertTrue('<input type="text" class="form-control" name="name" id="name" value="admin" autocomplete="off">' in resp.text)
        r.headers['X-LOGIN'] = "new_user1"
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/me")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('<input type="text" class="form-control" name="name" id="name" value="new_user1" autocomplete="off">' in resp.text)
        r.close()

        self.assertTrue(self.login('admin', 'admin123'))
        self.edit_user('new_user1', {'delete': 1})
        self.fill_basic_config({'config_allow_reverse_proxy_header_login': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()

    def test_login_rename_user(self):
        self.driver.get("http://127.0.0.1:" + PORTS[0] + "/login")
        self.login('admin', 'admin123')
        self.create_user('new_user', {'password': '123AbC*!', 'email': 'a12@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertTrue(self.login('new_user', '123AbC*!'))
        self.goto_page('user_setup')
        self.assertFalse(self.check_element_on_page((By.ID, "name")))
        self.logout()
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('new_user', {'name': 'old_user'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.assertFalse(self.login('new_user', '123AbC*!'))
        self.assertTrue(self.login('old_user', '123AbC*!'))
        self.logout()
        self.assertTrue(self.login('admin', 'admin123'))
        self.edit_user('old_user', {'delete': 1})

    def test_login_remember_me(self):
        # simulate login, close browser, restart browser, session shall be renewed, user stays logged in
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on", "csrf_token": token.group(1)}
        r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        remember = r.cookies['remember_token']
        r.close()
        r = requests.session()
        site = r.get("http://127.0.0.1:" + PORTS[0], cookies={'remember_token': remember})
        self.assertTrue(re.search("Calibre-Web | Books", site.content.decode('utf-8')))
        cover = r.get("http://127.0.0.1:" + PORTS[0] + "/cover/8")
        self.assertEqual('21896', cover.headers['Content-Length'])
        r.get("http://127.0.0.1:" + PORTS[0] + "/logout")
        r.close()

        # simulate login without remember me, close browser, restart browser, no remember me token, user logged out and
        # redirected to login page
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "csrf_token": token.group(1)}
        r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertFalse(r.cookies.get('remember_token'))
        r.close()
        r = requests.session()
        site = r.get("http://127.0.0.1:" + PORTS[0])
        self.assertTrue(re.search("Calibre-Web | Login", site.content.decode('utf-8')))
        r.close()

    # try to access robots.txt file
    def test_robots(self):
        self.assertEqual(self.fail_access_page("http://127.0.0.1:" + PORTS[0] + "/robots.txt"), 2)
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, 'cps', 'static', 'robots.txt'), 'wb') as robotsfile:
            robotsfile.write('This is a robÄtsfile'.encode('utf-8'))
        r = requests.get("http://127.0.0.1:" + PORTS[0] + "/robots.txt")
        self.assertEqual(200, r.status_code)
        self.assertEqual('This is a robÄtsfile', r.text)
        time.sleep(2)
        os.unlink(os.path.join(CALIBRE_WEB_PATH + INDEX,'cps', 'static','robots.txt'))

    def test_next(self):
        self.driver.get("http://127.0.0.1:" + PORTS[0] + "/me")
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "kindle_mail")))
        self.logout()
        # no next parameter
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertEqual(200, page.status_code)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.close()
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "http:///example.com", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.close()
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "https:///example.com", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.close()
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "https:///example.com/test", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.close()
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "/admin/1", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.close()
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "../stats", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Statistics</title>" in page.text)
        r.close()
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "ftp://" + socket.gethostname() + "/admin/view", "csrf_token": token.group(1)}
        page = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertTrue("<title>Calibre-Web | Books</title>" in page.text)
        r.close()

    def test_magic_remote_login(self):
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({"config_remote_login":1})
        time.sleep(BOOT_TIME)
        self.logout()
        remote = self.check_element_on_page((By.ID, "remote_login"))
        self.assertTrue(remote)
        remote.click()
        verify_element = self.check_element_on_page((By.ID, "verify_url"))
        self.assertTrue(verify_element)
        verifiy_url = "/" + verify_element.text.lstrip('http://127.0.0.1:{}'.format(PORTS[0]))
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin',
                   'password': 'admin123',
                   'submit': "",
                   'next': verifiy_url,
                   "remember_me": "on",
                   "csrf_token": token.group(1)
                   }
        resp = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertEqual(resp.status_code, 200)
        r.close()
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # reuse token without problem
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin',
                   'password': 'admin123',
                   'submit': "",
                   'next': verifiy_url,
                   "remember_me": "on",
                   "csrf_token": token.group(1)
                   }
        resp = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertEqual(resp.status_code, 200)
        r.close()
        self.fill_basic_config({"config_remote_login": 0})
        time.sleep(BOOT_TIME)
        self.logout()
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin',
                   'password': 'admin123',
                   'submit': "",
                   'next': verifiy_url,
                   "remember_me": "on",
                   "csrf_token": token.group(1)
                   }
        resp = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        # Remote token not fond so redirect after login puts us to 403 page
        self.assertEqual(resp.status_code, 403)
        r.close()

    def test_login_cookie_steal(self):
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me": "on", "csrf_token": token.group(1)}
        resp = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertEqual(resp.status_code, 200)
        cookies = r.cookies.get_dict()
        r.get("http://127.0.0.1:" + PORTS[0] + "/logout")
        r.close()
        cookie_stealer = requests.session()
        resp = cookie_stealer.get("http://127.0.0.1:" + PORTS[0], cookies=cookies)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("logout", resp.text)
        cookie_stealer.close()

    def test_login_log_hack(self):
        r = requests.session()
        login_page = r.get("http://127.0.0.1:" + PORTS[0] + "/login")
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        user = "test\nHackdata"
        payload = {'username': user, 'password': 'admin123', 'submit': "", 'next': "/", "remember_me": "on",
                   "csrf_token": token.group(1)}
        resp = r.post("http://127.0.0.1:" + PORTS[0] + "/login", data=payload)
        self.assertEqual(resp.status_code, 200)
        time.sleep(5)
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX,'calibre-web.log'),'r') as logfile:
            data = logfile.read()
        self.assertTrue(len(re.findall('Login failed for user "testhackdata"', data)), "Linefeed in username gives wrong loglines")
        r.get("http://127.0.0.1:" + PORTS[0] + "/logout")
        r.close()
