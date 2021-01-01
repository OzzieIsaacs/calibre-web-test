#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
import os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
import time
import shutil
from helper_ui import ui_class
from helper_func import get_Host_IP
from subproc_wrapper import process_open
from config_test import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME
import re
import sys
from helper_func import save_logfiles


class TestCli(unittest.TestCase, ui_class):

    @classmethod
    def setUpClass(cls):
        # startup function is not called, therfore direct print
        print("\n%s - %s: " % (cls.py_version, cls.__name__))
        cls.driver = webdriver.Firefox()
        cls.driver.implicitly_wait(10)
        cls.driver.maximize_window()
        shutil.rmtree(TEST_DB, ignore_errors=True)
        shutil.copytree('./Calibre_db', TEST_DB)

    def setUp(self):
        os.chdir(os.path.dirname(__file__))
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'app.db'))
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        # close the browser window
        cls.driver.quit()
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'app.db'))
            shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, u'hü lo'), ignore_errors=True)
        except Exception:
            pass
        save_logfiles(cls, cls.__name__)

    def test_cli_different_folder(self):
        os.chdir(CALIBRE_WEB_PATH)
        self.p = process_open([self.py_version, u'cps.py'], [1])
        os.chdir(os.path.dirname(__file__))
        try:
            # create a new Firefox session
            time.sleep(15)
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:8083")

            # Wait for config screen to show up
            self.fill_initial_config({'config_calibre_dir': TEST_DB})

            # wait for cw to reboot
            time.sleep(BOOT_TIME)

            # Wait for config screen with login button to show up
            login_button = self.check_element_on_page((By.NAME, "login"))
            self.assertTrue(login_button)
            login_button.click()

            # login
            self.login("admin", "admin123")
            time.sleep(3)
            self.assertTrue(self.check_element_on_page((By.NAME, "query")))
            self.stop_calibre_web(self.p)

        except Exception:
            pass
        self.p.terminate()

    def test_cli_different_settings_database(self):
        new_db = os.path.join(CALIBRE_WEB_PATH, 'hü go.app')  # .decode('UTF-8')
        new_db = new_db
        self.p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'),
                               '-p', new_db], [1, 3])

        time.sleep(15)
        # navigate to the application home page
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        self.driver.refresh()
        self.driver.get("http://127.0.0.1:8083")

        # Wait for config screen to show up
        self.check_element_on_page((By.ID, "config_calibre_dir"))
        self.assertFalse(self.check_element_on_page((By.ID, "calibre_modal_path")))
        self.fill_initial_config({'config_calibre_dir': TEST_DB})

        # wait for cw to reboot
        time.sleep(BOOT_TIME)

        # Wait for config screen with login button to show up
        login_button = self.check_element_on_page((By.NAME, "login"))
        self.assertTrue(login_button)
        login_button.click()
        self.login('admin', 'admin123')
        self.stop_calibre_web(self.p)
        self.p.terminate()
        time.sleep(3)
        self.assertTrue(os.path.isfile(new_db), "New settingsfile location not accepted")
        os.remove(new_db)

    def test_cli_SSL_files(self):
        os.chdir(os.path.dirname(__file__))
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, 'hü lo'), ignore_errors=True)
        path_like_file = CALIBRE_WEB_PATH
        only_path = CALIBRE_WEB_PATH + os.sep
        real_key_file = os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g.key')
        real_crt_file = os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g.crt')
        if sys.version_info < (3, 0):
            real_key_file = real_key_file.decode('UTF-8')
            real_crt_file = real_crt_file.decode('UTF-8')

        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'),
                          '-c', path_like_file], [1, 3])
        time.sleep(2)
        nextline = p.communicate()[0]
        if p.poll() is None:
            p.kill()
        self.assertIsNotNone(re.findall('Certfilepath is invalid. Exiting', nextline))

        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'),
                          '-k', path_like_file], [1, 3])
        time.sleep(2)
        nextline = p.communicate()[0]
        if p.poll() is None:
            p.kill()
        self.assertIsNotNone(re.findall('Keyfilepath is invalid. Exiting', nextline))

        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'),
                          '-c', only_path], [1, 3])
        time.sleep(2)
        nextline = p.communicate()[0]
        if p.poll() is None:
            p.kill()
        self.assertIsNotNone(re.findall('Certfilepath is invalid. Exiting', nextline))

        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'),
                          '-k', only_path], [1, 3])
        time.sleep(2)
        nextline = p.communicate()[0]
        if p.poll() is None:
            p.kill()
        self.assertIsNotNone(re.findall('Keyfilepath is invalid. Exiting', nextline))

        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'),
                         '-c', real_crt_file], (1, 3))
        time.sleep(2)
        if p.poll() is None:
            p.kill()
        nextline = p.communicate()[0]
        self.assertIsNotNone(re.findall('Certfilepath is invalid. Exiting', nextline))

        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'),
                         '-k', real_key_file], (1, 3))
        time.sleep(2)
        if p.poll() is None:
            p.kill()
        nextline = p.communicate()[0]
        self.assertIsNotNone(re.findall('Keyfilepath is invalid. Exiting', nextline))

        os.makedirs(os.path.join(CALIBRE_WEB_PATH, 'hü lo'))
        with open(real_key_file, 'wb') as fout:
            fout.write(os.urandom(124))
        with open(real_crt_file, 'wb') as fout:
            fout.write(os.urandom(124))

        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'),
                         '-c', real_crt_file], (1, 3))
        time.sleep(2)
        if p.poll() is None:
            p.kill()
        nextline = p.communicate()[0]
        self.assertIsNotNone(re.findall('Certfile and Keyfile have to be used together. Exiting', nextline))

        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'),
                         '-k', real_key_file], (1, 3))
        time.sleep(2)
        if p.poll() is None:
            p.kill()
        nextline = p.communicate()[0]
        self.assertIsNotNone(re.findall('Certfile and Keyfile have to be used together. Exiting', nextline))

        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'),
                         '-c', real_crt_file, '-k', real_key_file], (1, 3, 5))

        if p.poll() is not None:
            self.assertIsNone('Fail', 'Unexpected error')
            p.kill()
        p.terminate()
        time.sleep(10)
        p.poll()

        # navigate to the application home page
        try:
            self.driver.get("https://127.0.0.1:8083")
            self.assertIsNone("Error", "HTTPS Connection could established with wrong key/cert file")
        except WebDriverException as e:
            self.assertIsNotNone(re.findall('Reached error page: about:neterror?nssFailure', e.msg))
        p.kill()
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, 'hü lo'), ignore_errors=True)
        shutil.copytree('./files', os.path.join(CALIBRE_WEB_PATH, 'hü lo'))
        real_crt_file = os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'server.crt')
        real_key_file = os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'server.key')
        if sys.version_info < (3, 0):
            real_crt_file = real_crt_file.decode('UTF-8')
            real_key_file = real_key_file.decode('UTF-8')
        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'),
                         '-c', real_crt_file, '-k', real_key_file], (1, 3, 5))
        if p.poll() is not None:
            self.assertIsNone('Fail', 'Unexpected error')
        time.sleep(10)

        # navigate to the application home page
        try:
            self.driver.get("https://127.0.0.1:8083")
        except WebDriverException:
            self.assertIsNone("Error", "HTTPS Connection could not established with key/cert file")

        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, 'hü lo'), ignore_errors=True)
        self.assertTrue(self.check_element_on_page((By.ID, "config_calibre_dir")))
        p.terminate()
        time.sleep(3)
        p.poll()

    @unittest.skip("Not Implemented")
    def test_cli_gdrive_location(self):
        # ToDo: implement
        self.assertIsNone('not Implemented', 'Check if moving gdrive db on commandline works')

    def test_bind_to_single_interface(self):
        address = get_Host_IP()
        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'), '-i', 'http://'+address], [1])
        time.sleep(2)
        if p.poll() is None:
            p.kill()
        nextline = p.communicate()[0]
        self.assertIsNotNone(re.findall('Illegal IP address string', nextline))
        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py'), '-i', address], [1])

        time.sleep(BOOT_TIME)
        # navigate to the application home page
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        try:
            error = ""
            self.driver.get("http://127.0.0.1:8083")
        except WebDriverException as e:
            error = e.msg
        self.assertTrue(re.findall('Reached error page:\sabout:neterror\?e=connectionFailure', error))
        try:
            self.driver.get("http://" + address + ":8083")
        except WebDriverException:
            self.assertIsNone('Limit listening address not working')
        self.assertTrue(self.check_element_on_page((By.ID, "config_calibre_dir")))
        p.terminate()
        time.sleep(3)
        p.poll()

    def test_environ_port_setting(self):
        my_env = os.environ.copy()
        my_env["CALIBRE_PORT"] = '8082'
        p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH, u'cps.py')], [1], env=my_env)

        time.sleep(BOOT_TIME)
        # navigate to the application home page
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        try:
            error = ""
            self.driver.get("http://127.0.0.1:8082")
        except WebDriverException as e:
            error = e.msg
        self.assertFalse(re.findall('Reached error page:\sabout:neterror\?e=connectionFailure', error))
        self.assertTrue(self.check_element_on_page((By.ID, "config_calibre_dir")))
        p.terminate()
        time.sleep(3)
        p.poll()

    # start calibre-web in process A.
    # Start calibre-web in process B.
    # Check process B terminates with exit code 1
    # stop process A
    def test_already_started(self):
        os.chdir(CALIBRE_WEB_PATH)
        p1 = process_open([self.py_version, u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        p2 = process_open([self.py_version, u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        time.sleep(2)
        result = p2.poll()
        if result is None:
            p2.terminate()
            self.assertTrue('2nd process not terminated, port is already in use')
        self.assertEqual(result, 1)
        p1.terminate()
        time.sleep(3)
        p1.poll()

    # start calibre-web in process A.
    # Start calibre-web in process B.
    # Check process B terminates with exit code 1
    # stop process A
    def test_settingsdb_not_writeable(self):
        # check unconfigured database
        os.chdir(CALIBRE_WEB_PATH)
        p1 = process_open([self.py_version, u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        p1.terminate()
        time.sleep(BOOT_TIME)
        p1.poll()
        os.chmod("app.db", 0o400)
        p2 = process_open([self.py_version, u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        result = p2.poll()
        if result is None:
            p2.terminate()
            p2.poll()
            self.assertTrue('2nd process not terminated, port is already in use')
        self.assertEqual(result, 2)
        os.chmod("app.db", 0o644)
        # configure and check again
        p1 = process_open([self.py_version, u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        try:
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:8083")

            # Wait for config screen to show up
            self.fill_initial_config({'config_calibre_dir': TEST_DB})

            # wait for cw to reboot
            time.sleep(BOOT_TIME)
        except Exception:
            self.assertFalse(True, "Inital config failed with on test nonwriteable database")
        p1.terminate()
        time.sleep(BOOT_TIME)
        p1.poll()
        os.chmod("app.db", 0o400)
        p2 = process_open([self.py_version, u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        result = p2.poll()
        if result is None:
            p2.terminate()
            p2.poll()
            self.assertTrue('2nd process not terminated, port is already in use')
        self.assertEqual(result, 2)
        os.chmod("app.db", 0o644)