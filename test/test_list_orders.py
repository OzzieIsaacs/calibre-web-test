# -*- coding: utf-8 -*-

import unittest
import time
from selenium.webdriver.common.by import By

from helper_func import save_logfiles
from helper_ui import ui_class
from config_test import TEST_DB
# from parameterized import parameterized_class
from helper_func import startup, debug_startup

# other tests regardign order of elements is in test_visibilities
class TestCalibreWebListOrders(unittest.TestCase, ui_class):

    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB})
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_series_sort(self):
        self.goto_page('nav_serie')
        list = self.check_element_on_page((By.ID, "list-button"))
        self.assertTrue(list)
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")
        self.check_element_on_page((By.ID, "asc")).click()
        time.sleep(1)
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")
        self.check_element_on_page((By.ID, "desc")).click()
        time.sleep(1)
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Loko")
        self.assertEqual(list_element[1]['title'], "Djüngel")
        self.driver.refresh()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Loko")
        self.assertEqual(list_element[1]['title'], "Djüngel")
        self.check_element_on_page((By.ID, "list-button")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[1]['title'], "Loko")
        self.assertEqual(list_element[2]['title'], "Djüngel")
        grid = self.check_element_on_page((By.ID, "grid-button"))
        self.assertTrue(grid)
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[1]['title'], "Loko")
        self.assertEqual(list_element[2]['title'], "Djüngel")
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")
        self.driver.refresh()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")
        self.check_element_on_page((By.ID, "desc")).click()
        self.check_element_on_page((By.ID, "grid-button")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Loko")
        self.assertEqual(list_element[1]['title'], "Djüngel")
        self.check_element_on_page((By.ID, "desc")).click()
        time.sleep(1)
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Loko")
        self.assertEqual(list_element[1]['title'], "Djüngel")
        self.check_element_on_page((By.ID, "asc")).click()
        time.sleep(1)
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Djüngel")
        self.assertEqual(list_element[1]['title'], "Loko")

    def test_author_sort(self):
        self.goto_page('nav_author')
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Leo Baskerville")
        self.assertEqual(list_element[10]['title'], "Liu Yang")
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Leo Baskerville")
        self.assertEqual(list_element[10]['title'], "Liu Yang")
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Liu Yang")
        self.assertEqual(list_element[10]['title'], "Leo Baskerville")
        self.driver.refresh()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Liu Yang")
        self.assertEqual(list_element[10]['title'], "Leo Baskerville")
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Liu Yang")
        self.assertEqual(list_element[10]['title'], "Leo Baskerville")
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Leo Baskerville")
        self.assertEqual(list_element[10]['title'], "Liu Yang")
        self.check_element_on_page((By.ID, "sort_name")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Baskerville, Leo")
        self.assertEqual(list_element[10]['title'], "Yang, Liu")
        self.driver.refresh()   # sort_name is not saved
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Leo Baskerville")
        self.assertEqual(list_element[10]['title'], "Liu Yang")
        self.check_element_on_page((By.XPATH, "//div[contains(text(), 'L')]")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Sigurd Lindgren")
        self.assertEqual(list_element[1]['title'], "Asterix Lionherd")
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Asterix Lionherd")
        self.assertEqual(list_element[1]['title'], "Sigurd Lindgren")
        self.assertEqual(len(list_element),2)
        self.check_element_on_page((By.XPATH, "//div[contains(text(), 'D')]")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "John Döe")
        self.assertEqual(len(list_element), 1)
        self.check_element_on_page((By.ID, "all")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Liu Yang")
        self.assertEqual(list_element[10]['title'], "Leo Baskerville")
        self.assertEqual(len(list_element), 11)

    def test_publisher_sort(self):
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher': 'Alfafa'})
        self.goto_page('nav_publisher')
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Alfafa")
        self.assertEqual(list_element[1]['title'], "None")
        self.assertEqual(list_element[2]['title'], "Randomhäus")
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Alfafa")
        self.assertEqual(list_element[2]['title'], "Randomhäus")
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Randomhäus")
        self.assertEqual(list_element[1]['title'], "None")
        self.assertEqual(list_element[2]['title'], "Alfafa")
        self.check_element_on_page((By.ID, "asc")).click()
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher': ''})

    def test_format_sort(self):
        self.goto_page('nav_format')
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "CBR")
        self.assertEqual(list_element[4]['title'], "TXT")
        self.assertEqual(len(list_element), 5)
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "CBR")
        self.assertEqual(list_element[4]['title'], "TXT")
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "TXT")
        self.assertEqual(list_element[4]['title'], "CBR")
        self.check_element_on_page((By.ID, "asc")).click()

    def test_lang_sort(self):
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages': 'German'})
        self.goto_page('nav_lang')
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "English")
        self.assertEqual(list_element[1]['title'], "German")
        self.assertEqual(list_element[0]['count'], "3")
        self.assertEqual(list_element[1]['count'], "1")
        self.assertEqual(len(list_element), 4)
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "English")
        self.assertEqual(list_element[1]['title'], "German")
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Norwegian Bokmål")
        self.assertEqual(list_element[2]['title'], "German")
        self.goto_page('nav_lang')
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Norwegian Bokmål")
        self.assertEqual(list_element[1]['title'], "None")
        self.assertEqual(list_element[2]['title'], "German")
        self.assertEqual(list_element[0]['count'], "3")
        self.assertEqual(list_element[2]['count'], "1")
        self.assertEqual(list_element[1]['count'], "4")
        self.check_element_on_page((By.ID, "asc")).click()
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages': ''})

    def test_tags_sort(self):
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags': 'Älfafa'})
        self.goto_page('nav_cat')
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Gênot")
        self.assertEqual(list_element[1]['title'], "None")
        self.assertEqual(list_element[2]['title'], "Älfafa")
        self.assertEqual(len(list_element), 3)
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Gênot")
        self.assertEqual(list_element[1]['title'], "None")
        self.assertEqual(list_element[2]['title'], "Älfafa")
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "Älfafa")
        self.assertEqual(list_element[1]['title'], "None")
        self.assertEqual(list_element[2]['title'], "Gênot")
        self.check_element_on_page((By.ID, "asc")).click()
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags': ''})

    def test_ratings_sort(self):
        self.goto_page('nav_rate')
        list_element = self.get_list_books_displayed(True)
        self.assertEqual(list_element[1]['title'], "2")
        self.assertEqual(list_element[2]['title'], "5")
        self.assertEqual(len(list_element), 3)
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed(True)
        self.assertEqual(list_element[1]['title'], "2")
        self.assertEqual(list_element[2]['title'], "5")
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed(True)
        self.assertEqual(list_element[0]['title'], "5")
        self.assertEqual(list_element[1]['title'], "2")
        self.check_element_on_page((By.ID, "asc")).click()

    def test_download_sort(self):
        self.goto_page('nav_download')
        list_element = self.get_list_books_displayed()
        self.assertEqual(len(list_element), 0)
        # download 2 books and check if they are counted as downloads from admin
        self.download_book(9,"admin", "admin123")
        self.download_book(11, "admin", "admin123")
        self.goto_page('nav_download')
        list_element = self.get_list_books_displayed()
        self.assertEqual(len(list_element), 1)
        self.assertEqual(list_element[0]['count'], "2")
        #  redownload one book and check if it's not counted twice
        self.download_book(11, "admin", "admin123")
        self.goto_page('nav_download')
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['count'], "2")
        # create new ueser and download a book as this user
        self.create_user('down', {'email': 'd@a.com', 'password': '1234', 'download_role': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.download_book(11, "down", "1234")
        # check content of downloaded book section (2 users listed, admin still has 2 books downloaded)
        self.goto_page('nav_download')
        list_element = self.get_list_books_displayed()
        self.assertEqual(len(list_element), 2)
        self.assertEqual(list_element[0]['count'], "2")
        self.assertEqual(list_element[0]['title'], "admin")
        self.assertEqual(list_element[1]['title'], "down")
        # start asc (which is default), check nothing has changed
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "admin")
        self.assertEqual(list_element[1]['title'], "down")
        # start descending, check user down is the first one in list
        self.check_element_on_page((By.ID, "desc")).click()
        list_element = self.get_list_books_displayed()
        self.assertEqual(list_element[0]['title'], "down")
        self.assertEqual(list_element[1]['title'], "admin")
        self.assertEqual(list_element[1]['count'], "2")
        # put back default order
        self.check_element_on_page((By.ID, "asc")).click()
        # login as user down and check he sees only his downloads
        self.logout()
        self.login("down","1234")
        self.goto_page('nav_download')
        elements = self.get_books_displayed()
        self.assertEqual(1, len(elements[1]))
        #delete user and finish test
        self.logout()
        self.login("admin","admin123")
        self.edit_user('down', {'delete': 1})
        # enable anonymous browser
        self.fill_basic_config({'config_anonbrowse': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('Guest', {'download_role': 1})
        # check guest user is not listed, and check user "down" disappeared
        self.goto_page('nav_download')
        list_element = self.get_list_books_displayed()
        self.assertEqual(len(list_element), 1)
        # download book as Guest
        code, _ = self.download_book(11, "guest", "")
        self.assertEqual(200, code)
        # check guest user is not listed
        self.goto_page('nav_download')
        list_element = self.get_list_books_displayed()
        self.assertEqual(len(list_element), 1)
        # diable anonymous browser
        self.fill_basic_config({'config_anonbrowse': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_order_series_all_links(self):
        self.goto_page('nav_serie')
        list = self.check_element_on_page((By.ID, "list-button"))
        self.assertTrue(list)
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        list_element[0]['ele'].click()
        self.check_element_on_page((By.ID, "series_desc")).click()
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "Buuko")
        self.assertEqual(books[1][1]['title'], "comicdemo")
        self.assertEqual(books[1][0]['series'], "Djüngel")
        self.assertFalse("series_ele" in books[1][0])
        # discover
        self.goto_page('nav_rand')
        books = self.get_books_displayed()
        for book in books[1]:
            if book.get('series', "") == "Djüngel":
                book['series_ele'].click()
                break
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "Buuko")
        self.assertEqual(books[1][1]['title'], "comicdemo")
        # search
        books = self.search("Djüngel")
        books[0]['series_ele'].click()
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "Buuko")
        self.assertEqual(books[1][1]['title'], "comicdemo")
        # details_random
        stop = 0
        for i in range(0,8):
            self.goto_page('nav_new')
            books = self.get_books_displayed()
            for book in books[0]:
                if book.get('series', "") == "Djüngel":
                    book['series_ele'].click()
                    stop = 1
                    break
            if stop == 1:
                break
        self.assertEqual(stop, 1)
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "Buuko")
        self.assertEqual(books[1][1]['title'], "comicdemo")
        # shelf
        self.create_shelf("Series")
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'Series')]")).click()
        self.list_shelfs('Series')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        shelf_books[0]['series_ele'].click()
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "Buuko")
        self.assertEqual(books[1][1]['title'], "comicdemo")
        self.delete_shelf("Series")
        # author
        self.goto_page('nav_author')
        list_element = self.get_list_books_displayed()
        list_element[2]['ele'].click()
        author_books = self.get_books_displayed()
        author_books[1][0]['series_ele'].click()
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "Buuko")
        self.assertEqual(books[1][1]['title'], "comicdemo")
        self.check_element_on_page((By.ID, "new")).click()

    def test_order_authors_all_links(self):
        self.goto_page('nav_author')
        self.check_element_on_page((By.ID, "asc")).click()
        list_element = self.get_list_books_displayed()
        list_element[2]['ele'].click()
        self.check_element_on_page((By.ID, "desc")).click()
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "testbook")
        self.assertEqual(books[1][1]['title'], "Buuko")
        books[1][0]['author_ele'][0].click()
        # check if entered from same page authorlink
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "testbook")
        self.assertEqual(books[1][1]['title'], "Buuko")
        # discover
        self.goto_page('nav_rand')
        books = self.get_books_displayed()
        for book in books[1]:
            if book.get('author', "") == ["John Döe"]:
                book['author_ele'][0].click()
                break
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "testbook")
        self.assertEqual(books[1][1]['title'], "Buuko")
        # search
        books = self.search("Döe")
        books[0]['author_ele'][0].click()
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "testbook")
        self.assertEqual(books[1][1]['title'], "Buuko")
        # details_random
        stop = 0
        for i in range(0, 8):
            self.goto_page('nav_new')
            books = self.get_books_displayed()
            for book in books[0]:
                if book.get('author', "") == ["John Döe"]:
                    book['author_ele'][0].click()
                    stop = 1
                    break
            if stop == 1:
                break
        self.assertEqual(stop, 1)
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "testbook")
        self.assertEqual(books[1][1]['title'], "Buuko")
        # shelf
        self.create_shelf("Authors")
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'Authors')]")).click()
        self.list_shelfs('Authors')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        shelf_books[0]['author_ele'][0].click()
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['title'], "testbook")
        self.assertEqual(books[1][1]['title'], "Buuko")
        self.check_element_on_page((By.ID, "new")).click()
        self.delete_shelf("Authors")
