#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import time

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
        data = {"name": "lurgi", "value": "test", "pk": ["10", 7]}
        headers = {"X-CSRFToken": token.group(1)}
        response = r.post('http://127.0.0.1:{}/ajax/editbooks/lurgi'.format(PORTS[0]), json=data, headers=headers, timeout=5)
        self.assertEqual(400, response.status_code)
        self.assertTrue("Parameter" in response.text)
        data = {"value": "test", "pk": ["22", 10]}
        response = r.post('http://127.0.0.1:{}/ajax/editbooks/series'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json().get('msg', None))
        data = {"value": "fdt", "pk": [10, 11]}
        response = r.post('http://127.0.0.1:{}/ajax/editbooks/languages'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json().get('msg', None))
        data = {"pk": [10, 11]}
        response = r.post('http://127.0.0.1:{}/ajax/editbooks/languages'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json().get('msg', None))
        data = {"value": "fdt", "pk": ["hurtz", 10]}
        response = r.post('http://127.0.0.1:{}/ajax/editbooks/title'.format(PORTS[0]), json=data, headers=headers,
                          timeout=5)
        self.assertEqual(200, response.status_code)
        self.assertNotEqual(None, response.json().get('msg', None))
        r.close()

    def test_author_title_combi(self):
        # goto book table
        # select book 1 and 2
        # open mass edit dialog
        # check title_sort and author_sort are greyed out
        # close dialog
        # untick title_sort and author_sort are greyed out
        # open mass edit dialog
        # check title_sort and author_sort are editable
        # edit author, author_sort, title, title_sort
        # submit
        # check table content
        # tick title_sort and author_sort are greyed out
        # revert changes
        pass

    # Title, autor not exist multi edit
    def test_invalid_author_title(self):
        # goto book table
        # select book 3 and 4, 5
        # move author-book 3
        # move title-book 4
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

    # Title, autor write write protect  multi edit
    def test_protected_author_title(self):
        # goto book table
        # select book 3 and 4, 5
        # write protect author-book 3
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


Title, autor write protect single edit
