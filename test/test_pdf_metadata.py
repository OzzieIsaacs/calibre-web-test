#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase, skip
import os
import time
import requests
# from diffimg import diff
from fpdf import FPDF
import pikepdf
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from helper_ui import ui_class
from config_test import TEST_DB, base_path, BOOT_TIME
from helper_func import startup, debug_startup, add_dependency, remove_dependency
from helper_func import save_logfiles


class TestEditBooks(TestCase, ui_class):
    p = None
    driver = None
    dependencys = ['lxml']

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependencys, cls.__name__)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_uploading': 1})
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        os.remove(os.path.join(base_path, 'files', 'book1.pdf'))
        remove_dependency(cls.dependencys)
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def generate_pdf(self, filename, cover=None, title=None, author=None, description=None, tags=None, lang=None):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.image(cover, 10, 8, pdf.epw)
        '''pdf.set_title()
        pdf.set_lang()
        pdf.set_subject()
        pdf.set_author()
        pdf.set_keywords()
        pdf.set_creator()
        pdf.set_creation_date()'''
        pdf.output(filename)

        with pikepdf.open(filename, allow_overwriting_input=True) as pdf:
            with pdf.open_metadata() as meta:
                if title:
                    meta["dc:title"] = title
                if description:
                    meta["dc:description"] = description
                if author:
                    meta["dc:creator"] = [author]
                if lang:
                    meta["dc:language"] = set([lang])
                if tags:
                    meta["pdf:Keywords"] = tags
                meta["pdf:Producer"] = "test"
                meta["xmp:CreatorTool"] = "file"
                meta["xmp:MetadataDate"] = datetime.now(datetime.utcnow().astimezone().tzinfo).isoformat()
            pdf.save()
            '''<dc:language>
            <rdf:Bag>
              <rdf:li>de</rdf:li>
            </rdf:Bag>
            </dc:language>'''

    # check metadata recognition
    @skip('Not implemented in Calibre-Web')
    def test_upload_book_pdf(self):
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book1.pdf')
        cover_file = os.path.join(base_path, 'files', 'cover.jpg')
        self.generate_pdf(upload_file, cover_file, "Tütel", "Mani Mücks", lang="en")
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Tütel', details['title'])
        self.assertEqual('Mani Mücks', details['author'][0])
        self.assertEqual('German', details['languages'][0])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get('http://127.0.0.1:8083' + details['cover'])
        self.assertLess('23300', resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()

