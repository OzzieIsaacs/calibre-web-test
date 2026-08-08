# -*- coding: utf-8 -*-

from base_test import ParallelTestCase
import time
from diffimg import diff
from io import BytesIO

from selenium.webdriver.common.by import By
from helper_func import startup


class TestLoadMetadata(ParallelTestCase):

    dependency = ["beautifulsoup4"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': cls.temp_dir},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir)
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    def test_load_metadata(self):
        self.get_book_details(1)
        self.check_element_on_page((By.ID, "edit_book")).click()
        original_cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.check_element_on_page((By.ID, "get_meta")).click()
        time.sleep(1)
        self.assertEqual("Der Buchtitel", self.check_element_on_page((By.ID, "keyword")).get_attribute("value"))
        comic_vine = self.check_element_on_page((By.ID, "show-ComicVine"))
        google = self.check_element_on_page((By.ID, "show-Google Books"))
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
        time.sleep(4)
        # Check results -> no cover google
        results = self.find_metadata_results()
        self.assertTrue(len(results) > 0, "Error, No results for metadata query")
        allowed_sources = {'https://comicvine.gamespot.com/',
                           'https://books.google.com/',
                           'https://amazon.com/'}
        for result in results:
            self.assertIn(result['source'], allowed_sources, "Error, metadata links not found")
        source_to_checkbox = {'https://comicvine.gamespot.com/': comic_vine,
                              'https://books.google.com/': google,
                              'https://amazon.com/': amazon}
        source_counts = {source: len([result for result in results if result['source'] == source])
                         for source in allowed_sources}
        active_source = max(source_counts, key=source_counts.get)
        active_count = source_counts[active_source]
        self.assertGreater(active_count, 0, "Error, No active metadata source with results")

        # Keep only one source active to ensure follow-up checks are deterministic.
        for source, checkbox in source_to_checkbox.items():
            if source != active_source and checkbox.is_selected():
                checkbox.click()
        results = self.find_metadata_results()
        self.assertEqual(active_count, len(results))
        source_to_checkbox[active_source].click()
        results = self.find_metadata_results()
        self.assertEqual(0, len(results))
        source_to_checkbox[active_source].click()
        results = self.find_metadata_results()
        self.assertEqual(active_count, len(results))
        # leave Dialog
        self.check_element_on_page((By.ID, "meta_close")).click()
        time.sleep(1)
        # check results are loaded if button is initially deactivated
        self.check_element_on_page((By.ID, "get_meta")).click()
        comic_vine = self.check_element_on_page((By.ID, "show-ComicVine"))
        google = self.check_element_on_page((By.ID, "show-Google Books"))
        self.assertEqual(active_source == 'https://comicvine.gamespot.com/', comic_vine.is_selected())
        self.assertEqual(active_source == 'https://books.google.com/', google.is_selected())
        time.sleep(2)
        results = self.find_metadata_results()
        self.assertEqual(active_count, len(results))
        secondary_checkbox = google if active_source != 'https://books.google.com/' else comic_vine
        secondary_checkbox.click()
        time.sleep(8)
        results = self.find_metadata_results()
        self.assertGreaterEqual(len(results), active_count)
        secondary_checkbox.click()
        # redo a new search,
        # activate the other search element, check new search results visible
        search = self.check_element_on_page((By.ID, "keyword"))
        search.clear()
        search.send_keys("Clark")
        self.check_element_on_page((By.ID, "do-search")).click()
        time.sleep(2)
        results = self.find_metadata_results()
        self.assertGreater(len(results), 0, "Error, No results for metadata query")
        single_source_results = len(results)
        secondary_checkbox.click()
        time.sleep(8)
        results = self.find_metadata_results()
        self.assertGreaterEqual(len(results), single_source_results)
        # enter dialog, click on cover
        # -> check new cover (the no cover) is taken, check tags are merged check new title and authors
        selected_result = next((result for result in results if result['source'] == 'https://books.google.com/'),
                               results[2] if len(results) > 2 else results[0])
        selected_result['cover_element'].click()
        time.sleep(1)
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertLessEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.006)
        self.assertTrue(self.check_element_on_page((By.ID, "title")).get_attribute("value"))
        self.assertTrue(self.check_element_on_page((By.ID, "authors")).get_attribute("value"))
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
        time.sleep(5)
        comic_vine = self.check_element_on_page((By.ID, "show-ComicVine"))
        google = self.check_element_on_page((By.ID, "show-Google Books"))
        if not comic_vine.is_selected():
            comic_vine.click()
        if not google.is_selected():
            google.click()
        results = []
        for term in ("Buchtitel", "Clark"):
            search = self.check_element_on_page((By.ID, "keyword"))
            search.clear()
            search.send_keys(term)
            self.check_element_on_page((By.ID, "do-search")).click()
            time.sleep(5)
            results = self.find_metadata_results()
            if len(results) > 0:
                break
        self.assertGreater(len(results), 0, "Error, No results for metadata query")
        # Google results have changed
        results[0]['cover_element'].click()
        time.sleep(3)
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreaterEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.05)
        self.check_element_on_page((By.ID, "submit")).click()
        book_details = self.get_book_details(-1)
        pub_compare = book_details['publisher'][0] if len(book_details['publisher']) > 0 else ""
        expected_author = results[0]['author'] if results[0]['author'] else "Unknown"
        self.assertEqual(book_details['title'].replace(" ",""), results[0]['title'].replace(" ",""))
        self.assertEqual(book_details['author'][0], expected_author)
        self.assertEqual(pub_compare, results[0]['publisher'],"{} {}".format(book_details, results[0]) )
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreaterEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.05)

        self.fill_basic_config({'config_uploading': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(1)
        # enter dialog, click on empty cover
        # -> check empty cover is taken, check tags are merged check new title and authors
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.check_element_on_page((By.ID, "get_meta")).click()
        time.sleep(10)
        results = []
        for term in ("Buchtitel", "Clark"):
            search = self.check_element_on_page((By.ID, "keyword"))
            search.clear()
            search.send_keys(term)
            self.check_element_on_page((By.ID, "do-search")).click()
            time.sleep(6)
            results = self.find_metadata_results()
            if len(results) > 0:
                break
        self.assertGreater(len(results), 0, "Error, No results for metadata query")
        result_pos = 1 if len(results) > 1 else 0
        results[result_pos]['cover_element'].click()
        time.sleep(1)
        new_cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertLessEqual(diff(BytesIO(cover), BytesIO(new_cover), delete_diff_file=True), 0.03)
        self.assertTrue(self.check_element_on_page((By.ID, "title")).get_attribute("value"))
        # self.assertEqual("/static/generic_cover.jpg", self.check_element_on_page((By.ID, "cover_url")).get_attribute("value"))

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
        time.sleep(5)
        results = self.find_metadata_results()
        self.assertEqual(old_results, results)
        # check search without any ticked element
        comic_vine = self.check_element_on_page((By.ID, "show-ComicVine"))
        google = self.check_element_on_page((By.ID, "show-Google Books"))
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
        time.sleep(9)
        results = self.find_metadata_results()
        self.assertIsInstance(results, list)
        self.check_element_on_page((By.ID, "meta_close")).click()
