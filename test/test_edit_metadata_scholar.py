# -*- coding: utf-8 -*-

from base_test import ParallelTestCase
import time
from diffimg import diff
from io import BytesIO

from selenium.webdriver.common.by import By
from helper_func import startup


class TestLoadMetadataScholar(ParallelTestCase):


    dependency = ["scholarly", "beautifulsoup4"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': cls.temp_dir},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    )
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

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
        google = self.check_element_on_page((By.ID, "show-Google Books"))
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
        self.assertLessEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.009)
        self.assertEqual(results[0]['title'], self.check_element_on_page((By.ID, "title")).get_attribute("value"))
        self.assertEqual(results[0]['author'], self.check_element_on_page((By.ID, "authors")).get_attribute("value"))
        self.assertEqual(results[0]['publisher'], self.check_element_on_page((By.ID, "publisher")).get_attribute("value"))
        self.fill_basic_config({'config_uploading': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))




