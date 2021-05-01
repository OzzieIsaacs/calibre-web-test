#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import os
import time
from unittest import skip
from selenium.webdriver.common.by import By

from helper_ui import ui_class
from config_test import TEST_DB, CALIBRE_WEB_PATH
from helper_func import startup
from helper_func import save_logfiles


class TestFilePicker(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, parameter="-f", work_path=CALIBRE_WEB_PATH,
                    only_startup=True, only_metadata=True)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        # cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_filepicker_limited_file(self):
        filepicker = self.check_element_on_page((By.ID, "calibre_modal_path"))
        self.assertTrue(filepicker)
        # create subfolder with strange characters unicode unmlaut, %,,#~...
        subfolder = os.path.join(TEST_DB, "lÖ#~%d '")
        os.mkdir(subfolder)
        # open filepicker without path, navigate higher until end is reached
        filepicker.click()
        element = self.check_element_on_page((By.ID, "element_selected"))
        self.assertTrue(element)
        self.assertEqual(CALIBRE_WEB_PATH, element.text)
        folder_depth = CALIBRE_WEB_PATH.count(os.sep)
        for i in range(0, folder_depth):
            path_entries = self.driver.find_elements_by_xpath("//tr[@class='tr-clickable']/td[2]")
            self.assertEqual(path_entries[0].text, "..")
            path_entries[0].click()
        path_entries = self.driver.find_elements_by_xpath("//tr[@class='tr-clickable']/td[2]")
        self.assertNotEqual(path_entries[0].text, "..")
        self.check_element_on_page((By.ID, "file_abort")).click()
        time.sleep(1)
        self.assertEqual(self.check_element_on_page((By.ID, "config_calibre_dir")).text,"")

        # file_abort
        # self.driver.find_elements_by_class_name("tr-clickable")
        # check files with other ending than metadaa.db are not shown, only folders
        # check folder with name metadata.db is shown
        # nagigate back to older where we came from, select nothing, click abort -> field still empty
        # open filkepicker select nothing, click okay -> path taken
        # open filkepicker select metadata.db, click okay -> path taken incl. metadata.db
        # empty field -> open filepicker, check back to original path, abort -> field empty
        # put "." in field -> open filepicker, check back to original path, -> okay,value replaced
        # put invalid path to field, open fillepicker -> check back to original path, abort -> invalid path still present

    @skip("Not implemented")
    def test_filepicker_new_file(self):
        pass

    @skip("Not implemented")
    def test_filepicker_all_file(self):  # ?
        pass
