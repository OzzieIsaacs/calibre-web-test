#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import os
import unittest
import time
import requests

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB, base_path, BOOT_TIME
# from .parameterized import parameterized_class
from helper_func import startup, debug_startup, add_dependency, remove_dependency, unrar_path, is_unrar_not_present


@unittest.skipIf(is_unrar_not_present(), "Skipping convert, unrar not found")
class TestEditAdditionalBooks(TestCase, ui_class):
    p = None
    driver = None
    dependencys = ['Pillow', 'lxml', 'git|comicapi', 'rarfile']

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependencys, cls.__name__)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB})
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()


    @classmethod
    def tearDownClass(cls):
        remove_dependency(cls.dependencys)
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()

    def test_upload_metadate_cbr(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_rarfile_location': '/bin/ur'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.fill_basic_config({'config_rarfile_location': base_path})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.fill_basic_config({'config_rarfile_location': unrar_path()})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.cbr')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('Test 执book', details['title'])
        self.assertEqual('Author Name', details['author'][0])
        self.assertEqual('3.0', details['series_index'])
        self.assertEqual('No Series', details['series'])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('8936', resp.headers['Content-Length'])
        self.fill_basic_config({'config_rarfile_location': ''})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_uploading': 0})
        r.close()

    def test_upload_metadata_cbt(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.cbt')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('Test 执 to', details['title'])
        self.assertEqual('Author Nameless', details['author'][0])
        self.assertEqual('2.0', details['series_index'])
        self.assertEqual('No S', details['series'])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('8936', resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()


    def test_delete_book(self):
        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Rating 人物': '4',
                                       "Custom Text 人物 *'()&": 'test text',
                                       u'Custom Bool 1 Ä':u'Yes'})
        details = self.get_book_details(7)
        self.assertEqual('4', details['cust_columns'][0]['value'])
        self.assertEqual('ok', details['cust_columns'][1]['value'])
        self.assertEqual('test text', details['cust_columns'][2]['value'])
        book_path = os.path.join(TEST_DB, 'John Doe', 'Buuko (7)')

        # add folder to folder
        details = self.get_book_details(1)
        book_path1 = os.path.join(TEST_DB, details['author'][0], details['title'] + ' (1)')
        sub_folder = os.path.join(book_path1, 'new_subfolder')
        os.mkdir(sub_folder)
        # delete book, -> denied because of additional folder
        self.delete_book(1)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        # self.check_element_on_page((By.ID, 'edit_cancel')).click()
        os.rmdir(sub_folder)
        self.assertTrue(os.path.isdir(book_path1))
        self.assertEqual(0,len([name for name in os.listdir(book_path1) if os.path.isfile(name)]))
        self.get_book_details(1)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))

        details = self.get_book_details(7)
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB, 'John Doe')))
        self.assertEqual('Buuko', details['title'])
        self.assertEqual('John Döe', details['author'][0])
        self.assertEqual('4', details['cust_columns'][0]['value'])
        self.assertEqual('ok', details['cust_columns'][1]['value'])
        self.assertEqual('test text', details['cust_columns'][2]['value'])

        # change permission of folder -> delete denied because of access rights
        os.chmod(book_path, 0o400)
        self.delete_book(7)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))

        # change permission back
        os.chmod(book_path, 0o775)
        # delete book author folder stays
        self.delete_book(7)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(7)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB, 'John Doe')))
        # delete book -> author folder deleted
        self.delete_book(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(os.path.isdir(os.path.join(TEST_DB, 'John Doe')))

        # ToDo: what happens if folder isn't valid and no book or author folder is present?

    def test_writeonly_path(self):
        self.goto_page('nav_new')
        number_books = self.get_books_displayed()
        self.fill_view_config({'config_read_column': "Custom Bool 1 Ä"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_uploading':1})
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
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        details = self.get_book_details(9)
        self.assertEqual('Gênot', details['tag'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'book_title': 'Buuk'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        details = self.get_book_details(9)
        self.assertEqual('Buuko', details['title'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'bookAuthor': 'Jon Döe'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        details = self.get_book_details(9)
        self.assertEqual('John Döe', details['author'][0])


        values = self.get_book_details(8)
        self.assertFalse(values['read'])
        read = self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']"))
        self.assertTrue(read)
        read.click()
        values = self.get_book_details(8)
        self.assertFalse(values['read'])

        upload_file = os.path.join(base_path, 'files', 'book.cbr')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        books = self.get_books_displayed()
        self.assertEqual(len(number_books[1]), len(books[1]))
        # restart and check it fails
        self.restart_calibre_web()
        self.goto_page('nav_new')
        os.chmod(TEST_DB, rights)
        self.fill_initial_config(dict(config_calibre_dir=TEST_DB))
        # wait for cw to reboot
        time.sleep(BOOT_TIME)
        # Wait for config screen with login button to show up
        login_button = self.driver.find_element_by_name("login")
        login_button.click()
        self.login("admin", "admin123")
        self.fill_basic_config({'config_uploading': 0})

        book_path = os.path.join(TEST_DB, 'John Doe', 'Buuko (9)')
        self.assertTrue(os.path.isdir(book_path))

    def test_writeonly_database(self):
        pass
