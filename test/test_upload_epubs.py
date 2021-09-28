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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestUploadEPubs(TestCase, ui_class):
    p = None
    driver = None
    #dependencys = ['lxml']

    @classmethod
    def setUpClass(cls):
        #add_dependency(cls.dependencys, cls.__name__)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_uploading': 1})
            time.sleep(3)
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        # remove_dependency(cls.dependencys)
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
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details2 = self.get_book_details()
        self.delete_book(details['id'])
        self.delete_book(details2['id'])
        os.remove(epub_file)

    def verify_upload(self, epub_file, check_warning=False):
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        if check_warning:
            self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        return self.get_book_details()

    def test_upload_epub_lang(self):
        epub_file = os.path.join(base_path, 'files', 'lang.epub')
        self.change_visibility_me({'locale': "Italiano"})
        self.change_epub_meta(epub_file, element={'title': "Langtest", 'creator': "Nobody Perfect", "language": "xx"})
        details = self.verify_upload(epub_file, check_warning=True)
        self.assertEqual('Langtest', details['title'])
        self.assertEqual('Nobody Perfect', details['author'][0])
        self.assertNotIn('languages', details)
        self.delete_book(details['id'])
        self.change_epub_meta(epub_file, element={'title': "Langtest", 'creator': "Nobody Perfect", "language": "xyz"})
        details = self.verify_upload(epub_file, check_warning=True)
        self.assertNotIn('languages', details)
        self.delete_book(details['id'])
        self.change_epub_meta(epub_file, element={'title': "Langtest", 'creator': "Nobody Perfect", "language": "deu"})
        details = self.verify_upload(epub_file)
        self.assertEqual('Tedesco', details['languages'][0])
        list_element = self.goto_page("nav_lang")
        self.assertEqual('Tedesco', list_element[2].text)
        list_element[2].click()
        self.assertEqual("Lingua: Tedesco", self.driver.find_elements_by_tag_name("h2")[1].text)
        self.assertEqual(len(self.adv_search({u'include_language': u'Tedesco'})), 1)
        self.delete_book(details['id'])
        self.change_epub_meta(epub_file, element={'title': "Langtest", 'creator': "Nobody Perfect", "language": "lat"})
        details = self.verify_upload(epub_file)
        self.assertEqual('Latino', details['languages'][0])
        list_element = self.goto_page("nav_lang")
        self.assertEqual('Latino', list_element[2].text)
        list_element[2].click()
        self.assertEqual("Lingua: Latino", self.driver.find_elements_by_tag_name("h2")[1].text)
        self.assertEqual(len(self.adv_search({u'include_language': u'Latino'})), 1)
        self.delete_book(details['id'])
        self.change_epub_meta(epub_file, element={'title': "Langtest", 'creator': "Nobody Perfect", "language": "und"})
        details = self.verify_upload(epub_file)
        self.assertEqual('Non determinato', details['languages'][0])
        self.delete_book(details['id'])

        self.change_epub_meta(epub_file, element={'title': "Langtest", 'creator': "Nobody Perfect", "language": "de"})
        details = self.verify_upload(epub_file)
        self.assertEqual('Tedesco', details['languages'][0])
        self.delete_book(details['id'])
        self.change_visibility_me({'locale': "English", "default_language": "Inglese"})
        # Check uploaded book with applied visibility restriction is visible -> book language is changed
        details = self.verify_upload(epub_file)
        self.assertEqual('English', details['languages'][0])
        self.delete_book(details['id'])
        self.change_visibility_me({'default_language': "Show All"})
        os.remove(epub_file)

