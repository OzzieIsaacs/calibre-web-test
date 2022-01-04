#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase, skip
import os
import re
import time
import requests
from diffimg import diff
from shutil import copyfile

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import UnexpectedAlertPresentException
from helper_ui import ui_class
from config_test import TEST_DB, base_path, BOOT_TIME
from helper_func import startup, debug_startup, add_dependency, remove_dependency
from helper_func import save_logfiles


class TestEditMetadata(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB})
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_load_metadata(self):
        self.get_book_details(1)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.check_element_on_page((By.ID, "get_meta")).click()
        #self.assertEqual("", self.check_element_on_page((By.ID, "Der Buchtitel")))
        self.assertTrue(self.check_element_on_page((By.ID, "show-ComicVine")))
        self.assertTrue(self.check_element_on_page((By.ID, "show-Google")))
        self.assertFalse(self.check_element_on_page((By.ID, "show-Google Scholar")))
        # check active searches
        # Check results -> no cover google
        # Link to Google, Comicvine
        # Remove one search element
        # redo a new search,
        # activate the other search element, check new search results visible
        # leave Dialog
        # enter dialog, click on empty cover
        # -> check empty cover is taken, check tags are merged check new title and authors
        # enter dialog, click on cover
        # -> check new cover is taken, check tags are merged check new title and authors
        # check empty search does nothing
        # check chinese character search
        # check search wothout any ticked element





