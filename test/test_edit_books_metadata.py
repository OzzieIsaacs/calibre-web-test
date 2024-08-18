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
INDEX = ""


class TestLoadMetadata(TestCase, ui_class):
    p = None
    driver = None
    dependency = ["beautifulsoup4"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, port=PORTS[0], index=INDEX, env={"APP_MODE": "test"})
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
        self.get_book_details(1)
        self.check_element_on_page((By.ID, "edit_book")).click()
        original_cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.check_element_on_page((By.ID, "get_meta")).click()
        self.assertEqual("Der Buchtitel", self.check_element_on_page((By.ID, "keyword")).get_attribute("value"))
        comic_vine = self.check_element_on_page((By.ID, "show-ComicVine"))
        google = self.check_element_on_page((By.ID, "show-Google"))
        amazon = self.check_element_on_page((By.ID, "show-Amazon"))
        self.assertTrue(comic_vine)
        self.assertTrue(google)
        self.assertTrue(amazon)
        self.assertFalse(self.check_element_on_page((By.ID, "show-Google Scholar")))
        self.assertFalse(self.check_element_on_page((By.ID, "show-lubimyczytac")))
        # check active searches
        self.assertTrue(comic_vine.is_selected())
        self.assertTrue(google.is_selected())
        self.assertTrue(amazon.is_selected())
        # Check results -> no cover google
        results = self.find_metadata_results()
        # Link to Google, Comicvine
        if 'https://comicvine.gamespot.com/' == results[10]['source']:
            cv = 10
        elif 'https://comicvine.gamespot.com/' == results[0]['source']:
            cv = 0
        elif 'https://comicvine.gamespot.com/' == results[20]['source']:
            cv = 20
        else:
            cv = -1
        if 'https://books.google.com/' == results[10]['source']:
            go = 10
        elif 'https://books.google.com/' == results[0]['source']:
            go = 0
        elif 'https://books.google.com/' == results[20]['source']:
            go = 20
        else:
            go = -1

        if 'https://amazon.com/' == results[10]['source']:
            am = 10
        elif 'https://amazon.com/' == results[0]['source']:
            am = 0
        elif len(results)>19 and 'https://amazon.com/' == results[20]['source']:
            am = 20
        else:
            am = -1

        self.assertEqual('https://comicvine.gamespot.com/', results[cv]['source'])
        self.assertEqual('https://books.google.com/', results[go]['source'])
        self.assertEqual('https://amazon.com/', results[am]['source'])

        amazon.click()
        # Remove one search element
        comic_vine.click()
        results = self.find_metadata_results()
        self.assertEqual(10, len(results))
        google.click()
        results = self.find_metadata_results()
        self.assertEqual(0, len(results))
        google.click()
        results = self.find_metadata_results()
        self.assertEqual(10, len(results))
        # leave Dialog
        self.check_element_on_page((By.ID, "meta_close")).click()
        time.sleep(1)
        # check results are loaded if button is initially deactivated
        self.check_element_on_page((By.ID, "get_meta")).click()
        comic_vine = self.check_element_on_page((By.ID, "show-ComicVine"))
        google = self.check_element_on_page((By.ID, "show-Google"))
        self.assertFalse(comic_vine.is_selected())
        self.assertTrue(google.is_selected())
        time.sleep(2)
        results = self.find_metadata_results()
        self.assertEqual(10, len(results))
        comic_vine.click()
        time.sleep(2)
        results = self.find_metadata_results()
        self.assertEqual(20, len(results))
        comic_vine.click()
        # redo a new search,
        # activate the other search element, check new search results visible
        search = self.check_element_on_page((By.ID, "keyword"))
        search.clear()
        search.send_keys("Clark")
        self.check_element_on_page((By.ID, "do-search")).click()
        time.sleep(2)
        results = self.find_metadata_results()
        self.assertEqual(10, len(results))
        comic_vine.click()
        time.sleep(2)
        results = self.find_metadata_results()
        self.assertEqual(20, len(results))
        # enter dialog, click on cover
        # -> check new cover is taken, check tags are merged check new title and authors
        results[2]['cover_element'].click()
        time.sleep(1)
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertLessEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.001)
        self.assertEqual(results[2]['title'], self.check_element_on_page((By.ID, "title")).get_attribute("value"))
        self.assertEqual(results[2]['author'], self.check_element_on_page((By.ID, "bookAuthor")).get_attribute("value"))
        self.assertEqual(results[2]['publisher'], self.check_element_on_page((By.ID, "publisher")).get_attribute("value"))
        # click on abort -> nothing saved
        self.check_element_on_page((By.ID, "edit_cancel")).click()
        book_details = self.get_book_details(-1)
        self.assertEqual(book_details['title'], "Der Buchtitel")
        self.assertCountEqual(book_details['author'], ['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'])
        self.assertEqual(book_details['publisher'], [])
        # click on save -> everything saved, cover still the old one
        # enable uploading, and redo search
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(1)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.check_element_on_page((By.ID, "get_meta")).click()
        time.sleep(2)
        search = self.check_element_on_page((By.ID, "keyword"))
        search.clear()
        search.send_keys("Der Buchtitel")
        self.check_element_on_page((By.ID, "do-search")).click()
        time.sleep(3)
        results = self.find_metadata_results()
        results[0]['cover_element'].click()
        time.sleep(3)
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreaterEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.05)
        self.check_element_on_page((By.ID, "submit")).click()
        book_details = self.get_book_details(-1)
        self.assertEqual(book_details['title'], "Der Buchtitel in der römischen Poesie")
        self.assertEqual(book_details['author'][0], "Martin Vogt")
        self.assertEqual(book_details['publisher'], [])
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreaterEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.05)
        # enter dialog, click on empty cover
        # -> check empty cover is taken, check tags are merged check new title and authors
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.check_element_on_page((By.ID, "get_meta")).click()
        time.sleep(3)
        search = self.check_element_on_page((By.ID, "keyword"))
        search.clear()
        search.send_keys("Der Buchtitel")
        self.check_element_on_page((By.ID, "do-search")).click()
        time.sleep(2)
        results = self.find_metadata_results()
        results[1]['cover_element'].click()
        time.sleep(1)
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertLessEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.001)
        self.assertEqual(results[1]['title'], self.check_element_on_page((By.ID, "title")).get_attribute("value"))
        self.assertEqual(results[1]['author'], self.check_element_on_page((By.ID, "bookAuthor")).get_attribute("value"))
        self.assertEqual("/static/generic_cover.jpg", self.check_element_on_page((By.ID, "cover_url")).get_attribute("value"))

        self.fill_basic_config({'config_uploading': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(1)
        self.check_element_on_page((By.ID, "edit_book")).click()
        # check empty search does nothing
        self.check_element_on_page((By.ID, "get_meta")).click()
        time.sleep(2)
        old_results = self.find_metadata_results()
        search = self.check_element_on_page((By.ID, "keyword"))
        search.clear()
        search.send_keys("")
        self.check_element_on_page((By.ID, "do-search")).click()
        time.sleep(2)
        results = self.find_metadata_results()
        self.assertEqual(old_results, results)
        # check search without any ticked element
        comic_vine = self.check_element_on_page((By.ID, "show-ComicVine"))
        google = self.check_element_on_page((By.ID, "show-Google"))
        self.assertTrue(comic_vine.is_selected())
        self.assertTrue(google.is_selected())
        google.click()
        comic_vine.click()
        self.assertFalse(comic_vine.is_selected())
        self.assertFalse(google.is_selected())
        search = self.check_element_on_page((By.ID, "keyword"))
        search.clear()
        search.send_keys("test")
        self.check_element_on_page((By.ID, "do-search")).click()
        time.sleep(3)
        results = self.find_metadata_results()
        self.assertEqual(0, len(results))
        # check chinese character search
        google.click()
        comic_vine.click()
        search = self.check_element_on_page((By.ID, "keyword"))
        search.clear()
        search.send_keys("西遊記")
        self.check_element_on_page((By.ID, "do-search")).click()
        time.sleep(3)
        results = self.find_metadata_results()
        found = 0
        for r in results:
            if r['title'] == "奇想西遊記1":
                found = 1
                break
        self.assertEqual(1, found)
        self.check_element_on_page((By.ID, "meta_close")).click()






