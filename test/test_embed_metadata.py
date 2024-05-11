#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase
import time
import os
import shutil
import zipfile

from helper_email_convert import AIOSMTPServer
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup, save_logfiles, read_metadata_epub, read_opf_metadata, wait_Email_received
from helper_email_convert import calibre_path, kepubify_path

RESOURCES = {'ports': 2}

PORTS = ['8083', '1025']
INDEX = ""

class TestEmbedMetadata(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB},
                    port=PORTS[0],
                    index=INDEX, env={"APP_MODE": "test"})
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

    def test_download_check_metadata(self):
        # no calibre download
        self.fill_basic_config({'config_binariesdir': ''})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        code, txt_content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, code)
        self.assertEqual(15608, len(txt_content))
        code, epub_content = self.download_book(10, "admin", "admin123")
        self.assertEqual(200, code)
        self.assertEqual(5954, len(epub_content))
        epub_data = read_metadata_epub(epub_content)
        self.assertEqual("Unknown", epub_data['author'][0])
        self.assertEqual("", epub_data['pub_date'])
        code, pdf_content = self.download_book(13, "admin", "admin123")
        self.assertEqual(200, code)
        self.assertEqual(28590, len(pdf_content))
        self.fill_basic_config({'config_binariesdir': calibre_path(), 'config_embed_metadata': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        code, txt_content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, code)
        self.assertEqual(15608, len(txt_content))
        code, epub_content = self.download_book(10, "admin", "admin123")
        self.assertEqual(200, code)
        self.assertEqual(5954, len(epub_content))
        epub_data = read_metadata_epub(epub_content)
        self.assertEqual("Unknown", epub_data['author'][0])
        self.assertEqual("", epub_data['pub_date'])
        code, pdf_content = self.download_book(13, "admin", "admin123")
        self.assertEqual(200, code)
        self.assertEqual(28590, len(pdf_content))
        self.fill_basic_config({'config_embed_metadata': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        code, txt_content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, code)
        self.assertEqual(15608, len(txt_content))
        code, epub_content = self.download_book(10, "admin", "admin123")
        self.assertEqual(200, code)
        self.assertEqual(20746, len(epub_content))
        epub_data = read_metadata_epub(epub_content)
        self.assertEqual("book7", epub_data['title'])
        self.assertEqual("Peter Parker", epub_data['author'][0])
        self.assertEqual("en", epub_data['language'][0])
        self.assertEqual("Gênot", epub_data['tags'][0])
        code, pdf_content = self.download_book(13, "admin", "admin123")
        self.assertEqual(200, code)
        self.assertEqual(40028, len(pdf_content))

    def test_download_permissions_missing_file(self):
        txt_path = os.path.join(TEST_DB, "Frodo Beutlin", "Der Buchtitel (1)", "Der Buchtitel - Frodo Beutlin.txt")
        rights = os.stat(txt_path).st_mode & 0o777
        os.chmod(txt_path, 0o400)
        code, txt_content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, code)
        self.assertEqual(15608, len(txt_content))
        os.chmod(txt_path, rights)
        epub_path = os.path.join(TEST_DB, "Peter Parker", "book7 (10)", "book7 - Peter Parker.epub")
        epub_target = os.path.join(TEST_DB, "Peter Parker", "book7 (10)", "backup.xxx")
        rights = os.stat(epub_path).st_mode & 0o777
        os.chmod(epub_path, 0o400)
        code, epub_content = self.download_book(10, "admin", "admin123")
        self.assertEqual(200, code)
        self.assertEqual(20746, len(epub_content))
        epub_data = read_metadata_epub(epub_content)
        self.assertEqual("book7", epub_data['title'])
        self.assertEqual("Peter Parker", epub_data['author'][0])
        self.assertEqual("en", epub_data['language'][0])
        self.assertEqual("Gênot", epub_data['tags'][0])
        os.chmod(epub_path, rights)
        shutil.move(epub_path, epub_target)
        code, epub_content = self.download_book(10, "admin", "admin123")
        self.assertEqual(404, code)
        shutil.move(epub_target, epub_path)

    def test_convert_file_embed_metadata(self):
        tasks = self.check_tasks()
        vals = self.get_convert_book(12)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('PDF')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('EPUB')
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 20:
            time.sleep(2)
            task_len, ret = self.check_tasks(tasks)
            if task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(1, task_len)
        epub_path = os.path.join(TEST_DB, "Lulu de Marco", "book10 (12)", "book10 - Lulu de Marco.epub")
        with zipfile.ZipFile(epub_path) as thezip:
            contentopf = thezip.read("content.opf").decode('utf-8')
        epub_data = read_opf_metadata(contentopf)
        self.assertEqual("book10", epub_data['title'])
        self.assertEqual("Lulu de Marco", epub_data['author'][0])
        self.assertEqual("nb", epub_data['language'][0])
        self.assertEqual("Gênot", epub_data['tags'][0])
        self.delete_book_format(12, "EPUB")

    def test_convert_kepub_embed_metadata(self):
        tasks = self.check_tasks()
        vals = self.get_convert_book(9)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('KEPUB')
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 20:
            time.sleep(2)
            task_len, ret = self.check_tasks(tasks)
            if task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(1, task_len)
        epub_path = os.path.join(TEST_DB, "Sigurd Lindgren", "book6 (9)", "book6 - Sigurd Lindgren.kepub")
        with zipfile.ZipFile(epub_path) as thezip:
            contentopf = thezip.read("content.opf").decode('utf-8')
        epub_data = read_opf_metadata(contentopf)
        self.assertEqual("book6", epub_data['title'])
        self.assertEqual("Sigurd Lindgren", epub_data['author'][0])
        self.assertEqual("en", epub_data['language'][0])
        self.delete_book_format(12, "KEPUB")

    def test_download_kepub_embed_metadata(self):
        self.fill_basic_config({'config_embed_metadata': 0})
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        tasks = self.check_tasks()

        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('KEPUB')
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 20:
            time.sleep(2)
            task_len, ret = self.check_tasks(tasks)
            if task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(1, task_len)
        epub_path = os.path.join(TEST_DB, "Leo Baskerville", "book8 (8)", "book8 - Leo Baskerville.kepub")
        self.assertTrue(os.path.isfile(epub_path))
        code, epub_content = self.download_book(8, "admin", "admin123", format="KEPUB")
        self.assertEqual(200, code)
        epub_data = read_metadata_epub(epub_content)
        self.assertEqual("book8", epub_data['title'])
        self.assertEqual("Unknown", epub_data['author'][0])
        self.assertEqual("en", epub_data['language'][0])
        self.assertEqual([], epub_data['tags'])
        self.fill_basic_config({'config_kepubifypath': "", 'config_embed_metadata': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        code, epub_content = self.download_book(8, "admin", "admin123", format="KEPUB")
        self.assertEqual(200, code)
        epub_data = read_metadata_epub(epub_content)
        self.assertEqual("book8", epub_data['title'])
        self.assertEqual("Unknown", epub_data['author'][0])
        self.assertEqual("en", epub_data['language'][0])
        self.assertEqual([], epub_data['tags'])
        self.fill_basic_config({'config_kepubifypath': kepubify_path(), 'config_embed_metadata': 1})
        code, epub_content = self.download_book(8, "admin", "admin123", format="KEPUB")
        self.assertEqual(200, code)
        # self.assertEqual(5954, len(epub_content))
        epub_data = read_metadata_epub(epub_content)
        self.assertEqual("book8", epub_data['title'])
        self.assertEqual("Leo Baskerville", epub_data['author'][0])
        self.assertEqual("nb", epub_data['language'][0])
        self.assertEqual([], epub_data['tags'])

        self.delete_book_format(8, "KEPUB")

    def test_email_epub_embed_metadata(self):
        self.edit_user('admin', {'email': 'a5@b.com', 'kindle_mail': 'a1@b.com'})
        self.setup_server(False, {'mail_server': '127.0.0.1', 'mail_port': PORTS[1],
                        'mail_use_ssl': 'None', 'mail_login': 'name@host.com', 'mail_password_e': '10234',
                        'mail_from': 'name@host.com'})
        self.fill_basic_config({'config_embed_metadata': 0})
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        tasks = self.check_tasks()
        self.email_server = AIOSMTPServer(
            hostname='127.0.0.1',
            port=int(PORTS[1]),
            only_ssl=False,
            timeout=10
        )
        self.email_server.start()

        details = self.get_book_details(10)
        details['kindlebtn'].click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 10:
            time.sleep(2)
            task_len, ret = self.check_tasks(tasks)
            if task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Finished')
        self.assertTrue(wait_Email_received(self.email_server.handler.check_email_received))
        attachment = self.email_server.handler.get_email_attachment()
        epub_data = read_metadata_epub(attachment)
        self.assertEqual("book7", epub_data['title'])
        self.assertEqual("Unknown", epub_data['author'][0])
        self.assertEqual("en", epub_data['language'][0])
        self.fill_basic_config({'config_embed_metadata': 1})
        self.email_server.handler.reset_email_received()
        details = self.get_book_details(10)
        details['kindlebtn'].click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 10:
            time.sleep(2)
            task_len, ret = self.check_tasks(tasks)
            if task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Finished')
        self.assertTrue(wait_Email_received(self.email_server.handler.check_email_received))
        attachment = self.email_server.handler.get_email_attachment()
        epub_data = read_metadata_epub(attachment)
        self.assertEqual("book7", epub_data['title'])
        self.assertEqual("Peter Parker", epub_data['author'][0])
        self.assertEqual("en", epub_data['language'][0])
        self.assertEqual("Gênot", epub_data['tags'][0])
        self.email_server.stop()