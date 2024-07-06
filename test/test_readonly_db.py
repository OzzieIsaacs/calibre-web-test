from unittest import TestCase
import os
import unittest
import time
import requests
import re
from diffimg import diff
from io import BytesIO

from selenium.webdriver.common.by import By
from selenium.common.exceptions import UnexpectedAlertPresentException
from helper_ui import ui_class
from config_test import TEST_DB, base_path, BOOT_TIME
# from .parameterized import parameterized_class
from helper_func import startup, add_dependency, remove_dependency, unrar_path, is_unrar_not_present, createcbz
from helper_func import change_comic_meta
from helper_func import save_logfiles


RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


@unittest.skipIf(os.name == 'nt', 'writeonly database on windows is not checked')
class TestReadOnlyDatabase(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, port=PORTS[0], index=INDEX,)
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

    @unittest.skipIf(os.name == 'nt', 'readonly database on windows is not checked')
    def test_readonly_path(self):
        self.fill_basic_config({"config_unicode_filename": 1})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        number_books = self.get_books_displayed()
        self.fill_view_config({'config_read_column': "Custom Bool 1 Ä"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags': 'Gênot',
                                "bookAuthor": 'John Döe',
                                'book_title': 'Buuko'})
        rights = os.stat(TEST_DB).st_mode & 0o777
        os.chmod(TEST_DB, 0o400)
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'tags': 'Geno'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(9)
        self.assertEqual('Gênot', details['tag'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'book_title': 'Buuk'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(9)
        self.assertEqual('Buuko', details['title'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'bookAuthor': 'Jon Döe'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(9)
        self.assertEqual('John Döe', details['author'][0])

        values = self.get_book_details(8)
        self.assertFalse(values['read'])
        read = self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']"))
        self.assertTrue(read)
        read.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        values = self.get_book_details(8)
        self.assertFalse(values['read'])

        upload_file = os.path.join(base_path, 'files', 'book.cbr')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        books = self.get_books_displayed()
        self.assertEqual(len(number_books[1]), len(books[1]))
        # restart and check it fails
        self.restart_calibre_web()
        self.goto_page('nav_new')
        os.chmod(TEST_DB, rights)
        self.fill_db_config(dict(config_calibre_dir=TEST_DB))
        # wait for cw to reboot
        time.sleep(2)
        self.fill_basic_config({'config_uploading': 0, "config_unicode_filename": 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        book_path = os.path.join(TEST_DB, 'John Doe', 'Buuko (9)')
        self.assertTrue(os.path.isdir(book_path))
        self.goto_page('nav_new')


