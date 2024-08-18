
from unittest import TestCase
import time
import os

from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By

from helper_ui import ui_class
from helper_email_convert import AIOSMTPServer
from config_test import TEST_DB, SPLIT_LIB, BOOT_TIME, base_path, CALIBRE_WEB_PATH
from helper_func import startup, count_files, read_metadata_epub
from helper_func import save_logfiles


RESOURCES = {'ports': 2}

PORTS = ['8083', '1025']
INDEX = ""


class TestSplitLibrary(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls,
                    cls.py_version,
                    {'config_calibre_dir': TEST_DB},
                    port=PORTS[0],
                    index=INDEX,
                    env={"APP_MODE": "test"},
                    split=True,
                    lib_path=SPLIT_LIB
                    )
            time.sleep(3)
            cls.fill_db_config({'config_calibre_split': 1, 'config_calibre_split_dir': SPLIT_LIB})
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

    # check thumbnail generation working
    def test_thumbnails(self):
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.restart_calibre_web()
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH + INDEX, 'cps', 'cache', 'thumbnails')
        book_thumbnail_reference = count_files(thumbnail_cache_path)
        self.assertTrue(book_thumbnail_reference > 10)

    # check ebook can be converted
    def test_convert_ebook(self):
        tasks = self.check_tasks()
        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('EPUB')
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        time.sleep(1)
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
        details = self.get_book_details(7)
        self.assertTrue(len(details['reader']), 2)
        self.assertListEqual(details['reader'], ['pdf','epub'])

    # check ebook can be emailed
    def test_email_ebook(self):
        self.edit_user('admin', {'email': 'a5@b.com', 'kindle_mail': 'a1@b.com'})
        self.setup_server(False, {'mail_server': '127.0.0.1', 'mail_port': PORTS[1],
                        'mail_use_ssl': 'None', 'mail_login': 'name@host.com', 'mail_password_e': '10234',
                        'mail_from': 'name@host.com'})
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
        tasks = self.check_tasks()
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
        self.assertGreaterEqual(self.email_server.handler.message_size, 5995)
        # ToDo: embed metadata
        self.email_server.stop()

    # check kobo sync working
    def test_kobo(self):
        pass

    # check book can be renamed and is still found
    def test_change_ebook(self):
        self.fill_basic_config({"config_unicode_filename": 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        details = self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'title': u'O0ü 执'})
        values = self.get_book_details()
        self.assertEqual(u'O0ü 执', values['title'])
        self.assertTrue(os.path.isdir(os.path.join(SPLIT_LIB, values['author'][0], 'O0u Zhi (4)')))
        self.assertFalse(os.path.isdir(os.path.join(SPLIT_LIB, values['author'][0],
                                                    'Very long extra super turbo cool tit (4)')))
        # ToDo: embed metadata
        self.edit_book(4, content={'title': details['title']})

    def test_upload_ebook(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('admin', {'upload_role': 1})
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.epub')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('book9', details['title'])
        self.assertEqual('Noname 23', details['author'][0])
        self.assertTrue(os.path.isdir(os.path.join(SPLIT_LIB, details['author'][0],
                                                   details['title'] + " ({})".format(details['id']))))
        self.fill_basic_config({'config_uploading': 0})
        self.delete_book(details['id'])
        time.sleep(2)
        self.assertFalse(os.path.isdir(os.path.join(SPLIT_LIB, details['author'][0],
                                                   details['title'] + " ({})".format(details['id']))))

    def test_download_book(self):
        self.fill_basic_config({'config_embed_metadata': 0})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        code, epub_content = self.download_book(8, "admin", "admin123", format="EPUB")
        self.assertEqual(200, code)
        self.assertEqual(8250, len(epub_content))
        epub_metadata = read_metadata_epub(epub_content)
        self.assertEqual("Unknown", epub_metadata['author'][0])
        self.fill_basic_config({'config_embed_metadata': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        code, epub_content = self.download_book(8, "admin", "admin123", format="EPUB")
        self.assertEqual(200, code)
        epub_metadata = read_metadata_epub(epub_content)
        self.assertEqual("Leo Baskerville", epub_metadata['author'][0])
        self.fill_basic_config({'config_embed_metadata': 0})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
