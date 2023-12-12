#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import time
import shutil
import re

from helper_ui import ui_class
from helper_func import kill_dead_cps, save_logfiles
from subproc_wrapper import process_open
from config_test import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME, base_path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from helper_port_forward import SocketForwardServer


RESOURCES = {'ports': 2, 'socket':True}

PORTS = ['8083', '8000']
INDEX = ""

@unittest.skipIf(os.name=="nt", "Sockets are not available on Windows")
class TestSocket(unittest.TestCase, ui_class):
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
        cls.driver.quit()
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH + INDEX, 'app.db'))
        except Exception:
            pass
        save_logfiles(cls, cls.__name__)

    def test_socket_communication(self):
        my_env = os.environ.copy()
        socket_file = os.path.join(CALIBRE_WEB_PATH + INDEX, "socket_file.sock")
        my_env["CALIBRE_UNIX_SOCKET"] = socket_file
        self.p = process_open([self.py_version, os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py')],
                              env=my_env,
                              quotes=[0, 1])
        time.sleep(BOOT_TIME)
        try:
            # navigate to the application home page
            server = SocketForwardServer('localhost', int(PORTS[1]), socket_file)
            server.start()
            # Check server not reesponding on normal port
            try:
                error = ""
                self.driver.get("http://127.0.0.1:" + PORTS[0])
            except WebDriverException as e:
                error = e.msg
            self.assertTrue(re.findall(r'Reached error page:\sabout:neterror\?e=connectionFailure', error))
            time.sleep(3)
            self.driver.get("http://127.0.0.1:" + PORTS[1])
            self.check_element_on_page((By.ID, "username"))

            server.stop_server()

            # Check server not reesponding on forwarded socket port
            try:
                error = ""
                self.driver.get("http://127.0.0.1:" + PORTS[1])
            except WebDriverException as e:
                error = e.msg
            self.assertTrue(re.findall(r'Reached error page:\sabout:neterror\?e=connectionFailure', error))

        finally:
            server.stop_server()
            self.p.terminate()      # stop calibre-web
            self.p.stdout.close()
            self.p.stderr.close()
            time.sleep(2)
            self.p.kill()
