# -*- coding: utf-8 -*-

from base_test import ParallelTestCase
import time
from helper_func import startup
from selenium.webdriver.common.by import By


class TestDeleteDatabase(ParallelTestCase):



    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version,
                    {'config_calibre_dir': cls.temp_dir},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir
                    )
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    def test_delete_books_in_database(self):
        self.delete_book(1)
        self.delete_book(3)
        self.delete_book(4)
        self.delete_book(5)
        self.delete_book(7)
        self.delete_book(8)
        bl = self.get_books_list(1)
        bl['table'][4]['Delete']['element'].click()
        time.sleep(1)
        self.check_element_on_page((By.ID, "delete_confirm")).click()
        time.sleep(1)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "merge_books")))
        bl = self.get_books_list(-1)
        self.assertEqual(4, len(bl['table']))
        self.delete_book(10)
        self.delete_book(11)
        self.delete_book(12)
        # Check if users table is working
        self.goto_page('admin_setup')
        self.check_element_on_page((By.ID, "admin_user_table")).click()
        self.assertEqual(1, len(self.get_user_table(-1)['table']))

        self.delete_book(13)
        books = self.get_books_displayed()
        self.assertEqual(0, len(books[0]))
        self.assertEqual(0, len(books[1]))
        self.assertEqual(len(self.adv_search({'title': 'book10'})), 0)
        self.assertEqual(len(self.search('book10')), 0)
        list_element = self.goto_page("nav_serie")
        self.assertEqual(0, len(list_element))
        list_element = self.goto_page("nav_author")
        self.assertEqual(0, len(list_element))
        list_element = self.goto_page("nav_lang")
        self.assertEqual(0, len(list_element))
        list_element = self.goto_page("nav_publisher")
        self.assertEqual(0, len(list_element))
        list_element = self.goto_page("nav_cat")
        self.assertEqual(0, len(list_element))
        bl = self.get_books_list(1)
        self.assertEqual(1, len(bl['table']))
        self.assertEqual("No matching records found", bl['table'][0]['selector']['text'])
