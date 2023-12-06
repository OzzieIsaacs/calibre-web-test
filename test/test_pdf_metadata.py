#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import os
import time
import pikepdf
from fpdf import FPDF

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB, base_path
from helper_func import startup
from helper_func import save_logfiles
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


RESOURCES = {'ports': 1}

PORTS = ['8083']


class TestUploadPDF(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_uploading': 1}, env={"APP_MODE": "test"})
            time.sleep(3)
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(os.path.join(base_path, 'files', 'book1.pdf'))
        except FileNotFoundError:
            pass
        cls.driver.get("http://127.0.0.1:" + PORTS[0])
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def check_uploaded_pdf(self, book_properties, check_properties):
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book1.pdf')
        # generate pdf
        self.generate_pdf(upload_file, book_properties)
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual(check_properties['title'], details['title'])
        if isinstance(details['author'], list):
            self.assertTrue(all(elem in details['author'] for elem in check_properties['author']),
                            "Wrong authors: {} instead of {}".format(details['author'],
                                                                     check_properties['author']))
        else:
            self.assertTrue(all(elem in [details['author']] for elem in check_properties['author']),
                            "Wrong authors: {} instead of {}".format(details['author'],
                                                                     check_properties['author']))

        if 'languages' in check_properties:
            if check_properties['languages'] is None:
                self.assertTrue('languages' not in details)
            else:
                self.assertTrue(all(elem in details['languages'] for elem in check_properties['languages']),
                                "Wrong languages: {} instead of {}".format(details['languages'],
                                                                           check_properties['languages']))
        if 'tag' in check_properties:
            if check_properties['tag'] is None:
                self.assertTrue('tag' not in details)
            else:
                self.assertTrue(all(elem in details['tag'] for elem in check_properties['tag']),
                                "Wrong tags: {} instead of {}".format(details['tag'],
                                                                      check_properties['tag']))
        if 'comment' in check_properties:
            if check_properties['comment'] is None:
                self.assertTrue('comment' not in details)
            else:
                self.assertEqual(check_properties['comment'], details['comment'])

        # ToDo check cover image
        self.delete_book(details['id'])
        try:
            os.remove(os.path.join(base_path, 'files', 'book1.pdf'))
        except FileNotFoundError:
            pass

    @staticmethod
    def generate_pdf(filename, book_properties):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('helvetica', 'B', 16)
        pdf.image(book_properties['cover'], 10, 8, pdf.epw)
        pdf.output(filename)

        with pikepdf.open(filename, allow_overwriting_input=True) as pdf:
            # pdf.docinfo.Keywords = "123434\r\n32434"
            with pdf.open_metadata() as meta:
                if 'title' in book_properties:
                    meta["dc:title"] = book_properties['title']
                if 'comment' in book_properties:
                    meta["dc:description"] = book_properties['comment']
                if 'author' in book_properties:
                    meta["dc:creator"] = book_properties['author']
                if 'lang' in book_properties:
                    meta["dc:language"] = book_properties['lang']
                if 'tag' in book_properties:
                    meta["pdf:Keywords"] = book_properties['tag']
                if 'publishers' in book_properties:
                    meta["dc:publisher"] = book_properties['publishers']
                # meta["pdf:Producer"] = "test"
                # meta["xmp:CreatorTool"] = "file"
                # meta["xmp:MetadataDate"] = datetime.now(datetime.utcnow().astimezone().tzinfo).isoformat()
            pdf.save()

    # check metadata recognition of pdf files
    def test_upload_invalid_pdf(self):
        self.goto_page('nav_new')
        # invalid author and language and no title
        self.check_uploaded_pdf({'author': "Mani Mücks",
                                 "lang": "en",
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "book1",
                                 'author': ["Unknown"],
                                 'languages': None,
                                 'comment': ""
                                 }
                                )
        # Unicode author and Titel, with language
        self.check_uploaded_pdf({'title': "Tü执el",
                                 'author': ["Ma执i Mücks"],
                                 "lang": set(["de"]),
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "Tü执el",
                                 'author': ["Ma执i Mücks"],
                                 'languages' : ["German"],
                                 'comment': ""
                                 }
                                )
        # This example gives an bytes encodes tag
        self.check_uploaded_pdf({'title': "tit",
                                 'author': ["No Name"],
                                 'comment': "Holla die 执Wü",
                                 'tag': "123434\r\n32434",
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "tit",
                                 'author': ["No Name"],
                                 'comment' : "Holla die 执Wü",
                                 'tag': ["123434 32434"],
                                 }
                                )
        self.check_uploaded_pdf({'title': "tit",
                                 'author': ["No Name"],
                                 'comment': "Holla die 执Wü",
                                 'tag': "Hoä执",
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "tit",
                                 'author': ["No Name"],
                                 'comment': "Holla die 执Wü",
                                 'tag': ["Hoä执"],
                                 }
                                )
        # no author
        self.check_uploaded_pdf({'title': "title",
                                 # 'author': ["No Name"],
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "title",
                                 'author': ["Unknown"],
                                 }
                                )
        # 2 authors
        self.check_uploaded_pdf({'title': "title",
                                 'author': ["Author One", "Author Two"],
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "title",
                                 'author': ["Author One", "Author Two"],
                                 }
                                )
        # 2 authors with &
        self.check_uploaded_pdf({'title': "title",
                                 'author': ["Author One & Author Two"],
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "title",
                                 'author': ["Author One", "Author Two"],
                                 }
                                )
        # 2 authors with ,
        self.check_uploaded_pdf({'title': "title",
                                 'author': ["Author, One", "Author, Two"],
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "title",
                                 'author': ["One Author", "Two Author"],
                                 }
                                )
        # 2 authors with ;
        self.check_uploaded_pdf({'title': "The title",
                                 'author': ["Author, One ; Author, Two"],
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "The title",
                                 'author': ["One Author", "Two Author"],
                                 }
                                )
        # 2 2letter Languages and 2 tags
        self.check_uploaded_pdf({'title': "title",
                                 'author': ["Now Name"],
                                 'tag': "Hoä执, Huhu",
                                 "lang": set(["de", "en"]),
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "title",
                                 "lang": ["German", "English"],
                                 'author': ["Now Name"],
                                 'tag': ["Hoä执", "Huhu"],
                                 }
                                )
        # 2 3letter Languages
        self.check_uploaded_pdf({'title': "title",
                                 'author': ["Now Name"],
                                 "lang": set(["deu", "eng"]),
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "title",
                                 "lang": ["German", "English"],
                                 'author': ["Now Name"],
                                 }
                                )
        # One invalid language
        self.check_uploaded_pdf({'title': "title",
                                 'author': ["Now Name"],
                                 "lang": set(["deutsch", "eng"]),
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "title",
                                 "lang": ["English"],
                                 'author': ["Now Name"],
                                 }
                                )
        # One Publisher
        self.check_uploaded_pdf({'title': "title",
                                 'author': ["Now Name"],
                                 'publishers': set(["Hölder"]),
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "title",
                                 'publishers': ["Hölder"],
                                 'author': ["Now Name"],
                                 }
                                )
        # Two Publishers
        self.check_uploaded_pdf({'title': "title",
                                 'author': ["Now Name"],
                                 'publishers': set(["Hölder, Kurt"]),
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "title",
                                 'author': ["Now Name"],
                                 'publishers': ["Hölder, Kurt"],
                                 }
                                )
        # Empty title
        self.check_uploaded_pdf({'title': " ",
                                 'author': ["Now Name"],
                                 'publishers': set(["Hölder, Kurt"]),
                                 "cover": os.path.join(base_path, 'files', 'cover.jpg')},
                                {'title': "book1",
                                 'author': ["Now Name"],
                                 }
                                )
