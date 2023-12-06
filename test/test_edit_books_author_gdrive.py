#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase, skipIf
import time
import os
import shutil

from helper_ui import ui_class
from config_test import TEST_DB, base_path
from helper_func import startup, change_epub_meta
from config_test import CALIBRE_WEB_PATH, WAIT_GDRIVE
from helper_func import save_logfiles, add_dependency, remove_dependency
from helper_gdrive import prepare_gdrive, connect_gdrive
from selenium.webdriver.common.by import By


@skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
class TestEditAuthorsGdrive(TestCase, ui_class):
    p = None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]


    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)

        prepare_gdrive()
        try:
            src = os.path.join(base_path, "files", "client_secrets.json")
            dst = os.path.join(CALIBRE_WEB_PATH, "client_secrets.json")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            # delete settings_yaml file
            set_yaml = os.path.join(CALIBRE_WEB_PATH, "settings.yaml")
            if os.path.exists(set_yaml):
                os.unlink(set_yaml)

            # delete gdrive file
            gdrive_db = os.path.join(CALIBRE_WEB_PATH, "gdrive.db")
            if os.path.exists(gdrive_db):
                os.unlink(gdrive_db)

            # delete gdrive authenticated file
            src = os.path.join(base_path, 'files', "gdrive_credentials")
            dst = os.path.join(CALIBRE_WEB_PATH, "gdrive_credentials")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB,
                                          # 'config_log_level': 'DEBUG',
                                          'config_kepubifypath': '',
                                          'config_binariesdir': ''},
                    only_metadata=True, env={"APP_MODE": "test"})
            cls.fill_db_config({'config_use_google_drive': 1})
            time.sleep(2)
            cls.fill_db_config({'config_google_drive_folder': 'test'})
            time.sleep(2)
        except Exception as e:
            try:
                print(e)
                cls.driver.quit()
                cls.p.kill()
            except Exception:
                pass

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        remove_dependency(cls.dependency)

        src1 = os.path.join(CALIBRE_WEB_PATH, "client_secrets.json")
        src = os.path.join(CALIBRE_WEB_PATH, "gdrive_credentials")
        if os.path.exists(src):
            os.chmod(src, 0o764)
            try:
                os.unlink(src)
            except PermissionError:
                print('gdrive_credentials delete failed')
        if os.path.exists(src1):
            os.chmod(src1, 0o764)
            try:
                os.unlink(src1)
            except PermissionError:
                print('client_secrets.json delete failed')

        save_logfiles(cls, cls.__name__)

    # One book of the author present
    def test_change_capital_one_author_one_book(self):
        fs = connect_gdrive("test")
        self.assertTrue(fs.isfile(os.path.join('test', 'Leo Baskerville/book8 (8)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Leo Baskerville/book8 (8)',
                                                    'book8 - Leo Baskerville.epub').replace('\\', '/')))
        # rename uppercase to lowercase only of author
        self.edit_book(8, content={'bookAuthor': "Leo baskerville"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Leo baskerville'], details['author'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Leo baskerville/book8 (8)',
                                                    'book8 - Leo baskerville.epub').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Leo baskerville/book8 (8)',
                                                    'cover.jpg').replace('\\', '/')))
        # Check that name of author folder no longer is "Leo Baskerville"
        self.assertNotEqual("Leo Baskerville", fs.getinfo(os.path.join('test', 'Leo Baskerville').replace('\\', '/')).name)
        ret_code, content = self.download_book(8, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename book title and author in the same step
        self.edit_book(8, content={'bookAuthor': "Leo Baskerville", 'book_title': 'book 9'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Leo Baskerville'], details['author'])
        self.assertEqual('book 9', details['title'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Leo Baskerville/book 9 (8)',
                                                    'book 9 - Leo Baskerville.epub').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Leo Baskerville/book 9 (8)',
                                                    'cover.jpg').replace('\\', '/')))
        # Check that name of author folder no longer is "Leo baskerville"
        self.assertNotEqual("Leo baskerville",
                            fs.getinfo(os.path.join('test', 'Leo baskerville').replace('\\', '/')).name)
        ret_code, content = self.download_book(8, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename only book title
        self.edit_book(8, content={'bookAuthor': "Leo Baskerville", 'book_title': 'book8'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Leo Baskerville'], details['author'])
        self.assertEqual('book8', details['title'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Leo Baskerville/book8 (8)',
                                                    'book8 - Leo Baskerville.epub').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Leo Baskerville/book8 (8)',
                                                    'cover.jpg')))
        # Check that name of author folder no longer is "Leo baskerville"
        self.assertNotEqual("Leo baskerville",
                            fs.getinfo(os.path.join('test', 'Leo baskerville').replace('\\', '/')).name)
        ret_code, content = self.download_book(8, "admin", "admin123")
        self.assertEqual(200, ret_code)

    # 2 books of the author present
    def test_change_capital_one_author_two_books(self):
        fs = connect_gdrive("test")
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter Parker/book7 (10)',
                                                    'cover.jpg')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter Parker/book7 (10)',
                                                    'book7 - Peter Parker.epub').replace('\\', '/')))
        # rename uppercase to lowercase only of author
        self.edit_book(10, content={'bookAuthor': "Peter parker"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Peter parker'], details['author'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter parker/book7 (10)',
                                                    'book7 - Peter parker.epub').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter parker/book7 (10)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter parker/Very long extra super turbo cool tit (4)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter parker/Very long extra super turbo cool tit (4)',
                                                    'Very long extra super turbo cool title wit - Peter parker.pdf')
                                  .replace('\\', '/')))
        # Check that name of author folder no longer is "Peter Parker"
        self.assertNotEqual("Peter Parker",
                            fs.getinfo(os.path.join('test', 'Peter Parker').replace('\\', '/')).name)
        ret_code, content = self.download_book(10, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(4, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename book title and author in the same step
        self.edit_book(10, content={'bookAuthor': "Peter Parker", 'book_title': 'book 7'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Peter Parker'], details['author'])
        self.assertEqual('book 7', details['title'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter Parker/book 7 (10)',
                                                    'book 7 - Peter Parker.epub').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter Parker/book 7 (10)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter Parker/Very long extra super turbo cool tit (4)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter Parker/Very long extra super turbo cool tit (4)',
                                                    'Very long extra super turbo cool title wit - Peter Parker.pdf')
                                  .replace('\\', '/')))
        # Check that name of author folder no longer is "Peter parker"
        self.assertNotEqual("Peter parker",
                            fs.getinfo(os.path.join('test', 'Peter parker').replace('\\', '/')).name)
        ret_code, content = self.download_book(10, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(4, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename only book title
        self.edit_book(10, content={'bookAuthor': "Peter Parker", 'book_title': 'book7'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Peter Parker'], details['author'])
        self.assertEqual('book7', details['title'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter Parker/book7 (10)',
                                                    'book7 - Peter Parker.epub').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Peter Parker/book7 (10)',
                                                    'cover.jpg').replace('\\', '/')))
        # Check that name of author folder no longer is "Peter parker"
        self.assertNotEqual("Peter parker",
                            fs.getinfo(os.path.join('test', 'Peter parker').replace('\\', '/')).name)

        ret_code, content = self.download_book(8, "admin", "admin123")
        self.assertEqual(200, ret_code)

    # 1 books of the author, one co-author
    def test_change_capital_one_author_two_books(self):
        fs = connect_gdrive("test")
        self.assertTrue(fs.isfile(os.path.join('test', 'Norbert Halagal/book11 (13)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Norbert Halagal/book11 (13)',
                                                    'book11 - Norbert Halagal.pdf').replace('\\', '/')))
        # rename uppercase to lowercase only of author
        self.edit_book(13, content={'bookAuthor': "Norbert halagal"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Norbert halagal'], details['author'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Norbert halagal/book11 (13)',
                                                    'book11 - Norbert halagal.pdf').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Norbert halagal/book11 (13)',
                                                    'cover.jpg').replace('\\', '/')))
        # Check that name of author folder no longer is "Peter parker"
        self.assertNotEqual("Norbert Halagal",
                            fs.getinfo(os.path.join('test', 'Norbert Halagal').replace('\\', '/')).name)
        details = self.get_book_details(1)
        self.assertCountEqual(['Frodo Beutlin', 'Norbert halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        ret_code, content = self.download_book(13, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # rename book title and author in the same step
        self.edit_book(13, content={'bookAuthor': "Norbert Halagal", 'book_title': 'book 11'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Norbert Halagal'], details['author'])
        self.assertEqual('book 11', details['title'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Norbert Halagal/book 11 (13)',
                                                    'book 11 - Norbert Halagal.pdf').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Norbert Halagal/book 11 (13)',
                                                    'cover.jpg').replace('\\', '/')))
        # Check that name of author folder no longer is "Norbert halagal"
        self.assertNotEqual("Norbert halagal",
                            fs.getinfo(os.path.join('test', 'Norbert halagal').replace('\\', '/')).name)

        ret_code, content = self.download_book(13, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename only book title
        self.edit_book(13, content={'book_title': 'book11'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Norbert Halagal'], details['author'])
        self.assertEqual('book11', details['title'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Norbert Halagal/book11 (13)',
                                                    'book11 - Norbert Halagal.pdf').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Norbert Halagal/book11 (13)',
                                                    'cover.jpg').replace('\\', '/')))
        # Check that name of author folder no longer is "Norbert halagal"
        self.assertNotEqual("Norbert halagal",
                            fs.getinfo(os.path.join('test', 'Norbert halagal').replace('\\', '/')).name)

        ret_code, content = self.download_book(13, "admin", "admin123")
        self.assertEqual(200, ret_code)

    # Author only co-author
    def test_change_capital_co_author(self):
        fs = connect_gdrive("test")
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt').replace('\\', '/')))
        # rename uppercase to lowercase only of author
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu yang & Hector Gonçalves"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu yang', 'Hector Gonçalves'], details['author'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt').replace('\\', '/')))
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg').replace('\\', '/')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # rename book title and author in the same step
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & Hector Gonçalves",
                                   'book_title': 'Derbook 1'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Derbook 1', details['title'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Derbook 1 (1)',
                                                    'Derbook 1 - Frodo Beutlin.txt').replace('\\', '/')))
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Derbook 1 (1)',
                                                    'cover.jpg').replace('\\', '/')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        # rename only book title
        self.edit_book(1, content={'book_title': 'Der Buchtitel'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Der Buchtitel', details['title'])
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt').replace('\\', '/')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

    # Author rename co-author and author is also main author somewhere
    def test_change_capital_rename_co_author(self):
        fs = connect_gdrive("test")
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Hector Goncalves/book9 (11)',
                                                    'book9 - Hector Goncalves.pdf').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Hector Goncalves/book9 (11)',
                                                    'cover.jpg').replace('\\', '/')))
        # Author folder is not found due to utf characters not represented in filename
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & hector Gonçalves"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'hector Gonçalves'], details['author'])
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Hector Goncalves/book9 (11)',
                                                    'book9 - Hector Goncalves.pdf').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Hector Goncalves/book9 (11)',
                                                    'cover.jpg').replace('\\', '/')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(11, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # ToDo: currently empty folder Hector Goncalves remains
        self.edit_book(11, content={'bookAuthor': "hector Gonçalves & Unbekannt"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['hector Gonçalves', 'Unbekannt'], details['author'])

        self.edit_book(11, content={'bookAuthor': "Hector Gonçalve"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        self.edit_book(11, content={'bookAuthor': "Hector Gonçalves & unbekannt"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        # rename uppercase to lowercase only of author
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & Hector gonçalves"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector gonçalves'], details['author'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt').replace('\\', '/')))
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Hector gonçalves/book9 (11)',
                                                    'book9 - Hector gonçalves.pdf').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Hector gonçalves/book9 (11)',
                                                    'cover.jpg').replace('\\', '/')))
        # Check that name of author folder no longer is "Hector Gonçalves"
        self.assertNotEqual("Hector Gonçalves",
                            fs.getinfo(os.path.join('test', 'Hector Gonçalves').replace('\\', '/')).name)

        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(11, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # rename book title and author in the same step
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & Hector Gonçalves",
                                   'book_title': 'Derbook 1'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Derbook 1', details['title'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Derbook 1 (1)',
                                                    'Derbook 1 - Frodo Beutlin.txt').replace('\\', '/')))
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Derbook 1 (1)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Hector Gonçalves/book9 (11)',
                                                    'book9 - Hector Gonçalves.pdf').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Hector Gonçalves/book9 (11)',
                                                    'cover.jpg').replace('\\', '/')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(11, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # rename only book title
        self.edit_book(1, content={'book_title': 'Der Buchtitel'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Der Buchtitel', details['title'])
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Hector Gonçalves/book9 (11)',
                                                    'book9 - Hector Gonçalves.pdf').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Hector Gonçalves/book9 (11)',
                                                    'cover.jpg').replace('\\', '/')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

    # Author rename co-author on 2 books
    def test_change_capital_rename_two_co_authors(self):
        fs = connect_gdrive("test")
        # check initial filenames
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt').replace('\\', '/')))
        # Add 2. author to book to have usecase
        self.edit_book(3, content={'bookAuthor': "Asterix Lionherd & Liu Yang"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Asterix Lionherd', 'Liu Yang'], details['author'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg').replace('\\', '/')))

        #rename co-author
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & liu Yang & Hector Gonçalves"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'liu Yang', 'Hector Gonçalves'], details['author'])
        details = self.get_book_details(3)
        self.assertEqual(['Asterix Lionherd', 'liu Yang'], details['author'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt').replace('\\', '/')))

        ret_code, content = self.download_book(3, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

        # rename book title and author in the same step
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & Hector Gonçalves",
                                   'book_title': 'Derbook 1'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Derbook 1', details['title'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Derbook 1 (1)',
                                                    'Derbook 1 - Frodo Beutlin.txt').replace('\\', '/')))
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Derbook 1 (1)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg').replace('\\', '/')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(3, "admin", "admin123")
        self.assertEqual(200, ret_code)
        self.edit_book(3, content={'bookAuthor': "Asterix Lionherd"})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Asterix Lionherd'], details['author'])

        # rename only book title
        self.edit_book(1, content={'book_title': 'Der Buchtitel'})
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])
        self.assertEqual('Der Buchtitel', details['title'])
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg').replace('\\', '/')))
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)

    def test_rename_capital_on_upload(self):
        fs = connect_gdrive("test")
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # Upload book with one author in database
        epub_file = os.path.join(base_path, 'files', 'title.epub')
        change_epub_meta(epub_file, meta={'title': "Useless", 'creator': "asterix Lionherd"})
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details()
        self.assertEqual('Useless', details['title'])
        self.assertEqual(['asterix Lionherd'], details['author'])
        self.assertTrue(fs.isfile(os.path.join('test', 'asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - asterix Lionherd.cbr').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg').replace('\\', '/')))
        ret_code, content = self.download_book(3, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(details['id'], "admin", "admin123")
        self.assertEqual(200, ret_code)

        self.delete_book(details['id'])
        time.sleep(WAIT_GDRIVE)
        self.edit_book(3, content={'bookAuthor': "Asterix Lionherd"})
        time.sleep(WAIT_GDRIVE)
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Asterix Lionherd'], details['author'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'comicdemo - Asterix Lionherd.cbr').replace('\\', '/')))
        self.assertTrue(fs.isfile(os.path.join('test', 'Asterix Lionherd/comicdemo (3)',
                                                    'cover.jpg').replace('\\', '/')))

        # Upload book with one co-author in database
        change_epub_meta(epub_file, meta={'title': "Useless", 'creator': 'liu yang'})
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(WAIT_GDRIVE)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(WAIT_GDRIVE)
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual('Useless', details['title'])
        self.assertEqual(['liu yang'], details['author'])
        ret_code, content = self.download_book(1, "admin", "admin123")
        self.assertEqual(200, ret_code)
        ret_code, content = self.download_book(details['id'], "admin", "admin123")
        self.assertEqual(200, ret_code)
        self.delete_book(details['id'])
        time.sleep(WAIT_GDRIVE)
        details = self.get_book_details(1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'liu yang', 'Hector Gonçalves'], details['author'])
        self.assertTrue(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'Der Buchtitel - Frodo Beutlin.txt').replace('\\', '/')))
        self.assertFalse(fs.isfile(os.path.join('test', 'Frodo Beutlin/Der Buchtitel (1)',
                                                    'cover.jpg').replace('\\', '/')))
        self.edit_book(1, content={'bookAuthor': "Frodo Beutlin & Norbert Halagal & Liu Yang & Hector Gonçalves"})
        time.sleep(WAIT_GDRIVE)
        self.assertFalse(self.check_element_on_page((By.ID, "flash_danger")))
        details = self.get_book_details(-1)
        self.assertEqual(['Frodo Beutlin', 'Norbert Halagal', 'Liu Yang', 'Hector Gonçalves'], details['author'])

        # ToDo: Upload file with multiple existing authors
        self.fill_basic_config({'config_uploading': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
