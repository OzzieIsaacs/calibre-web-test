#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import time
import shutil

import helper_email_convert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from helper_ui import ui_class
from config_test import CALIBRE_WEB_PATH, TEST_DB, base_path, WAIT_GDRIVE
from helper_func import startup
from helper_func import save_logfiles, add_dependency, remove_dependency
from helper_gdrive import prepare_gdrive


RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
@unittest.skipIf(helper_email_convert.is_kepubify_not_present(), "Skipping convert, kepubify not found")
class TestEbookConvertGDriveKepubify(unittest.TestCase, ui_class):
    p = None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]
    email_server = None

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)
        prepare_gdrive()
        try:
            src = os.path.join(base_path, "files", "client_secrets.json")
            dst = os.path.join(CALIBRE_WEB_PATH + INDEX, "client_secrets.json")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            # delete settings_yaml file
            set_yaml = os.path.join(CALIBRE_WEB_PATH + INDEX, "settings.yaml")
            if os.path.exists(set_yaml):
                os.unlink(set_yaml)

            # delete gdrive file
            gdrive_db = os.path.join(CALIBRE_WEB_PATH + INDEX, "gdrive.db")
            if os.path.exists(gdrive_db):
                os.unlink(gdrive_db)

            # delete gdrive authenticated file
            src = os.path.join(base_path, 'files', "gdrive_credentials")
            dst = os.path.join(CALIBRE_WEB_PATH + INDEX, "gdrive_credentials")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,
                                          'config_binariesdir':'',
                                          'config_kepubifypath':helper_email_convert.kepubify_path()},
                    port=PORTS[0], index=INDEX, env={"APP_MODE": "test"})
            cls.fill_db_config({'config_use_google_drive': 1})
            time.sleep(2)

            cls.edit_user('admin', {'email': 'a5@b.com', 'kindle_mail': 'a1@b.com'})
            time.sleep(2)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        try:
            # close the browser window and stop calibre-web
            cls.driver.get("http://127.0.0.1:" + PORTS[0])
            cls.stop_calibre_web()
            cls.driver.quit()
            cls.p.terminate()
        except Exception as e:
            print(e)
        time.sleep(2)
        remove_dependency(cls.dependency)

        src1 = os.path.join(CALIBRE_WEB_PATH + INDEX, "client_secrets.json")
        src = os.path.join(CALIBRE_WEB_PATH + INDEX, "gdrive_credentials")
        if os.path.exists(src):
            os.chmod(src, 0o764)
            try:
                os.unlink(src)
            except PermissionError:
                print('gdrive_credentials delete failed')
        if os.path.exists(src1):
            os.chmod(src1, 0o764)
            try:
                os.unlink(src1)
            except PermissionError:
                print('client_secrets.json delete failed')

        save_logfiles(cls, cls.__name__)

    def tearDown(self):
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
        self.fill_basic_config({'config_kepubifypath':helper_email_convert.kepubify_path()})

    # Set excecutable to wrong exe and start convert
    # set excecutable not existing and start convert
    # set excecutable non excecutable and start convert
    def test_convert_wrong_excecutable(self):
        self.fill_basic_config({'config_kepubifypath':'/opt/kepubify/ebook-polish'})
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='Kepubify']/following::td[1]"))
        self.assertEqual(element.text, 'not installed')
        details = self.get_book_details(1)
        self.assertFalse(details['kindlebtn'])
        details = self.get_book_details(5)
        self.assertEqual(len(details['kindle']), 1)
        vals = self.get_convert_book(5)
        # ToDo: change behavior convert should only be visible if ebookconverter has valid entry
        self.assertTrue(vals['btn_from'])
        self.assertTrue(vals['btn_to'])

        nonexec = os.path.join(CALIBRE_WEB_PATH + INDEX, 'app.db')
        self.fill_basic_config({'config_kepubifypath': nonexec})
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='Kepubify']/following::td[1]"))
        self.assertEqual(element.text, 'Execution permissions missing')
        self.fill_basic_config({'config_kepubifypath': helper_email_convert.calibre_path()})

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
        #i = 0
        #while i < 10:
        #    time.sleep(2)
        #    task_len, ret = self.check_tasks(tasks)
        #    if task_len == 1:
        #        if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
        #            break
        #    i += 1
        self.assertEqual(ret[-1]['result'], 'Finished')
        memory = len(ret)

        self.logout()
        self.login('solo', '123AbC*!')
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
        # tasks = ret
        task_len, ret = self.wait_tasks(tasks, 1)
        #i = 0
        #while i < 10:
        #    time.sleep(2)
        #    task_len, ret = self.check_tasks(ret)
        #    if task_len == 1:
        #        if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
        #            break
        #    i += 1
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
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        time.sleep(1)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(WAIT_GDRIVE*2)
        #i = 0
        task_len, ret = self.wait_tasks(tasks, 1)
        #tasks = ret
        #while i < 10:
        #    time.sleep(2)
        #    task_len, ret = self.check_tasks(tasks)
        #    if task_len == 1:
        #        if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
        #            break
        #    i += 1
        self.assertEqual(ret[-1]['result'], 'Finished')
        # self.assertEqual(len(ret), len(ret2), "Reconvert of book started")
        self.assertEqual(ret[-1]['result'], 'Finished')
