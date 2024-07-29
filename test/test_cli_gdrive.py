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
from helper_func import add_dependency, remove_dependency
from helper_func import save_logfiles
from helper_gdrive import prepare_gdrive
from subproc_wrapper import process_open

RESOURCES = {'ports': 1, "gdrive": True}

PORTS = ['8083']
INDEX = ""

# test gdrive database
@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
class TestCliGdrivedb(unittest.TestCase, ui_class):
    p = None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)

        prepare_gdrive()
        try:
            shutil.rmtree(os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo'), ignore_errors=True)
            try:
                os.remove(os.path.join(CALIBRE_WEB_PATH + INDEX, 'app.db'))
            except Exception:
                pass
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
        os.chdir(base_path)
        try:
            cls.driver.get("http://127.0.0.1:" + PORTS[0])
            cls.stop_calibre_web()
            # close the browser window and stop calibre-web
            cls.p.terminate()
        except Exception as e:
            print(e)
        try:
            cls.driver.quit()
        except Exception:
            pass
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
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo'), ignore_errors=True)
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH + INDEX, 'app.db'))
        except Exception as e:
            print(e)
        os.chdir(base_path)

    def wait_page_has_loaded(self):
        time.sleep(5)
        while True:
            time.sleep(1)
            page_state = self.driver.execute_script('return document.readyState;')
            if page_state == 'complete':
                break
        time.sleep(5)

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
        self.driver.get("http://127.0.0.1:" + PORTS[0])

        # Wait for config screen to show up
        self.fill_db_config({'config_calibre_dir': TEST_DB})

        # wait for cw to be ready
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.NAME, "query")))

    def test_gdrive_db_nonwrite(self):
        self.start_cw(os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'))
        self.fill_db_config({'config_use_google_drive': 1})
        time.sleep(BOOT_TIME)
        self.fill_db_config({'config_google_drive_folder': 'test'})
        time.sleep(BOOT_TIME)
        self.driver.get("http://127.0.0.1:" + PORTS[0])
        self.stop_calibre_web()
        time.sleep(5)  # shutdowntime
        self.p.terminate()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        gdrive_db = os.path.join(CALIBRE_WEB_PATH + INDEX, "gdrive.db")
        self.assertTrue(os.path.exists(gdrive_db))
        os.chmod(gdrive_db, 0o400)
        self.p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py')], [1])
        # create a new Firefox session
        time.sleep(BOOT_TIME)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + PORTS[0])
        os.chmod(gdrive_db, 0o654)
        self.stop_calibre_web()
        self.p.terminate()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass

    def test_cli_gdrive_location(self):
        gdrive_dir = os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo')
        os.makedirs(gdrive_dir)
        self.start_cw(os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'), os.path.join(gdrive_dir, u'gü dr.app'))
        self.fill_db_config({'config_use_google_drive': 1})
        time.sleep(BOOT_TIME)
        self.fill_db_config({'config_google_drive_folder': 'test'})
        time.sleep(BOOT_TIME)
        self.driver.get("http://127.0.0.1:" + PORTS[0])
        time.sleep(WAIT_GDRIVE)
        self.stop_calibre_web()
        time.sleep(5)  # shutdowntime
        self.p.terminate()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        self.assertTrue(os.path.isfile(os.path.join(gdrive_dir, u'gü dr.app')))

    def test_cli_gdrive_folder(self):
        gdrive_dir = os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo')
        os.makedirs(gdrive_dir)
        self.start_cw(os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'), gdrive_dir)
        self.fill_db_config({'config_use_google_drive': 1})
        time.sleep(BOOT_TIME)
        self.fill_db_config({'config_google_drive_folder': 'test'})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.driver.get("http://127.0.0.1:" + PORTS[0])
        time.sleep(WAIT_GDRIVE)
        self.stop_calibre_web()
        time.sleep(5)  # shutdowntime
        self.p.terminate()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        self.assertTrue(os.path.isfile(os.path.join(gdrive_dir, u'gdrive.db')))

    def test_no_database(self):
        # check unconfigured database
        os.chdir(CALIBRE_WEB_PATH + INDEX)
        p1 = process_open([self.py_version, u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        try:
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:" + PORTS[0])
            # Wait for config screen to show up
            self.fill_db_config({'config_calibre_dir': TEST_DB})
            # wait for cw to reboot
            time.sleep(2)
            self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
            self.fill_db_config({'config_use_google_drive': 1})
            time.sleep(2)
            self.fill_db_config({'config_google_drive_folder': 'test'})
            time.sleep(2)
            self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        except Exception:
            self.assertFalse(True, "Inital config failed with normal database")
        # create shelf, add book to shelf
        self.create_shelf("database")
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        self.get_book_details(1)
        time.sleep(2)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'database')]")).click()
        self.list_shelfs("database")['ele'].click()
        time.sleep(2)
        book_shelf = self.get_shelf_books_displayed()
        self.assertEqual(1, len(book_shelf))
        # rename database file and restart
        # ToDo: deleting local database results in delete of all shelfs, new database is accepted
        '''os.rename(os.path.join(TEST_DB, "metadata.db"), os.path.join(TEST_DB, "_metadata.db"))
        self.restart_calibre_web(p1)        
        self.goto_page("user_setup")
        database_dir = self.check_element_on_page((By.ID, "config_calibre_dir"))
        self.assertTrue(database_dir)
        self.assertEqual(TEST_DB, database_dir.get_attribute("value"))
        self.check_element_on_page((By.ID, "config_back")).click()
        time.sleep(2)
        self.check_element_on_page((By.ID, "config_calibre_dir"))
        self.check_element_on_page((By.ID, "db_submit")).click()
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))
        database_dir = self.check_element_on_page((By.ID, "config_calibre_dir"))
        self.assertTrue(database_dir)
        self.assertEqual(TEST_DB, database_dir.get_attribute("value"))
        os.rename(os.path.join(TEST_DB, "_metadata.db"), os.path.join(TEST_DB, "metadata.db"))
        self.check_element_on_page((By.ID, "db_submit")).click()
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        # check shelf is still there
        self.list_shelfs("database")['ele'].click()
        book_shelf = self.get_shelf_books_displayed()
        self.assertEqual(1, len(book_shelf))'''
        # copy database to different location, move location, check shelf is still there
        alt_location = os.path.abspath(os.path.join(TEST_DB, "..", "alternate"))
        os.makedirs(alt_location, exist_ok=True)
        shutil.copy(os.path.join(TEST_DB, "metadata.db"), os.path.join(alt_location, "metadata.db"))
        self.fill_db_config({'config_calibre_dir': alt_location})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        # check shelf is still there
        self.list_shelfs("database")['ele'].click()
        book_shelf = self.get_shelf_books_displayed()
        self.assertEqual(1, len(book_shelf))
        # Fails on Samba drive, because file is new created before return of command
        shutil.rmtree(alt_location, ignore_errors=True)
        self.delete_shelf("database")
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        self.stop_calibre_web(p1)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        os.unlink(os.path.join(CALIBRE_WEB_PATH + INDEX, "gdrive.db"))
        shutil.rmtree(alt_location, ignore_errors=True)
