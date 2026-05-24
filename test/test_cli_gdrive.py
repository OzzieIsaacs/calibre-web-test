# -*- coding: utf-8 -*-

from base_test import ParallelTestCase
import os
import time
import shutil
import unittest

from selenium.webdriver.common.by import By
from selenium import webdriver

from config_test import base_path, BOOT_TIME, WAIT_GDRIVE
from helper_func import copy_calibre_web_for_test, wait_for_reboot
from subproc_wrapper import process_open
import subprocess

# test gdrive database
@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
class TestCliGdrivedb(ParallelTestCase):
    resource_lock = "gdrive"
    p = None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        copy_calibre_web_for_test(cls.app_dir)
        shutil.copy(os.path.join(base_path, 'Calibre_db', 'metadata.db'), os.path.join(cls.temp_dir,
                                                                                       'metadata.db'))
        try:
            shutil.rmtree(os.path.join(cls.app_dir, 'hü lo'), ignore_errors=True)
            try:
                os.remove(os.path.join(cls.app_dir, 'app.db'))
            except Exception:
                pass

            cls.driver = webdriver.Firefox()
            # cls.driver.implicitly_wait(10)
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
            cls.driver.get("http://127.0.0.1:" + cls.worker_port)
            cls.stop_calibre_web()
            # close the browser window and stop calibre-web
            cls.driver.quit()
            cls.p.terminate()
        except Exception as e:
            pass
        finally:
            super().tearDownClass()

        src1 = os.path.join(cls.app_dir, "client_secrets.json")
        src = os.path.join(cls.app_dir, "gdrive_credentials")
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

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(os.path.join(self.app_dir, 'hü lo'), ignore_errors=True)
        try:
            os.remove(os.path.join(self.app_dir, 'app.db'))
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

    def start_cw(self, cw_path, gdrive_path=None, env=None):
        if env:
            my_env = os.environ.copy()
            env = {**my_env, **env}

        parameter = [self.py_version, cw_path]
        quotes = [1]
        if gdrive_path:
            parameter.extend(['-g', gdrive_path])
            quotes.extend([3])

        self.p = process_open(parameter, quotes, env=env)
        # create a new Firefox session
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + self.worker_port)

        # Wait for config screen to show up
        self.fill_db_config({'config_calibre_dir': self.temp_dir})

        # wait for cw to be ready
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.NAME, "query")))

    def test_gdrive_db_nonwrite(self):
        self.start_cw(os.path.join(self.app_dir, u'cps.py'), env={"APP_MODE": "test", "CALIBRE_PORT": self.worker_port})
        self.fill_db_config({'config_use_google_drive': 1})
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        self.fill_db_config({'config_google_drive_folder': 'test'})
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        self.driver.get("http://127.0.0.1:" + self.worker_port)
        self.stop_calibre_web()
        time.sleep(5)  # shutdowntime
        try:
            self.p.terminate()
            self.p.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.communicate()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        gdrive_db = os.path.join(self.app_dir, "gdrive.db")
        self.assertTrue(os.path.exists(gdrive_db))
        os.chmod(gdrive_db, 0o400)
        self.p = process_open([self.py_version, os.path.join(self.app_dir, u'cps.py')], [1])
        # create a new Firefox session
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        time.sleep(5)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + self.worker_port)
        os.chmod(gdrive_db, 0o654)
        self.stop_calibre_web()
        try:
            self.p.terminate()
            self.p.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.communicate()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass

    def test_cli_gdrive_location(self):
        gdrive_dir = os.path.join(self.app_dir, 'hü lo')
        os.makedirs(gdrive_dir)
        self.start_cw(os.path.join(self.app_dir, u'cps.py'), os.path.join(gdrive_dir, u'gü dr.app'), env={"APP_MODE": "test", "CALIBRE_PORT": self.worker_port})
        self.fill_db_config({'config_use_google_drive': 1})
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        self.fill_db_config({'config_google_drive_folder': 'test'})
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        self.driver.get("http://127.0.0.1:" + self.worker_port)
        time.sleep(WAIT_GDRIVE)
        self.stop_calibre_web()
        time.sleep(5)  # shutdowntime
        try:
            self.p.terminate()
            self.p.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.communicate()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        self.assertTrue(os.path.isfile(os.path.join(gdrive_dir, u'gü dr.app')))

    def test_cli_gdrive_folder(self):
        gdrive_dir = os.path.join(self.app_dir, 'hü lo')
        os.makedirs(gdrive_dir)
        self.start_cw(os.path.join(self.app_dir, u'cps.py'), gdrive_dir, env={"APP_MODE": "test", "CALIBRE_PORT": self.worker_port})
        self.fill_db_config({'config_use_google_drive': 1})
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        self.fill_db_config({'config_google_drive_folder': 'test'})
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.driver.get("http://127.0.0.1:" + self.worker_port)
        time.sleep(WAIT_GDRIVE)
        self.stop_calibre_web()
        time.sleep(5)  # shutdowntime
        try:
            self.p.terminate()
            self.p.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.communicate()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        self.assertTrue(os.path.isfile(os.path.join(gdrive_dir, u'gdrive.db')))

    def test_no_database(self):
        # check unconfigured database
        os.chdir(self.app_dir)
        p1 = process_open([self.py_version, u'cps.py'], [1])
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        try:
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:" + self.worker_port)
            # Wait for config screen to show up
            self.fill_db_config({'config_calibre_dir': self.temp_dir})
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
        # copy database to different location, move location, check shelf is still there
        alt_location = os.path.abspath(os.path.join(self.temp_dir, "..", "alternate"))
        os.makedirs(alt_location, exist_ok=True)
        shutil.copy(os.path.join(self.temp_dir, "metadata.db"), os.path.join(alt_location, "metadata.db"))
        self.fill_db_config({'config_calibre_dir': alt_location})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        # check shelf is still there
        self.list_shelfs("database")['ele'].click()
        book_shelf = self.get_shelf_books_displayed()
        self.assertEqual(1, len(book_shelf))
        # Fails on Samba drive, because file is new created before return of command
        shutil.rmtree(alt_location, ignore_errors=True)
        self.list_shelfs("database")['ele'].click()
        element = self.check_element_on_page((By.XPATH, '//*[@title="Return to Database config"]'))
        self.assertTrue(element)
        element.click()
        self.assertTrue(self.check_element_on_page((By.ID, 'config_calibre_dir')))
        self.stop_calibre_web(p1)
        try:
            p1.terminate()
            p1.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            p1.kill()
            p1.communicate()

        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        os.unlink(os.path.join(self.app_dir, "gdrive.db"))
        shutil.rmtree(alt_location, ignore_errors=True)
