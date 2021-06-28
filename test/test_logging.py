#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import shutil
from helper_ui import ui_class
from config_test import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME
import re
from helper_func import startup
from helper_func import save_logfiles
import requests
import zipfile
import io

class TestLogging(unittest.TestCase, ui_class):
    p = None

    @classmethod
    def setUpClass(cls):
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log'))
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log.1'))
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log.2'))
        except Exception:
            pass
        startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_log_level': 'DEBUG'})
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)
        try:
            shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, u'hü lo'), ignore_errors=True)
            shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, u'hö lo'), ignore_errors=True)
        except:
            pass

    def test_failed_login(self):
        self.driver.find_element_by_id("logout").click()
        self.assertFalse(self.login("admin", "123"))
        self.assertTrue(self.login("admin", "admin123"))
        with open(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log'), 'r') as logfile:
            data = logfile.read()
        self.assertIsNotNone(re.findall('Login failed for user "admin" IP-adress:', data),
                             "Login failed message not in Logfile")

    @unittest.skip("Not Implemented")
    def test_failed_register(self):
        self.assertIsNone('not Implemented', 'Registering user with wrong domain is not in Logfile')

    def test_debug_log(self):
        # check Debug entry from starting
        with open(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log'), 'r') as logfile:
            data = logfile.read()
        self.assertIsNotNone(re.findall('DEBUG - Computing cache-busting values', data))

        # Change setting to warning
        self.fill_basic_config({'config_log_level': 'WARNING'})
        time.sleep(BOOT_TIME)
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        # error entry by deleting book with subfolder
        self.driver.get("http://127.0.0.1:8083/delete/5")
        time.sleep(4)
        # No Info entry by adding shelf
        self.driver.get("http://127.0.0.1:8083/shelf/add/7/7")
        time.sleep(4)

        with open(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log'), 'r') as logfile:
            data = logfile.read()
        self.assertListEqual(re.findall('INFO in web: Invalid shelf specified', data), [])
        self.assertIsNotNone(re.findall('ERROR in helper: Deleting book 5 failed', data))

        # Change setting back to Info
        # Info entry by adding shelf
        self.fill_basic_config({'config_log_level': 'INFO'})
        time.sleep(BOOT_TIME)
        self.driver.get("http://127.0.0.1:8083/shelf/add/7/7")
        time.sleep(4)
        with open(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log'), 'r') as logfile:
            data = logfile.read()
        self.assertIsNotNone(re.findall('INFO in web: Invalid shelf specified', data))

    def test_logfile_change(self):
        # check if path is accepted
        try:
            self.fill_basic_config({'config_logfile': CALIBRE_WEB_PATH})
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_danger")))
            # check if path with trailing slash is accepted
            self.fill_basic_config({'config_logfile': CALIBRE_WEB_PATH+os.sep})
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_danger")))
            # check if non existing path is accepted
            self.fill_basic_config({'config_logfile': os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g.log')})
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_danger")))
            # check if path without extension is accepted
            os.makedirs(os.path.join(CALIBRE_WEB_PATH, 'hü lo'))
            self.fill_basic_config({'config_logfile': os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g')})
            time.sleep(BOOT_TIME)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
            time.sleep(7)
            # wait for restart
            self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g')))
            shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, u'hü lo'), ignore_errors=True)
            # Reset Logfile to default
            self.fill_basic_config({'config_logfile': ''})
            time.sleep(BOOT_TIME)
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
            time.sleep(7)

        except TimeoutException:
            self.assertIsNotNone('Fail', 'Element could not be found')

    def test_logfile_recover(self):
        if not os.path.isdir(os.path.join(CALIBRE_WEB_PATH, 'hü lo')):
            os.makedirs(os.path.join(CALIBRE_WEB_PATH, 'hü lo'))
        self.fill_basic_config({'config_logfile': os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g')})
        self.check_element_on_page((By.ID, "flash_success"))
        time.sleep(BOOT_TIME)
        # delete old logfile and check new logfile present
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log'))
        except Exception:
            pass
        self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g')))
        # restart calibre-web and check if old logfile is used again
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, u'hü lo'), ignore_errors=True)
        self.restart_calibre_web()
        if os.name != 'nt':
            self.assertFalse(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g')))
            self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log')))
            # check if logpath is deleted
            self.goto_page("basic_config")
            accordions = self.driver.find_elements_by_class_name("accordion-toggle")
            accordions[2].click()
            logpath = self.driver.find_element_by_id("config_logfile").get_attribute("value")
            self.assertEqual(logpath, "", "logfile config value is not empty after reseting to default")
        else:
            # It's NOT possible to delete the path, therefore changed folder/file is taken
            self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g')))
            self.assertFalse(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log')))
            # ToDo: Stop Calibre-Web delete folder restart it and check if folder is the new one
        self.fill_basic_config({'config_logfile': ''})
        time.sleep(BOOT_TIME)
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, u'hü lo'), ignore_errors=True)

    def test_access_log_recover(self):
        if not os.path.isdir(os.path.join(CALIBRE_WEB_PATH, 'hö lo')):
            os.makedirs(os.path.join(CALIBRE_WEB_PATH, 'hö lo'))
        self.fill_basic_config({'config_access_log': 1,
                                'config_access_logfile': os.path.join(CALIBRE_WEB_PATH, 'hö lo', 'lü g')})
        self.check_element_on_page((By.ID, "flash_success"))
        time.sleep(BOOT_TIME)
        # delete old logfile and check new logfile present
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'access.log'))
        except Exception:
            pass
        self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'hö lo', 'lü g')))
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, u'hö lo'), ignore_errors=True)
        # restart calibre-web and check if old logfile is used again
        self.restart_calibre_web()
        self.goto_page("basic_config")
        if os.name != 'nt':
            # It's possible to delete the path, therefore original file is taken
            self.assertFalse(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'hö lo', 'lü g')))
            self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'access.log')))
            # check if logpath is deleted
            accordions = self.driver.find_elements_by_class_name("accordion-toggle")
            accordions[2].click()
            logpath = self.driver.find_element_by_id("config_access_logfile").get_attribute("value")
            self.assertEqual(logpath, "", "Access logfile config value is not empty after reseting to default")
        else:
            # It's NOT possible to delete the path, therefore changed folder/file is taken
            self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'hö lo', 'lü g')))
            self.assertFalse(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'access.log')))
            # ToDo: Stop Calibre-Web delete folder restart it and check if folder is the new one
        self.fill_basic_config({'config_access_log': 0, 'config_access_logfile': ''})
        time.sleep(BOOT_TIME)
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, u'hö lo'), ignore_errors=True)


    def test_logviewer(self):
        self.fill_basic_config({'config_logfile': '/dev/stdout',
                                'config_access_log': 1,
                                'config_access_logfile': 'access.log'})
        self.check_element_on_page((By.ID, "flash_success"))
        time.sleep(BOOT_TIME)
        self.goto_page('logviewer')
        time.sleep(2)
        # check stream test is there, no radiobox for calibre log, access logger ticked
        self.assertTrue(self.check_element_on_page((By.XPATH, '//label[@for="log1"]')))
        self.assertFalse(self.check_element_on_page((By.ID, 'log1')))
        self.assertTrue(self.check_element_on_page((By.ID, 'log0')).is_selected())
        # Just check if there is output in the field
        self.assertGreater(len(self.check_element_on_page((By.ID, 'renderer')).text), 100)

        self.fill_basic_config({'config_logfile': 'log.log',
                                'config_access_log': 0,
                                'config_access_logfile': ''})
        self.check_element_on_page((By.ID, "flash_success"))
        time.sleep(BOOT_TIME)
        self.goto_page('logviewer')
        # check stream test is there, no radiobox for calibre log, access logger ticked
        self.assertTrue(self.check_element_on_page((By.ID, 'log1')).is_selected())
        self.assertFalse(self.check_element_on_page((By.ID, 'log0')))
        # Just check if there is output in the field
        self.assertGreater(len(self.check_element_on_page((By.ID, 'renderer')).text), 100)

        self.fill_basic_config({'config_logfile': 'log.log',
                                'config_access_log': 1,
                                'config_access_logfile': 'access.log'})
        self.check_element_on_page((By.ID, "flash_success"))
        time.sleep(BOOT_TIME)
        self.goto_page('logviewer')
        # check stream test is there, no radiobox for calibre log, access logger ticked
        logger = self.check_element_on_page((By.ID, 'log1'))
        access = self.check_element_on_page((By.ID, 'log0'))
        self.assertTrue(access)
        self.assertFalse(access.is_selected())
        self.assertTrue(logger.is_selected())
        text1 = len(self.check_element_on_page((By.ID, 'renderer')).text)
        access.click()
        time.sleep(2)
        self.assertTrue(access.is_selected())
        self.assertFalse(logger.is_selected())
        text2 = len(self.check_element_on_page((By.ID, 'renderer')).text)
        self.assertNotEqual(text1, text2)
        # Just check if there is output in the field

    def test_debuginfo_download(self):
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/admin", "remember_me": "on"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083/admin/debug')
        self.assertGreater(len(resp.content), 2600)
        self.assertEqual(resp.headers['Content-Type'], 'application/zip')
        zip = zipfile.ZipFile(io.BytesIO(resp.content))
        self.assertIsNone(zip.testzip())
        r.close()

    def test_debuginfo_download(self):
        self.fill_basic_config({'config_logfile': '',
                                'config_access_log': 1})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('logviewer')
        self.assertTrue(self.check_element_on_page((By.ID, "log_file_0")))
        self.assertTrue(self.check_element_on_page((By.ID, "log_file_1")))
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/admin", "remember_me": "on"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083/admin/logdownload/0')
        self.assertTrue(resp.headers['Content-Type'].startswith('text/html'))
        resp = r.get('http://127.0.0.1:8083/admin/logdownload/1')
        self.assertTrue(resp.headers['Content-Type'].startswith('text/html'))
        r.close()
