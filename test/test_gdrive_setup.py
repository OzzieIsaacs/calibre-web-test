#!/usr/bin/env python
# -*- coding: utf-8 -*-


import unittest
from base_test import ParallelTestCase
import os
import json
import time
import shutil

from selenium.webdriver.common.by import By
from config_test import base_path
from helper_func import startup


@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
class TestSetupGdrive(ParallelTestCase):
    p=None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version, {},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir,
                    only_startup=True)
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
            cls.driver.get("http://127.0.0.1:" + cls.worker_port)
            cls.stop_calibre_web()
            # close the browser window and stop calibre-web
            cls.driver.quit()
            cls.p.terminate()
        except Exception as e:
            print(e)

        src1 = os.path.join(cls.app_dir, "client_secrets.json")
        src = os.path.join(cls.app_dir, "client_secret.json")
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
        super().tearDownClass()


    def test_config_gdrive(self):
        # invalid db and tick gdrive
        self.fill_db_config(dict(config_calibre_dir=self.temp_dir[:-1], config_use_google_drive=1))
        confirm = self.check_element_on_page((By.ID, 'invalid_confirm'))
        time.sleep(1)
        self.assertTrue(confirm)
        confirm.click()
        # Tick gdrive and valid db
        time.sleep(1)
        self.fill_db_config(dict(config_calibre_dir=self.temp_dir, config_use_google_drive=1))
        # error no json file
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))
        use_gdrive = self.check_element_on_page((By.ID, "config_use_google_drive"))
        self.assertTrue(use_gdrive)
        self.assertFalse(use_gdrive.is_selected())

        dst = os.path.join(self.app_dir, "client_secrets.json")
        src = os.path.join(base_path, "files", "client_secrets.json")
        shutil.copy(src, dst)
        os.chmod(dst, 0o040)
        self.fill_db_config(dict(config_use_google_drive=1))

        use_gdrive = self.check_element_on_page((By.ID, "config_use_google_drive"))
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))
        self.assertTrue(use_gdrive)
        self.assertFalse(use_gdrive.is_selected())

        os.chmod(dst, 0o700)
        with open(dst, 'r') as settings:
            content = json.load(settings)
        content.pop('web', None)
        with open(dst, 'w') as data_file:
            json.dump(content, data_file)
        time.sleep(1)

        self.fill_db_config(dict(config_use_google_drive=1))
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))

        shutil.copy(src, dst)
        time.sleep(1)
        self.fill_db_config(dict(config_use_google_drive=1))
        # no error in json file
        self.assertFalse(self.check_element_on_page((By.ID, 'flash_danger')))
        time.sleep(1)
        auth_button = self.check_element_on_page((By.ID, "gdrive_auth"))
        self.assertTrue(auth_button)
        auth_button.click()
        g_login = self.check_element_on_page((By.ID, "identifierId"))
        self.assertTrue(g_login)

