#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import time
import requests
import re
import lxml
from StringIO import StringIO

import helper_email_convert
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from helper_ui import ui_class
from config_test import CALIBRE_WEB_PATH, TEST_DB
from helper_func import startup
from helper_func import save_logfiles
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


@unittest.skipIf(helper_email_convert.is_kepubify_not_present(), "Skipping convert, kepubify not found")
class TestEbookConvertKepubify(unittest.TestCase, ui_class):
    p = None
    driver = None
    email_server = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,
                                          'config_binariesdir':'',
                                          'config_kepubifypath':helper_email_convert.kepubify_path()}, 
                    port=PORTS[0], index=INDEX, env={"APP_MODE": "test"})

            cls.edit_user('admin', {'email': 'a5@b.com', 'kindle_mail': 'a1@b.com'})
            time.sleep(2)
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        except Exception as e:
            print("Dead on Init - check Calibre-Web is starting")
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        try:
            # close the browser window and stop calibre-web
            cls.driver.get("http://127.0.0.1:" + PORTS[0])
            cls.stop_calibre_web()
            cls.driver.quit()
            cls.p.terminate()
        except Exception as e:
            print(e)
        time.sleep(2)
        save_logfiles(cls, cls.__name__)

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin', 'admin123')

    # deactivate converter and check convert are not visible anymore
    def test_convert_deactivate(self):
        self.fill_basic_config({'config_kepubifypath': ""})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='Kepubify']/following::td[1]"))
        self.assertEqual(element.text, 'not installed')
        details = self.get_book_details(1)
        self.assertFalse(details['kindlebtn'])
        vals = self.get_convert_book(1)
        self.assertFalse(vals['btn_from'])
        self.assertFalse(vals['btn_to'])
        self.fill_basic_config({'config_kepubifypath':helper_email_convert.kepubify_path()})

    # Set excecutable to wrong exe and start convert
    # set excecutable not existing and start convert
    # set excecutable non excecutable and start convert
    def test_convert_wrong_excecutable(self):
        self.fill_basic_config({'config_kepubifypath':'/opt/kepubify/ebook-polish'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='Kepubify']/following::td[1]"))
        self.assertEqual(element.text, 'not installed')
        details = self.get_book_details(1)
        self.assertFalse(details['kindlebtn'])
        details = self.get_book_details(5)
        self.assertEqual(len(details['kindle']), 1)
        vals = self.get_convert_book(5)
        # ToDo: change behavior convert should only be visible if ebookconverter has valid entry
        self.assertTrue(vals['btn_from'])
        self.assertTrue(vals['btn_to'])

        nonexec = os.path.join(CALIBRE_WEB_PATH + INDEX, 'app.db')
        self.fill_basic_config({'config_kepubifypath': nonexec})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='Kepubify']/following::td[1]"))
        self.assertEqual(element.text, 'Execution permissions missing')
        self.fill_basic_config({'config_kepubifypath': helper_email_convert.kepubify_path()})

    # convert epub to kepub
    # try start conversion of mobi -> not visible
    # start conversion of epub -> kepub
    # create user
    # logout
    # check conversion result for non admin user -> nothing visible
    # start conversion for non admin user
    # check conversion result for non admin user -> own conversion visible without username
    # logout
    # login as admin
    # check conversion result conversion of other user visible
    def test_convert_only(self):
        tasks = self.check_tasks()
        vals = self.get_convert_book(7)
        self.assertFalse(vals['btn_from'])
        self.assertFalse(vals['btn_to'])

        vals = self.get_convert_book(10)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        self.assertEqual(len(select.options), 2)
        select = Select(vals['btn_to'])
        self.assertEqual(len(select.options), 2)
        select.select_by_visible_text('KEPUB')
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)
        self.create_user('solo', {'password': '123AbC*!', 'email': 'a@b.com', 'edit_role':1})
        time.sleep(2)
        task_len, ret = self.wait_tasks(tasks, 1)
        self.assertEqual(ret[-1]['result'], 'Finished')
        memory = len(ret)

        self.logout()
        self.login('solo', '123AbC*!')
        ret = self.check_tasks()
        self.assertEqual(0, len(ret))

        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        self.assertEqual(len(select.options), 2)
        select = Select(vals['btn_to'])
        self.assertEqual(len(select.options), 2)
        select.select_by_visible_text('KEPUB')
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(5)
        ret = self.check_tasks()
        self.assertEqual(ret[-1]['result'], 'Finished')

        self.logout()
        self.login('admin', 'admin123')
        ret = self.check_tasks()
        self.assertEqual(memory + 1, len(ret))

        # Check reconvert denied, but task succeded
        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('KEPUB')
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        time.sleep(6)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        ret = self.check_tasks()
        # self.assertEqual(len(ret), len(ret2), "Reconvert of book started")
        self.assertEqual(ret[-1]['result'], 'Finished')

    def test_kobo_kepub_formats(self):
        # convert book to kepub -> 2 formats
        vals = self.get_convert_book(5)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        self.assertEqual(len(select.options), 2)
        select = Select(vals['btn_to'])
        self.assertEqual(len(select.options), 2)
        select.select_by_visible_text('KEPUB')
        self.check_element_on_page((By.ID, "btn-book-convert")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)
        # create shelf
        self.create_shelf('Ko Test', False)
        shelves = self.list_shelfs()
        self.assertEqual(1, len(shelves))
        # add book to shelf
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        # try to download book from shelf as kobo reader -> kepub.epub

        r = requests.session()
        r.headers["User-Agent"] = 'kobo 1.0'
        login_page = r.get('http://127.0.0.1:{}/login'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on",
                   "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:{}/login'.format(PORTS[0]), data=payload)
        resp = r.get('http://127.0.0.1:{}/book/8'.format(PORTS[0]))
        # try to download book from details as kobo reader -> kepub.epub
        parser = lxml.etree.HTMLParser()
        tree = lxml.etree.parse(StringIO(resp.txt), parser)
        download_link = tree.findall("//*[@aria-labelledby='btnGroupDrop1']//a")
        self.assertTrue(download_link[1].get_attribute("href").endswith('/5.kepub.epub'),
                        'Download Link has invalid format for kobo browser, has to end with filename')
        # delete epub
        self.delete_book_format(5, "EPUB")
        # try to download book from details as kobo reader -> kepub.epub
        resp = r.get('http://127.0.0.1:{}/book/8'.format(PORTS[0]))
        tree = lxml.etree.parse(StringIO(resp.txt), parser)
        download_link = tree.xpath("//*[starts-with(@id,'btnGroupDrop')]")
        self.assertTrue(download_link.get_attribute("href").endswith('/5.kepub.epub'),
                        'Download Link has invalid format for kobo browser, has to end with filename')
        resp = r.get('http://127.0.0.1:{}/simpleshelf/{}'.format(PORTS[0], shelves[0]['id']))
        tree = lxml.etree.parse(StringIO(resp.txt), parser)
        download_link = tree.xpath("//*[@aria-labelledby='Download']//a")
        self.assertTrue(download_link.get_attribute("href").endswith('/5.kepub.epub'),
                        'Download Link has invalid format for kobo browser, has to end with filename')
        r.close()