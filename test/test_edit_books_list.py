#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase, skip
import os
import time
import requests

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from helper_ui import ui_class
from config_test import TEST_DB, base_path
from helper_func import startup, debug_startup, add_dependency, remove_dependency
from helper_func import save_logfiles


class TestEditBooksList(TestCase, ui_class):
    p = None
    driver = None
    # dependencys = ['Pillow', 'lxml']

    @classmethod
    def setUpClass(cls):
        # add_dependency(cls.dependencys, cls.__name__)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB})
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        # remove_dependency(cls.dependencys)
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    # goto books list, check content of table
    # delete one book
    # change no of books per page to 5
    # goto page 2 check content
    def test_edit_books_list(self):
        self.get_blist(2)
        pass


    # change visibility of some columns
    # goto other page, return to books list, check if visibility is same
    # create user, logout, login new user, check visibility is reset to default
    def test_list_visibility(self):
        pass

    # select one book on page one -> button greyed
    # select two books on page one -> button accessible, click unselect books -> no book selected
    # select book on page 1, select book on page 2, -> button accessible, go to different page and return -> books unselected
    # select book on page 1, select book on page 2 -> press unselect, both books unselected
    # select book on page 1, select book on page 2 -> merge -> abort, everything like before
    # select book on page 1, select book on page 2 -> merge -> one book less, both formats available
    def test_merge_book(self):
        pass