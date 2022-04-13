#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import time
import unittest
from diffimg import diff
from io import BytesIO

from helper_ui import ui_class
from config_test import TEST_DB, base_path, CALIBRE_WEB_PATH
from helper_func import startup, debug_startup, get_Host_IP, add_dependency, remove_dependency
from helper_func import count_files, create_2nd_database
from helper_settings_db import get_thumbnail_files
from helper_db import add_books
from selenium.webdriver.common.by import By
from helper_func import save_logfiles
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



class TestThumbnails(unittest.TestCase, ui_class):

    p = None
    driver = None
    json_line = ["APScheduler"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.json_line, cls.__name__)

        try:

            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB},
                    env={"APP_MODE": "test"})
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
        # remove_dependency(cls.json_line)
        save_logfiles(cls, cls.__name__)

    def test_cover_for_series(self):
        # ToDo: difficult finish test several cases
        # what to do if number of books changes since last cover cache update
        # what to do if cover of one or all books were changed after series cache was generated
        # how to handle case: some books are hidden from several users and should not be visible by then, what if this status changes after cover cache generation
        # self.fill_thumbnail_config({'schedule_generate_book_covers': 1, 'schedule_generate_series_covers': 1})
        # Add 2 books to djüngel series
        # check cover for djüngel, and the other
        self.fill_thumbnail_config({'schedule_generate_series_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        # check series cover changed for djüngel but not for the other one

    def test_cover_cache_on_database_change(self):
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.restart_calibre_web()

        # check cover folder is filled
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH, 'cps', 'cache', 'thumbnails')
        self.assertTrue(os.path.exists(thumbnail_cache_path))
        self.assertEqual(count_files(thumbnail_cache_path), 110*2)
        # change database
        new_path = TEST_DB + '_2'
        create_2nd_database(new_path)
        self.fill_db_config(dict(config_calibre_dir=new_path))
        time.sleep(1)
        self.check_element_on_page((By.ID, "btnConfirmYes-GeneralChangeModal")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(3)   # give system time to delete cache
        self.assertEqual(count_files(thumbnail_cache_path), 0)
        self.restart_calibre_web()
        # check cover folder is filled with new covers
        time.sleep(3) # give system time to create cache
        self.assertEqual(count_files(thumbnail_cache_path), 20)
        # deactivate cache
        self.fill_thumbnail_config({'schedule_generate_book_covers': 0})
        # change database
        self.fill_db_config(dict(config_calibre_dir=TEST_DB))
        time.sleep(1)
        self.check_element_on_page((By.ID, "btnConfirmYes-GeneralChangeModal")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(1)
        # check cover folder is empty
        self.assertEqual(count_files(thumbnail_cache_path), 0)

    @unittest.skip
    # ToDo: Finish test
    def test_cover_change_on_upload_new_cover(self):
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.restart_calibre_web()
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(4)


        self.fill_basic_config({'config_uploading': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_thumbnail_config({'schedule_generate_book_covers': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    # check what happens if a cover is deleted from cache while the cache is used
    def test_remove_cover_from_cache(self):
        self.get_book_details(5)
        original_cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.restart_calibre_web()
        time.sleep(2)
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH, 'cps', 'cache', 'thumbnails')
        book_thumbnail_reference = count_files(thumbnail_cache_path)
        # open app.db file -> thumbnails table -> find entries for book5
        # delete covers of book 5
        books = get_thumbnail_files(os.path.join(CALIBRE_WEB_PATH, "app.db"), 5)
        for book in books:
            os.remove(os.path.join(thumbnail_cache_path, book.uuid[:2], book.filename))
        self.get_book_details(5)
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertEqual(book_thumbnail_reference - 2, count_files(thumbnail_cache_path))
        self.assertAlmostEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.0, delta=0.0001)
        self.restart_calibre_web()
        # cover should get regenerated
        time.sleep(2)
        self.assertEqual(book_thumbnail_reference, count_files(thumbnail_cache_path))
        self.fill_thumbnail_config({'schedule_generate_book_covers': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        shutil.rmtree(thumbnail_cache_path, ignore_errors=True)

    def test_cache_of_deleted_book(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        upload_file = os.path.join(base_path, 'files', 'book.epub')
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH, 'cps', 'cache', 'thumbnails')
        book_thumbnail_reference = count_files(thumbnail_cache_path)
        # covers for new books are generated according to schedule
        self.assertEqual(book_thumbnail_reference, 0)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        # ToDo: check cover is displayed properly
        self.restart_calibre_web()
        time.sleep(2)
        self.delete_book(details['id'])
        time.sleep(2)

        self.assertEqual(book_thumbnail_reference-2, count_files(thumbnail_cache_path))
        self.fill_thumbnail_config({'schedule_generate_book_covers': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        shutil.rmtree(thumbnail_cache_path, ignore_errors=True)

    def test_cache_non_writable(self):
        # makedir cache
        cache_dir = os.path.join(CALIBRE_WEB_PATH, 'cps', 'cache')
        os.makedirs(cache_dir)
        # change to readonly
        os.chmod(cache_dir, 0o400)
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.restart_calibre_web()
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH, 'cps', 'cache', 'thumbnails')
        book_thumbnail_reference = count_files(thumbnail_cache_path)
        self.assertEqual(book_thumbnail_reference, 0)
        # ToDo: check covers are still displayed properly
        self.fill_thumbnail_config({'schedule_generate_book_covers': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        os.chmod(cache_dir, 0o764)
        shutil.rmtree(thumbnail_cache_path, ignore_errors=True)

    @unittest.skip
    def test_gdrive_cache(self):
        # ToDo: Local cache?
        pass

    @unittest.skip
    def test_cache_of_deleted_book_gdrive(self):
        pass

    @unittest.skip
    def test_cache_with_kobo_sync(self):
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        pass

    @unittest.skip
    def test_cover_on_upload_book(self):
        # check that cover is generated after upload
        # usecase: Upload book to calibre-web and sync your kobo reader right after
        # ToDo: Current implementation differs
        pass

    @unittest.skip
    def test_what_about_the_tasks_section(self):
        pass
        # check after restart that message for cover generating is showing up for admin
        # check nothing is shown for normal user
        # after reboot no message for cover generation is shown
        # ToDo: I'm not happy with message ThumbnailsClear after uploading new cover from hdd


    @unittest.skip
    def test_what_happens_on_remove_cache_checkbox(self):
        pass

    @unittest.skip
    def test_what_happens_if_series_has_less_than_four_books_after_thumbnail_generated(self):
        pass

    @unittest.skip
    def test_update_with_cache(self):
        pass
        # check number of covers in cache before update
        # update
        # check number of covers in cache after update == before update, folder still there

    @unittest.skip
    def test_sideloaded_book(self):
        pass
        # sideload a book
        # check cover is shown correct in calibre-web
        # restart calibre-web to update cover cache
        # check cover is in cover cache

        # delete book "sideways"
        # restart calibre-web to update cover cache
        # check cover is removed from cover cache

        # update cover "sideways"
        # calibre-web uses old cover till next cover cache update
        # ToDo: do we need a button force cover cache update
        # restart calibre-web to update cover cache
        # check if new cover used

