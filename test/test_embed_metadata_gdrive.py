#!/usr/bin/env python
# -*- coding: utf-8 -*-
from unittest import TestCase
import time
import os
import shutil
import zipfile

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from helper_ui import ui_class
from config_test import CALIBRE_WEB_PATH, TEST_DB, base_path, WAIT_GDRIVE
from helper_func import startup, save_logfiles, read_metadata_epub, read_opf_metadata
from helper_func import add_dependency, remove_dependency
from helper_gdrive import prepare_gdrive, connect_gdrive
from helper_email_convert import calibre_path, kepubify_path

RESOURCES = {'ports': 1, "gdrive": True}

PORTS = ['8083']
INDEX = ""

class TestEmbedMetadataGdrive(TestCase, ui_class):
    p = None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH + INDEX, 'cps', 'cache', 'thumbnails')
        shutil.rmtree(thumbnail_cache_path, ignore_errors=True)

        prepare_gdrive()
        try:
            src = os.path.join(base_path, "files", "client_secrets.json")
            dst = os.path.join(CALIBRE_WEB_PATH + INDEX, "client_secrets.json")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            # delete settings_yaml file
            set_yaml = os.path.join(CALIBRE_WEB_PATH + INDEX, "settings.yaml")
            if os.path.exists(set_yaml):
                os.unlink(set_yaml)

            # delete gdrive file
            gdrive_db = os.path.join(CALIBRE_WEB_PATH + INDEX, "gdrive.db")
            if os.path.exists(gdrive_db):
                os.unlink(gdrive_db)

            # delete gdrive authenticated file
            src = os.path.join(base_path, 'files', "gdrive_credentials")
            dst = os.path.join(CALIBRE_WEB_PATH + INDEX, "gdrive_credentials")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB},
                    port=PORTS[0],
                    index=INDEX, only_metadata=True, env={"APP_MODE": "test"})
            cls.fill_db_config({'config_use_google_drive': 1})
            time.sleep(2)
            cls.fill_db_config({'config_google_drive_folder': 'test'})
            time.sleep(2)
            cls.fill_thumbnail_config({'schedule_generate_book_covers': 1})
            cls.restart_calibre_web()
            time.sleep(180)
        except Exception as e:
            try:
                print(e)
                cls.driver.quit()
                cls.p.kill()
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        save_logfiles(cls, cls.__name__)
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH + INDEX, 'cps', 'cache', 'thumbnails')
        shutil.rmtree(thumbnail_cache_path, ignore_errors=True)
        try:
            cls.driver.get("http://127.0.0.1:" + PORTS[0])
            cls.stop_calibre_web()
            # close the browser window and stop calibre-web
            cls.driver.quit()
            cls.p.terminate()
        except Exception as e:
            print(e)

        remove_dependency(cls.dependency)

        src1 = os.path.join(CALIBRE_WEB_PATH + INDEX, "client_secrets.json")
        src = os.path.join(CALIBRE_WEB_PATH + INDEX, "gdrive_credentials")
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
        # self.assertEqual(20746, len(epub_content))
        epub_data = read_metadata_epub(epub_content)
        self.assertEqual("book7", epub_data['title'])
        self.assertEqual("Peter Parker", epub_data['author'][0])
        self.assertEqual("en", epub_data['language'][0])
        self.assertEqual("Gênot", epub_data['tags'][0])
        code, pdf_content = self.download_book(13, "admin", "admin123")
        self.assertEqual(200, code)
        # self.assertEqual(40028, len(pdf_content))

    def test_convert_file_embed_metadata(self):
        tasks = self.check_tasks()
        vals = self.get_convert_book(12)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('PDF')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('EPUB')
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.wait_tasks(tasks, 1)
        #i = 0
        #while i < 20:
        #    time.sleep(2)
        #    task_len, ret = self.check_tasks(tasks)
        #    if task_len == 1:
        #        if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
        #            break
        #    i += 1
        #self.assertEqual(1, task_len)
        fs = connect_gdrive("test")
        epub_path = os.path.join("test", "Lulu de Marco", "book10 (12)", "book10 - Lulu de Marco.epub")
        epub_path.replace('\\', '/')
        with zipfile.ZipFile(fs.open(epub_path, "rb")) as thezip:
            contentopf = thezip.read("content.opf").decode('utf-8')
        fs.close()
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
        self.wait_tasks(tasks, 1)
        #i = 0
        #while i < 20:
        #    time.sleep(2)
        #    task_len, ret = self.check_tasks(tasks)
        #    if task_len == 1:
        #        if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
        #            break
        #    i += 1
        #self.assertEqual(1, task_len)
        fs = connect_gdrive("test")
        epub_path = os.path.join("test", "Sigurd Lindgren", "book6 (9)", "book6 - Sigurd Lindgren.kepub")
        with zipfile.ZipFile(fs.open(epub_path, "rb")) as thezip:
            contentopf = thezip.read("content.opf").decode('utf-8')
        fs.close()
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
        self.wait_tasks(tasks, 1)
        #i = 0
        #while i < 20:
        #    time.sleep(2)
        #    task_len, ret = self.check_tasks(tasks)
        #    if task_len == 1:
        #        if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
        #            break
        #    i += 1
        #self.assertEqual(1, task_len)
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