# -*- coding: utf-8 -*-

from base_test import ParallelTestCase
import virtualenv
import glob
import time
import os
import shutil

from selenium import webdriver
from selenium.webdriver.common.by import By
from helper_func import kill_dead_cps, wait_for_reboot
from config_test import base_path, CALIBRE_WEB_PATH
from subproc_wrapper import process_open
from build_release import make_release


class TestPipInstall(ParallelTestCase):

    package_path = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # startup function is not called, therefore direct print
        cls.driver = webdriver.Firefox()
        cls.driver.implicitly_wait(10)
        cls.driver.maximize_window()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
        shutil.copytree(os.path.join(base_path, 'Calibre_db'), cls.temp_dir)
        #generate pypi install package
        args = make_release.parse_arguments(['-p'])
        make_release.main(args)
        result = glob.glob(os.path.join(CALIBRE_WEB_PATH, "dist", "*.whl"))
        if not result:
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            raise FileNotFoundError("Whl file not found for pip, aborting pip install test")
        # generate new venv python
        cls.package_path = cls.app_dir + "_pack"
        virtualenv.cli_run([cls.package_path, "--clear"])
        # venv.create(cls.package_path, clear=True, with_pip=True)
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
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, "dist"), ignore_errors=True)
        shutil.rmtree(cls.package_path, ignore_errors=True)
        # close the browser window
        os.chdir(base_path)
        kill_dead_cps(cls.worker_port)
        cls.driver.quit()
        try:
            os.remove(os.path.join(cls.app_dir, 'app.db'))
        except Exception:
            pass
        super().tearDownClass(no=True)

    def test_module_start(self):
        package_python = os.path.join(self.package_path, "bin", "python3")
        app_db = os.path.join(self.package_path, "app.db")
        my_env = os.environ.copy()
        my_env["CALIBRE_PORT"] = self.worker_port
        p = process_open([package_python, "-m", "calibreweb", "-p", app_db],[1], env=my_env)
        # create a new Firefox session
        wait_for_reboot(f"http://127.0.0.1:{self.worker_port}")
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + self.worker_port)
        self.login("admin", "admin123")
        self.fill_db_config({'config_calibre_dir': self.temp_dir})
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
        my_env = os.environ.copy()
        my_env["CALIBRE_PORT"] = self.worker_port
        p = process_open([package_command, "-p", app_db],[1], env=my_env)
        # create a new Firefox session
        wait_for_reboot(f"http://127.0.0.1:{self.worker_port}")
        # navigate to the application home page
        self.driver.get(f"http://127.0.0.1:{self.worker_port}")
        self.login("admin", "admin123")
        self.fill_db_config({'config_calibre_dir': self.temp_dir})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.stop_calibre_web(p)
        time.sleep(1)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass

    def test_foldername_database_location(self):
        package_command = os.path.join(self.package_path, "bin", "cps")
        my_env = os.environ.copy()
        my_env["CALIBRE_PORT"] = self.worker_port
        p = process_open([package_command, "-p",self.package_path],[1], env=my_env)
        # create a new Firefox session
        wait_for_reboot(f"http://127.0.0.1:{self.worker_port}")
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + self.worker_port)
        self.login("admin", "admin123")
        self.fill_db_config({'config_calibre_dir': self.temp_dir})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.stop_calibre_web(p)
        time.sleep(1)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
