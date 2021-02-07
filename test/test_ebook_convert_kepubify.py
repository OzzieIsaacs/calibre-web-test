#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import time

from helper_email_convert import AIOSMTPServer
import helper_email_convert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from helper_ui import ui_class
from config_test import CALIBRE_WEB_PATH, TEST_DB
from helper_func import startup
from helper_func import save_logfiles


@unittest.skipIf(helper_email_convert.is_kepubify_not_present(), "Skipping convert, kepubify not found")
class TestEbookConvertKepubify(unittest.TestCase, ui_class):
    p = None
    driver = None
    email_server = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,
                                          'config_converterpath':'',
                                          'config_kepubifypath':helper_email_convert.kepubify_path()})

            cls.edit_user('admin', {'email': 'a5@b.com', 'kindle_mail': 'a1@b.com'})
            time.sleep(2)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        try:
            # close the browser window and stop calibre-web
            cls.driver.get("http://127.0.0.1:8083")
            cls.stop_calibre_web()
            cls.driver.quit()
            cls.p.terminate()
        except Exception as e:
            print(e)
        time.sleep(2)
        save_logfiles(cls, cls.__name__)

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin', 'admin123')

    # deactivate converter and check convert are not visible anymore
    def test_convert_deactivate(self):
        self.fill_basic_config({'config_kepubifypath': ""})
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='kepubify']/following::td[1]"))
        self.assertEqual(element.text, 'not installed')
        details = self.get_book_details(5)
        self.assertFalse(details['kindlebtn'])
        vals = self.get_convert_book(5)
        self.assertFalse(vals['btn_from'])
        self.assertFalse(vals['btn_to'])
        self.fill_basic_config({'config_kepubifypath':helper_email_convert.kepubify_path()})

    # Set excecutable to wrong exe and start convert
    # set excecutable not existing and start convert
    # set excecutable non excecutable and start convert
    def test_convert_wrong_excecutable(self):
        task_len = len(self.check_tasks())
        self.fill_basic_config({'config_kepubifypath':'/opt/kepubify/ebook-polish'})
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='kepubify']/following::td[1]"))
        self.assertEqual(element.text, 'not installed')
        details = self.get_book_details(5)
        self.assertFalse(details['kindlebtn'])
        vals = self.get_convert_book(5)
        # ToDo: change behavior convert should only be visible if ebookconverter has valid entry
        self.assertTrue(vals['btn_from'])
        self.assertTrue(vals['btn_to'])

        nonexec = os.path.join(CALIBRE_WEB_PATH, 'app.db')
        self.fill_basic_config({'config_kepubifypath': nonexec})
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='kepubify']/following::td[1]"))
        self.assertEqual(element.text, 'Execution permissions missing')
        self.fill_basic_config({'config_kepubifypath': helper_email_convert.kepubify_path()})

    # convert epub to kepub
    # try start conversion of mobi -> not visible
    # start conversion of epub -> kepub
    # create user
    # logout
    # check conversion result for non admin user -> nothing visible
    # start conversion for non admin user
    # check conversion result for non admin user -> own conversion visible without username
    # logout
    # login as admin
    # check conversion result conversion of other user visible
    def test_convert_only(self):
        vals = self.get_convert_book(7)
        self.assertFalse(vals['btn_from'])
        self.assertFalse(vals['btn_to'])

        vals = self.get_convert_book(10)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        self.assertEqual(len(select.options), 2)
        select = Select(vals['btn_to'])
        self.assertEqual(len(select.options), 2)
        select.select_by_visible_text('KEPUB')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)

        self.create_user('solo', {'password': '123', 'email': 'a@b.com', 'edit_role':1})
        time.sleep(2)
        ret = self.check_tasks()
        self.assertEqual(ret[-1]['result'], 'Finished')
        memory = len(ret)

        self.logout()
        self.login('solo', '123')
        ret = self.check_tasks()
        self.assertEqual(0, len(ret))

        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        self.assertEqual(len(select.options), 2)
        select = Select(vals['btn_to'])
        self.assertEqual(len(select.options), 2)
        select.select_by_visible_text('KEPUB')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(5)
        ret = self.check_tasks()
        self.assertEqual(ret[-1]['result'], 'Finished')

        self.logout()
        self.login('admin', 'admin123')
        ret = self.check_tasks()
        self.assertEqual(memory + 1, len(ret))

        # Check reconvert denied, but task succeded
        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('KEPUB')
        self.driver.find_element_by_id("btn-book-convert").click()
        time.sleep(1)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(5)
        ret = self.check_tasks()
        # self.assertEqual(len(ret), len(ret2), "Reconvert of book started")
        self.assertEqual(ret[-1]['result'], 'Finished')
