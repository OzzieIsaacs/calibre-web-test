# -*- coding: utf-8 -*-

from base_test import ParallelTestCase
import os

from selenium.webdriver.common.by import By
from helper_db import change_book_path
from helper_func import startup


class TestBookDatabase(ParallelTestCase):



    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': cls.temp_dir},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    '''@classmethod
    def tearDownClass(cls):        
        cls.driver.get("http://127.0.0.1:" + cls.worker_port)
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        super().tearDownClass()'''

    def test_invalid_book_path(self):
        change_book_path(os.path.join(self.temp_dir, "metadata.db"), 10)
        self.restart_calibre_web()
        self.delete_book(10)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertTrue(10, len(books[1]))

