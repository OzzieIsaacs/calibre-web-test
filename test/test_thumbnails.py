#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import unittest
import requests
import json

from helper_ui import ui_class
from config_test import TEST_DB, base_path
from helper_func import startup, debug_startup, get_Host_IP, add_dependency, remove_dependency
from helper_db import add_books
from selenium.webdriver.common.by import By
from helper_func import save_logfiles
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestThumbnails(unittest.TestCase, ui_class):

    p = None
    driver = None
    kobo_adress = None
    syncToken = dict()
    header = dict()
    data = dict()
    json_line = ["APScheduler"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.json_line, cls.__name__)

        try:

            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB},
                    env={"APP_MODE": "test"})
            time.sleep(3)
            add_books(os.path.join(TEST_DB, "metadata.db"), 100, cover=True)  # 1520
            '''WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
            cls.goto_page('user_setup')
            cls.driver.get('http://127.0.0.1:8083')
            cls.login('admin', 'admin123')
            time.sleep(2)'''
        except Exception as e:
            print(e)
            cls.driver.quit()
            cls.p.terminate()
            cls.p.poll()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        cls.driver.quit()
        cls.p.terminate()
        # close the browser window and stop calibre-web
        # remove_dependency(cls.json_line)
        save_logfiles(cls, cls.__name__)

    def test_cover_for_series(self):
        # self.fill_thumbnail_config({'schedule_generate_book_covers': 1, 'schedule_generate_series_covers': 1})
        # Add 2 books to djüngel series
        # check cover for djüngel, and the other
        self.fill_thumbnail_config({'schedule_generate_series_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        # check series cover changed for djüngel but not for the other one

    @unittest.skip
    def test_cover_cache_on_database_change(self):
        pass

    @unittest.skip
    def test_cover_location_by_environment_variable(self):
        pass

    @unittest.skip
    def test_cover_change_on_upload_new_cover(self):
        pass

    @unittest.skip
    def test_remove_cover_from_cache(self):
        pass

    @unittest.skip
    def test_cache_with_kobo_sync(self):
        pass

    @unittest.skip
    def test_cache_of_deleted_book(self):
        pass

    @unittest.skip
    def test_cache_non_writable(self):
        pass

    @unittest.skip
    def test_gdrive_cache(self):
        pass

    @unittest.skip
    def test_cover_on_upload(self):
        pass

    @unittest.skip
    def test_what_about_the_tasks_section(self):
        pass

    @unittest.skip
    def test_what_happens_on_remove_cache_checkbox(self):
        pass

    @unittest.skip
    def test_what_happens_if_series_has_less_than_four_books_after_thumbnail_generated(self):
        pass
