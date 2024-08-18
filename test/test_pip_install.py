#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import sys
import shutil
from helper_ui import ui_class
from helper_func import kill_dead_cps
from config_test import CALIBRE_WEB_PATH, TEST_DB, base_path, BOOT_TIME
from subproc_wrapper import process_open
from helper_func import save_logfiles
import venv
import glob
import time

from build_release import make_release

RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""

class TestPipInstall(unittest.TestCase, ui_class):
    package_path = None
    @classmethod
    def setUpClass(cls):
        # startup function is not called, therefore direct print
        print("\n%s - %s: " % (cls.py_version, cls.__name__))
        cls.driver = webdriver.Firefox()
        cls.driver.implicitly_wait(10)
        cls.driver.maximize_window()
        shutil.rmtree(TEST_DB, ignore_errors=True)
        shutil.copytree(os.path.join(base_path, 'Calibre_db'), TEST_DB)
        #generate pypi install package
        args = make_release.parse_arguments(['-p'])
        make_release.main(args)
        result = glob.glob(os.path.join(CALIBRE_WEB_PATH + INDEX, "dist", "*.whl"))
        assert result
        # generate new venv python
        cls.package_path = CALIBRE_WEB_PATH + INDEX + "_pack"
        venv.create(cls.package_path, clear=True, with_pip=True)
        package_python = os.path.join(cls.package_path, "bin", "python3")
        with process_open([package_python, "-m", "pip", "install", result[0]]) as p:
            p.wait()
            p.stdout.readlines()

    def setUp(self):
        try:
            os.remove(os.path.join(self.package_path, 'app.db'))
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH + INDEX, "dist"), ignore_errors=True)
        shutil.rmtree(cls.package_path, ignore_errors=True)
        # close the browser window
        os.chdir(base_path)
        kill_dead_cps()
        cls.driver.quit()
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH + INDEX, 'app.db'))
        except Exception:
            pass
        save_logfiles(cls, cls.__name__)

    def test_module_start(self):
        package_python = os.path.join(self.package_path, "bin", "python3")
        app_db = os.path.join(self.package_path, "app.db")
        p = process_open([package_python, "-m", "calibreweb", "-p", app_db])
        # create a new Firefox session
        time.sleep(BOOT_TIME)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + PORTS[0])
        self.login("admin", "admin123")
        self.fill_db_config({'config_calibre_dir': TEST_DB})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.stop_calibre_web(p)
        time.sleep(1)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass


    def test_command_start(self):
        package_command = os.path.join(self.package_path, "bin", "cps")
        app_db = os.path.join(self.package_path, "app.db")
        p = process_open([package_command, "-p", app_db])
        # create a new Firefox session
        time.sleep(BOOT_TIME)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + PORTS[0])
        self.login("admin", "admin123")
        self.fill_db_config({'config_calibre_dir': TEST_DB})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.stop_calibre_web(p)
        time.sleep(1)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass

    def test_foldername_database_location(self):
        package_command = os.path.join(self.package_path, "bin", "cps")
        p = process_open([package_command, "-p",self.package_path])
        # create a new Firefox session
        time.sleep(BOOT_TIME)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + PORTS[0])
        self.login("admin", "admin123")
        self.fill_db_config({'config_calibre_dir': TEST_DB})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.stop_calibre_web(p)
        time.sleep(1)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
