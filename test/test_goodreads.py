# -*- coding: utf-8 -*-

import unittest
from helper_ui import ui_class
from testconfig import TEST_DB, VENV_PYTHON, CALIBRE_WEB_PATH, base_path
from helper_func import startup, debug_startup, get_Host_IP, add_dependency, remove_dependency, kill_old_cps
from selenium.webdriver.common.by import By
from config_goodreads import GOODREADS_API_KEY, GOODREADS_API_SECRET


class test_goodreads(unittest.TestCase, ui_class):

    p=None
    driver = None
    dependency = ["goodreads", "python-Levenshteinf"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,
                                          'config_use_goodreads':1})
        except Exception as e:
            cls.driver.quit()
            cls.p.terminate()
            cls.p.poll()

    @classmethod
    def tearDownClass(cls):
        cls.stop_calibre_web()
        cls.driver.quit()
        cls.p.terminate()
        # close the browser window and stop calibre-web
        remove_dependency(cls.dependency)


    def test_author_page_invalid(self):
        self.fill_basic_config({'config_goodreads_api_key': 'rgg',
                                'config_goodreads_api_secret': 'rgfg'
                                })
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor': u'Ken Follett'})
        list_element = self.goto_page('nav_author')
        self.assertIsNotNone(list_element)
        for el in list_element:
            if el.text == u'Ken Follett':
                el.click()
                break
        self.assertFalse(self.check_element_on_page((By.CLASS_NAME, "author-photo")))
        self.assertFalse(self.check_element_on_page((By.XPATH,"//*/h3[contains(text(), 'More by')]")))
        self.assertEqual(1,len(self.get_books_displayed()[1]))
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor': u'John Döe'})


    def test_author_page(self):
        self.fill_basic_config({'config_goodreads_api_key': GOODREADS_API_KEY,
                                'config_goodreads_api_secret': GOODREADS_API_SECRET
                                })
        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor': u'Andreas Eschbach'})
        list_element = self.goto_page('nav_author')
        self.assertIsNotNone(list_element)
        for el in list_element:
            if el.text == u'Andreas Eschbach':
                el.click()
                break
        self.assertTrue(self.check_element_on_page((By.CLASS_NAME, "author-photo")))
        self.assertTrue(self.check_element_on_page((By.XPATH,"//*/h3[contains(text(), 'More by')]")))
        self.assertEqual(1,len(self.get_books_displayed()[1]))
        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor': u'John Döe'})
        list_element = self.goto_page('nav_author')
        self.assertIsNotNone(list_element)
        for el in list_element:
            if el.text == u'Sigurd Lindgren':
                el.click()
                break
        self.assertFalse(self.check_element_on_page((By.CLASS_NAME, "author-photo")))
        self.assertFalse(self.check_element_on_page((By.XPATH,"//*/h3[contains(text(), 'More by')]")))
        self.assertEqual(1,len(self.get_books_displayed()[1]))





    def test_kobo_about(self):
        self.assertTrue(self.goto_page('nav_about'))