#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import time
import os

from helper_ui import ui_class
from helper_db import change_tag
from config_test import TEST_DB, base_path, BOOT_TIME
from helper_func import startup, change_epub_meta
from helper_func import save_logfiles
from selenium.webdriver.common.by import By


RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


class TestEditAuthors(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, port=PORTS[0], index=INDEX,
                    env={"APP_MODE": "test"})
            time.sleep(3)
        except Exception as e:
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

    # One book of the author present
    def test_change_capital_one_author_one_book(self):
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Leo Baskerville/book8 (8)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Leo Baskerville/book8 (8)',
                                                    'book8 - Leo Baskerville.epub')))
        # rename uppercase to lowercase only of author
        self.edit_book(8, content={'bookAuthor': "Leo baskerville"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Leo baskerville'], details['author'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Leo baskerville/book8 (8)',
                                                    'book8 - Leo baskerville.epub')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Leo baskerville/book8 (8)',
                                                    'cover.jpg')))
        # 'Leo baskerville' in os.listdir(TEST_DB)
        self.assertFalse('Leo Baskerville' in os.listdir(SMB_LIB))
        ret_code, content = self.download_book(8, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename book title and author in the same step
        self.edit_book(8, content={'bookAuthor': "Leo Baskerville", 'book_title': 'book 9'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Leo Baskerville'], details['author'])
        self.assertEqual('book 9', details['title'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Leo Baskerville/book 9 (8)',
                                                    'book 9 - Leo Baskerville.epub')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Leo Baskerville/book 9 (8)',
                                                    'cover.jpg')))
        self.assertFalse('Leo baskerville' in os.listdir(SMB_LIB))
        ret_code, content = self.download_book(8, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename only book title
        self.edit_book(8, content={'bookAuthor': "Leo Baskerville", 'book_title': 'book8'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Leo Baskerville'], details['author'])
        self.assertEqual('book8', details['title'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Leo Baskerville/book8 (8)',
                                                    'book8 - Leo Baskerville.epub')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Leo Baskerville/book8 (8)',
                                                    'cover.jpg')))
        self.assertFalse('Leo baskerville' in os.listdir(SMB_LIB))
        ret_code, content = self.download_book(8, "admin", "admin123")
        self.assertEqual(200, ret_code)

    # 2 books of the author present
    def test_change_capital_one_author_two_books(self):
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter Parker/book7 (10)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter Parker/book7 (10)',
                                                    'book7 - Peter Parker.epub')))
        # rename uppercase to lowercase only of author
        self.edit_book(10, content={'bookAuthor': "Peter parker"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Peter parker'], details['author'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter parker/book7 (10)',
                                                    'book7 - Peter parker.epub')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter parker/book7 (10)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter parker/Very long extra super turbo cool tit (4)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter parker/Very long extra super turbo cool tit (4)',
                                                    'Very long extra super turbo cool title wit - Peter parker.pdf')))
        self.assertFalse('Peter Parker' in os.listdir(SMB_LIB))
        ret_code, content = self.download_book(10, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(4, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename book title and author in the same step
        self.edit_book(10, content={'bookAuthor': "Peter Parker", 'book_title': 'book 7'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Peter Parker'], details['author'])
        self.assertEqual('book 7', details['title'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter Parker/book 7 (10)',
                                                    'book 7 - Peter Parker.epub')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter Parker/book 7 (10)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter Parker/Very long extra super turbo cool tit (4)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter Parker/Very long extra super turbo cool tit (4)',
                                                    'Very long extra super turbo cool title wit - Peter Parker.pdf')))
        self.assertFalse('Peter parker' in os.listdir(SMB_LIB))
        ret_code, content = self.download_book(10, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(4, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename only book title
        self.edit_book(10, content={'bookAuthor': "Peter Parker", 'book_title': 'book7'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Peter Parker'], details['author'])
        self.assertEqual('book7', details['title'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter Parker/book7 (10)',
                                                    'book7 - Peter Parker.epub')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Peter Parker/book7 (10)',
                                                    'cover.jpg')))
        self.assertFalse('Peter parker' in os.listdir(SMB_LIB))
        ret_code, content = self.download_book(8, "admin", "admin123")
        self.assertEqual(200, ret_code)

    # 1 books of the author, one co-author
    def test_change_capital_one_author_two_books_coauthor(self):
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Norbert Halagal/book11 (13)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Norbert Halagal/book11 (13)',
                                                    'book11 - Norbert Halagal.pdf')))
        # rename uppercase to lowercase only of author
        self.edit_book(13, content={'bookAuthor': "Norbert halagal"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Norbert halagal'], details['author'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Norbert halagal/book11 (13)',
                                                    'book11 - Norbert halagal.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Norbert halagal/book11 (13)',
                                                    'cover.jpg')))
        self.assertFalse('Norbert Halagal' in os.listdir(SMB_LIB))
        details = self.get_book_details(1)
        self.assertCountEqual(['Frodo Beutlin', 'Norbert halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        ret_code, content = self.download_book(13, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # rename book title and author in the same step
        self.edit_book(13, content={'bookAuthor': "Norbert Halagal", 'book_title': 'book 11'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Norbert Halagal'], details['author'])
        self.assertEqual('book 11', details['title'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Norbert Halagal/book 11 (13)',
                                                    'book 11 - Norbert Halagal.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Norbert Halagal/book 11 (13)',
                                                    'cover.jpg')))
        self.assertFalse('Norbert halagal' in os.listdir(SMB_LIB))
        ret_code, content = self.download_book(13, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename only book title
        self.edit_book(13, content={'book_title': 'book11'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Norbert Halagal'], details['author'])
        self.assertEqual('book11', details['title'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Norbert Halagal/book11 (13)',
                                                    'book11 - Norbert Halagal.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Norbert Halagal/book11 (13)',
                                                    'cover.jpg')))
        self.assertFalse('Norbert halagal' in os.listdir(SMB_LIB))
        ret_code, content = self.download_book(13, "admin", "admin123")
        self.assertEqual(200, ret_code)

    # Author only co-author
    def test_change_capital_co_author(self):
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt')))
        # rename uppercase to lowercase only of author
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu yang & Hector Gonçalves"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu yang', 'Hector Gonçalves'], details['author'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt')))
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # rename book title and author in the same step
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & Hector Gonçalves",
                                   'book_title': 'Derbook 1'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Derbook 1', details['title'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Derbook 1 (1)',
                                                    'Derbook 1 - Frodo Beutlin.txt')))
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Derbook 1 (1)',
                                                    'cover.jpg')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename only book title
        self.edit_book(1, content={'book_title': 'Der Buchtitel'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Der Buchtitel', details['title'])
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

    # Author rename co-author and author is also main author somewhere
    def test_change_capital_rename_co_author(self):
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Hector Goncalves/book9 (11)',
                                                    'book9 - Hector Goncalves.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Hector Goncalves/book9 (11)',
                                                    'cover.jpg')))
        # Author folder is not found due to utf characters not represented in filename
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & hector Gonçalves"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'hector Gonçalves'], details['author'])
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'hector Gonçalves/book9 (11)',
                                                    'book9 - hector Gonçalves.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'hector Gonçalves/book9 (11)',
                                                    'cover.jpg')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(11, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # ToDo: currently empty folder Hector Goncalves remains
        self.edit_book(11, content={'bookAuthor': "hector Gonçalves & Unbekannt"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['hector Gonçalves', 'Unbekannt'], details['author'])

        self.edit_book(11, content={'bookAuthor': "Hector Gonçalve"})
        self.edit_book(11, content={'bookAuthor': "Hector Gonçalves & unbekannt"})
        # rename uppercase to lowercase only of author
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & Hector gonçalves"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector gonçalves'], details['author'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt')))
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Hector gonçalves/book9 (11)',
                                                    'book9 - Hector gonçalves.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Hector gonçalves/book9 (11)',
                                                    'cover.jpg')))
        self.assertFalse('Hector Gonçalves' in os.listdir(SMB_LIB))

        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(11, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # rename book title and author in the same step
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & Hector Gonçalves",
                                   'book_title': 'Derbook 1'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Derbook 1', details['title'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Derbook 1 (1)',
                                                    'Derbook 1 - Frodo Beutlin.txt')))
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Derbook 1 (1)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Hector Gonçalves/book9 (11)',
                                                    'book9 - Hector Gonçalves.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Hector Gonçalves/book9 (11)',
                                                    'cover.jpg')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(11, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # rename only book title
        self.edit_book(1, content={'book_title': 'Der Buchtitel'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Der Buchtitel', details['title'])
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Hector Gonçalves/book9 (11)',
                                                    'book9 - Hector Gonçalves.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Hector Gonçalves/book9 (11)',
                                                    'cover.jpg')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

    # Author rename co-author on 2 books
    def test_change_capital_rename_two_co_authors(self):
        # check initial filenames
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg')))
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt')))
        # Add 2. author to book to have usecase
        self.edit_book(3, content={'bookAuthor': "Asterix Lionherd & Liu Yang"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Asterix Lionherd', 'Liu Yang'], details['author'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg')))

        #rename co-author
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & liu Yang & Hector Gonçalves"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'liu Yang', 'Hector Gonçalves'], details['author'])
        details = self.get_book_details(3)
        self.assertEqual(['Asterix Lionherd', 'liu Yang'], details['author'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg')))
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt')))

        ret_code, content = self.download_book(3, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # rename book title and author in the same step
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & Hector Gonçalves",
                                   'book_title': 'Derbook 1'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Derbook 1', details['title'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Derbook 1 (1)',
                                                    'Derbook 1 - Frodo Beutlin.txt')))
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Derbook 1 (1)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(3, "admin", "admin123")
        self.assertEqual(200, ret_code)
        self.edit_book(3, content={'bookAuthor': "Asterix Lionherd"})
        details = self.get_book_details(-1)
        self.assertEqual(['Asterix Lionherd'], details['author'])

        # rename only book title
        self.edit_book(1, content={'book_title': 'Der Buchtitel'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Der Buchtitel', details['title'])
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

    def test_rename_capital_on_upload(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # Upload book with one author in database
        epub_file = os.path.join(base_path, 'files', 'title.epub')
        change_epub_meta(epub_file, meta={'title': "Useless", 'creator': "asterix Lionherd"})
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details()
        self.assertEqual('Useless', details['title'])
        self.assertEqual(['asterix Lionherd'], details['author'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - asterix Lionherd.cbr')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg')))
        ret_code, content = self.download_book(3, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(details['id'], "admin", "admin123")
        self.assertEqual(200, ret_code)

        self.delete_book(details['id'])
        self.edit_book(3, content={'bookAuthor': "Asterix Lionherd"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Asterix Lionherd'], details['author'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg')))

        # Upload book with one co-author in database
        change_epub_meta(epub_file, meta={'title': "Useless", 'creator': 'liu yang'})
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details()
        self.assertEqual('Useless', details['title'])
        self.assertEqual(['liu yang'], details['author'])
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(details['id'], "admin", "admin123")
        self.assertEqual(200, ret_code)
        self.delete_book(details['id'])
        details = self.get_book_details(1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'liu yang', 'Hector Gonçalves'], details['author'])
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt')))
        self.assertFalse(os.path.isfile(os.path.join(TEST_DB, 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & Hector Gonçalves"})
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])

        # ToDo: Upload file with multiple existing authors
        self.fill_basic_config({'config_uploading': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_rename_author_emphasis_mark_onupload(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # Upload book with one author in database
        epub_file = os.path.join(base_path, 'files', 'author.epub')
        change_epub_meta(epub_file, meta={'title': "Useless", 'creator': "Stanislav lem"})
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details()
        self.assertEqual('Useless', details['title'])
        self.assertEqual(['Stanislav lem'], details['author'])
        change_epub_meta(epub_file, meta={'title': "More Useless", 'creator': "Stanislav łem"})
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        new_details = self.get_book_details()
        self.assertEqual('More Useless', new_details['title'])
        self.assertEqual(['Stanislav łem'], new_details['author'])
        first_details = self.get_book_details(details['id'])
        self.assertEqual(['Stanislav łem'], first_details['author'])
        self.delete_book(details['id'])
        self.delete_book(new_details['id'])
        self.fill_basic_config({'config_uploading': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_rename_tag_emphasis_mark_onupload(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # Upload book with one author in database
        epub_file = os.path.join(base_path, 'files', 'tag.epub')
        change_epub_meta(epub_file, meta={'title': "Useless", 'creator': "Theo so", "subject": "Genot"})
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details()
        self.assertEqual('Useless', details['title'])
        self.assertEqual(['Theo so'], details['author'])
        self.assertEqual(['Genot'], details['tag'])
        list_element = self.goto_page("nav_cat")
        self.assertTrue(list_element[0].text, "Genot")
        self.assertEqual(len(list_element), 2)
        self.edit_book(details['id'], content={u'tags': 'Gênot'})
        self.delete_book(details['id'])
        self.edit_book(10, content={u'tags': 'Georg'})
        change_tag(os.path.join(TEST_DB, "metadata.db"), "Georg", "Genot")
        details = self.get_book_details(10)
        self.assertEqual(['Genot'], details['tag'])
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details()
        self.assertEqual('Useless', details['title'])
        self.assertEqual(['Theo so'], details['author'])
        self.assertEqual(['Genot'], details['tag'])
        list_element = self.goto_page("nav_cat")
        self.assertTrue(list_element[0].text, "Genot")
        self.assertTrue(list_element[1].text, "Gênot")
        self.assertEqual(len(list_element), 3)
        self.delete_book(details['id'])
        self.edit_book(10, content={u'tags': 'Gênot'})
        self.fill_basic_config({'config_uploading': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
