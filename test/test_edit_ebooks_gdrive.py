#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import io
import os
import re
from selenium.webdriver.common.by import By
import time
import requests
import shutil
from helper_ui import ui_class
from PIL import Image
from diffimg import diff

from config_test import CALIBRE_WEB_PATH, TEST_DB, base_path, WAIT_GDRIVE
from helper_func import add_dependency, remove_dependency, startup
from helper_func import save_logfiles
from helper_gdrive import prepare_gdrive, connect_gdrive, check_path_gdrive


# test editing books on gdrive
@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
class TestEditBooksOnGdrive(unittest.TestCase, ui_class):
    p = None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)

        prepare_gdrive()
        try:
            src = os.path.join(base_path, "files", "client_secrets.json")
            dst = os.path.join(CALIBRE_WEB_PATH, "client_secrets.json")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            # delete settings_yaml file
            set_yaml = os.path.join(CALIBRE_WEB_PATH, "settings.yaml")
            if os.path.exists(set_yaml):
                os.unlink(set_yaml)

            # delete gdrive file
            gdrive_db = os.path.join(CALIBRE_WEB_PATH, "gdrive.db")
            if os.path.exists(gdrive_db):
                os.unlink(gdrive_db)

            # delete gdrive authenticated file
            src = os.path.join(base_path, 'files', "gdrive_credentials")
            dst = os.path.join(CALIBRE_WEB_PATH, "gdrive_credentials")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            startup(cls,
                    cls.py_version,
                    {'config_calibre_dir': TEST_DB},
                    only_metadata=True, env={"APP_MODE": "test"})
            cls.fill_db_config({'config_use_google_drive': 1})
            time.sleep(4)
            cls.fill_db_config({'config_google_drive_folder': 'test'})
            time.sleep(5)
        except Exception as e:
            try:
                print(e)
                cls.driver.quit()
                cls.p.kill()
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        try:
            cls.driver.get("http://127.0.0.1:8083")
            cls.stop_calibre_web()
            # close the browser window and stop calibre-web
            cls.driver.quit()
            cls.p.terminate()
        except Exception as e:
            print(e)
        save_logfiles(cls, cls.__name__)

        remove_dependency(cls.dependency)

        src1 = os.path.join(CALIBRE_WEB_PATH, "client_secrets.json")
        src = os.path.join(CALIBRE_WEB_PATH, "gdrive_credentials")
        if os.path.exists(src):
            os.chmod(src, 0o764)
            try:
                os.unlink(src)
            except PermissionError:
                print('gdrive_credentials delete failed')
        if os.path.exists(src1):
            os.chmod(src1, 0o764)
            try:
                os.unlink(src1)
            except PermissionError:
                print('client_secrets.json delete failed')
        for f in ['original.png', 'jpeg.png', 'page.png']:
            if os.path.exists(f):
                os.unlink(f)

    def wait_page_has_loaded(self):
        time.sleep(1)
        while True:
            time.sleep(1)
            page_state = self.driver.execute_script('return document.readyState;')
            if page_state == 'complete':
                break
        time.sleep(1)

    def test_edit_title(self):
        self.fill_basic_config({"config_unicode_filename": 1})
        self.check_element_on_page((By.ID, 'flash_success'))
        fs = connect_gdrive("test")
        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'book_title': u'O0ü 执'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'O0ü 执', values['title'])
        new_book_path = os.path.join('test', values['author'][0], 'O0u Zhi (4)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        old_book_path = os.path.join('test', values['author'][0], 'Very long extra super turbo cool tit (4)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        # file operation
        fout = io.BytesIO()
        fout.write(os.urandom(124))
        fs.upload(os.path.join('test', values['author'][0], 'O0u Zhi (4)', 'test.dum').replace('\\', '/'), fout)
        fout.close()
        self.edit_book(content={'book_title': u' O0ü 执'}, detail_v=True)
        self.wait_page_has_loaded()
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        title = self.check_element_on_page((By.ID, "book_title"))
        # calibre strips spaces in beginning
        self.assertEqual(u'O0ü 执', title.get_attribute('value'))
        new_book_path = os.path.join('test', values['author'][0], 'O0u Zhi (4)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.wait_page_has_loaded()
        self.edit_book(content={'book_title': u'O0ü name'}, detail_v=True)
        self.wait_page_has_loaded()
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        title = self.check_element_on_page((By.ID, "book_title"))
        # calibre strips spaces in the end
        self.assertEqual(u'O0ü name', title.get_attribute('value'))
        new_book_path = os.path.join('test', values['author'][0], 'O0u name (4)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        # self.assertFalse(os.path.isdir(os.path.join(TEST_DB, values['author'][0], 'O0u Zhi (4)')))
        old_book_path = os.path.join('test', values['author'][0], 'O0u Zhi (4)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)

        self.edit_book(content={'book_title': ''})
        self.wait_page_has_loaded()
        time.sleep(2)
        values = self.get_book_details()
        # os.path.join(TEST_DB, values['author'][0], 'Unknown')
        self.assertEqual('Unknown', values['title'])
        # self.assertTrue(os.path.isdir(os.path.join(TEST_DB, values['author'][0], 'Unknown (4)')))
        new_book_path = os.path.join('test', values['author'][0], 'Unknown (4)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        old_book_path = os.path.join('test', values['author'][0], 'Unknown').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'book_title': 'The camicdemo'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual('The camicdemo', values['title'])
        self.goto_page('nav_new')
        self.wait_page_has_loaded()
        books = self.get_books_displayed()
        self.assertEqual('The camicdemo', books[1][8]['title'])
        file_path = os.path.join('test', values['author'][0], 'The camicdemo (4)').replace('\\', '/')
        not_file_path = os.path.join('test', values['author'][0], 'camicdemo').replace('\\', '/')

        # file operation
        fs.movedir(file_path, not_file_path, create=True)
        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'book_title': u'Not found'})
        self.wait_page_has_loaded()
        time.sleep(4)
        self.check_element_on_page((By.ID, 'flash_danger'))
        values = self.get_book_details(4)
        # title = self.check_element_on_page((By.ID, "book_title"))
        # calibre strips spaces in the end
        self.assertEqual('The camicdemo', values['title'])
        # file operation
        fs.movedir(not_file_path, file_path, create=True)
        # missing cover file is not detected, and cover file is moved
        cover_file = os.path.join('test', values['author'][0], 'The camicdemo (4)', 'cover.jpg').replace('\\', '/')
        not_cover_file = os.path.join('test', values['author'][0], 'The camicdemo (4)', 'no_cover.jpg').replace('\\', '/')

        # file operation
        fs.move(cover_file, not_cover_file)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': u'No Cover'}, detail_v=True)
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, 'flash_success'))
        title = self.check_element_on_page((By.ID, "book_title"))
        self.assertEqual('No Cover', title.get_attribute('value'))
        cover_file = os.path.join('test', values['author'][0], 'No Cover (4)', 'cover.jpg').replace('\\', '/')
        not_cover_file = os.path.join('test', values['author'][0], 'No Cover (4)', 'no_cover.jpg').replace('\\', '/')

        fs.move(not_cover_file, cover_file)
        fs.close()
        self.edit_book(content={'book_title': u'Pipo|;.:'}, detail_v=True)
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, 'flash_success'))
        title = self.check_element_on_page((By.ID, "book_title"))
        self.assertEqual(u'Pipo|;.:', title.get_attribute('value'))
        self.edit_book(content={'book_title': u'Very long extra super turbo cool title without any issue of displaying including ö utf-8 characters'})
        time.sleep(5)
        self.wait_page_has_loaded()
        ele = self.check_element_on_page((By.ID, "title"))
        self.assertEqual(ele.text, u'Very long extra super turbo cool title without any issue of displaying including ö utf-8 characters')
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': u'book6'})
        self.wait_page_has_loaded()
        self.fill_basic_config({"config_unicode_filename": 0})
        self.check_element_on_page((By.ID, 'flash_success'))

    # goto Book 2
    # Change Author with unicode chars
    # save book, go to show books page
    # check Author
    # edit Author with spaces on beginning (Single name)
    # save book, stay on page
    # check Author correct, check folder name correct, old folder deleted (last book of author)
    # edit Author of book 7, book 2 and 7 have same author now
    # check author folder has 2 sub folders
    # change author of book 2
    # save book, stay on page
    # check Author correct, check folder name correct, old folder still existing (not last book of author)
    # edit Author remove Author
    # save book, stay on page
    # check Author correct (Unknown)
    # edit Author, add 2nd not existing author
    # save book, stay on page
    # check Authors correct
    # Author Alfa Alfa & Beta Beta (where is book saved?) -> Alfa Alfa
    # Author Beta Beta & Alfa Alfa (where is book saved?) -> Beta Beta
    # change author to something with ',' in it
    # save book, stay on page
    # check author correct, check if author correct in order authors (author sort should be 2nd 1st)
    # change author to something with '|' in it
    # save book, stay on page
    # check author correct (what is correct)???
    # add files to folder of author
    # change author of book,
    # check folder moves completely with all files
    # remove folder permissions
    # change author of book
    # error should occur
    # remove folder of author
    # change author of book
    # error should occur
    # Test Capital letters and lowercase characters
    def test_edit_author(self):
        self.fill_basic_config({"config_unicode_filename": 1})
        self.check_element_on_page((By.ID, 'flash_success'))
        fs = connect_gdrive("test")
        self.get_book_details(8)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'bookAuthor': u'O0ü 执'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'O0ü 执', values['author'][0])
        new_book_path = os.path.join('test', 'O0u Zhi', 'book8 (8)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        old_book_path = os.path.join('test', 'Leo Baskerville', 'book8 (8)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor': ' O0ü name '}, detail_v=True)
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, 'flash_success'))
        author = self.check_element_on_page((By.ID, "bookAuthor"))
        # calibre strips spaces in the end
        self.assertEqual(u'O0ü name', author.get_attribute('value'))
        # self.assertTrue(os.path.isdir(os.path.join(TEST_DB, 'O0u name', 'book8 (8)')))
        new_book_path = os.path.join('test', 'O0u name', 'book8 (8)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)

        self.edit_book(content={'bookAuthor': ''})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        # os.path.join(TEST_DB, 'Unknown', 'book8 (8)')
        self.assertEqual('Unknown', values['author'][0])
        # self.assertTrue(os.path.isdir(os.path.join(TEST_DB, values['author'][0], 'book8 (8)')))
        new_book_path = os.path.join('test', values['author'][0], 'book8 (8)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)

        self.check_element_on_page((By.ID, "edit_book")).click()
        # Check authorsort
        self.edit_book(content={'bookAuthor': 'Marco, Lulu de'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        # os.path.join(TEST_DB, values['author'][0], 'book8 (8)')
        self.assertEqual(values['author'][0], 'Marco, Lulu de')
        list_element = self.goto_page('nav_author')
        # ToDo check names of List elements
        self.get_book_details(8)
        self.check_element_on_page((By.ID, "edit_book")).click()

        self.edit_book(content={'bookAuthor': 'Sigurd Lindgren'}, detail_v=True)
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, 'flash_success'))
        author = self.check_element_on_page((By.ID, "bookAuthor")).get_attribute('value')
        self.assertEqual(u'Sigurd Lindgren', author)
        new_book_path = os.path.join('test', author, 'book8 (8)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)

        # self.assertTrue(os.path.isdir(os.path.join(TEST_DB, author, 'book8 (8)')))
        self.edit_book(content={'bookAuthor': 'Sigurd Lindgren&Leo Baskerville'}, detail_v=True)
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, 'flash_success'))
        new_book_path = os.path.join('test',  'Sigurd Lindgren', 'book8 (8)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        old_book_path = os.path.join('test', 'Leo Baskerville', 'book8 (8)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)

        author = self.check_element_on_page((By.ID, "bookAuthor"))
        self.assertEqual(u'Sigurd Lindgren & Leo Baskerville', author.get_attribute('value'))
        self.edit_book(content={'bookAuthor': ' Leo Baskerville & Sigurd Lindgren '}, detail_v=True)
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, 'flash_success'))

        new_book_path = os.path.join('test',  'Leo Baskerville', 'book8 (8)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        old_book_path = os.path.join('test', 'Sigurd Lindgren', 'book8 (8)').replace('\\', '/')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)
        time.sleep(5)
        self.edit_book(content={'bookAuthor': 'Pipo| Pipe'}, detail_v=True)
        time.sleep(4)
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, 'flash_success'))
        author = self.check_element_on_page((By.ID, "bookAuthor"))
        self.assertEqual(u'Pipo, Pipe', author.get_attribute('value'))
        self.goto_page('nav_author')

        file_path = os.path.join('test', 'Pipo, Pipe', 'book8 (8)').replace('\\', '/')
        not_file_path = os.path.join('test', 'Pipo, Pipe', 'nofolder').replace('\\', '/')
        fs.movedir(file_path, not_file_path, create=True)
        self.get_book_details(8)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor': u'Not found'})
        time.sleep(WAIT_GDRIVE)
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, 'flash_danger'))
        values = self.get_book_details(8)
        self.assertEqual(values['author'][0], 'Pipo, Pipe')
        fs.movedir(not_file_path, file_path, create=True)
        fs.close()
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor': 'Leo Baskerville'}, detail_v=True)
        self.wait_page_has_loaded()
        time.sleep(5)
        self.check_element_on_page((By.ID, 'flash_success'))
        self.fill_basic_config({"config_unicode_filename": 0})
        self.check_element_on_page((By.ID, 'flash_success'))

    # series with unicode spaces, ,|,
    def test_edit_series(self):
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'series': 'O0ü 执'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'O0ü 执', values['series'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'series': 'Alf|alfa, Kuko'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'Alf|alfa, Kuko', values['series'])
        self.goto_page('nav_serie')
        self.wait_page_has_loaded()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], 'Alf|alfa, Kuko')

        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'series': ''})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertFalse('series' in values)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'series': 'Loko'}, detail_v=True)
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, 'flash_success'))
        series = self.check_element_on_page((By.ID, "series"))
        self.assertEqual(u'Loko', series.get_attribute('value'))

        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'series': 'loko'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'loko', values['series'])
        self.goto_page('nav_serie')
        self.wait_page_has_loaded()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[1]['title'], 'loko')

        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'series': 'Loko', 'series_index': '1.0'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'Loko', values['series'])
        self.check_element_on_page((By.XPATH, "//*[contains(@href,'series')]/ancestor::p/a")).click()
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 2)
        books[1][0]['ele'].click()
        self.wait_page_has_loaded()
        time.sleep(2)
        ele = self.check_element_on_page((By.ID, "title"))
        self.assertEqual(u'book6', ele.text)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'series': u''})
        self.wait_page_has_loaded()

    def test_edit_category(self):
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'tags': 'O0ü 执'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(len(values['tag']), 1)
        self.assertEqual(u'O0ü 执', values['tag'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'tags': 'Alf|alfa'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'Alf|alfa', values['tag'][0])
        list_element = self.goto_page('nav_cat')
        self.wait_page_has_loaded()
        self.assertEqual(list_element[0].text, 'Alf|alfa')

        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'tags': ''})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(len(values['tag']), 0)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'tags': ' Gênot & Peter '}, detail_v=True)
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, 'flash_success'))
        tags = self.check_element_on_page((By.ID, "tags"))
        self.assertEqual(u'Gênot & Peter', tags.get_attribute('value'))

        self.edit_book(content={'tags': ' Gênot , Peter '})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'Gênot', values['tag'][0])
        self.assertEqual(u'Peter', values['tag'][1])

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'tags': 'gênot'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'gênot', values['tag'][0])
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'tags': 'Gênot'})
        self.wait_page_has_loaded()

    def test_edit_publisher(self):
        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'publisher': 'O0ü 执'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(len(values['publisher']), 1)
        self.assertEqual(u'O0ü 执', values['publisher'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'publisher': 'Beta|,Bet'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'Beta|,Bet', values['publisher'][0])
        list_element = self.goto_page('nav_publisher')
        self.wait_page_has_loaded()
        self.assertEqual(list_element[0].text,  'Beta|,Bet', "Publisher Sorted according to name, B before R")

        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'publisher': ''})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(len(values['publisher']), 0)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'publisher': ' Gênot & Peter '}, detail_v=True)
        self.wait_page_has_loaded()
        self.check_element_on_page((By.ID, 'flash_success'))
        publisher = self.check_element_on_page((By.ID, "publisher"))
        self.assertEqual(u'Gênot & Peter', publisher.get_attribute('value'))

        self.edit_book(content={'publisher': ' Gênot , Peter '})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'Gênot , Peter', values['publisher'][0])

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'publisher': 'gênot'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'gênot', values['publisher'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'publisher': 'Gênot'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'Gênot', values['publisher'][0])

    # choose language not part ob lib
    def test_edit_language(self):
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages': 'english'})
        values = self.get_book_details()
        self.assertEqual(len(values['languages']), 1)
        self.assertEqual('English', values['languages'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages': 'German'})
        values = self.get_book_details()
        self.assertEqual('German', values['languages'][0])
        list_element = self.goto_page('nav_lang')
        self.assertEqual(list_element[1].text,  'German')
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages': 'German & English'}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_danger'))
        # self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages': 'German, English'})
        # self.get_book_details(3)
        time.sleep(WAIT_GDRIVE)
        values = self.get_book_details()
        self.assertEqual(len(values['languages']), 2)
        self.assertEqual('German', values['languages'][1])
        self.assertEqual('English', values['languages'][0])

    # change rating, delete rating
    # check if book with rating of 4 stars appears in list of hot books
    def test_edit_rating(self):
        self.goto_page('nav_rated')
        books = self.get_books_displayed()
        self.assertEqual(1, len(books[1]))
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'rating': 4})
        values = self.get_book_details()
        self.assertEqual(4, values['rating'])
        self.goto_page('nav_rated')
        self.wait_page_has_loaded()
        books = self.get_books_displayed()
        self.assertEqual(1, len(books[1]))
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'rating': 5})
        values = self.get_book_details()
        self.assertEqual(5, values['rating'])
        self.goto_page('nav_rated')
        self.wait_page_has_loaded()
        books = self.get_books_displayed()
        self.assertEqual(2, len(books[1]))
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'rating': 0})
        values = self.get_book_details()
        self.assertEqual(0, values['rating'])

    # change comments, add comments, delete comments
    def test_edit_comments(self):
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'description': 'bogomirä 人物'})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual(u'bogomirä 人物', values['comment'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.wait_page_has_loaded()
        self.edit_book(content={'description': ''})
        self.wait_page_has_loaded()
        values = self.get_book_details()
        self.assertEqual('', values['comment'])

    # change comments, add comments, delete comments
    def test_edit_custom_bool(self):
        self.assertEqual(len(self.adv_search({u'custom_column_3': u'Yes'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Bool 1 Ä': 'Yes'})
        vals = self.get_book_details(5)
        self.assertEqual(u'ok', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_3': u'No'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_3': u'Yes'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Bool 1 Ä': u""})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))

    def test_edit_custom_rating(self):
        self.assertEqual(len(self.adv_search({u'custom_column_1': u'3'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Rating 人物': '3'})
        vals = self.get_book_details(5)
        self.assertEqual('3', vals['cust_columns'][0]['value'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Rating 人物': '6'})
        vals = self.get_book_details(5)
        self.assertEqual('3', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_1': u'4'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_1': u'3'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Rating 人物': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))

    def test_edit_custom_single_select(self):
        self.assertEqual(len(self.adv_search({u'custom_column_9': u'人物'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom 人物 Enum': '人物'})
        vals = self.get_book_details(5)
        self.assertEqual(u'人物', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_9': u'Alfa'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_9': u'人物'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom 人物 Enum': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))

    # change comments, add comments, delete comments
    def test_edit_custom_text(self):
        self.assertEqual(len(self.adv_search({u'custom_column_10': u'人 Ä'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Text 人物 *\'()&': u'Lulu 人 Ä'})
        vals = self.get_book_details(5)
        self.assertEqual(u'Lulu 人 Ä', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_10': u'Koko'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_10': u'lu'})), 1)
        self.assertEqual(len(self.adv_search({u'custom_column_10': u'人 Ä'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Text 人物 *\'()&': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))

    # change comments, add comments, delete comments
    def test_edit_custom_categories(self):
        self.assertEqual(len(self.adv_search({u'custom_column_6': u'人 Ü'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={r'Custom categories\|, 人物': u'KuKu 人 Ü'})
        vals = self.get_book_details(5)
        self.assertEqual(u'KuKu 人 Ü', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_6': u'Koko'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_6': u'Ku'})), 1)
        self.assertEqual(len(self.adv_search({u'custom_column_6': u'人 Ü'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={r'Custom categories\|, 人物': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))

    # change comments, add comments, delete comments
    def test_edit_custom_float(self):
        self.assertEqual(len(self.adv_search({u'custom_column_8': u'-2.5'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Float 人物': u'-2.5'})
        vals = self.get_book_details(5)
        self.assertEqual(u'-2.5', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_8': u'-2.3'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_8': u'-2.5'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Float 人物': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))

    # change comments, add comments, delete comments
    def test_edit_custom_int(self):
        self.assertEqual(len(self.adv_search({u'custom_column_4': u'0'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Integer 人物': u'0'})
        vals = self.get_book_details(5)
        self.assertEqual(u'0', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_4': u'5'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_4': u'0'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Integer 人物': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))

    @unittest.expectedFailure
    def test_upload_cover_hdd(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        self.edit_user('admin', {'upload_role': 1})
        self.get_book_details(5)
        self.save_cover_screenshot('original.png')
        self.check_element_on_page((By.ID, "edit_book")).click()
        jpegcover = os.path.join(base_path, 'files', 'cover.jpg')
        self.edit_book(content={'local_cover': jpegcover})
        time.sleep(5)
        self.get_book_details(5)
        time.sleep(5)
        self.save_cover_screenshot('jpeg.png')
        self.assertGreater(diff('original.png', 'jpeg.png', delete_diff_file=True), 0.02)
        os.unlink('original.png')

        self.check_element_on_page((By.ID, "edit_book")).click()
        bmpcover = os.path.join(base_path, 'files', 'cover.bmp')
        self.edit_book(content={'local_cover': bmpcover})
        self.assertFalse(self.check_element_on_page((By.CLASS_NAME, "alert")))
        time.sleep(5)
        self.save_cover_screenshot('bmp.png')
        self.assertGreater(diff('bmp.png', 'jpeg.png', delete_diff_file=True), 0.006)
        os.unlink('jpeg.png')
        self.get_book_details(5)
        time.sleep(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        pngcover = os.path.join(base_path, 'files', 'cover.png')
        self.edit_book(content={'local_cover': pngcover})
        time.sleep(5)
        self.get_book_details(5)
        time.sleep(5)
        self.save_cover_screenshot('png.png')
        self.assertGreater(diff('bmp.png', 'png.png', delete_diff_file=True), 0.005)
        os.unlink('bmp.png')

        self.check_element_on_page((By.ID, "edit_book")).click()
        pngcover = os.path.join(base_path, 'files', 'cover.webp')
        self.edit_book(content={'local_cover': pngcover})
        time.sleep(5)
        self.get_book_details(5)
        time.sleep(5)
        self.save_cover_screenshot('webp.png')
        self.assertGreater(diff('webp.png', 'png.png', delete_diff_file=True), 0.005)
        os.unlink('webp.png')
        os.unlink('png.png')
        os.unlink('page.png')

        self.fill_basic_config({'config_uploading': 0})
        time.sleep(2)

    def test_upload_book_lit(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        self.edit_user('admin', {'upload_role': 1})
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.lit')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        # ToDo: check file contents
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('book', details['title'])
        self.assertEqual('Unknown', details['author'][0])
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "remember_me": "on",
                   "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('19501', resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()

    @unittest.expectedFailure
    def test_upload_book_epub(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        self.edit_user('admin', {'upload_role': 1})
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.epub')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)

        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details()
        self.assertEqual('book9', details['title'])
        self.assertEqual('Noname 23', details['author'][0])
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('8936', resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        r.close()
        # ToDo: Check folders are right

    # download of books
    def test_download_book(self):
        list_element = self.goto_page('nav_download')
        self.assertEqual(len(list_element), 0)
        self.get_book_details(5)
        element = self.check_element_on_page((By.XPATH, "//*[starts-with(@id,'btnGroupDrop')]"))
        download_link = element.get_attribute("href")
        self.assertTrue(download_link.endswith('/5.epub'),
                        'Download Link has invalid format for kobo browser, has to end with filename')
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "",
                   'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get(download_link)
        self.assertEqual(resp.headers['Content-Type'], 'application/epub+zip')
        self.assertEqual(resp.status_code, 200)
        self.edit_user('admin', {'download_role': 0})
        resp = r.get(download_link)
        self.assertEqual(resp.status_code, 403)
        book = self.get_book_details(5)
        self.assertNotIn('download', book)
        self.edit_user('admin', {'download_role': 1})
        r.close()
        list_element = self.goto_page('nav_download')
        self.assertEqual(len(list_element), 1)
        list_element[0].click()
        number_books = self.get_books_displayed()
        self.assertEqual(1, len(number_books[1]))

    # download of books
    def test_watch_metadata(self):
        # enable watch metadata
        self.goto_page("db_config")
        button = self.check_element_on_page((By.ID, "enable_gdrive_watch"))
        self.assertTrue(button)
        button.click()
        self.wait_page_has_loaded()
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "config_google_drive_watch_changes_response")))
        # Check revoke is working
        revoke = self.check_element_on_page((By.ID, "watch_revoke"))
        self.assertTrue(revoke)
        revoke.click()
        self.wait_page_has_loaded()
        time.sleep(5)
        button = self.check_element_on_page((By.ID, "enable_gdrive_watch"))
        self.assertTrue(button)
        button.click()
        self.wait_page_has_loaded()
        time.sleep(5)
        # change book series content
        self.edit_book(5, content={'series': 'test'})
        self.wait_page_has_loaded()
        time.sleep(10)
        book = self.get_book_details(-1)
        self.assertEqual(book['series'], 'test')
        # upload new metadata.db from outside
        fs = connect_gdrive("test")
        # upload unchanged database from hdd -> watch metadata should recognize this and replace current
        # used metadata.db
        metadata = open(os.path.join(base_path, 'Calibre_db', 'metadata.db'), 'rb')
        fs.upload(os.path.join('test', 'metadata.db').replace('\\', '/'), metadata)
        metadata.close()
        loop = 0
        while loop < 3:
            loop += 1
            # wait a bit
            time.sleep(5)
            self.wait_page_has_loaded()
            time.sleep(10)
            # check book series content changed back
            book = self.get_book_details(5)
            if 'series' not in book:
                break
        self.assertNotIn('series', book)
        self.goto_page("db_config")
        self.wait_page_has_loaded()
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "config_google_drive_watch_changes_response")))
        # Check revoke is working
        revoke = self.check_element_on_page((By.ID, "watch_revoke"))
        self.assertTrue(revoke)
        revoke.click()
        self.wait_page_has_loaded()
        time.sleep(5)
