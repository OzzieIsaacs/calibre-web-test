#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import shutil
from ui_helper import ui_class
from subproc_wrapper import process_open
from testconfig import CALIBRE_WEB_PATH, TEST_DB

# test editing books on gdrive


class test_edit_books(unittest.TestCase, ui_class):
    p=None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH,'app.db'))
        except:
            pass
        shutil.rmtree(TEST_DB,ignore_errors=True)
        shutil.copytree('./Calibre_db', TEST_DB)
        cls.p = process_open([u"python", os.path.join(CALIBRE_WEB_PATH,u'cps.py')],(1))

        # create a new Firefox session
        cls.driver = webdriver.Firefox()
        # time.sleep(15)
        cls.driver.implicitly_wait(5)
        print('Calibre-web started')

        cls.driver.maximize_window()

        # navigate to the application home page
        cls.driver.get("http://127.0.0.1:8083")

        # Wait for config screen to show up
        cls.fill_initial_config({'config_calibre_dir':TEST_DB})

        # wait for cw to reboot
        time.sleep(5)

        # Wait for config screen with login button to show up
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.NAME, "login")))
        login_button = cls.driver.find_element_by_name("login")
        login_button.click()

        # login and create 2nd user
        cls.login("admin", "admin123")
        # time.sleep(3)
        cls.create_user('shelf', {'edit_shelf_role':1, 'password':'123', 'email':'a@b.com'})
        cls.edit_user('admin',{'edit_shelf_role':1, 'email':'e@fe.de'})


    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin','admin123')
        while True:
            shelfs = self.list_shelfs()
            if not len(shelfs):
                break
            try:
                shelfs[0]['ele'].click()
                self.check_element_on_page((By.ID, "delete_shelf")).click()
                self.check_element_on_page((By.ID, "confirm")).click()
            except:
                pass

    # goto Book 1
    # Change Title with unicode chars
    # save title, go to show books page
    # check title
    # edit title with spaces on beginning
    # save title, stay on page
    # check title correct, check folder name correct, old folder deleted
    # edit title remove title
    # save title, stay on page
    # check title correct (unknown)
    # change title to something where the title regex matches
    # check title correct, check if book correct in order of a-z books
    # add files to folder of book
    # change title of book,
    # check folder moves completly with all files
    # remove folder permissions
    # change title of book
    # error should occour
    # delete cover file
    # change title of book
    # error metadata should occour
    # change title of book
    # delete book format
    # error metadata should occour
    # Test Capital letters and lowercase characters
    # booktitle with ,;|
    def test_edit_title(self):
        self.assertIsNone('Not Implemented')

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
    # check Author correct (unknown)
    # edit Author, add 2nd not exisiting author
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
        pass

    # series with unicode spaces, ,|,
    def test_edit_series(self):
        pass

    def test_edit_category(self):
        pass

    # choose language not part ob lib
    def test_edit_language(self):
        pass

    def test_edit_publishing_date(self):
        pass

    def test_edit_publisher(self):
        pass

    # change rating, delete rating
    # check if book with rating of 4 stars appears in list of hot books
    def test_edit_rating(self):
        pass

    # change comments, add comments, delete comments
    def test_edit_comments(self):
        pass

    # change comments, add comments, delete comments
    def test_edit_custom_bool(self):
        pass

    # change comments, add comments, delete comments
    def test_edit_custom_rating(self):
        pass

    # change comments, add comments, delete comments
    def test_edit_custom_single_select(self):
        pass

    # change comments, add comments, delete comments
    def test_edit_custom_text(self):
        pass

    # change comments, add comments, delete comments
    def test_typeahead_language(self):
        pass

    def test_typeahead_series(self):
        pass

    def test_typeahead_author(self):
        pass

    def test_typeahead_tag(self):
        pass

    def test_typeahead_publisher(self):
        pass

    def test_upload_cover_hdd(self):
        pass

    def test_delete_format(self):
        pass

    def test_delete_book(self):
        pass

    # check metadata_recocknition
    def upload_book_pdf(self):
        pass

    # check metadata_recocknition
    def upload_book_fb2(self):
        pass

    def upload_book_lit(self):
        pass

    # check metadata_recocknition
    def upload_book_epub(self):
        pass

    # check cover recocknition
    def upload_book_cbz(self):
        pass

    # check cover recocknition
    def upload_book_cbt(self):
        pass

    # check cover recocknition
    def upload_book_cbr(self):
        pass

    # database errors
    def test_database_errors(self):
        pass

    # download of books
    def test_database_errors(self):
        pass

