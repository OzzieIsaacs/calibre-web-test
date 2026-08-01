# -*- coding: utf-8 -*-

from base_test import ParallelTestCase
import time
import os
import shutil
import zipfile

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from config_test import base_path
from helper_func import startup, read_metadata_epub, read_opf_metadata
from helper_func import add_dependency, remove_dependency
from helper_gdrive import prepare_gdrive, connect_gdrive
from helper_email_convert import calibre_path, kepubify_path


class TestEmbedMetadataGdrive(ParallelTestCase):
    resource_lock = "gdrive"


    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        thumbnail_cache_path = os.path.join(cls.app_dir, 'cps', 'cache', 'thumbnails')
        shutil.rmtree(thumbnail_cache_path, ignore_errors=True)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir': cls.temp_dir},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir)
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
        thumbnail_cache_path = os.path.join(cls.app_dir, 'cps', 'cache', 'thumbnails')
        shutil.rmtree(thumbnail_cache_path, ignore_errors=True)
        super().tearDownClass()

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