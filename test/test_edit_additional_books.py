#!/usr/bin/env python
# -*- coding: utf-8 -*-

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


@unittest.skipIf(is_unrar_not_present(), "Skipping convert, unrar not found")
class TestEditAdditionalBooks(TestCase, ui_class):
    p = None
    driver = None
    dependencys = ['comicapi', 'rarfile']

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependencys, cls.__name__)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB})
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        remove_dependency(cls.dependencys)
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def check_identifier(self, result, key, name, value, only_value=False):
        identifier = [sub[key] for sub in result['identifier'] if key in sub]
        self.assertTrue(len(identifier))
        if not only_value:
            self.assertTrue(name in identifier[0])
        self.assertTrue(value in identifier[0])

    def test_cbz_comicinfo(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

        upload_file = os.path.join(base_path, 'files', 'book2.cbz')
        other_file = os.path.join(base_path, 'files', 'book1.cbz')
        zipdata = [os.path.join(base_path, 'files', 'cover.webp')]
        names = ['cover1.weBp']
        createcbz(other_file, zipdata, names)
        change_comic_meta(upload_file, other_file, element={"Writer": "Test Writer",
                                                            "Summary": "Testdummy",
                                                            "Series": "Hilo",
                                                            "Title": "With Title"})
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('With Title', details['title'])
        self.assertEqual('Test Writer', details['author'][0])
        self.assertEqual('3', details['series_index'])
        self.assertEqual('Hilo', details['series'])
        self.assertEqual('Testdummy', details['comment'])

        self.fill_basic_config({'config_uploading': 0})
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.delete_book(details['id'])
        os.remove(upload_file)
        os.remove(other_file)

    def test_upload_cbz_coverformats(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # Upload book to be sure we have a reference (delete book test runs maybe before this test)
        upload_file = os.path.join(base_path, 'files', 'book.fb2')
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        original_cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.delete_book(-1)

        upload_file = os.path.join(base_path, 'files', 'book1.cbz')
        # upload webp book
        zipdata = [os.path.join(base_path, 'files', 'cover.webp')]
        names = ['cover1.weBp']
        createcbz(upload_file, zipdata, names)
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreaterEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.05)
        self.delete_book(-1)

        # upload png book
        zipdata = [os.path.join(base_path, 'files', 'cover.png')]
        names = ['cover10.png']
        createcbz(upload_file, zipdata, names)
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreaterEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.05)
        self.delete_book(-1)

        # upload bmp book
        zipdata = [os.path.join(base_path, 'files', 'cover.bmp')]
        names = ['cover-0.bmp']
        createcbz(upload_file, zipdata, names)
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        cover = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
        self.assertGreaterEqual(diff(BytesIO(cover), BytesIO(original_cover), delete_diff_file=True), 0.049)
        self.delete_book(-1)
        time.sleep(2)

        self.fill_basic_config({'config_uploading': 0})
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        os.remove(upload_file)

    def test_upload_metadata_cbr(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_rarfile_location': '/bin/ur'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.fill_basic_config({'config_rarfile_location': base_path})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.fill_basic_config({'config_rarfile_location': unrar_path()})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.cbr')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Test 执book', details['title'])
        self.assertEqual('Author Name', details['author'][0])
        self.assertEqual('3', details['series_index'])
        self.assertEqual('No Series', details['series'])
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('8936', resp.headers['Content-Length'])
        self.fill_basic_config({'config_rarfile_location': ''})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_uploading': 0})
        r.close()
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_upload_metadata_cbt(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.cbt')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Test 执 to', details['title'])
        self.assertEqual('Author Nameless', details['author'][0])
        self.assertEqual('2', details['series_index'])
        self.assertEqual('No S', details['series'])
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083' + details['cover'])
        self.fill_basic_config({'config_uploading': 0})
        self.assertEqual('8936', resp.headers['Content-Length'])
        r.close()
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    # limit upload formats to epub -> check pdf -> denied, upload epub allowed
    # limit upload formats to FB2 -> upload fb2 allowed
    def test_change_upload_formats(self):
        self.fill_basic_config({'config_uploading': 1, 'config_upload_formats': 'epub'})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.pdf')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))

        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.epub')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, 'edit_cancel')))
        self.delete_book(int(self.driver.current_url.split('/')[-1]))

        self.fill_basic_config({'config_upload_formats': 'FB2'})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.fb2')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, 'edit_cancel')))
        self.delete_book(int(self.driver.current_url.split('/')[-1]))

        self.fill_basic_config({'config_upload_formats': 'jpg'})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'cover.jpg')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, 'edit_cancel')))
        self.delete_book(int(self.driver.current_url.split('/')[-1]))

        self.fill_basic_config({'config_upload_formats': ''})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'cover.bmp')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, 'edit_cancel')))
        self.delete_book(int(self.driver.current_url.split('/')[-1]))

        # dublicate formats
        self.fill_basic_config({'config_upload_formats': 'epub, ePub'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

        accordions = self.driver.find_elements(By.CLASS_NAME, "accordion-toggle")
        accordions[3].click()
        formats = self.check_element_on_page((By.ID, 'config_upload_formats'))
        self.assertEqual('epub', formats.get_attribute('value'))
        self.fill_basic_config({'config_upload_formats': 'txt,pdf,epub,kepub,mobi,azw,azw3,cbr,cbz,cbt,djvu,prc,doc,'
                                                         'docx,fb2,html,rtf,lit,odt,mp3,mp4,ogg,opus,wav,flac,m4a,m4b'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_delete_book(self):
        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Rating 人物': '4',
                                       "Custom Text 人物 *'()&": 'test text',
                                       u'Custom Bool 1 Ä': u'Yes'})
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
        os.rmdir(sub_folder)
        self.assertTrue(os.path.isdir(book_path1))
        self.assertEqual(0, len([name for name in os.listdir(book_path1) if os.path.isfile(name)]))
        self.get_book_details(1)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))

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
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))

        # change permission back
        os.chmod(book_path, 0o775)
        # delete book author folder stays
        self.delete_book(7)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(7)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB, 'John Doe')))
        # delete book -> author folder deleted
        self.delete_book(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(os.path.isdir(os.path.join(TEST_DB, 'John Doe')))
        # ToDo: what happens if folder isn't valid and no book or author folder is present?
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page("nav_new")
        upload_file = os.path.join(base_path, 'files', 'book.epub')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.edit_book(content={'bookAuthor': u'John Döe', 'book_title': u'testbook', 'languages': 'english'})
        self.fill_basic_config({'config_uploading': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    '''@unittest.skipIf(os.name == 'nt', 'writeonly database on windows is not checked')
    def test_writeonly_path(self):
        self.fill_basic_config({'config_rarfile_location': unrar_path(), "config_unicode_filename": 1})
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
        self.fill_basic_config({'config_uploading': 0, 'config_rarfile_location': "", "config_unicode_filename": 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        book_path = os.path.join(TEST_DB, 'John Doe', 'Buuko (9)')
        self.assertTrue(os.path.isdir(book_path))
        self.goto_page('nav_new')

    @unittest.skip('Not implemented')
    def test_writeonly_calibre_database(self):
        pass'''

    def test_edit_book_identifier(self):
        reference_length = len(self.get_book_details(9)['identifier'])
        # press 3 times on add identifier save -> nothing
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.add_identifier('', '')
        self.add_identifier('', '')
        self.add_identifier('', '')
        self.check_element_on_page((By.ID, "edit_cancel")).click()
        result = self.get_book_details()
        self.assertFalse(reference_length, len(result['identifier']))

        # add identifier, don't save -> nothing
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.add_identifier('Hallo', 'bert')
        self.check_element_on_page((By.ID, "edit_cancel")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length, len(result['identifier']))

        # add identifier, remove it, save -> nothing
        self.check_element_on_page((By.ID, "edit_book")).click()
        key_id = self.add_identifier('Hallo', 'bert')
        self.delete_identifier(key_id)
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length, len(result['identifier']))

        # add identifier, save -> visible
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.add_identifier('Hallo', 'bert')
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length + 1, len(result['identifier']))
        self.assertEqual('Hallo', list(result['identifier'][-1].keys())[0])

        # edit identifier value and key, don't save -> old value
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_identifier_value('Hallo', 'bert1')
        self.edit_identifier_key('Hallo', 'Hallo1')
        self.check_element_on_page((By.ID, "edit_cancel")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length + 1, len(result['identifier']))
        self.assertEqual('Hallo', list(result['identifier'][-1].keys())[0])

        # edit identifier value and key, save -> new value
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertEqual('bert', self.get_identifier_value('Hallo'))
        self.edit_identifier_value('Hallo', 'bert1')
        self.edit_identifier_key('Hallo', 'Hallo1')
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length + 1, len(result['identifier']))
        self.assertEqual('Hallo1', list(result['identifier'][-1].keys())[0])

        # edit identifier value, save -> new value
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertEqual('bert1', self.get_identifier_value('Hallo1'))

        self.edit_identifier_value('Hallo1', 'bert2')
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length + 1, len(result['identifier']))
        self.assertEqual('Hallo1', list(result['identifier'][-1].keys())[0])

        # edit identifier key, save -> new key
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertEqual('bert2', self.get_identifier_value('Hallo1'))

        self.edit_identifier_key('Hallo1', 'Hallo2')
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length + 1, len(result['identifier']))
        self.assertEqual('Hallo2', list(result['identifier'][-1].keys())[0])

        # delete identifier, don't save -> still there
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.delete_identifier('Hallo2')
        self.check_element_on_page((By.ID, "edit_cancel")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length + 1, len(result['identifier']))
        self.assertEqual('Hallo2', list(result['identifier'][-1].keys())[0])

        # delete identifier, save -> gone
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.delete_identifier('Hallo2')
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length, len(result['identifier']))

        # add 2 identifier, save -> both there
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.add_identifier('koli', 'bri')
        self.add_identifier('kilo', 'bro')
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length + 2, len(result['identifier']))
        self.assertEqual('kilo', list(result['identifier'][-2].keys())[0])
        self.assertEqual('koli', list(result['identifier'][-1].keys())[0])

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.delete_identifier('kilo')
        self.delete_identifier('koli')
        self.check_element_on_page((By.ID, "submit")).click()

    def test_edit_special_book_identifier(self):
        reference_length = len(self.get_book_details(3)['identifier'])

        # add identifier with unicode key and value -> okay
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.add_identifier('O0ü 执', '一 Öl')
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length + 1, len(result['identifier']))
        self.assertEqual('O0ü 执', list(result['identifier'][-1].keys())[0])

        # add identifier with space at end -> okay
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertEqual('一 Öl', self.get_identifier_value('O0ü 执'))
        self.add_identifier('O0ü ', '1234 ')
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length + 2, len(result['identifier']))
        self.assertEqual('O0ü ', list(result['identifier'][-2].keys())[0])

        # add identifier with ,|:;_#+\?^ -> okay
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertEqual('1234 ', self.get_identifier_value('O0ü '))
        self.add_identifier(',|:;_#+\?^', '^!:;,|_#+\?')
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length + 3, len(result['identifier']))
        self.assertEqual(',|:;_#+\?^', list(result['identifier'][-3].keys())[0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertEqual('^!:;,|_#+\?', self.get_identifier_value(',|:;_#+\?^'))
        self.delete_identifier('O0ü 执')
        self.delete_identifier(',|:;_#+\?^')
        self.delete_identifier('O0ü ')
        self.check_element_on_page((By.ID, "submit")).click()

    def test_edit_book_identifier_capital(self):
        # add identifier with same name except capital letter and lowercase letter -> Warning is displayed
        reference_length = len(self.get_book_details(13)['identifier'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.add_identifier('alfa', '123456')
        self.add_identifier('AlfA', '1246')
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()
        self.assertEqual(reference_length + 1, len(result['identifier']))
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertTrue(self.delete_identifier('AlfA'))
        self.check_element_on_page((By.ID, "submit")).click()

    def test_edit_book_identifier_standard(self):
        reference_length = len(self.get_book_details(4)['identifier'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.add_identifier('aMazon', '123456')
        self.add_identifier('IsBN', '897654')
        self.add_identifier('doI', 'abcdef')
        self.add_identifier('gooDreads', 'fedcba')
        self.add_identifier('gooGle', 'xyz')
        self.add_identifier('lubimyCzytac', 'jikuz')
        self.add_identifier('asin', 'abc123')
        self.add_identifier('douBan', '123abc')
        self.add_identifier('kObo', 'mnopqrst')
        self.add_identifier('url', '987654')
        self.add_identifier('AMaZON_DE', 'a1b2c3')
        self.add_identifier('kurl', '9876ä4')
        self.add_identifier('knöffi', 'http://susi.com/huhu')
        self.add_identifier('javascript', 'javascript:alert(1)')
        self.check_element_on_page((By.ID, "submit")).click()
        result = self.get_book_details()

        self.check_identifier(result, 'Amazon', 'amazon.com', '123456')
        self.check_identifier(result, 'ISBN', 'worldcat', '897654')
        self.check_identifier(result, 'DOI', 'doi.org', 'abcdef')
        self.check_identifier(result, 'Goodreads', 'goodreads', 'fedcba')
        self.check_identifier(result, 'Google Books', 'books.google', 'xyz')
        self.check_identifier(result, 'Lubimyczytac', 'lubimyczytac', 'jikuz')
        self.check_identifier(result, 'asin', 'amazon', 'abc123')
        self.check_identifier(result, 'Douban', 'douban', '123abc')
        self.check_identifier(result, 'Kobo', 'kobo', 'mnopqrst')
        self.check_identifier(result, 'url', '', '987654', True)
        self.check_identifier(result, 'kurl', '', '9876ä4', True)
        self.check_identifier(result, 'knöffi', '', 'http://susi.com/huhu', True)
        self.check_identifier(result, 'Amazon.de', 'amazon.de', 'a1b2c3', True)
        self.check_identifier(result, 'javascript', '', 'javascript%3Aalert%281%29', True)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.delete_identifier('aMazon')
        self.delete_identifier('IsBN')
        self.delete_identifier('doI')
        self.delete_identifier('gooDreads')
        self.delete_identifier('gooGle')
        self.delete_identifier('lubimyCzytac')
        self.delete_identifier('asin')
        self.delete_identifier('douBan')
        self.delete_identifier('kObo')
        self.delete_identifier('url')
        self.delete_identifier('AMaZON_DE')
        self.delete_identifier('kurl')
        self.delete_identifier('knöffi')
        self.delete_identifier('javascript')
        self.check_element_on_page((By.ID, "submit")).click()
        final_length = len(self.get_book_details(4)['identifier'])
        self.assertEqual(final_length, reference_length)

    def test_upload_edit_role(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_user('user0', {'password': '1234', 'email': 'a@b.com', 'upload_role': 0, 'edit_role': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'user0', 'password': '1234', 'submit': "", 'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        upload_file = open(os.path.join(base_path, 'files', 'book.cbt'), 'rb')
        files = {'btn-upload': upload_file}
        result = r.post('http://127.0.0.1:8083/upload', files=files, data={"csrf_token": token.group(1)})
        self.assertEqual(403, result.status_code)
        upload_file.close()
        book_page = r.get('http://127.0.0.1:8083/admin/book/13')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', book_page.text)
        values = {'book_title': 'Buuko', 'author_name': 'John Döe', 'description': '',
                  'tags': 'Gênot', 'series': 'Djüngel', 'series_index': '3.0', 'ratings': '4',
                  'pubdate': '', 'languages': '', 'detail_view': 'on', "csrf_token": token.group(1)}
        upload_file = open(os.path.join(base_path, 'files', 'book.cbt'), 'rb')
        files_format = {'btn-upload-format': upload_file}
        result = r.post('http://127.0.0.1:8083/admin/book/13', files=files_format, data=values)
        self.assertEqual(200, result.status_code)
        self.assertTrue("flash_danger" in result.text)
        upload_file.close()
        cover_file = open(os.path.join(base_path, 'files', 'cover.jpg'), 'rb')
        files_cover = {'btn-upload-cover': cover_file}
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', book_page.text)
        values['csrf_token'] = token.group(1)
        result = r.post('http://127.0.0.1:8083/admin/book/13', files=files_cover, data=values)
        self.assertEqual(200, result.status_code)
        self.assertTrue("flash_danger" in result.text)
        cover_file.close()
        values['cover_url'] = "/home/user/kurt.jpg"
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', book_page.text)
        values['csrf_token'] = token.group(1)
        result = r.post('http://127.0.0.1:8083/admin/book/13', data=values)
        self.assertEqual(200, result.status_code)
        self.assertTrue("flash_danger" in result.text)
        r.close()
        self.login('user0', '1234')
        self.assertFalse(self.check_element_on_page((By.ID, 'btn-upload')))
        self.get_book_details(13)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertFalse(self.check_element_on_page((By.ID, 'btn-upload-cover')))
        self.assertFalse(self.check_element_on_page((By.ID, 'btn-upload-format')))
        self.assertFalse(self.check_element_on_page((By.ID, 'cover_url')))
        self.logout()
        self.login('admin', 'admin123')
        self.edit_user('user0', {'upload_role': 1})
        self.logout()
        self.login('user0', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, 'btn-upload')))
        self.get_book_details(13)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertTrue(self.check_element_on_page((By.ID, 'btn-upload-cover')))
        self.assertTrue(self.check_element_on_page((By.ID, 'btn-upload-format')))
        self.assertTrue(self.check_element_on_page((By.ID, 'cover_url')))
        self.logout()
        self.login('admin', 'admin123')
        self.edit_user('user0', {'edit_role': 0})
        self.logout()
        self.login('user0', '1234')
        self.get_book_details(13)
        self.assertFalse(self.check_element_on_page((By.ID, "edit_book")))
        self.logout()
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'user0', 'password': '1234', 'submit': "", 'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        result = r.get('http://127.0.0.1:8083/admin/book/13')
        self.assertEqual(403, result.status_code)
        r.close()

        self.login('admin', 'admin123')
        self.edit_user('user0', {'delete': 1})
        self.fill_basic_config({'config_uploading': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_delete_role(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()

        upload = self.check_element_on_page((By.ID, 'btn-upload-format'))
        upload_file = os.path.join(base_path, 'files', 'book.fb2')
        upload.send_keys(upload_file)
        submit = self.check_element_on_page((By.ID, "submit"))
        submit.click()
        self.fill_basic_config({'config_uploading': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

        self.create_user('user2', {'password': '1234', 'email': 'a2@b.com', 'edit_role': 0, 'delete_role': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'user2', 'password': '1234', 'submit': "", 'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        result = r.get('http://127.0.0.1:8083/book/12')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', result.text)
        payload = {"csrf_token": token.group(1)}
        result = r.post('http://127.0.0.1:8083/delete/12/FB2', data=payload)
        self.assertEqual(403, result.status_code)
        result = r.post('http://127.0.0.1:8083/delete/12', data=payload)
        self.assertEqual(403, result.status_code)
        result = r.post('http://127.0.0.1:8083/ajax/delete/12', data=payload)
        self.assertEqual(200, result.status_code)
        self.assertEqual("danger", result.json()['type'])

        self.login('admin', 'admin123')
        self.edit_user('user2', {'edit_role': 1, 'delete_role': 0})
        self.logout()
        self.login('user2','1234')
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertFalse(self.check_element_on_page((By.ID, "delete")))
        self.logout()
        result = r.post('http://127.0.0.1:8083/delete/12/FB2', data=payload)
        self.assertEqual(200, result.status_code)
        self.assertTrue('flash_danger' in result.text)
        result = r.post('http://127.0.0.1:8083/delete/12', data=payload)
        self.assertEqual(200, result.status_code)
        self.assertTrue('flash_danger' in result.text)
        self.login('admin', 'admin123')
        self.edit_user('user2', {'delete_role': 1})
        self.logout()
        self.login('user2','1234')
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "delete")))
        self.assertTrue(self.delete_book_format(12, 'FB2'))
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('admin', 'admin123')
        self.edit_user('user2', {'delete': 1})
        # ToDo: Test book delete rights on book list

    def test_title_sort(self):
        # check trim of whitespaces work
        self.assertEqual(7, len(self.search(' book ')))
        self.edit_book(3, content={'book_title': u'The Audiobok'})
        self.edit_book(13, content={'book_title': u'A bok'})
        self.search('bok')
        time.sleep(2)
        order = {'asc': (3, 13)}  # Audiobok, The is before bok, A
        self.verify_order("search", order=order)

        self.edit_book(3, content={'book_title': u'A Audiobok'})
        self.edit_book(13, content={'book_title': u'The bok'})
        self.search('bok')
        time.sleep(2)
        order = {'asc': (3, 13)}  # Audiobok, A is before bok, The
        self.verify_order("search", order=order)

        self.fill_view_config({'config_title_regex': '^(Beta)\s+'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_book(3, content={'book_title': u'Beta Audiobok'})
        self.edit_book(13, content={'book_title': u'A bok'})
        self.search('bok')
        time.sleep(2)
        order = {'asc': (13, 3)}  # A bok is before Audiobook, Beta
        self.verify_order("search", order=order)

        self.edit_book(13, content={'book_title': u'book11'})
        self.edit_book(3, content={'book_title': u'Comicdemo'})
        self.fill_view_config({'config_title_regex':
                                   '^(A|The|An|Der|Die|Das|Den|Ein|Eine|Einen|Dem|Des|Einem|Eines)\s+'})

    def test_xss_comment_edit(self):
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        book_page = r.get('http://127.0.0.1:8083/admin/book/3')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', book_page.text)
        book_payload = {'description': '<p>calibre Quick Start Guide</p><img src=x onerror=alert("Huhu")>', 'author_name': 'Asterix Lionherd', 'book_title': 'Comicdemo', 'tags':'', 'series':'Djüngel', 'series_index':'1', 'languages':'', 'publisher':'', 'pubdate':'', 'rating': '', 'custom_column_1':'', 'custom_column_2':'', 'custom_column_3':'', 'custom_column_4':'', 'custom_column_5':'', 'custom_column_6':'','custom_column_7':'', 'custom_column_8':'', 'custom_column_9':'', 'custom_column_10':'', "csrf_token": token.group(1)}
        result = r.post('http://127.0.0.1:8083/admin/book/3', data=book_payload)
        self.assertEqual(200, result.status_code)
        r.close()
        try:
            self.get_book_details(3)
        except UnexpectedAlertPresentException:
            self.assertFalse(True,"XSS in comments")
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'description': ''})
        values = self.get_book_details()
        self.assertEqual('', values['comment'])

    def test_xss_custom_comment_edit(self):
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        book_page = r.get('http://127.0.0.1:8083/admin/book/3')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', book_page.text)
        book_payload = {'description': '', 'author_name': 'Asterix Lionherd', 'book_title': '<p>calibre Quick Start Guide</p><img src=x onerror=alert("hoho")>', 'tags':'<p>calibre Quick Start Guide</p><img src=x onerror=alert("ddd")>', 'series':'<p>calibre Quick Start Guide</p><img src=x onerror=alert("hh")>', 'series_index':'1', 'languages':'', 'publisher':'', 'pubdate':'', 'rating': '', 'custom_column_1':'', 'custom_column_2':'', 'custom_column_3':'', 'custom_column_4':'', 'custom_column_5':'<p>calibre Quick Start Guide</p><img src=x onerror=alert("Huhu")>', 'custom_column_6':'','custom_column_7':'', 'custom_column_8':'', 'custom_column_9':'', 'custom_column_10':'', "csrf_token": token.group(1)}
        result = r.post('http://127.0.0.1:8083/admin/book/3', data=book_payload)
        self.assertEqual(200, result.status_code)
        r.close()
        try:
            self.get_book_details(3)
        except UnexpectedAlertPresentException:
            self.assertFalse(True,"XSS in custom comments")
        time.sleep(1)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={"book_title":"Comicdemo","tags":"", "series":"Djüngel",  }, custom_content={'Custom Comment 人物': ''})
        values = self.get_book_details()
        self.assertEqual(0, len(values['cust_columns']))

    @unittest.skip
    def test_xss_author_edit(self):
        r = requests.session()
        login_page = r.get('http://127.0.0.1:8083/login')
        #token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "remember_me": "on"} #, "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        book_page = r.get('http://127.0.0.1:8083/admin/book/3')
        # token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', book_page.text)
        book_payload = {'description': '', 'author_name': "-->'\"<script>alert(1)</script>", 'book_title': '<p>calibre Quick Start Guide</p><img src=x onerror=alert("hoho")>', 'tags':'<p>calibre Quick Start Guide</p><img src=x onerror=alert("ddd")>', 'series':'<p>calibre Quick Start Guide</p><img src=x onerror=alert("hh")>', 'series_index':'1', 'languages':'', 'publisher':'', 'pubdate':'', 'rating': '', 'custom_column_1':'', 'custom_column_2':'', 'custom_column_3':'', 'custom_column_4':'', 'custom_column_5':'<p>calibre Quick Start Guide</p><img src=x onerror=alert("Huhu")>', 'custom_column_6':'','custom_column_7':'', 'custom_column_8':'', 'custom_column_9':'', 'custom_column_10':''} #, "csrf_token": token.group(1)}
        result = r.post('http://127.0.0.1:8083/admin/book/3', data=book_payload)
        self.assertEqual(200, result.status_code)
        r.close()
        try:
            self.get_book_details(3)
        except UnexpectedAlertPresentException:
            self.assertFalse(True,"XSS in custom comments")
        time.sleep(1)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={"book_title":"Comicdemo","tags":"", "series":"Djüngel",  }, custom_content={'Custom Comment 人物': ''})
        values = self.get_book_details()
        self.assertEqual(0, len(values['cust_columns']))

    def test_details_popup(self):
        self.goto_page("nav_new")
        books = self.get_books_displayed()
        # make first book read
        books[1][0]['ele'].click()
        time.sleep(2)
        self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        self.check_element_on_page((By.ID, "details_close")).click()
        time.sleep(2)
        self.goto_page("nav_read")
        books = self.get_books_displayed()
        self.assertEqual(1, len(books[1]))
        # unread first book
        books[1][0]['ele'].click()
        time.sleep(2)
        self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        self.check_element_on_page((By.ID, "details_close")).click()
        time.sleep(2)
        self.goto_page("nav_read")
        books = self.get_books_displayed()
        self.assertEqual(0, len(books[1]))

        self.goto_page("nav_new")
        books = self.get_books_displayed()
        # make first book archived
        books[1][0]['ele'].click()
        time.sleep(2)
        self.check_element_on_page((By.XPATH, "//*[@id='archived_cb']")).click()
        self.check_element_on_page((By.ID, "details_close")).click()
        time.sleep(2)
        self.goto_page("nav_archived")
        books = self.get_books_displayed()
        self.assertEqual(1, len(books[1]))
        # unarchive first book
        books[1][0]['ele'].click()
        time.sleep(2)
        self.check_element_on_page((By.XPATH, "//*[@id='archived_cb']")).click()
        self.check_element_on_page((By.ID, "details_close")).click()
        time.sleep(2)
        self.goto_page("nav_archived")
        books = self.get_books_displayed()
        self.assertEqual(0, len(books[1]))

        # Create shelf, add book to shelf, check shelf, remove book from shelf, delete shelf
        self.create_shelf("Detail_shelf")
        self.goto_page("nav_new")
        books = self.get_books_displayed()
        # make first book archived
        books[1][0]['ele'].click()
        time.sleep(2)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'Detail_shelf')]")).click()
        self.assertTrue(self.check_element_on_page((By.XPATH, "//*[@id='remove-from-shelves']//a")))
        self.check_element_on_page((By.ID, "details_close")).click()
        time.sleep(2)
        self.list_shelfs('Detail_shelf')['ele'].click()
        books = self.get_shelf_books_displayed()
        self.assertEqual(1, len(books))
        books[0]['ele'].click()
        time.sleep(2)
        self.check_element_on_page(
            (By.XPATH, "//div[@id='remove-from-shelves']/a[contains(.,'Detail_shelf')]")).click()
        self.check_element_on_page((By.ID, "details_close")).click()
        time.sleep(2)
        self.list_shelfs('Detail_shelf')['ele'].click()
        books = self.get_shelf_books_displayed()
        self.assertEqual(0, len(books))
        self.delete_shelf("Detail_shelf")

