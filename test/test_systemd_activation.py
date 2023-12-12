#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import time
import shutil
import re

from helper_ui import ui_class
from helper_func import kill_dead_cps, save_logfiles
from config_test import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME, base_path
from selenium import webdriver
from selenium.webdriver.common.by import By


RESOURCES = {'fix_ports': 5555}


@unittest.skipIf(os.name=="nt", "Sockets are not available on Windows")
class TestSystemdActivation(unittest.TestCase, ui_class):
    driver = None

    @classmethod
    def setUpClass(cls):
        cls.driver = webdriver.Firefox()
        cls.driver.implicitly_wait(10)
        cls.driver.maximize_window()
        # startup function is not called, therefore direct print
        print("\n%s - %s: " % (cls.py_version, cls.__name__))
        shutil.rmtree(TEST_DB, ignore_errors=True)
        shutil.copytree('./Calibre_db', TEST_DB)

    def setUp(self):
        os.chdir(base_path)
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH + INDEX, 'app.db'))
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        # close the browser window
        os.chdir(base_path)
        kill_dead_cps()
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH + INDEX, 'app.db'))
        except Exception:
            print("Can't delete app.db")
            pass
        save_logfiles(cls, cls.__name__)


    # to make this work a running systemd with the following unit files is needed:
    # /etc/systemd/system/cps.socket
    # [Unit]
    # Description=calibre-web Socket
    #
    # [Socket]
    # ListenStream=5555

    # [Install]
    # WantedBy=sockets.target

    # /etc/systemd/system/cps.service
    # [Unit]
    # Description=Calibre-web
    # Wants=network-online.service
    # After=network-online.service

    # [Service]
    # ExecStart=VENV_PYTHON [CALIBRE_WEB_PATH]/cps.py
    # Type=notify
    # NotifyAccess=all
    #
    # [Install]
    # WantedBy=default.target

    # The network-online.service waits for the network to be up
    def test_systemd_activation(self):

        if os.path.exists(os.path.join(CALIBRE_WEB_PATH, "calibre-web.log")):
            os.unlink(os.path.join(CALIBRE_WEB_PATH, "calibre-web.log"))

        try:
            # create a new Firefox session
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:5555")

            # wait for cw to reboot
            time.sleep(BOOT_TIME)

            # load again if startup takes to long
            self.driver.get("http://127.0.0.1:5555")

            # Wait for config screen with login button to show up
            self.assertTrue(self.check_element_on_page((By.NAME, "username")))
            time.sleep(2)
            with open(os.path.join(CALIBRE_WEB_PATH, 'calibre-web.log'), 'r') as logfile:
                data = logfile.read()
            self.assertIsNotNone(re.findall('server on systemd-socket:[::]:5555', data),
                                 "Systemd startup not in logfile")
        except Exception:
            pass
        self.fill_db_config({'config_calibre_dir': TEST_DB})
        time.sleep(BOOT_TIME)

        self.assertTrue(self.check_element_on_page((By.NAME, "query")))
        self.stop_calibre_web()
        # service has a timeout and will stop on it's own after approx 90sec
        self.driver.close()
        time.sleep(100)
        self.driver.quit()
