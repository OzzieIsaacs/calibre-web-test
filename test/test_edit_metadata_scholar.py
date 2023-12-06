#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import time
from diffimg import diff
from io import BytesIO

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup, add_dependency, remove_dependency
from helper_func import save_logfiles


RESOURCES = {'ports': 1}

PORTS = ['8083']


class TestLoadMetadataScholar(TestCase, ui_class):
    p = None
    driver = None
    dependency = ["scholarly", "beautifulsoup4"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, port=PORTS[0], env={"APP_MODE": "test"})
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:" + PORTS[0])
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)
        remove_dependency(cls.dependency)

    def test_load_metadata(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(1)
        self.check_element_on_page((By.ID, "edit_book")).click()
        original_cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.check_element_on_page((By.ID, "get_meta")).click()
        time.sleep(3)
        self.assertEqual("Der Buchtitel", self.check_element_on_page((By.ID, "keyword")).get_attribute("value"))
        google_scholar = self.check_element_on_page((By.ID, "show-Google Scholar"))
        google = self.check_element_on_page((By.ID, "show-Google"))
        comic_vine = self.check_element_on_page((By.ID, "show-ComicVine"))
        amazon = self.check_element_on_page((By.ID, "show-Amazon"))
        time.sleep(3)
        self.assertTrue(amazon)
        amazon.click()
        self.assertTrue(google_scholar)
        self.assertTrue(google)
        self.assertTrue(comic_vine)
        # check active searches
        self.assertTrue(google_scholar.is_selected())
        self.assertTrue(google.is_selected())
        self.assertTrue(comic_vine.is_selected())
        # Check results
        results = self.find_metadata_results()
        self.assertEqual(30, len(results))
        # Remove one search element
        comic_vine.click()
        google.click()
        results = self.find_metadata_results()
        self.assertEqual(10, len(results))
        results[0]['cover_element'].click()
        time.sleep(1)
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertLessEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.001)
        self.assertEqual(results[0]['title'], self.check_element_on_page((By.ID, "book_title")).get_attribute("value"))
        self.assertEqual(results[0]['author'], self.check_element_on_page((By.ID, "bookAuthor")).get_attribute("value"))
        self.assertEqual(results[0]['publisher'], self.check_element_on_page((By.ID, "publisher")).get_attribute("value"))
        self.fill_basic_config({'config_uploading': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))




