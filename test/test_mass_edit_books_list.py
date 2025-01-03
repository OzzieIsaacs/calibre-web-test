#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import time
import os
import shutil

from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup, debug_startup
from helper_func import save_logfiles
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import requests
import re

RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


class TestMassEditBooksList(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, port=PORTS[0], index=INDEX,
                    env={"APP_MODE": "test"})
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

    def test_wrong_parameter_single(self):
        r = requests.session()
        login_page = r.get('http://127.0.0.1:{}/login'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:{}/login'.format(PORTS[0]), data=payload)
        table = r.get('http://127.0.0.1:{}/table?data=list&sort_param=stored'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', table.text)
        data = {"name": "lurgi", "value": "test", "pk": ["10"]}
        headers = {"X-CSRFToken": token.group(1)}
        response = r.post('http://127.0.0.1:{}/ajax/editbooks/lurgi'.format(PORTS[0]), json=data, headers=headers, timeout=5)
        self.assertEqual(400, response.status_code)
        self.assertTrue("Parameter" in response.text)
        data = {"value": "test", "pk": ["22"]}
        response = r.post('http://127.0.0.1:{}/ajax/editbooks/series'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json().get('msg', None))
        data = {"value": "fdt", "pk": [10]}
        response = r.post('http://127.0.0.1:{}/ajax/editbooks/languages'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json().get('msg', None))
        data = {"pk": [10]}
        response = r.post('http://127.0.0.1:{}/ajax/editbooks/languages'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json().get('msg', None))
        data = {"value": "fdt"}
        response = r.post('http://127.0.0.1:{}/ajax/editbooks/languages'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json().get('msg', None))
        data = {"value": "fdt", "pk": "hurtz"}
        response = r.post('http://127.0.0.1:{}/ajax/editbooks/title'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json().get('msg', None))
        r.close()

    def test_wrong_parameter_multi(self):
        r = requests.session()
        login_page = r.get('http://127.0.0.1:{}/login'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:{}/login'.format(PORTS[0]), data=payload)
        table = r.get('http://127.0.0.1:{}/table?data=list&sort_param=stored'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', table.text)
        data = {"name": "lurgi", "value": "test", "selections": ["10", 7]}
        headers = {"X-CSRFToken": token.group(1)}
        response = r.post('http://127.0.0.1:{}/ajax/editselectedbooks'.format(PORTS[0]), json=data, headers=headers, timeout=5)
        self.assertEqual(400, response.status_code)
        self.assertTrue("Parameter" in response.text)
        data = {"series": "test", "selections": ["22", 10]}
        response = r.post('http://127.0.0.1:{}/ajax/editselectedbooks'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json()[0].get('msg', None))
        data = {"languages": "fdt", "selections": [10, 11]}
        response = r.post('http://127.0.0.1:{}/ajax/editselectedbooks'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json()[0].get('msg', None))
        data = {"selections": [10, 11]}
        response = r.post('http://127.0.0.1:{}/ajax/editselectedbooks'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(400, response.status_code)
        self.assertTrue("Parameter" in response.text)
        data = {"title": "fdt", "selections": [10, "hurtz"]}
        response = r.post('http://127.0.0.1:{}/ajax/editselectedbooks'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json()[0].get('msg', None))
        r.close()

    def test_author_title_combi(self):
        bl = self.get_books_list(1)
        # select book 1 and 2
        bl['table'][0]['selector']['element'].click()
        bl['table'][1]['selector']['element'].click()
        # open mass edit dialog
        self.check_element_on_page((By.ID, "edit_selected_books")).click()
        time.sleep(1)
        # check title_sort and author_sort are greyed out
        self.assertFalse(self.check_element_on_page((By.ID, "title_sort_input")).is_enabled())
        self.assertFalse(self.check_element_on_page((By.ID, "author_sort_input")).is_enabled())
        # close dialog
        self.check_element_on_page((By.ID, "edit_selected_abort")).click()
        time.sleep(1)
        # untick title_sort and author_sort are greyed out
        self.check_element_on_page((By.ID, "autoupdate_titlesort")).click()
        self.check_element_on_page((By.ID, "autoupdate_authorsort")).click()
        # open mass edit dialog
        self.check_element_on_page((By.ID, "edit_selected_books")).click()
        time.sleep(1)
        # check title_sort and author_sort are editable
        self.assertTrue(self.check_element_on_page((By.ID, "title_sort_input")).is_enabled())
        self.assertTrue(self.check_element_on_page((By.ID, "author_sort_input")).is_enabled())
        # edit author, author_sort, title, title_sort
        self.check_element_on_page((By.ID, "title_input")).send_keys("Test")
        self.check_element_on_page((By.ID, "title_sort_input")).send_keys("Sort Test")
        self.check_element_on_page((By.ID, "authors_input")).send_keys("Kurt Saart & Schurt Kölv")
        self.check_element_on_page((By.ID, "author_sort_input")).send_keys("Aäthor sorto")
        # submit
        self.check_element_on_page((By.ID, "edit_selected_confirm")).click()
        time.sleep(1)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # check table content
        bl = self.get_books_list()
        self.assertFalse(bl['table'][0]['selector']['element'].is_selected())
        self.assertFalse(bl['table'][1]['selector']['element'].is_selected())
        self.assertEqual(bl['table'][0]['Title']['text'], "Test")
        self.assertEqual(bl['table'][1]['Title']['text'], "Test")
        self.assertEqual(bl['table'][0]['Title Sort']['text'], "Sort Test")
        self.assertEqual(bl['table'][1]['Title Sort']['text'], "Sort Test")
        self.assertEqual(bl['table'][0]['Authors']['text'], "Kurt Saart & Schurt Kölv")
        self.assertEqual(bl['table'][1]['Authors']['text'], "Kurt Saart & Schurt Kölv")
        self.assertEqual(bl['table'][0]['Author Sort']['text'], "Aäthor sorto")
        self.assertEqual(bl['table'][1]['Author Sort']['text'], "Aäthor sorto")
        self.assertTrue(self.check_element_on_page((By.ID, "autoupdate_titlesort")).is_enabled())
        self.assertTrue(self.check_element_on_page((By.ID, "autoupdate_authorsort")).is_enabled())
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Kurt Saart/Test (12)',
                                                    'Test - Kurt Saart.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Kurt Saart/Test (13)',
                                                    'Test - Kurt Saart.pdf')))

        # revert changes
        self.edit_table_element(bl['table'][0]['Title']['element'], "book11")
        bl = self.get_books_list()
        self.edit_table_element(bl['table'][1]['Title']['element'], "book10")
        bl = self.get_books_list()
        self.edit_table_element(bl['table'][0]['Authors']['element'], "Norbert Halagal")
        bl = self.get_books_list()
        self.edit_table_element(bl['table'][1]['Authors']['element'], "Lulu de Marco")
        bl = self.get_books_list()
        self.assertEqual(bl['table'][0]['Title']['text'], "book11")
        self.assertEqual(bl['table'][1]['Title']['text'], "book10")
        self.assertEqual(bl['table'][0]['Title Sort']['text'], "book11")
        self.assertEqual(bl['table'][1]['Title Sort']['text'], "book10")
        self.assertEqual(bl['table'][0]['Authors']['text'], "Norbert Halagal")
        self.assertEqual(bl['table'][1]['Authors']['text'], "Lulu de Marco")
        self.assertEqual(bl['table'][0]['Author Sort']['text'], "Halagal, Norbert")
        self.assertEqual(bl['table'][1]['Author Sort']['text'], "Marco, Lulu de")
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Norbert Halagal/book11 (13)',
                                                    'book11 - Norbert Halagal.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Lulu de Marco/book10 (12)',
                                                    'book10 - Lulu de Marco.pdf')))

    # Title, autor not exist multi edit
    def test_invalid_author_title(self):
        # goto book table
        bl = self.get_books_list(1)
        # select book 3 and 4, 5
        bl['table'][2]['selector']['element'].click()
        bl['table'][3]['selector']['element'].click()
        bl['table'][4]['selector']['element'].click()
        # move author-book 3
        author_book = os.path.join(TEST_DB, 'Peter Parker', 'book7 (10)', 'book7 - Peter Parker.epub')
        new_author_book = os.path.join(TEST_DB, 'Peter Parker', 'book7 (10)', 'book7 - Nos Parker.epub')
        shutil.move(author_book, new_author_book)
        # open mass edit dialog
        self.check_element_on_page((By.ID, "edit_selected_books")).click()
        time.sleep(1)
        # edit author
        self.check_element_on_page((By.ID, "authors_input")).send_keys("Kurt Jilo")
        # submit
        self.check_element_on_page((By.ID, "edit_selected_confirm")).click()
        time.sleep(1)
        # check response
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        bl = self.get_books_list()
        self.assertEqual(bl['table'][2]['Authors']['text'], "Kurt Jilo")
        self.assertEqual(bl['table'][3]['Authors']['text'], "Kurt Jilo")
        self.assertEqual(bl['table'][4]['Authors']['text'], "Kurt Jilo")
        self.assertEqual(bl['table'][2]['Author Sort']['text'], "Jilo, Kurt")
        self.assertEqual(bl['table'][3]['Author Sort']['text'], "Jilo, Kurt")
        self.assertEqual(bl['table'][4]['Author Sort']['text'], "Jilo, Kurt")

        # move title-book 4

        # open mass edit dialog
        bl['table'][2]['selector']['element'].click()
        bl['table'][3]['selector']['element'].click()
        bl['table'][4]['selector']['element'].click()
        self.check_element_on_page((By.ID, "edit_selected_books")).click()
        time.sleep(1)
        # edit title
        self.check_element_on_page((By.ID, "title_input")).send_keys("Test")
        # submit
        self.check_element_on_page((By.ID, "edit_selected_confirm")).click()
        time.sleep(1)
        # check response
        # revert changes
        self.assertEqual(bl['table'][2]['Title']['text'], "book11")
        self.assertEqual(bl['table'][3]['Title']['text'], "book10")
        self.assertEqual(bl['table'][4]['Title']['text'], "book10")

        self.assertEqual(bl['table'][0]['Title Sort']['text'], "book11")
        self.assertEqual(bl['table'][1]['Title Sort']['text'], "book10")
        self.assertEqual(bl['table'][0]['Authors']['text'], "Norbert Halagal")
        self.assertEqual(bl['table'][1]['Authors']['text'], "Lulu de Marco")
        self.assertEqual(bl['table'][0]['Author Sort']['text'], "Halagal, Norbert")
        self.assertEqual(bl['table'][1]['Author Sort']['text'], "Marco, Lulu de")
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Norbert Halagal/book11 (13)',
                                                    'book11 - Norbert Halagal.pdf')))
        self.assertTrue(os.path.isfile(os.path.join(TEST_DB, 'Lulu de Marco/book10 (12)',
                                                    'book10 - Lulu de Marco.pdf')))

    # Title, autor write write protect  multi edit
    def test_protected_author_title(self):
        # goto book table
        # select book 3 and 4, 5
        # write protect author-book 3
        txt_path = os.path.join(TEST_DB, "Frodo Beutlin", "Der Buchtitel (1)", "Der Buchtitel - Frodo Beutlin.txt")
        rights = os.stat(txt_path).st_mode & 0o777
        os.chmod(txt_path, 0o400)
        # write protect title-book 4
        # open mass edit dialog
        # edit author
        # submit
        # check response
        # open mass edit dialog
        # edit title
        # submit
        # check response
        # revert changes
        pass
        #Title, autor write protect single edit
