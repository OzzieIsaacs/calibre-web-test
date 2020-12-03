#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import time
import shutil
import io

from helper_email_convert import AIOSMTPServer
import helper_email_convert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from helper_ui import ui_class
from config_test import CALIBRE_WEB_PATH, TEST_DB, base_path, WAIT_GDRIVE
from helper_func import startup
from helper_func import save_logfiles, add_dependency, remove_dependency
from helper_gdrive import prepare_gdrive, connect_gdrive


@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
@unittest.skipIf(helper_email_convert.is_calibre_not_present(), "Skipping convert, calibre not found")
class TestEbookConvertCalibreGDrive(unittest.TestCase, ui_class):
    p=None
    driver = None
    dependency = ["oauth2client", "PyDrive", "PyYAML", "google-api-python-client", "httplib2", "Pillow", "lxml"]
    email_server = None

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)

        prepare_gdrive()
        try:
            src = os.path.join(base_path, "files", "client_secrets.json")
            dst = os.path.join(CALIBRE_WEB_PATH, "client_secrets.json")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            # delete settings_yaml file
            set_yaml = os.path.join(CALIBRE_WEB_PATH, "settings.yaml")
            if os.path.exists(set_yaml):
                os.unlink(set_yaml)

            # delete gdrive file
            gdrive_db = os.path.join(CALIBRE_WEB_PATH, "gdrive.db")
            if os.path.exists(gdrive_db):
                os.unlink(gdrive_db)

            # delete gdrive authenticated file
            src = os.path.join(base_path, 'files', "gdrive_credentials")
            dst = os.path.join(CALIBRE_WEB_PATH, "gdrive_credentials")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            # start email server
            cls.email_server = AIOSMTPServer(
                hostname='127.0.0.1',
                port=1025,
                only_ssl=False,
                timeout=10
            )

            cls.email_server.start()

            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,
                                          'config_use_google_drive': 1,
                                          'config_log_level': 'DEBUG',
                                          'config_kepubifypath': '',
                                          'config_converterpath':helper_email_convert.calibre_path()},
                    only_metadata=True)
            cls.fill_basic_config({'config_google_drive_folder': 'test'})

            cls.edit_user('admin', {'email': 'a5@b.com', 'kindle_mail': 'a1@b.com'})
            cls.setup_server(True, {'mail_server':'127.0.0.1', 'mail_port':'1025',
                                    'mail_use_ssl':'None', 'mail_login':'name@host.com', 'mail_password':'1234',
                                    'mail_from':'name@host.com'})
            time.sleep(2)
        except Exception as e:
            try:
                print(e)
                cls.driver.quit()
                cls.p.kill()
            except Exception:
                pass


    @classmethod
    def tearDownClass(cls):
        cls.email_server.stop()
        try:
            cls.driver.get("http://127.0.0.1:8083")
            cls.stop_calibre_web()
            # close the browser window and stop calibre-web
            cls.driver.quit()
            cls.p.terminate()
        except Exception as e:
            print(e)
        time.sleep(2)

        remove_dependency(cls.dependency)

        src1 = os.path.join(CALIBRE_WEB_PATH, "client_secrets.json")
        src = os.path.join(CALIBRE_WEB_PATH, "gdrive_credentials")
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

        save_logfiles(cls.__name__)

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin', 'admin123')
        self.fill_basic_config({'config_calibre': ''})


    # set parameters for convert ( --margin-right 11.9) and start conversion -> conversion okay
    # set parameters for convert ( --margin-righ) and start conversion -> conversion failed
    # remove parameters for conversion
    def test_convert_parameter(self):
        time.sleep(WAIT_GDRIVE)
        task_len = len(self.check_tasks())
        self.fill_basic_config({'config_calibre': '--margin-right 11.9'})
        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('LIT')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 20:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(len(ret) - 1, task_len)
        self.assertEqual(ret[-1]['result'], 'Finished')

        self.fill_basic_config({'config_calibre': '--margin-rght 11.9'})
        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('LRF')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(8)
        ret = self.check_tasks()
        self.assertEqual(len(ret), (task_len + 2) % 20)
        self.assertEqual(ret[-1]['result'], 'Failed')
        self.fill_basic_config({'config_calibre': ''})

    # press send to kindle for not converted book
    # wait for finished
    # check email received
    def test_convert_email(self):
        self.setup_server(True, {'mail_password': '10234', 'mail_use_ssl':'None'})
        task_len = len(self.check_tasks())
        details = self.get_book_details(9)
        self.assertEqual(len(details['kindle']), 1)
        details['kindlebtn'].click()
        i = 0
        while i < 40:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 2:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertTrue("Email" in ret[-1]['task'])
        self.assertTrue("Convert" in ret[-2]['task'])
        self.assertEqual(ret[-2]['result'], 'Finished')
        self.assertEqual(ret[-1]['result'], 'Finished')
        self.setup_server(True, {'mail_password': '1234'})


    # check conversion and email started and conversion fails
    # move valid file to invalid filename and create random file with extension for conversion
    # start conversion. Check conversion fails
    # delete ranom file and move invalid filename back to vaild filename
    # convert valid file
    def test_convert_failed_and_email(self):
        fs = connect_gdrive("test")
        orig_file = os.path.join( 'test', 'Leo Baskerville','book8 (8)',
                                 u'book8 - Leo Baskerville.epub').replace('\\', '/')
        moved_file = os.path.join('test', 'Leo Baskerville', 'book8 (8)',
                                  u'book8.epub').replace('\\', '/')
        fs.move(orig_file, moved_file, overwrite=True)

        fout = io.BytesIO()
        fout.write(os.urandom(124))
        fs.upload(orig_file, fout)
        fout.close()

        # with open(orig_file, 'wb') as fout:
        #    fout.write(os.urandom(124))
        self.setup_server(True, {'mail_password': '10234'})
        task_len = len(self.check_tasks())
        details = self.get_book_details(8)
        self.assertEqual(len(details['kindle']), 1)
        details['kindlebtn'].click()
        i = 0
        while i < 20:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Failed')
        self.setup_server(True, {'mail_password': '1234'})
        fs.remove(orig_file)
        fs.move(moved_file, orig_file, overwrite=True)
        fs.close()

    # convert everything to everything
    # start conversion of mobi -> azw3
    # start conversion of epub -> pdf
    # start conversion of epub -> txt
    # start conversion of epub -> fb2
    # start conversion of epub -> lit
    # start conversion of epub -> html
    # start conversion of epub -> rtf
    # start conversion of epub -> odt
    # start conversion of azw3 -> mobi
    # create user
    # logout
    # check conversion result for non admin user -> nothing visible
    # start conversion for non admin user
    # check conversion result for non admin user -> own conversion visible without username
    # logout
    # login as admin
    # check conversion result conversion of other user visible
    def test_convert_only(self):
        task_len = len(self.check_tasks())
        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('AZW3')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('EPUB')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('TXT')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('FB2')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('LIT')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('HTMLZ')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

        self.create_user('solo', {'password': '123', 'email': 'a@b.com', 'edit_role':1})
        i = 0
        while i < 50:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len >= 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        lenret = len(ret)
        if lenret > 6:
            self.assertEqual(ret[-6]['result'], 'Finished')
        if lenret > 5:
            self.assertEqual(ret[-5]['result'], 'Finished')
        if lenret > 4:
            self.assertEqual(ret[-4]['result'], 'Finished')
        if lenret > 3:
            self.assertEqual(ret[-3]['result'], 'Finished')
        if lenret > 2:
            self.assertEqual(ret[-2]['result'], 'Finished')
        if lenret > 1:
            self.assertEqual(ret[-1]['result'], 'Finished')
        memory = len(ret)

        self.logout()
        self.login('solo', '123')
        ret = self.check_tasks()
        task_len = len(ret)
        self.assertEqual(0, task_len)

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('PDF')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('RTF')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 10:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Finished')

        self.logout()
        self.login('admin', 'admin123')
        time.sleep(WAIT_GDRIVE)
        ret = self.check_tasks()
        self.assertEqual(memory + 1, len(ret))


    # start conversion of epub -> mobi
    # wait for finished
    # start sending e-mail
    # check email received
    # check filename
    def test_email_only(self):
        self.setup_server(True, {'mail_use_ssl': 'None', 'mail_password': '10234'})
        task_len = len(self.check_tasks())
        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('MOBI')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 20:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Finished')
        details = self.get_book_details(8)
        details['kindlebtn'].click()
        # conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        # self.assertTrue(conv)
        # conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 20:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 2:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Finished')
        self.assertGreaterEqual(self.email_server.handler.message_size, 17477)
        self.setup_server(False, {'mail_password':'1234'})


    # check behavior for failed email (size)
    # conversion okay, email failed
    def test_email_failed(self):
        self.setup_server(False, {'mail_password': '10234'})
        task_len = len(self.check_tasks())
        details = self.get_book_details(5)
        self.email_server.handler.set_return_value(552)
        # = '552 Requested mail action aborted: exceeded storage allocation'
        details['kindlebtn'].click()
        # conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][1].text))
        # self.assertTrue(conv)
        # conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 30:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 2:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Failed')
        self.email_server.handler.set_return_value(0)
        self.setup_server(False, {'mail_password':'1234'})
