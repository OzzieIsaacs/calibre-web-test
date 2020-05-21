#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import os
import unittest
from selenium.webdriver.common.by import By
import time
from helper_ui import ui_class
from config_test import TEST_DB, base_path
from parameterized import parameterized_class
from helper_func import startup, debug_startup, add_dependency, remove_dependency, unrar_path, is_unrar_not_present
import requests

'''@parameterized_class([
   { "py_version": u'/usr/bin/python'},
   { "py_version": u'/usr/bin/python3'}
],names=('Python27','Python36'))'''
@unittest.skipIf(is_unrar_not_present(),"Skipping convert, unrar not found")
class test_edit_additional_books(TestCase, ui_class):
    p=None
    driver = None
    dependencys = ['Pillow','lxml', 'git|comicapi', 'rarfile']

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependencys, cls.__name__)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB})
            time.sleep(3)
        except Exception as e:
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
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = r.get( 'http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('8936',resp.headers['Content-Length'])
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
        self.assertEqual('Test 执book', details['title'])
        self.assertEqual('Author Name', details['author'][0])
        self.assertEqual('3.0', details['series_index'])
        self.assertEqual('No Series', details['series'])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = requests.get( 'http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('8936',resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()


    def test_delete_book(self):
        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Rating 人物': '4',
                                       "Custom Text 人物 *'()&": 'test text',
                                       u'Custom Bool 1 Ä':u'Yes'})
        details = self.get_book_details(7)
        self.assertEqual('4',details['cust_columns'][0]['value'])
        self.assertEqual('ok', details['cust_columns'][1]['value'])
        self.assertEqual('test text', details['cust_columns'][2]['value'])
        book_path = os.path.join(TEST_DB, 'John Doe', 'Buuko (7)')

        # add folder to folder
        sub_folder = os.path.join(book_path, 'new_subfolder')
        os.mkdir(sub_folder)
        # delete book, -> denied because of additional folder
        self.delete_book(7)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('Buuko', details['title'])
        self.assertEqual('John Döe', details['author'][0])
        self.assertEqual('4',details['cust_columns'][0]['value'])
        self.assertEqual('ok', details['cust_columns'][1]['value'])
        self.assertEqual('test text', details['cust_columns'][2]['value'])
        os.rmdir(sub_folder)

        # change permission of folder -> denied because of access rights
        os.chmod(book_path, 0o400)
        self.delete_book(7)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))

        # change permission back
        os.chmod(book_path, 0o775)
        # delete book author folder stays
        self.delete_book(7)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        details = self.get_book_details(7)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB, 'John Doe')))
        # delete book -> author folder deleted
        self.delete_book(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(os.path.isdir(os.path.join(TEST_DB, 'John Doe')))
