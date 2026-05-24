# -*- coding: utf-8 -*-

import unittest
from base_test import ParallelTestCase, acquire_resource, release_resource
import os
import time
import shutil
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from helper_func import kill_dead_cps
from subproc_wrapper import process_open
from config_test import BOOT_TIME, base_path
from helper_port_forward import SocketForwardServer


@unittest.skipIf(os.name=="nt", "Sockets are not available on Windows")
class TestSocket(ParallelTestCase):
    driver = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.port = acquire_resource("port")
        cls.driver = webdriver.Firefox()
        cls.driver.implicitly_wait(10)
        cls.driver.maximize_window()
        # startup function is not called, therefore direct print
        # print("\n%s - %s: " % (cls.py_version, cls.__name__))
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(__file__)),'Calibre_db'), cls.temp_dir)

    def setUp(self):
        os.chdir(base_path)
        try:
            os.remove(os.path.join(self.app_dir, 'app.db'))
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        # close the browser window
        os.chdir(base_path)
        kill_dead_cps(cls.worker_port)
        cls.driver.quit()
        try:
            os.remove(os.path.join(cls.app_dir, 'app.db'))
        except Exception:
            pass
        release_resource("port", cls.port)
        super().tearDownClass()

    def test_socket_communication(self):
        my_env = os.environ.copy()
        socket_file = os.path.join(self.app_dir, "socket_file.sock")
        my_env["CALIBRE_UNIX_SOCKET"] = socket_file
        self.p = process_open([self.py_version, os.path.join(self.app_dir, u'cps.py')],
                              env=my_env,
                              quotes=[0, 1])
        time.sleep(BOOT_TIME)
        try:
            # navigate to the application home page
            server = SocketForwardServer('localhost', int(self.port), socket_file)
            server.start()
            # Check server not reesponding on normal port
            try:
                error = ""
                self.driver.get("http://127.0.0.1:" + self.worker_port)
            except WebDriverException as e:
                error = e.msg
            self.assertTrue(re.findall(r'Reached error page:\sabout:neterror\?e=connectionFailure', error))
            time.sleep(3)
            self.driver.get("http://127.0.0.1:" + self.port)
            self.check_element_on_page((By.ID, "username"))

            server.stop_server()

            # Check server not reesponding on forwarded socket port
            try:
                error = ""
                self.driver.get("http://127.0.0.1:" + self.port)
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
