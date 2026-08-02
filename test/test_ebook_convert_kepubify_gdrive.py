# -*- coding: utf-8 -*-

import unittest
from base_test import ParallelTestCase
import os
import time
import stat

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from config_test import base_path, WAIT_GDRIVE
from helper_func import startup
from helper_email_convert import kepubify_path, is_kepubify_not_present

@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
@unittest.skipIf(is_kepubify_not_present(), "Skipping convert, kepubify not found")
class TestEbookConvertGDriveKepubify(ParallelTestCase):
    resource_lock = "gdrive"


    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]
    email_server = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir':cls.temp_dir,
                                          'config_binariesdir':'',
                                          'config_kepubifypath':kepubify_path()},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir)
            cls.fill_db_config({'config_use_google_drive': 1})
            time.sleep(2)

            cls.edit_user('admin', {'email': 'a5@b.com', 'kindle_mail': 'a1@b.com'})
            time.sleep(2)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    def tearDown(self):
        super().tearDown()
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin', 'admin123')

    # deactivate converter and check convert are not visible anymore
    def test_convert_deactivate(self):
        time.sleep(WAIT_GDRIVE)
        self.fill_basic_config({'config_kepubifypath': ""})
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='Kepubify']/following::td[1]"))
        self.assertEqual(element.text, 'not installed')
        details = self.get_book_details(1)
        self.assertFalse(details['kindlebtn'])
        vals = self.get_convert_book(1)
        self.assertFalse(vals['btn_from'])
        self.assertFalse(vals['btn_to'])
        self.fill_basic_config({'config_kepubifypath':kepubify_path()})

    # Set excecutable to wrong exe and start convert
    # set excecutable not existing and start convert
    # set excecutable non excecutable and start convert
    def test_convert_wrong_excecutable(self):
        self.fill_basic_config({'config_kepubifypath':'/opt/kepubify/ebook-polish'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='Kepubify']/following::td[1]"))
        self.assertEqual(element.text, 'not installed')
        details = self.get_book_details(1)
        self.assertFalse(details['kindlebtn'])
        details = self.get_book_details(5)
        self.assertEqual(len(details['kindle']), 1)
        vals = self.get_convert_book(5)
        self.assertTrue(vals['btn_from'])
        self.assertTrue(vals['btn_to'])

        kepubify = kepubify_path()
        original_mode = os.stat(kepubify).st_mode
        try:
            os.chmod(kepubify, original_mode & ~stat.S_IXUSR & ~stat.S_IXGRP & ~stat.S_IXOTH)
            self.fill_basic_config({'config_kepubifypath': os.path.dirname(kepubify)})
            self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
            self.goto_page('nav_about')
            element = self.check_element_on_page((By.XPATH, "//tr/th[text()='Kepubify']/following::td[1]"))
            self.assertEqual(element.text, 'not installed')
        finally:
            os.chmod(kepubify, original_mode)
        self.fill_basic_config({'config_kepubifypath': os.path.dirname(kepubify)})

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
        tasks = self.check_tasks()
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
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        time.sleep(1)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(WAIT_GDRIVE)

        self.create_user('solo', {'password': '123AbC*!', 'email': 'a@b.com', 'edit_role': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(WAIT_GDRIVE*2 + 5)
        task_len, ret = self.wait_tasks(tasks, 1)
        self.assertEqual(ret[-1]['result'], 'Finished')
        memory = len(ret)

        self.logout()
        self.login('solo', '123AbC*!')
        time.sleep(WAIT_GDRIVE*2 + 5)
        ret = self.check_tasks()
        self.assertEqual(0, len(ret))

        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        self.assertEqual(len(select.options), 2)
        select = Select(vals['btn_to'])
        self.assertEqual(len(select.options), 2)
        select.select_by_visible_text('KEPUB')
        self.check_element_on_page((By.ID,"btn-book-convert")).click()
        time.sleep(1)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(WAIT_GDRIVE*2)
        task_len, ret = self.wait_tasks(ret, 1)
        self.assertEqual(ret[-1]['result'], 'Finished')

        self.logout()
        self.login('admin', 'admin123')
        time.sleep(WAIT_GDRIVE*2)
        ret = self.check_tasks()
        self.assertEqual(memory + 1, len(ret))

        # Check reconvert denied, but task succeded
        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('KEPUB')
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        time.sleep(1)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(WAIT_GDRIVE*2)
        task_len, tasks = self.wait_tasks(ret, 1)
        self.assertEqual(tasks[-1]['result'], 'Finished')
        # self.assertEqual(len(ret), len(ret2), "Reconvert of book started")
        self.assertEqual(tasks[-1]['result'], 'Finished')