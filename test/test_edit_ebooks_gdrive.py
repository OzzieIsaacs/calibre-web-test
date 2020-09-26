#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
import re
import io
import os
from selenium.webdriver.common.by import By
import time
import requests
import shutil
from helper_ui import ui_class

from config_test import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME, base_path
from helper_func import add_dependency, remove_dependency, startup
from helper_func import save_logfiles
from helper_gdrive import prepare_gdrive, remove_gdrive, connect_gdrive, check_path_gdrive
# test editing books on gdrive


WAIT_GDRIVE = 15

@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
class TestEditBooksOnGdrive(unittest.TestCase, ui_class):
    p=None
    driver = None
    dependency = ["oauth2client", "PyDrive", "PyYAML", "google-api-python-client", "httplib2", "Pillow", "lxml"]

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
                    {'config_calibre_dir': TEST_DB,'config_use_google_drive':1 },
                    only_metadata=True)
            cls.fill_basic_config({'config_google_drive_folder':'test'})
        except Exception as e:
            try:
                cls.driver.quit()
                cls.p.kill()
            except Exception:
                pass


    @classmethod
    def tearDownClass(cls):
        # remove_gdrive()
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()

        remove_dependency(cls.dependency)

        src1 = os.path.join(CALIBRE_WEB_PATH, "client_secrets.json")
        src = os.path.join(CALIBRE_WEB_PATH, "gdrive_credentials")
        if os.path.exists(src):
            os.chmod(src, 0o764)
            try:
                os.unlink(src)
            except PermissionError:
                print('File delete failed')
        if os.path.exists(src1):
            os.chmod(src1, 0o764)
            try:
                os.unlink(src1)
            except PermissionError:
                print('File delete failed')

        save_logfiles(cls.__name__)


    def test_edit_title(self):
        fs = connect_gdrive("test")
        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': u'O0ü 执'})
        values = self.get_book_details()
        self.assertEqual(u'O0ü 执', values['title'])
        new_book_path = os.path.join('test', values['author'][0], 'O0u Zhi (4)')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        old_book_path = os.path.join('test', values['author'][0], 'Very long extra super turbo cool tit (4)')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)
        self.check_element_on_page((By.ID, "edit_book")).click()
        # file operation
        fout = io.BytesIO()
        fout.write(os.urandom(124))
        #with open(os.path.join(TEST_DB, values['author'][0], 'O0u Zhi (4)', 'test.dum'), 'wb') as fout:
        # fout.write(os.urandom(124))
        fs.upload(os.path.join('test', values['author'][0], 'O0u Zhi (4)', 'test.dum'), fout)
        fout.close()
        self.edit_book(content={'book_title': u' O0ü 执'}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_success'))
        title = self.check_element_on_page((By.ID, "book_title"))
        # calibre strips spaces in beginning
        self.assertEqual(u'O0ü 执', title.get_attribute('value'))
        # self.assertTrue(os.path.isdir(os.path.join(TEST_DB, values['author'][0], 'O0u Zhi (4)')))
        new_book_path = os.path.join('test', values['author'][0], 'O0u Zhi (4)')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        self.edit_book(content={'book_title': u'O0ü name'}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_success'))
        title = self.check_element_on_page((By.ID, "book_title"))
        # calibre strips spaces in the end
        self.assertEqual(u'O0ü name', title.get_attribute('value'))
        # self.assertTrue(os.path.isdir(os.path.join(TEST_DB, values['author'][0], 'O0u name (4)')))
        new_book_path = os.path.join('test', values['author'][0], 'O0u name (4)')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        # self.assertFalse(os.path.isdir(os.path.join(TEST_DB, values['author'][0], 'O0u Zhi (4)')))
        old_book_path = os.path.join('test', values['author'][0], 'O0u Zhi (4)')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)

        self.edit_book(content={'book_title': ''})
        time.sleep(WAIT_GDRIVE)
        values = self.get_book_details()
        # os.path.join(TEST_DB, values['author'][0], 'Unknown')
        self.assertEqual('Unknown', values['title'])
        # self.assertTrue(os.path.isdir(os.path.join(TEST_DB, values['author'][0], 'Unknown (4)')))
        new_book_path = os.path.join('test', values['author'][0], 'Unknown (4)')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        old_book_path = os.path.join('test', values['author'][0], 'Unknown')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': 'The camicdemo'})
        values = self.get_book_details()
        # os.path.join(TEST_DB, values['author'][0], 'The camicdemo')
        self.assertEqual('The camicdemo', values['title'])
        self.goto_page('nav_new')
        time.sleep(WAIT_GDRIVE)
        books = self.get_books_displayed()
        self.assertEqual('The camicdemo', books[1][8]['title'])
        file_path = os.path.join('test', values['author'][0], 'The camicdemo (4)')
        not_file_path = os.path.join('test', values['author'][0], 'camicdemo')

        # file operation
        fs.movedir(file_path, not_file_path, create=True)
        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': u'Not found'})
        self.check_element_on_page((By.ID, 'flash_alert'))
        title = self.check_element_on_page((By.ID, "book_title"))
        # calibre strips spaces in the end
        self.assertEqual('The camicdemo', title.get_attribute('value'))
        # file operation
        fs.movedir(not_file_path, file_path, create=True)
        # missing cover file is not detected, and cover file is moved
        cover_file = os.path.join('test', values['author'][0], 'The camicdemo (4)', 'cover.jpg')
        not_cover_file = os.path.join('test', values['author'][0], 'The camicdemo (4)', 'no_cover.jpg')

        # file operation
        fs.move(cover_file, not_cover_file)
        self.edit_book(content={'book_title': u'No Cover'}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_success'))
        title = self.check_element_on_page((By.ID, "book_title"))
        self.assertEqual('No Cover', title.get_attribute('value'))
        cover_file = os.path.join('test', values['author'][0], 'No Cover (4)', 'cover.jpg')
        not_cover_file = os.path.join('test', values['author'][0], 'No Cover (4)', 'no_cover.jpg')

        fs.move(not_cover_file, cover_file)
        fs.close()
        self.edit_book(content={'book_title': u'Pipo|;.:'}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_success'))
        title = self.check_element_on_page((By.ID, "book_title"))
        self.assertEqual(u'Pipo|;.:', title.get_attribute('value'))
        self.edit_book(content={'book_title': u'Very long extra super turbo cool title without any issue of displaying including ö utf-8 characters'})
        ele = self.check_element_on_page((By.ID, "title"))
        self.assertEqual(ele.text, u'Very long extra super turbo cool title without any issue of ...')
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': u'book6'})


    # goto Book 2
    # Change Author with unicode chars
    # save book, go to show books page
    # check Author
    # edit Author with spaces on beginning (Single name)
    # save book, stay on page
    # check Author correct, check folder name correct, old folder deleted (last book of author)
    # edit Author of book 7, book 2 and 7 have same author now
    # check authorfolder has 2 subfolders
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
    # check folder moves completly with all files
    # remove folder permissions
    # change author of book
    # error should occour
    # remove folder of author
    # change author of book
    # error should occour
    # Test Capital letters and lowercase characters
    def test_edit_author(self):
        fs = connect_gdrive("test")
        self.get_book_details(8)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor':u'O0ü 执'})
        values = self.get_book_details()
        self.assertEqual(u'O0ü 执', values['author'][0])
        new_book_path = os.path.join('test', 'O0u Zhi', 'book8 (8)')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        old_book_path = os.path.join('test', 'Leo Baskerville', 'book8 (8)')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor':u' O0ü name '}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_success'))
        author = self.check_element_on_page((By.ID, "bookAuthor"))
        # calibre strips spaces in the end
        self.assertEqual(u'O0ü name', author.get_attribute('value'))
        # self.assertTrue(os.path.isdir(os.path.join(TEST_DB, 'O0u name', 'book8 (8)')))
        new_book_path = os.path.join('test', 'O0u name', 'book8 (8)')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)

        self.edit_book(content={'bookAuthor':''})
        values = self.get_book_details()
        os.path.join(TEST_DB, 'Unknown', 'book8 (8)')
        self.assertEqual('Unknown', values['author'][0])
        # self.assertTrue(os.path.isdir(os.path.join(TEST_DB, values['author'][0], 'book8 (8)')))
        new_book_path = os.path.join('test', values['author'][0], 'book8 (8)')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)

        self.check_element_on_page((By.ID, "edit_book")).click()
        # Check authorsort
        self.edit_book(content={'bookAuthor':'Marco, Lulu de'})
        values = self.get_book_details()
        # os.path.join(TEST_DB, values['author'][0], 'book8 (8)')
        self.assertEqual(values['author'][0], 'Marco, Lulu de')
        list_element = self.goto_page('nav_author')
        # ToDo check names of List elements
        self.get_book_details(8)
        self.check_element_on_page((By.ID, "edit_book")).click()

        self.edit_book(content={'bookAuthor': 'Sigurd Lindgren'}, detail_v=True)
        time.sleep(11)
        self.check_element_on_page((By.ID, 'flash_success'))
        author = self.check_element_on_page((By.ID, "bookAuthor")).get_attribute('value')
        self.assertEqual(u'Sigurd Lindgren', author)
        new_book_path = os.path.join('test', author, 'book8 (8)')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)

        # self.assertTrue(os.path.isdir(os.path.join(TEST_DB, author, 'book8 (8)')))
        self.edit_book(content={'bookAuthor': 'Sigurd Lindgren&Leo Baskerville'}, detail_v=True)
        time.sleep(11)
        self.check_element_on_page((By.ID, 'flash_success'))
        new_book_path = os.path.join('test',  'Sigurd Lindgren', 'book8 (8)')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        old_book_path = os.path.join('test', 'Leo Baskerville', 'book8 (8)')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)

        author = self.check_element_on_page((By.ID, "bookAuthor"))
        self.assertEqual(u'Sigurd Lindgren & Leo Baskerville', author.get_attribute('value'))
        self.edit_book(content={'bookAuthor': ' Leo Baskerville & Sigurd Lindgren '}, detail_v=True)
        time.sleep(11)
        self.check_element_on_page((By.ID, 'flash_success'))

        new_book_path = os.path.join('test',  'Leo Baskerville', 'book8 (8)')
        gdrive_path = check_path_gdrive(fs, new_book_path)
        self.assertTrue(gdrive_path)
        old_book_path = os.path.join('test', 'Sigurd Lindgren', 'book8 (8)')
        gdrive_path = check_path_gdrive(fs, old_book_path)
        self.assertFalse(gdrive_path)

        self.edit_book(content={'bookAuthor': 'Pipo| Pipe'}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_success'))
        author = self.check_element_on_page((By.ID, "bookAuthor"))
        self.assertEqual(u'Pipo, Pipe', author.get_attribute('value'))
        list_element = self.goto_page('nav_author')

        file_path = os.path.join('test', 'Pipo, Pipe', 'book8 (8)')
        not_file_path = os.path.join('test', 'Pipo, Pipe', 'nofolder')
        fs.movedir(file_path, not_file_path, create=True)
        self.get_book_details(8)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor': u'Not found'})
        self.check_element_on_page((By.ID, 'flash_alert'))
        author = self.check_element_on_page((By.ID, "bookAuthor"))
        self.assertEqual('Pipo, Pipe', author.get_attribute('value'))
        fs.movedir(not_file_path, file_path, create=True)
        fs.close()
        self.edit_book(content={'bookAuthor': 'Leo Baskerville'}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_success'))


    # series with unicode spaces, ,|,
    def test_edit_series(self):
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':u'O0ü 执'})
        values = self.get_book_details()
        self.assertEqual(u'O0ü 执', values['series'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':u'Alf|alfa, Kuko'})
        values = self.get_book_details()
        self.assertEqual(u'Alf|alfa, Kuko', values['series'])
        list_element = self.goto_page('nav_serie')
        # list_element = self.get_series_books_displayed()
        self.assertEqual(list_element[0].text, u'Alf|alfa, Kuko')

        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':''})
        values = self.get_book_details()
        self.assertFalse('series' in values)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':'Loko'}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_success'))
        series = self.check_element_on_page((By.ID, "series"))
        self.assertEqual(u'Loko', series.get_attribute('value'))

        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':u'loko'})
        values = self.get_book_details()
        self.assertEqual(u'loko', values['series'])
        list_element = self.goto_page('nav_serie')
        # list_element = self.get_series_books_displayed()
        self.assertEqual(list_element[1].text, u'loko')

        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':u'Loko', 'series_index':'1.0'})
        values = self.get_book_details()
        self.assertEqual(u'Loko', values['series'])
        self.check_element_on_page((By.XPATH, "//*[contains(@href,'series')]/ancestor::p/a")).click()
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 2)
        books[1][0]['ele'].click()
        time.sleep(2)
        ele = self.check_element_on_page((By.ID, "title"))
        self.assertEqual(u'book6', ele.text)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series': u''})

    def test_edit_category(self):
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':u'O0ü 执'})
        values = self.get_book_details()
        self.assertEqual(len(values['tag']), 1)
        self.assertEqual(u'O0ü 执', values['tag'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':u'Alf|alfa'})
        values = self.get_book_details()
        self.assertEqual(u'Alf|alfa', values['tag'][0])
        list_element = self.goto_page('nav_cat')
        self.assertEqual(list_element[0].text, u'Alf|alfa')

        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':''})
        values = self.get_book_details()
        self.assertEqual(len(values['tag']), 0)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':u' Gênot & Peter '}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_success'))
        tags = self.check_element_on_page((By.ID, "tags"))
        self.assertEqual(u'Gênot & Peter', tags.get_attribute('value'))

        self.edit_book(content={'tags':u' Gênot , Peter '})
        values = self.get_book_details()
        self.assertEqual(u'Gênot', values['tag'][0])
        self.assertEqual(u'Peter', values['tag'][1])

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':u'gênot'})
        values = self.get_book_details()
        self.assertEqual(u'gênot', values['tag'][0])
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':'Gênot'})


    def test_edit_publisher(self):
        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':u'O0ü 执'})
        values = self.get_book_details()
        self.assertEqual(len(values['publisher']), 1)
        self.assertEqual(u'O0ü 执', values['publisher'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':u'Beta|,Bet'})
        values = self.get_book_details()
        self.assertEqual(u'Beta|,Bet', values['publisher'][0])
        list_element = self.goto_page('nav_publisher')
        self.assertEqual(list_element[0].text, u'Beta|,Bet', "Publisher Sorted according to name, B before R")

        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':''})
        values = self.get_book_details()
        self.assertEqual(len(values['publisher']), 0)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':u' Gênot & Peter '}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_success'))
        publisher = self.check_element_on_page((By.ID, "publisher"))
        self.assertEqual(u'Gênot & Peter', publisher.get_attribute('value'))

        self.edit_book(content={'publisher':u' Gênot , Peter '})
        values = self.get_book_details()
        self.assertEqual(u'Gênot , Peter', values['publisher'][0])

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':u'gênot'})
        values = self.get_book_details()
        self.assertEqual(u'gênot', values['publisher'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':u'Gênot'})
        values = self.get_book_details()
        self.assertEqual(u'Gênot', values['publisher'][0])


    # choose language not part ob lib
    def test_edit_language(self):
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages':u'english'})
        values = self.get_book_details()
        self.assertEqual(len(values['languages']), 1)
        self.assertEqual('English', values['languages'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages':u'German'})
        values = self.get_book_details()
        self.assertEqual('German', values['languages'][0])
        list_element = self.goto_page('nav_lang')
        self.assertEqual(list_element[2].text, u'German')
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages':'German & English'}, detail_v=True)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'flash_alert'))
        self.edit_book(content={'languages': 'German, English'})
        self.get_book_details(3)
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
        self.edit_book(content={'rating':4})
        values = self.get_book_details()
        self.assertEqual(4, values['rating'])
        self.goto_page('nav_rated')
        books = self.get_books_displayed()
        self.assertEqual(1, len(books[1]))
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'rating':5})
        values = self.get_book_details()
        self.assertEqual(5, values['rating'])
        self.goto_page('nav_rated')
        books = self.get_books_displayed()
        self.assertEqual(2, len(books[1]))
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'rating':0})
        values = self.get_book_details()
        self.assertEqual(0, values['rating'])

    # change comments, add comments, delete comments
    def test_edit_comments(self):
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'description':u'bogomirä 人物'})
        values = self.get_book_details()
        self.assertEqual(u'bogomirä 人物', values['comment'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'description':''})
        values = self.get_book_details()
        self.assertEqual('', values['comment'])

    # change comments, add comments, delete comments
    def test_edit_custom_bool(self):
        self.assertEqual(len(self.adv_search({u'custom_column_3': u'Yes'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Bool 1 Ä':u'Yes'})
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
        self.edit_book(custom_content={u'Custom Rating 人物':'3'})
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
        self.edit_book(custom_content={u'Custom 人物 Enum':u'人物'})
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

    def test_upload_cover_hdd(self):
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        jpegcover = os.path.join(base_path, 'files', 'cover.jpg')
        self.edit_book(content={'local_cover': jpegcover})
        self.driver.refresh()
        time.sleep(2)
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083/cover/5')
        with open(jpegcover, 'rb') as reader:
            self.assertEqual(reader.read(), resp.content)

        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        bmpcover = os.path.join(base_path, 'files', 'cover.bmp')
        self.edit_book(content={'local_cover': bmpcover})
        self.assertTrue(self.check_element_on_page((By.CLASS_NAME, "alert")))
        self.driver.refresh()
        time.sleep(2)
        resp = r.get('http://127.0.0.1:8083/cover/5')
        with open(jpegcover, 'rb') as reader:
            self.assertEqual(reader.read(), resp.content)

        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        pngcover = os.path.join(base_path, 'files', 'cover.png')
        self.edit_book(content={'local_cover': pngcover})
        self.driver.refresh()
        time.sleep(2)
        resp = r.get('http://127.0.0.1:8083/cover/5')
        self.assertAlmostEqual(20317, int(resp.headers['Content-Length']), delta=300)

        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        pngcover = os.path.join(base_path, 'files', 'cover.webp')
        self.edit_book(content={'local_cover': pngcover})
        self.driver.refresh()
        time.sleep(2)
        resp = r.get('http://127.0.0.1:8083/cover/5')
        self.assertAlmostEqual(17420, int(resp.headers['Content-Length']), delta=300)
        r.close()
        self.assertTrue(False, "Browser-Cache Problem: Old Cover is displayed instead of New Cover")


    def test_upload_book_lit(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.lit')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        # ToDo: check file contents
        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('book', details['title'])
        self.assertEqual('Unknown', details['author'][0])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('182574', resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()

    def test_upload_book_epub(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.epub')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)

        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('book9', details['title'])
        self.assertEqual('Noname 23', details['author'][0])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('8936', resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()
        # ToDo: Check folder are right


    # download of books
    def test_download_book(self):
        self.goto_page('user_setup')
        book_downloads = self.driver.find_elements_by_class_name("media-object")
        self.assertEqual(0, len(book_downloads))
        self.get_book_details(5)
        element = self.check_element_on_page((By.XPATH, "//*[starts-with(@id,'btnGroupDrop')]"))
        download_link = element.get_attribute("href")
        self.assertTrue(download_link.endswith('/5.epub'),
                        'Download Link has invalid format for kobo browser, has to end with filename')
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get(download_link)
        self.assertEqual(resp.headers['Content-Type'], 'application/epub+zip')
        self.assertEqual(resp.status_code, 200)
        self.edit_user('admin', {'download_role':0})
        resp = r.get(download_link)
        self.assertEqual(resp.status_code, 403)
        book = self.get_book_details(5)
        self.assertNotIn('download', book)
        self.edit_user('admin', {'download_role': 1})
        r.close()
        self.goto_page('user_setup')
        book_downloads = self.driver.find_elements_by_class_name("media-object")
        self.assertEqual(1, len(book_downloads))
        book_downloads[0].click()
        book = self.get_book_details()
        self.assertEqual('testbook', book['title'])
        # self.assertFalse(self.check_element_on_page((By.XPATH, "//*/h2/div/")))'''
