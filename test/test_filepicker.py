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


RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


class TestFilePicker(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, work_path=CALIBRE_WEB_PATH + INDEX,
                    port=PORTS[0], index=INDEX,
                    only_startup=True, only_metadata=True, env={"APP_MODE": "test"})
            cls.login("admin", "admin123")
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
        time.sleep(1)
        element = self.check_element_on_page((By.ID, "element_selected"))
        self.assertTrue(element)
        self.assertEqual(CALIBRE_WEB_PATH + INDEX, element.text)
        folder_depth = (CALIBRE_WEB_PATH + INDEX).count(os.sep)
        for i in range(0, folder_depth):
            path_entries = self.driver.find_elements(By.XPATH, "//tr[@class='tr-clickable']/td[2]")
            self.assertEqual(path_entries[0].text, "..")
            path_entries[0].click()
        path_entries = self.driver.find_elements(By.XPATH, "//tr[@class='tr-clickable']/td[2]")
        self.assertNotEqual(path_entries[0].text, "..")
        self.check_element_on_page((By.ID, "file_abort")).click()
        time.sleep(1)
        self.assertEqual(self.check_element_on_page((By.ID, "config_calibre_dir")).text,"")

        # file_abort
        # self.driver.find_elements(By.CLASS_NAME, "tr-clickable")
        # check files with other ending than metadata.db are not shown, only folders
        # check folder with name metadata.db is shown
        # navigate back to older where we came from, select nothing, click abort -> field still empty
        # open filepicker select nothing, click okay -> path taken
        # open filepicker select metadata.db, click okay -> path taken incl. metadata.db
        # empty field -> open filepicker, check back to original path, abort -> field empty
        # put "." in field -> open filepicker, check back to original path, -> okay,value replaced
        # put invalid path to field, open filepicker -> check back to original path, abort -> invalid path still present

    def test_two_filepickers(self):
        CALIBRE_WEB_PATH_PARENT = (CALIBRE_WEB_PATH + INDEX)[:(CALIBRE_WEB_PATH + INDEX).rfind(os.sep)]

        self.fill_db_config(dict(config_calibre_dir=TEST_DB))
        self.goto_page('basic_config')
        time.sleep(1)
        accordions = self.driver.find_elements(by=By.CLASS_NAME, value='accordion-toggle')
        accordions[0].click()

        input1 = self.check_element_on_page((By.ID, 'config_certfile'))
        filepicker1 = self.check_element_on_page((By.ID, 'certfile_path'))
        filepicker1.click()
        time.sleep(1)
        self.check_element_on_page((By.ID, 'file_confirm')).click()

        # the dialog needs some time to animate away
        time.sleep(1)

        input2 = self.check_element_on_page((By.ID, 'config_keyfile'))
        filepicker2 = self.check_element_on_page((By.ID, 'keyfile_path'))
        filepicker2.click()
        time.sleep(1)
        path_entries = self.driver.find_elements(by=By.XPATH, value='//tr[@class=\'tr-clickable\']/td[2]')
        path_entries[0].click()
        self.check_element_on_page((By.ID, 'file_confirm')).click()

        time.sleep(3)
        self.assertEqual(input1.get_attribute('value'), CALIBRE_WEB_PATH + INDEX)
        self.assertEqual(input2.get_attribute('value'), CALIBRE_WEB_PATH_PARENT)

    @skip("Not implemented")
    def test_filepicker_new_file(self):
        pass
