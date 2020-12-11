#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import json
from selenium.webdriver.common.by import By
import time
import shutil
from helper_ui import ui_class

from config_test import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME, base_path
from helper_func import add_dependency, remove_dependency, startup
from helper_func import save_logfiles
# test editing books on gdrive


# @unittest.skip("Not Implemented")
class TestSetupGdrive(unittest.TestCase, ui_class):
    p=None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)

        # remove slient_secrets.file
        try:
            dst = os.path.join(CALIBRE_WEB_PATH, "client_secrets.json")
            if os.path.exists(dst):
                os.unlink(dst)


            # delete settings_yaml file
            set_yaml = os.path.join(CALIBRE_WEB_PATH, "settings.yaml")
            if os.path.exists(set_yaml):
                os.unlink(set_yaml)

            # delete gdrive file
            gdrive_db = os.path.join(CALIBRE_WEB_PATH, "gdrive.db")
            if os.path.exists(gdrive_db):
                os.unlink(gdrive_db)

            # delete gdrive authenticated file
            gdauth = os.path.join(CALIBRE_WEB_PATH, "gdrive_credentials")
            if os.path.exists(gdauth):
                os.unlink(gdauth)

            startup(cls, cls.py_version, {}, only_startup=True)
        except Exception as e:
            try:
                print(e)
                cls.driver.quit()
                cls.p.kill()
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.get("http://127.0.0.1:8083")
            cls.stop_calibre_web()
            # close the browser window and stop calibre-web
            cls.driver.quit()
            cls.p.terminate()
        except Exception as e:
            print(e)

        remove_dependency(cls.dependency)

        src1 = os.path.join(CALIBRE_WEB_PATH, "client_secrets.json")
        src = os.path.join(CALIBRE_WEB_PATH, "client_secret.json")
        if os.path.exists(src1):
            os.chmod(src1, 0o764)
            try:
                os.unlink(src1)
            except PermissionError:
                print('File delete failed')

        if os.path.exists(src):
            os.chmod(src, 0o764)
            try:
                os.unlink(src)
            except PermissionError:
                print('File delete failed')
        save_logfiles(cls, cls.__name__)


    def test_config_gdrive(self):
        # invalid db and tick gdrive
        self.fill_initial_config(dict(config_calibre_dir=TEST_DB[:-1], config_use_google_drive=1))
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_alert')))
        # Tick gdrive and valid db
        self.fill_initial_config(dict(config_calibre_dir=TEST_DB, config_use_google_drive=1))
        # error no json file
        self.assertFalse(self.check_element_on_page((By.ID, "gdrive_error")).is_displayed())
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        login = self.check_element_on_page((By.NAME, "login"))
        use_gdrive = self.check_element_on_page((By.ID, "config_use_google_drive"))
        self.assertTrue(use_gdrive)
        self.assertFalse(use_gdrive.is_selected())
        use_gdrive.click()
        self.assertTrue(self.check_element_on_page((By.ID, "gdrive_error")).is_displayed())

        dst = os.path.join(CALIBRE_WEB_PATH, "client_secrets.json")
        src = os.path.join(base_path, "files", "client_secrets.json")
        shutil.copy(src, dst)
        os.chmod(dst, 0o040)

        self.assertTrue(login)
        login.click()
        # message continue after login
        time.sleep(BOOT_TIME)
        self.login('admin', 'admin123')
        self.goto_page('basic_config')
        if os.name != 'nt':
            gdriveError = self.check_element_on_page((By.ID, "gdrive_error"))
            self.assertTrue(gdriveError)
            self.assertFalse(gdriveError.is_displayed())
        use_gdrive = self.check_element_on_page((By.ID, "config_use_google_drive"))
        self.assertTrue(use_gdrive)
        use_gdrive.click()
        if os.name != 'nt':
            # error json file not readable
            self.assertTrue(self.check_element_on_page((By.ID, "gdrive_error")).is_displayed())
        os.chmod(dst, 0o700)
        with open(dst, 'r') as settings:
            content = json.load(settings)

        # callback = content['web']['redirect_uris'][0].strip('/gdrive/callback')
        content.pop('web', None)

        with open(dst, 'w') as data_file:
            json.dump(content, data_file)
        time.sleep(1)
        self.goto_page('basic_config')
        use_gdrive = self.check_element_on_page((By.ID, "config_use_google_drive"))
        use_gdrive.click()
        # error json file not configured for web
        self.assertTrue(self.check_element_on_page((By.ID, "gdrive_error")).is_displayed())

        shutil.copy(src, dst)
        time.sleep(1)
        self.goto_page('basic_config')
        use_gdrive = self.check_element_on_page((By.ID, "config_use_google_drive"))
        use_gdrive.click()
        # no error in json file
        self.assertFalse(self.check_element_on_page((By.ID, "gdrive_error")))
        save = self.check_element_on_page((By.NAME, "submit"))
        self.assertTrue(save)
        save.click()
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        time.sleep(1)
        auth_button = self.check_element_on_page((By.ID, "gdrive_auth"))
        time.sleep(1)
        self.assertTrue(auth_button)
        auth_button.click()
        g_login = self.check_element_on_page((By.ID, "identifierId"))
        self.assertTrue(g_login)















    def edit_author(self):
        self.assertIsNone('Not Implemented')

    # series with unicode spaces, ,|,
    def edit_series(self):
        pass

    def edit_category(self):
        pass

    # choose language not part ob lib
    def edit_language(self):
        self.assertIsNone('Not Implemented')

    def edit_publishing_date(self):
        self.assertIsNone('Not Implemented')

    def edit_publisher(self):
        self.assertIsNone('Not Implemented')

    # change rating, delete rating
    # check if book with rating of 4 stars appears in list of hot books
    def edit_rating(self):
        self.assertIsNone('Not Implemented')

    # change comments, add comments, delete comments
    def edit_comments(self):
        self.assertIsNone('Not Implemented')

    # change comments, add comments, delete comments
    def edit_custom_bool(self):
        self.assertIsNone('Not Implemented')

    # change comments, add comments, delete comments
    def edit_custom_rating(self):
        self.assertIsNone('Not Implemented')

    # change comments, add comments, delete comments
    def edit_custom_single_select(self):
        self.assertIsNone('Not Implemented')

    # change comments, add comments, delete comments
    def edit_custom_text(self):
        self.assertIsNone('Not Implemented')

    # change comments, add comments, delete comments
    def typeahead_language(self):
        self.assertIsNone('Not Implemented')

    def typeahead_series(self):
        self.assertIsNone('Not Implemented')

    def typeahead_author(self):
        self.assertIsNone('Not Implemented')

    def typeahead_tag(self):
        self.assertIsNone('Not Implemented')

    def typeahead_publisher(self):
        self.assertIsNone('Not Implemented')

    def upload_cover_hdd(self):
        self.assertIsNone('Not Implemented')

    def delete_format(self):
        self.assertIsNone('Not Implemented')

    def delete_book(self):
        self.assertIsNone('Not Implemented')

    # check metadata_recognition
    def upload_book_pdf(self):
        self.assertIsNone('Not Implemented')

    # check metadata_recognition
    def upload_book_fb2(self):
        self.assertIsNone('Not Implemented')

    def upload_book_lit(self):
        self.assertIsNone('Not Implemented')

    # check metadata_recognition
    def upload_book_epub(self):
        self.assertIsNone('Not Implemented')

    # check cover recognition
    def upload_book_cbz(self):
        self.assertIsNone('Not Implemented')

    # check cover recognition
    def upload_book_cbt(self):
        self.assertIsNone('Not Implemented')

    # check cover recognition
    def upload_book_cbr(self):
        self.assertIsNone('Not Implemented')

    # database errors
    def database_errors(self):
        self.assertIsNone('Not Implemented')

    # download of books
    def download_books(self):
        self.assertIsNone('Not Implemented')

