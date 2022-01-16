#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
from selenium.webdriver.common.by import By
from selenium import webdriver
import time
import shutil
from helper_ui import ui_class

from config_test import CALIBRE_WEB_PATH, TEST_DB, base_path, BOOT_TIME, WAIT_GDRIVE
from helper_func import add_dependency, remove_dependency, startup
from helper_func import save_logfiles
from helper_gdrive import prepare_gdrive
from subproc_wrapper import process_open

# test gdrive database
@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
class TestCliGdrivedb(unittest.TestCase, ui_class):
    p=None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)

        prepare_gdrive()
        try:
            try:
                os.remove(os.path.join(CALIBRE_WEB_PATH, 'app.db'))
                shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, 'hü lo'), ignore_errors=True)
            except Exception:
                pass
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

            cls.driver = webdriver.Firefox()
            cls.driver.implicitly_wait(10)
            cls.driver.maximize_window()

        except Exception as e:
            try:
                print(e)
                cls.driver.quit()
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.get("http://127.0.0.1:8083")
            cls.stop_calibre_web()
            # close the browser window and stop calibre-web
            cls.p.terminate()
        except Exception as e:
            print(e)
        try:
            cls.driver.quit()
        except Exception as e:
            pass
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

        save_logfiles(cls, cls.__name__)

    def tearDown(self):
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'app.db'))
            shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, 'hü lo'), ignore_errors=True)
        except Exception as e:
            print(e)

    def wait_page_has_loaded(self):
        time.sleep(1)
        while True:
            time.sleep(1)
            page_state = self.driver.execute_script('return document.readyState;')
            if page_state == 'complete':
                break
        time.sleep(1)

    def start_cw(self, cw_path, gdrive_path=None):
        parameter = [self.py_version, cw_path]
        quotes = [1]
        if gdrive_path:
            parameter.extend(['-g', gdrive_path])
            quotes.extend([3])
        self.p = process_open(parameter, quotes)
        # create a new Firefox session
        time.sleep(BOOT_TIME)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:8083")

        # Wait for config screen to show up
        self.fill_db_config({'config_calibre_dir': TEST_DB})

        # wait for cw to be ready
        time.sleep(2)

        self.assertTrue(self.check_element_on_page((By.NAME, "query")))

    def test_gdrive_db_nonwrite(self):
        self.start_cw(os.path.join(CALIBRE_WEB_PATH, u'cps.py'))
        self.fill_db_config({'config_use_google_drive': 1})
        time.sleep(BOOT_TIME)
        self.fill_db_config({'config_google_drive_folder': 'test'})
        time.sleep(BOOT_TIME)
        self.driver.get("http://127.0.0.1:8083")
        self.stop_calibre_web()
        time.sleep(5) # shutdowntime
        self.p.terminate()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        gdrive_db = os.path.join(CALIBRE_WEB_PATH, "gdrive.db")
        self.assertTrue(os.path.exists(gdrive_db))
        os.chmod(gdrive_db, 0o400)
        self.p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py')], [1])
        # create a new Firefox session
        time.sleep(BOOT_TIME)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:8083")
        os.chmod(gdrive_db, 0o654)
        self.stop_calibre_web()
        self.p.terminate()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass

    def test_cli_gdrive_location(self):
        gdrivedir = os.path.join(CALIBRE_WEB_PATH, 'hü lo')
        os.makedirs(gdrivedir)
        self.start_cw(os.path.join(CALIBRE_WEB_PATH, u'cps.py'), os.path.join(gdrivedir, u'gü dr.app'))
        self.fill_db_config({'config_use_google_drive': 1})
        time.sleep(BOOT_TIME)
        # self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_db_config({'config_google_drive_folder': 'test'})
        time.sleep(BOOT_TIME)
        self.driver.get("http://127.0.0.1:8083")
        self.stop_calibre_web()
        self.p.terminate()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        self.assertTrue(os.path.join(gdrivedir, u'gü dr.app'))
