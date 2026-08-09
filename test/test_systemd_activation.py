# -*- coding: utf-8 -*-

import unittest
from base_test import ParallelTestCase
import os
import time
import shutil
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from helper_func import kill_dead_cps, wait_for_reboot
from config_test import base_path, CALIBRE_WEB_PATH


@unittest.skipIf(os.name=="nt", "Sockets are not available on Windows")
class TestSystemdActivation(ParallelTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = webdriver.Firefox()
        cls.driver.maximize_window()
        # Activation file has hardcoded folder for original location of calibre-web, so it has to work with the original and not with one of the copies
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Calibre_db'), cls.temp_dir)
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'app.db'))
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        # close the browser window
        os.chdir(base_path)
        kill_dead_cps(cls.worker_port)
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH, 'app.db'))
        except Exception:
            cls.log_class("Can't delete app.db")
        super().tearDownClass(no=True)


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
        # The test works on the original location of calibre-web and not one of the venvs!
        if os.path.exists(os.path.join(CALIBRE_WEB_PATH, "calibre-web.log")):
            os.unlink(os.path.join(CALIBRE_WEB_PATH, "calibre-web.log"))

        try:
            # create a new Firefox session
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:5555")

            # wait for cw to reboot
            wait_for_reboot(f"http://127.0.0.1:5555")

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
            self.assertTrue(False, "Systemd startup failed")
        self.fill_db_config({'config_calibre_dir': self.temp_dir})
        wait_for_reboot(f"http://127.0.0.1:5555")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page("nav_new")
        self.assertTrue(self.check_element_on_page((By.NAME, "query")))
        self.stop_calibre_web()
        # service has a timeout and will stop on it's own after approx 90sec
        time.sleep(100)
