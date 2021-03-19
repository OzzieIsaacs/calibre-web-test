#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from helper_ui import ui_class
from config_test import TEST_DB, base_path
from helper_func import startup, debug_startup, add_dependency, remove_dependency
from selenium.webdriver.common.by import By
from helper_func import save_logfiles
import time
import os


class TestReader(unittest.TestCase, ui_class):

    p = None
    driver = None

    @classmethod
    def setUpClass(cls):

        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB})
            cls.current_handle = cls.driver.current_window_handle

        except Exception:
            cls.driver.quit()
            cls.p.terminate()
            cls.p.poll()

    @classmethod
    def tearDown(cls):
        new_handle = cls.driver.current_window_handle
        if new_handle != cls.current_handle:
            cls.driver.close()
            cls.driver.switch_to.window(cls.current_handle)

    @classmethod
    def tearDownClass(cls):
        cls.driver.switch_to.window(cls.current_handle)
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        cls.driver.quit()
        cls.p.terminate()
        # close the browser window and stop calibre-web
        # remove_dependency(cls.dependency)
        save_logfiles(cls, cls.__name__)


    def test_txt_reader(self):
        self.get_book_details(1)
        self.assertFalse(self.check_element_on_page((By.ID, "read-in-browser")))
        current_handles = self.driver.window_handles
        read_button = self.check_element_on_page((By.ID, "readbtn"))
        self.assertTrue("txt" in read_button.text)
        read_button.click()
        #self.check_element_on_page((By.ID, "read-in-browser")).click()
        #current_handles = self.driver.window_handles
        #self.check_element_on_page((By.XPATH, "//ul[@aria-labelledby='read-in-browser']/li/a[contains(.,'txt')]")).click()
        new_handle = [x for x in self.driver.window_handles if x not in current_handles]
        if len(new_handle) != 1:
            self.assertFalse('Not exactly one new tab was opened')
        self.driver.switch_to.window(new_handle[0])
        time.sleep(3)
        content = self.check_element_on_page((By.ID, "content"))
        self.assertTrue(content)
        self.assertTrue('hörte' in content.text, 'Encoding of textfile viewer is not respected properly')

    def test_epub_reader(self):
        self.get_book_details(8)
        self.assertFalse(self.check_element_on_page((By.ID, "read-in-browser")))
        current_handles = self.driver.window_handles
        read_button = self.check_element_on_page((By.ID, "readbtn"))
        self.assertTrue("epub" in read_button.text)
        read_button.click()
        #self.check_element_on_page((By.ID, "read-in-browser")).click()
        #current_handles = self.driver.window_handles
        #self.check_element_on_page((By.XPATH, "//ul[@aria-labelledby='read-in-browser']/li/a[contains(.,'epub')]")).click()
        new_handle = [x for x in self.driver.window_handles if x not in current_handles]
        if len(new_handle) != 1:
            self.assertFalse('Not exactly one new tab was opened')
        self.driver.switch_to.window(new_handle[0])
        self.driver.switch_to.frame(self.check_element_on_page((By.XPATH,"//iframe[starts-with(@id, 'epubjs-view')]")))
        content = self.driver.find_elements_by_class_name("calibre1")
        # content = self.check_element_on_page((By.XPATH, "//@id=viewer/")) # "//div[@id='viewer']/div" [starts-with(@id, 'serie_')]"
        self.assertTrue(content)
        self.assertTrue('Überall dieselbe alte Leier.' in content[1].text)
        self.driver.switch_to.default_content()
        self.driver.close()
        self.driver.switch_to.window(self.current_handle)
        # remove viewer rights
        self.edit_user('admin', {'viewer_role': 0})
        self.get_book_details(8)
        self.assertFalse(self.check_element_on_page((By.ID, "read-in-browser")))
        self.assertFalse(self.check_element_on_page((By.ID, "readbtn")))
        self.edit_user('admin', {'viewer_role': 1})


    def test_pdf_reader(self):
        self.get_book_details(13)
        self.assertFalse(self.check_element_on_page((By.ID, "read-in-browser")))
        current_handles = self.driver.window_handles
        read_button = self.check_element_on_page((By.ID, "readbtn"))
        self.assertTrue("pdf" in read_button.text)
        read_button.click()
        #self.check_element_on_page((By.ID, "read-in-browser")).click()
        #current_handles = self.driver.window_handles
        #self.check_element_on_page((By.XPATH, "//ul[@aria-labelledby='read-in-browser']/li/a[contains(.,'pdf')]")).click()
        new_handle = [x for x in self.driver.window_handles if x not in current_handles]
        if len(new_handle) != 1:
            self.assertFalse('Not exactly one new tab was opened')
        self.driver.switch_to.window(new_handle[0])
        time.sleep(3)
        content = self.driver.find_elements_by_xpath("//div[@class='textLayer']/span")
        self.assertTrue(content)
        self.assertTrue('Lorem ipsum dolor sit amet, consectetuer adipiscing elit' in content[0].text)
        self.driver.close()
        self.driver.switch_to.window(self.current_handle)
        self.fill_basic_config({'config_anonbrowse': 1})
        time.sleep(3)
        self.edit_user('Guest', {'viewer_role': 1})
        self.logout()
        self.get_book_details(13)
        self.assertFalse(self.check_element_on_page((By.ID, "read-in-browser")))
        current_handles = self.driver.window_handles
        read_button = self.check_element_on_page((By.ID, "readbtn"))
        self.assertTrue("pdf" in read_button.text)
        read_button.click()
        #self.check_element_on_page((By.ID, "read-in-browser")).click()
        #current_handles = self.driver.window_handles
        #self.check_element_on_page((By.XPATH, "//ul[@aria-labelledby='read-in-browser']/li/a[contains(.,'pdf')]")).click()
        new_handle = [x for x in self.driver.window_handles if x not in current_handles]
        if len(new_handle) != 1:
            self.assertFalse('Not exactly one new tab was opened')
        self.driver.switch_to.window(new_handle[0])
        time.sleep(3)
        self.assertFalse(self.check_element_on_page((By.ID, "print")))
        self.assertFalse(self.check_element_on_page((By.ID, "download")))
        self.driver.close()
        self.driver.switch_to.window(self.current_handle)
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.edit_user('Guest', {'download_role': 1})
        self.logout()
        self.get_book_details(13)
        self.assertFalse(self.check_element_on_page((By.ID, "read-in-browser")))
        current_handles = self.driver.window_handles
        read_button = self.check_element_on_page((By.ID, "readbtn"))
        self.assertTrue("pdf" in read_button.text)
        read_button.click()
        #self.check_element_on_page((By.ID, "read-in-browser")).click()
        #self.check_element_on_page((By.XPATH, "//ul[@aria-labelledby='read-in-browser']/li/a[contains(.,'pdf')]")).click()
        new_handle = [x for x in self.driver.window_handles if x not in current_handles]
        if len(new_handle) != 1:
            self.assertFalse('Not exactly one new tab was opened')
        self.driver.switch_to.window(new_handle[0])
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "print")))
        self.assertTrue(self.check_element_on_page((By.ID, "download")))
        self.driver.close()
        self.driver.switch_to.window(self.current_handle)
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.fill_basic_config({'config_anonbrowse': 0})



    def test_comic_reader(self):
        self.get_book_details(3)
        self.assertFalse(self.check_element_on_page((By.ID, "read-in-browser")))
        current_handles = self.driver.window_handles
        read_button = self.check_element_on_page((By.ID, "readbtn"))
        self.assertTrue("cbr" in read_button.text)
        read_button.click()
        # self.check_element_on_page((By.XPATH, "//ul[@aria-labelledby='read-in-browser']/li/a[contains(.,'cbr')]")).click()
        new_handle = [x for x in self.driver.window_handles if x not in current_handles]
        if len(new_handle) != 1:
            self.assertFalse('Not exactly one new tab was opened')
        self.driver.switch_to.window(new_handle[0])
        content = self.check_element_on_page((By.ID, "mainImage"))
        self.assertTrue(content)
        # ToDO: Check displayed content

    def sound_test(self, file_name, title, duration):
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', file_name)
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertFalse(self.check_element_on_page((By.ID, "listen-in-browser")))
        #self.check_element_on_page((By.ID, "listen-in-browser")).click()
        current_handles = self.driver.window_handles
        listen_button = self.check_element_on_page((By.ID, "listenbtn"))
        self.assertTrue(os.path.splitext(file_name)[1][1:] in listen_button.text)
        listen_button.click()
        #self.check_element_on_page((By.XPATH,
        #                            "//ul[@aria-labelledby='listen-in-browser']/li/a[contains(.,'" + os.path.splitext(file_name)[1][1:] + "')]")).click()
        new_handle = [x for x in self.driver.window_handles if x not in current_handles]
        if len(new_handle) != 1:
            self.assertFalse('Not exactly one new tab was opened')
        self.driver.switch_to.window(new_handle[0])
        time.sleep(2)
        play_button = self.check_element_on_page((By.CLASS_NAME, "sm2-icon-play-pause"))
        self.assertTrue(play_button)
        play_button.click()
        time.sleep(2)
        title_item = self.check_element_on_page((By.XPATH, "//ul[@class='sm2-playlist-bd']/li"))
        self.assertTrue(title_item)
        if title_item.text.startswith("✖ ✖") and os.name == 'nt':
            self.assertEqual(title, title_item.text,
                             "May fail due to inactive sound output on Windows Remotedesktop connection")
        else:
            self.assertEqual(title, title_item.text)
        duration_item = self.check_element_on_page((By.CLASS_NAME, "sm2-inline-duration"))
        self.assertTrue(duration_item)
        self.assertEqual(duration, duration_item.text)
        self.driver.close()
        self.driver.switch_to.window(self.current_handle)
        self.delete_book(int(details['cover'].split('/')[-1].split('?')[0]))


    def test_sound_listener(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.sound_test('music.flac', 'Unknown - music', '0:02')
        self.sound_test('music.mp3', 'Unknown - music', '0:03')
        self.sound_test('music.ogg', 'Unknown - music', '0:02')
        self.sound_test('music.opus', 'Unknown - music', '0:02')
        self.sound_test('music.wav', 'Unknown - music', '0:02')
        self.sound_test('music.mp4', 'Unknown - music', '0:02')
        self.fill_basic_config({'config_uploading': 0})
        time.sleep(3)

