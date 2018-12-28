#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import shutil
from ui_helper import ui_class
from subproc_wrapper import process_open
from testconfig import CALIBRE_WEB_PATH, TEST_DB
import re

class test_logging(unittest.TestCase, ui_class):

    p=None

    @classmethod
    def setUpClass(cls):
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH,'app.db'))
        except:
            pass
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log'))
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log.1'))
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log.2'))
        except:
            pass
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, u'hü lo').encode('UTF-8'), ignore_errors=True)
        shutil.rmtree(TEST_DB,ignore_errors=True)
        shutil.copytree('./Calibre_db', TEST_DB)
        test_logging.p = process_open([u"python", os.path.join(CALIBRE_WEB_PATH,u'cps.py')],(1))

        # create a new Firefox session
        cls.driver = webdriver.Firefox()
        time.sleep(10)
        cls.driver.implicitly_wait(10)
        print('Calibre-web started')

        cls.driver.maximize_window()

        # navigate to the application home page
        cls.driver.get("http://127.0.0.1:8083")

        # Wait for config screen to show up
        cls.fill_initial_config({'config_calibre_dir':TEST_DB,'config_log_level':'DEBUG'})

        # wait for cw to reboot
        time.sleep(5)

        # Wait for config screen with login button to show up
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.NAME, "login")))
        login_button = cls.driver.find_element_by_name("login")
        login_button.click()

        # login
        cls.login("admin", "admin123")
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        test_logging.p.terminate()

    def test_failed_login(self):
        self.driver.find_element_by_id("logout").click()
        self.assertFalse(self.login("admin","123"))
        self.assertTrue(self.login("admin", "admin123"))
        with open(os.path.join(CALIBRE_WEB_PATH,'calibre-web.log'),'r') as logfile:
            data = logfile.read()
        self.assertIsNotNone(re.findall('Login failed for user "admin" IP-adress:',data),"Login failed message not in Logfile")

    @unittest.skip("Not Implemented")
    def test_failed_register(self):
        self.assertIsNone('not Implemented','Registering user with wrong domain is not in Logfile')


    def test_debug_log(self):
        # check Debug entry from starting
        with open(os.path.join(CALIBRE_WEB_PATH,'calibre-web.log'),'r') as logfile:
            data = logfile.read()
        self.assertIsNotNone(re.findall('DEBUG - Computing cache-busting values', data))

        # Change setting to warning
        self.fill_basic_config({'config_log_level':'WARNING'})
        alf = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        # error entry by deleting book with subfolder
        self.driver.get("http://127.0.0.1:8083/delete/5")
        time.sleep(4)
        # No Info entry by adding shelf
        self.driver.get("http://127.0.0.1:8083/shelf/add/7/7")
        time.sleep(4)

        with open(os.path.join(CALIBRE_WEB_PATH,'calibre-web.log'),'r') as logfile:
            data = logfile.read()
        self.assertListEqual(re.findall('INFO in web: Invalid shelf specified',data),[])
        self.assertIsNotNone(re.findall('ERROR in helper: Deleting book 5 failed',data))

        # Change setting back to Info
        # Info entry by adding shelf
        self.fill_basic_config({'config_log_level':'INFO'})
        self.driver.get("http://127.0.0.1:8083/shelf/add/7/7")
        time.sleep(4)
        with open(os.path.join(CALIBRE_WEB_PATH,'calibre-web.log'),'r') as logfile:
            data = logfile.read()
        self.assertIsNotNone(re.findall('INFO in web: Invalid shelf specified',data))

    def test_logfile_change(self):
        # check if path is accepted
        try:
            self.fill_basic_config({'config_logfile': CALIBRE_WEB_PATH})
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_alert")))
            # check if path with trailing slash is accepted
            self.fill_basic_config({'config_logfile': CALIBRE_WEB_PATH+os.sep})
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_alert")))
            # check if non exsiting path is accepted
            self.fill_basic_config({'config_logfile': os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g.log').decode('UTF-8')})
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_alert")))
            # check if path without extension is accepted
            os.makedirs(os.path.join(CALIBRE_WEB_PATH, 'hü lo'))
            self.fill_basic_config({'config_logfile': os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g').decode('UTF-8')})
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
            time.sleep(7)
            # wait for restart
            self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'hü lo','lö g')))
            shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, u'hü lo').encode('UTF-8'), ignore_errors=True)
            #Reset Logfile to default
            self.fill_basic_config({'config_logfile': ''.decode('UTF-8')})
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
            time.sleep(7)

        except TimeoutException:
            self.assertIsNotNone('Fail','Element could not be found')

    def test_logfile_recover(self):
        os.makedirs(os.path.join(CALIBRE_WEB_PATH, 'hü lo'))
        self.fill_basic_config({'config_logfile': os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g').decode('UTF-8')})
        self.check_element_on_page((By.ID, "flash_success"))
        time.sleep(7)
        # delete old logfile and check new logfile present
        os.remove(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log'))
        self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g')))
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, u'hü lo').encode('UTF-8'), ignore_errors=True)
        # restart calibre-web and check if old logfile is used again
        self.restart_calibre_web()
        self.assertFalse(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'hü lo', 'lö g')))
        self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log')))
        # check if logpath is deleted
        self.goto_page("basic_config")
        accordions = self.driver.find_elements_by_class_name("accordion-toggle")
        accordions[2].click()
        logpath = self.driver.find_element_by_id("config_logfile").get_attribute("value")
        self.assertTrue(logpath=="", "logfile config value is not empty after reseting to default")


