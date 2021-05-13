#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase, skip
import os
import time
import requests
import zipfile
from bs4 import BeautifulSoup
import codecs

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB, base_path, BOOT_TIME
from helper_func import add_dependency, remove_dependency, save_logfiles, startup


class TestUploadEPubs(TestCase, ui_class):
    p = None
    driver = None
    dependencys = ['lxml']

    @classmethod
    def setUpClass(cls):
        pass
        add_dependency(cls.dependencys, cls.__name__)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_uploading': 1})
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        pass
        remove_dependency(cls.dependencys)
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def updateZip(self, zipname_new, zipname_org, filename, data):
        # create a temp copy of the archive without filename
        with zipfile.ZipFile(zipname_org, 'r') as zin:
            with zipfile.ZipFile(zipname_new, 'w') as zout:
                zout.comment = zin.comment  # preserve the comment
                for item in zin.infolist():
                    if item.filename != filename:
                        zout.writestr(item, zin.read(item.filename))

        # now add filename with its new data
        with zipfile.ZipFile(zipname_new, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(filename, data)

    def change_epub_meta(self, zipname_new=None, zipname_org='./files/book.epub', element={}):
        with codecs.open('./files/test.opf', "r", "utf-8") as f:
            soup = BeautifulSoup(f.read(), "xml")
        for el in soup.findAll("meta"):
            el.prefix = ""
            el.namespace=""
        soup.find("metadata").prefix = ""
        for k, v in element.items():
            if k == "author":
                pass
            el = soup.find(k)
            el.string = v
        self.updateZip(zipname_new, zipname_org, 'content.opf', str(soup))

    def test_upload_epub_duplicate(self):
        epub_file = os.path.join(base_path, 'files', 'title.epub')
        self.change_epub_meta(epub_file, element={'title': "Der titel", 'creator': "Kurt Hugo"})
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Der titel', details['title'])
        self.assertEqual('Kurt Hugo', details['author'][0])
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        os.remove(epub_file)
