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


RESOURCES = {'ports': 1}

PORTS = ['8083']


@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
class TestSetupGdrive(unittest.TestCase, ui_class):
    p=None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)


        try:
            # remove client_secrets.file
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

            startup(cls, cls.py_version, {}, port=PORTS[0], 
                    only_startup=True, env={"APP_MODE": "test"})
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
            cls.driver.get("http://127.0.0.1:" + PORTS[0])
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
        self.fill_db_config(dict(config_calibre_dir=TEST_DB[:-1], config_use_google_drive=1))
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))
        # Tick gdrive and valid db
        self.fill_db_config(dict(config_calibre_dir=TEST_DB, config_use_google_drive=1))
        # error no json file
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))
        use_gdrive = self.check_element_on_page((By.ID, "config_use_google_drive"))
        self.assertTrue(use_gdrive)
        self.assertFalse(use_gdrive.is_selected())

        dst = os.path.join(CALIBRE_WEB_PATH, "client_secrets.json")
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

