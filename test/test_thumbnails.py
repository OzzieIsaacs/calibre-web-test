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
from helper_func import startup, add_dependency, remove_dependency
from helper_func import count_files, create_2nd_database
from helper_settings_db import get_thumbnail_files
from helper_db import add_books, remove_book, change_book_cover
from selenium.webdriver.common.by import By
from helper_func import save_logfiles
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



class TestThumbnails(unittest.TestCase, ui_class):

    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, env={"APP_MODE": "test"})
            time.sleep(3)
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
            # generate new id for database to make calibre-web aware of database change
            add_books(os.path.join(TEST_DB, "metadata.db"), 100, cover=True, set_id=True)
            thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH, 'cps', 'cache', 'thumbnails')
            shutil.rmtree(thumbnail_cache_path, ignore_errors=True)
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
        save_logfiles(cls, cls.__name__)

    def tearDown(self):
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH, 'cps', 'cache', 'thumbnails')
        shutil.rmtree(thumbnail_cache_path, ignore_errors=True)

    @unittest.skip
    def test_cover_for_series(self):
        # ToDo: difficult finish test several cases -> deactivated
        # what to do if number of books changes since last cover cache update
        # what to do if cover of one or all books were changed after series cache was generated
        # how to handle case: some books are hidden from several users and should not be visible by then,
        # what if this status changes after cover cache generation
        # self.fill_thumbnail_config({'schedule_generate_book_covers': 1, 'schedule_generate_series_covers': 1})
        # Add 2 books to "djüngel" series
        # check cover for "djüngel", and the other
        self.fill_thumbnail_config({'schedule_generate_series_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        # check series cover changed for djüngel but not for the other one
        # what_happens_if_series_has_less_than_four_books_after_thumbnail_generated(self) -> should get deleted

    def test_cover_cache_on_database_change(self):
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.restart_calibre_web()
        res = self.check_tasks()
        self.assertLessEqual(len(res), 1, res)
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
        res2 = self.check_tasks()
        self.assertEqual(len(res2), len(res) + 1)
        #self.assertEqual(res[0]['user'], "System")
        #self.assertTrue(res[0]['task'].startswith, "Cover Thumbnails")
        self.assertEqual(res2[-1]['user'], "System")
        self.assertTrue(res2[-1]['task'].startswith, "Cover Thumbnails")
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
        # check cover folder is still full
        self.assertEqual(count_files(thumbnail_cache_path), 0)

    def test_cover_change_on_upload_new_cover(self):
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.restart_calibre_web()
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        res = self.check_tasks()
        self.assertLessEqual(len(res), 1)
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH, 'cps', 'cache', 'thumbnails')
        self.assertTrue(os.path.exists(thumbnail_cache_path))
        self.assertEqual(110*2, count_files(thumbnail_cache_path))
        self.get_book_details(104)
        original_cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        new_cover = os.path.join(base_path, 'files', 'cover.jpg')
        self.edit_book(104, content={'local_cover': new_cover})
        time.sleep(5)
        self.get_book_details(104)
        time.sleep(5)
        updated_cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreaterEqual(diff(BytesIO(updated_cover), BytesIO(original_cover), delete_diff_file=True), 0.05)
        # number of covers unchanged
        self.assertEqual(110*2, count_files(thumbnail_cache_path),)
        # ToDo: do the same with cover from url
        self.fill_basic_config({'config_uploading': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_thumbnail_config({'schedule_generate_book_covers': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        res2 = self.check_tasks()
        self.assertLessEqual(len(res2), 1)

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
        # covers for new books are generated directly after upload
        self.assertEqual(book_thumbnail_reference, 2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        # ToDo: check cover is displayed properly
        # Check only upload message in task list present
        res = self.check_tasks()
        self.assertEqual(len(res), 1)
        # All other covers are created
        self.restart_calibre_web()
        time.sleep(2)
        self.delete_book(details['id'])
        time.sleep(2)
        self.assertEqual(220, count_files(thumbnail_cache_path))
        self.fill_thumbnail_config({'schedule_generate_book_covers': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

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

    # check that cover is generated after upload
    # usecase: Upload book to calibre-web and sync your kobo reader right after
    def test_cover_on_upload_book(self):
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.restart_calibre_web()
        res = self.check_tasks()
        self.assertLessEqual(len(res), 1)
        if len(res):
            self.assertEqual(res[0]['user'], "System")
            self.assertTrue(res[0]['task'].startswith, "Cover Thumbnails")
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH, 'cps', 'cache', 'thumbnails')
        book_thumbnail_reference = count_files(thumbnail_cache_path)
        upload_file = os.path.join(base_path, 'files', 'book.epub')
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        # covers for new books are generated according to schedule
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        # ToDo: check cover is displayed properly
        res2 = self.check_tasks()
        self.assertEqual(len(res2), len(res) + 1)
        self.assertEqual(book_thumbnail_reference+2, count_files(thumbnail_cache_path))
        self.fill_thumbnail_config({'schedule_generate_book_covers': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.delete_book(details['id'])
        time.sleep(2)
        # Check normal user isn't seeing System task
        self.create_user('thumb', {'password': '123', 'email': 'a@b.com'})
        self.logout()
        self.login("thumb", "123")
        res = self.check_tasks()
        self.assertEqual(len(res), 0)
        self.logout()
        self.login("admin", "admin123")

    def test_sideloaded_book(self):
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.restart_calibre_web()
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH, 'cps', 'cache', 'thumbnails')
        book_thumbnail_reference = count_files(thumbnail_cache_path)

        # sideload a book
        add_books(os.path.join(TEST_DB, "metadata.db"), 1, cover=True)

        # check cover is shown correct in calibre-web
        # check cover is in cover cache
        self.goto_page("nav_new")
        books = self.get_books_displayed()
        self.assertEqual(book_thumbnail_reference, count_files(thumbnail_cache_path))
        # check cover
        self.get_book_details(int(books[1][0]['id']))
        # ToDO: Check cover
        # restart calibre-web to update cover cache
        self.restart_calibre_web()
        self.assertEqual(book_thumbnail_reference + 2, count_files(thumbnail_cache_path))

        # delete book "sideways"
        remove_book(os.path.join(TEST_DB, "metadata.db"), books[1][0]['id'])
        self.goto_page("nav_new")
        del_books = self.get_books_displayed()
        self.assertNotEqual(int(books[1][0]['id']), int(del_books[1][0]['id']))
        old_list_cover = del_books[1][2]['ele'].screenshot_as_png
        # cache unchanged
        self.assertEqual(book_thumbnail_reference + 2, count_files(thumbnail_cache_path))
        # restart calibre-web to update cover cache
        self.restart_calibre_web()
        # check cover is removed from cover cache
        self.assertEqual(book_thumbnail_reference, count_files(thumbnail_cache_path))

        self.get_book_details(112)
        old_cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        # update cover "sideways"
        cover_file = os.path.join(base_path, 'files', 'cover.jpg')
        change_book_cover(os.path.join(TEST_DB, "metadata.db"), 112, cover_file)
        # check if new cover used
        time.sleep(2)
        self.goto_page("nav_new")
        cover_books = self.get_books_displayed()
        list_cover = cover_books[1][2]['ele'].screenshot_as_png
        self.get_book_details(112)
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreaterEqual(diff(BytesIO(cover), BytesIO(old_cover), delete_diff_file=True), 0.04)
        # Problem: Cover cache is not updated
        self.assertAlmostEqual(diff(BytesIO(list_cover), BytesIO(old_list_cover), delete_diff_file=True), 0.0,
                               delta=0.0001)
        # restart calibre-web to update cover cache and check cover still the new one
        self.restart_calibre_web()
        self.get_book_details(112)
        new_cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.goto_page("nav_new")
        cached_cover_books = self.get_books_displayed()
        new_list_cover = cached_cover_books[1][2]['ele'].screenshot_as_png

        self.assertGreaterEqual(diff(BytesIO(list_cover), BytesIO(new_list_cover), delete_diff_file=True), 0.04)
        self.assertAlmostEqual(diff(BytesIO(cover), BytesIO(new_cover), delete_diff_file=True), 0.0, delta=0.0001)
        self.assertEqual(book_thumbnail_reference, count_files(thumbnail_cache_path))


        self.fill_thumbnail_config({'schedule_generate_book_covers': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

