from base_test import ParallelTestCase
import unittest
import os
import time

from selenium.webdriver.common.by import By
from helper_func import startup, wait_for_reboot


@unittest.skipIf(os.name == 'nt', 'writeonly database on windows is not checked')
class TestReadOnlyDatabase(ParallelTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': cls.temp_dir},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir)
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @unittest.skipIf(os.name == 'nt', 'readonly database on windows is not checked')
    def test_readonly_path(self):
        self.fill_basic_config({"config_unicode_filename": 1})
        wait_for_reboot(f"http://127.0.0.1:{self.worker_port}")
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
                                "authors": 'John Döe',
                                'title': 'Buuko'})
        rights = os.stat(self.temp_dir).st_mode & 0o777
        os.chmod(self.temp_dir, 0o400)
        self.get_book_details(9)
        element = self.check_element_on_page((By.XPATH, '//*[@title="Return to Database config"]'))
        self.assertTrue(element)
        element.click()
        self.assertTrue(self.check_element_on_page((By.ID, 'config_calibre_dir')))
        '''self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'tags': 'Geno'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(9)
        self.assertEqual('Gênot', details['tag'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'title': 'Buuk'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(9)
        self.assertEqual('Buuko', details['title'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'authors': 'Jon Döe'})
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
        self.goto_page('nav_new')'''
        os.chmod(self.temp_dir, rights)
        self.fill_db_config(dict(config_calibre_dir=self.temp_dir))
        # wait for cw to reboot
        time.sleep(2)
        self.fill_basic_config({'config_uploading': 0, "config_unicode_filename": 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        book_path = os.path.join(self.temp_dir, 'John Doe', 'Buuko (9)')
        self.assertTrue(os.path.isdir(book_path))
        self.goto_page('nav_new')


