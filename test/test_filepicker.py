# -*- coding: utf-8 -*-

from base_test import ParallelTestCase
import os
import time
from unittest import skip
from selenium.webdriver.common.by import By
from helper_func import startup


class TestFilePicker(ParallelTestCase):



    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': cls.temp_dir}, work_path=cls.app_dir,
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir,
                    only_startup=True, only_metadata=True)
            cls.login("admin", "admin123")
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    def test_filepicker_limited_file(self):
        filepicker = self.check_element_on_page((By.ID, "calibre_modal_path"))
        self.assertTrue(filepicker)
        # create subfolder with strange characters unicode unmlaut, %,,#~...
        subfolder = os.path.join(self.temp_dir, "lÖ#~%d '")
        os.mkdir(subfolder)
        # open filepicker without path, navigate higher until end is reached
        filepicker.click()
        time.sleep(1)
        element = self.check_element_on_page((By.ID, "element_selected"))
        self.assertTrue(element)
        self.assertEqual(self.app_dir, element.text)
        folder_depth = (self.app_dir).count(os.sep)
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
        CALIBRE_WEB_PATH_PARENT = (self.app_dir)[:(self.app_dir).rfind(os.sep)]
        self.fill_db_config(dict(config_calibre_dir=self.temp_dir))
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        self.goto_page('basic_config')
        time.sleep(2)
        accordions = self.driver.find_elements(by=By.CLASS_NAME, value='accordion-toggle')
        time.sleep(1)
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
        self.assertEqual(input1.get_attribute('value'), self.app_dir)
        self.assertEqual(input2.get_attribute('value'), CALIBRE_WEB_PATH_PARENT)

    @skip("Not implemented")
    def test_filepicker_new_file(self):
        pass
