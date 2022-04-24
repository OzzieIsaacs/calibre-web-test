#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import time
import unittest

from helper_ui import ui_class
from config_test import TEST_DB, base_path, CALIBRE_WEB_PATH
from helper_func import startup, add_dependency, remove_dependency
from helper_func import count_files, create_2nd_database
from helper_db import add_books
from selenium.webdriver.common.by import By
from helper_func import save_logfiles
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestThumbnailsEnv(unittest.TestCase, ui_class):

    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.json_line, cls.__name__)

        try:
            shutil.rmtree(TEST_DB + '_3', ignore_errors=True)
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB},
                    env={"APP_MODE": "test", "CACHE_DIR": TEST_DB + '_3' })
            time.sleep(3)
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
            # generate new id for database to make calibre-web aware of database change
            add_books(os.path.join(TEST_DB, "metadata.db"), 100, cover=True, set_id=True)  # 1520
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
        shutil.rmtree(TEST_DB + '_2', ignore_errors=True)
        shutil.rmtree(TEST_DB + '_3', ignore_errors=True)
        # remove_dependency(cls.json_line)
        save_logfiles(cls, cls.__name__)


    def test_cover_cache_env_on_database_change(self):
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.restart_calibre_web()

        # check cover folder is filled
        thumbail_cache_path = os.path.join(TEST_DB + '_3', 'thumbnails')
        self.assertTrue(os.path.exists(thumbail_cache_path))
        self.assertEqual(count_files(thumbail_cache_path), 110*2)
        # change database
        new_path = TEST_DB + '_2'
        create_2nd_database(new_path)
        self.fill_db_config(dict(config_calibre_dir=new_path))
        time.sleep(1)
        self.check_element_on_page((By.ID, "btnConfirmYes-GeneralChangeModal")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(3)   # give system time to delete cache
        self.assertEqual(count_files(thumbail_cache_path), 0)
        self.restart_calibre_web()
        # check cover folder is filled with new covers
        time.sleep(3) # give system time to create cache
        self.assertEqual(count_files(thumbail_cache_path), 20)
        # deactivate cache
        self.fill_thumbnail_config({'schedule_generate_book_covers': 0})
        # change database
        self.fill_db_config(dict(config_calibre_dir=TEST_DB))
        time.sleep(1)
        self.check_element_on_page((By.ID, "btnConfirmYes-GeneralChangeModal")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(1)
        # check cover folder is empty
        self.assertEqual(count_files(thumbail_cache_path), 0)
