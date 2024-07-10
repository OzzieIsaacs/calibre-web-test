#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from datetime import date
from unittest import TestCase
import time
import glob
import json

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB, base_path, BOOT_TIME
from helper_func import startup
from helper_func import save_logfiles, read_opf_metadata

RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


class TestBackupMetadata(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, port=PORTS[0], index=INDEX, env={"APP_MODE": "test"})
            time.sleep(3)
            cls.fill_thumbnail_config({'schedule_metadata_backup': 1})
            # cls.restart_calibre_web()
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:" + PORTS[0])
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_backup_all(self):
        # press backup all
        ref = self.check_tasks()
        self.queue_metadata_backup()
        count, tasks = self.check_tasks(ref)
        self.assertEqual(1, count)
        self.restart_calibre_web()
        res = self.check_tasks()
        self.assertEqual(1, len(res))
        # check alle opf files present
        all_files = glob.glob(TEST_DB + '/**/*.opf', recursive=True)
        self.assertEqual(11, len(all_files))
        # alle opf daten löschen
        for f in all_files:
            os.unlink(f)
        # Gesamt Ordner Schreibrechte entziehen -> geht nicht, da nach Neustart Datenbank nicht gelesen werden kann
        rights = os.stat(TEST_DB).st_mode & 0o777
        os.chmod(TEST_DB, 0o500)
        # backup all drücken
        self.queue_metadata_backup()
        # müsste Fehlermeldung geben
        count, tasks = self.check_tasks(res)
        self.assertEqual(1, count)
        self.assertEqual(tasks[-1]['result'], "Failed")
        # Gesamt Ordner Schreibrechte geben
        os.chmod(TEST_DB, rights)
        # einem Author ordner Schreibrechte entziehen
        author_path = os.path.join(TEST_DB, "Asterix Lionherd")
        rights = os.stat(author_path).st_mode & 0o777
        os.chmod(author_path, 0o400)
        # backup all drücken
        self.queue_metadata_backup()
        count, tasks = self.check_tasks(res)
        self.assertEqual(tasks[-1]['result'], "Finished")
        self.restart_calibre_web()
        # müsste Fehlermeldung geben
        tasks = self.check_tasks()
        self.assertEqual(1, len(tasks))
        self.assertEqual(tasks[-1]['result'], "Failed")
        # Author Ordner Schreibrechte geben
        os.chmod(author_path, rights)
        # einem Buch Ordner Schreibrechte entziehen
        book_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)")
        rights = os.stat(author_path).st_mode & 0o777
        os.chmod(book_path, 0o400)
        # backup all drücken
        self.queue_metadata_backup()
        count, tasks = self.check_tasks(res)
        self.assertEqual(tasks[-1]['result'], "Finished")
        self.restart_calibre_web()
        # müsste Fehlermeldung geben
        tasks = self.check_tasks()
        self.assertEqual(1, len(tasks))
        self.assertEqual(tasks[-1]['result'], "Failed")
        # Buch Ordner Schreibrechte wieder geben
        os.chmod(book_path, rights)

    def test_backup_change_book_series_index(self):
        meta_path = os.path.join(TEST_DB, "Frodo Beutlin", "Der Buchtitel (1)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check series_index content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        # edit series_index
        self.assertEqual(metadata['series_index'], "")
        self.assertEqual(metadata['series'], "")
        self.edit_book(1, content={'series_index':'1.53'})
        # restart cw
        time.sleep(2)
        self.restart_calibre_web()
        # check series_index content of metadata.opf file -> as long as no series is set, the index is not present
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['series_index'], "")
        self.assertEqual(metadata['series'], "")
        self.edit_book(1, content={'series':'test'})
        # restart cw
        time.sleep(2)
        self.restart_calibre_web()
        # check series_index content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['series_index']['content'], "1.53")
        self.assertEqual(metadata['series']['content'], "test")
        self.edit_book(1, content={'series': 'tEst', 'series_index':'1.0'})
        # restart cw
        time.sleep(2)
        self.restart_calibre_web()
        # check series_index content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['series']['content'], "tEst")
        self.assertEqual(metadata['series_index']['content'], "1.0")
        self.edit_book(1, content={'series': 't,st'})
        # restart cw
        time.sleep(2)
        self.restart_calibre_web()
        # check series_index content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['series']['content'], "t,st")
        self.edit_book(1, content={'series': ''})

    def test_backup_change_book_publisher(self):
        meta_path = os.path.join(TEST_DB, "Frodo Beutlin", "Der Buchtitel (1)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check publisher content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['publisher'], "")
        # edit Publisher
        self.edit_book(1, content={'publisher':'Lo,执|1u'})
        time.sleep(2)
        self.restart_calibre_web()
        # check series_index content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['publisher'], 'Lo,执|1u')
        self.edit_book(1, content={'publisher': ''})

    def test_backup_change_book_title(self):
        meta_path = os.path.join(TEST_DB, "John Doe", "Buuko (7)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check publisher content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['title'], "Buuko")
        # edit Title
        self.edit_book(7, content={'book_title':'The bok Lo,执|1u'})
        time.sleep(2)
        self.restart_calibre_web()
        # check title content of metadata.opf file
        metadata = read_opf_metadata(os.path.join(TEST_DB, "John Döe", "The bok Lo,执,1u (7)", "metadata.opf"))
        self.assertEqual(metadata['title'], 'The bok Lo,执|1u')
        self.edit_book(7, content={'book_title': 'Buuko'})

    def test_backup_change_book_author(self):
        meta_path = os.path.join(TEST_DB, "Frodo Beutlin", "Der Buchtitel (1)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check author content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(["Frodo Beutlin","Norbert Halagal","Liu Yang","Hector Gonçalves"], metadata['author'])
        self.assertEqual("Beutlin, Frodo & Halagal, Norbert & Yang, Liu & Gonçalves, Hector", metadata['author_attr'][0]['opf:file-as'])
        # edit author
        self.edit_book(1, content={'bookAuthor': 'Frodo Beutlin & Norbert Halagal & Hector Gonçalves'})
        time.sleep(2)
        self.restart_calibre_web()
        # check author content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(["Frodo Beutlin","Norbert Halagal", "Hector Gonçalves"], metadata['author'])
        self.assertEqual("Beutlin, Frodo & Halagal, Norbert & Gonçalves, Hector", metadata['author_attr'][0]['opf:file-as'])
        self.edit_book(1, content={'bookAuthor': 'Hector Gonçalves'})
        time.sleep(2)
        self.restart_calibre_web()
        time.sleep(3)
        metadata = read_opf_metadata(os.path.join(TEST_DB, "Hector Gonçalves", "Der Buchtitel (1)", "metadata.opf"))
        self.assertEqual(["Hector Gonçalves"], metadata['author'])
        self.assertEqual("Gonçalves, Hector", metadata['author_attr'][0]['opf:file-as'])
        self.edit_book(1, content={'bookAuthor': 'Frodo Beutlin & Norbert Halagal & Liu Yang & Hector Gonçalves'})

    def test_backup_change_book_publishing_date(self):
        meta_path = os.path.join(TEST_DB, "Hector Goncalves", "book9 (11)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['pub_date'].date(), date(101, 1, 1))
        # edit Publisher
        self.edit_book(11, content={'pubdate': '3/6/2023'})
        time.sleep(2)
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['pub_date'].date(), date(2023, 6, 3))
        self.edit_book(11, content={'pubdate': ''})

    def test_backup_change_book_tags(self):
        meta_path = os.path.join(TEST_DB, "Peter Parker", "Very long extra super turbo cool tit (4)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['tags'], [])
        # edit tags
        self.edit_book(4, content={'tags': 'Lo执|1u'})
        time.sleep(2)
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['tags'], ['Lo执|1u'])
        self.edit_book(4, content={'tags': 'Ku,kOl'})
        time.sleep(2)
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertCountEqual(metadata['tags'], ['Ku','kOl'])
        self.edit_book(4, content={'tags': ''})

    def test_backup_change_book_identifier(self):
        meta_path = os.path.join(TEST_DB, "Peter Parker", "Very long extra super turbo cool tit (4)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check identifier content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(len(metadata['identifier']), 2)
        # edit Identifier
        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.add_identifier('Hallo', 'Lo执|1u')
        self.check_element_on_page((By.ID, "submit")).click()
        time.sleep(2)
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(len(metadata['identifier']), 3)
        self.assertEqual(metadata['identifier'][2].contents, ["Lo执|1u"])
        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.delete_identifier("Hallo")
        self.check_element_on_page((By.ID, "submit")).click()
        time.sleep(2)
        self.restart_calibre_web()
        # check identifier content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(len(metadata['identifier']), 2)

    def test_backup_change_book_language(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['language'], ["en"])
        # edit Language
        self.edit_book(3, content={'languages': 'German, English'})
        time.sleep(2)
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertCountEqual(metadata['language'], ["eng", "deu"])
        self.edit_book(3, content={'languages': 'Italian'})
        time.sleep(2)
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['language'], ["ita"])
        self.edit_book(3, content={'languages': ''})

    def test_backup_change_book_rating(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['rating'], "")
        # edit ratings
        self.edit_book(3, content={'rating': 3})
        time.sleep(2)
        self.restart_calibre_web()
        # check ratings content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertCountEqual(metadata['rating']['content'], "6")
        self.edit_book(3, content={'rating': 0})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['rating'], "")

    def test_backup_change_book_description(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['description'], "")
        # edit description
        self.edit_book(3, content={'description': "<strong>Test</strong>"})
        time.sleep(2)
        self.restart_calibre_web()
        # check description content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertCountEqual(metadata['description'], "<p><strong>Test</strong></p>")
        self.edit_book(3, content={'description': ""})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        time.sleep(1)
        self.assertEqual(metadata['description'], "")

    def test_backup_change_custom_bool(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_1']['content'])
        self.assertEqual(custom["datatype"], "bool")
        self.assertEqual(custom["name"], "Custom Bool 1 Ä")
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)
        # edit custom column
        self.edit_book(3, custom_content={'Custom Bool 1 Ä': 'Yes'})
        time.sleep(2)
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        time.sleep(2)
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_1']['content'])
        self.assertEqual(custom["#value#"], True)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Bool 1 Ä': 'No'})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_1']['content'])
        self.assertEqual(custom["#value#"], False)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Bool 1 Ä': ''})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_1']['content'])
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)

    def test_backup_change_custom_float(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_5']['content'])
        self.assertEqual(custom["datatype"], "float")
        self.assertEqual(custom["name"], "Custom Float 人物")
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)
        # edit custom column
        self.edit_book(3, custom_content={'Custom Float 人物': '3.33'})
        time.sleep(2)
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_5']['content'])
        self.assertEqual(custom["#value#"], 3.33)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Float 人物': '-34'})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_5']['content'])
        self.assertEqual(custom["#value#"], -34.0)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Float 人物': ''})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_5']['content'])
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)

    def test_backup_change_custom_int(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_4']['content'])
        self.assertEqual(custom["datatype"], "int")
        self.assertEqual(custom["name"], "Custom Integer 人物")
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)
        # edit custom column
        self.edit_book(3, custom_content={'Custom Integer 人物': '213213123'})
        time.sleep(2)
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_4']['content'])
        self.assertEqual(custom["#value#"], 213213123)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Integer 人物': '-34213213123'})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_4']['content'])
        self.assertEqual(custom["#value#"], -34213213123)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Integer 人物': ''})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_4']['content'])
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)

    def test_backup_change_custom_rating(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_3']['content'])
        self.assertEqual(custom["datatype"], "rating")
        self.assertEqual(custom["name"], "Custom Rating 人物")
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)
        # edit custom column
        self.edit_book(3, custom_content={'Custom Rating 人物': '3.5'})
        time.sleep(2)
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_3']['content'])
        self.assertEqual(custom["#value#"], 7)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Rating 人物': ''})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_3']['content'])
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)

    def test_backup_change_custom_text(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_10']['content'])
        self.assertEqual(custom["datatype"], "text")
        self.assertEqual(custom["name"], "Custom Text 人物 *'()&")
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)
        # edit custom column
        self.edit_book(3, custom_content={"Custom Text 人物 *'()&": "人物 *'(}\""})
        time.sleep(2)
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_10']['content'])
        self.assertEqual(custom["#value#"], "人物 *'(}\"")
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={"Custom Text 人物 *'()&": ''})
        time.sleep(5)
        self.restart_calibre_web()
        time.sleep(2)
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_10']['content'])
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)

    def test_backup_change_custom_date(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_2']['content'])
        self.assertEqual(custom["datatype"], "datetime")
        self.assertEqual(custom["name"], "Custom Date Column 人物")
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)
        # edit custom column
        self.edit_book(3, custom_content={"Custom Date Column 人物": "3/8/2023"})
        time.sleep(2)
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_2']['content'])
        self.assertEqual(custom["#value#"]['__class__'], "datetime.datetime")
        self.assertEqual(custom["#value#"]['__value__'], "2023-08-03T00:00:00+00:00")
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={"Custom Date Column 人物": ''})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_2']['content'])
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)

    def test_backup_change_custom_Comment(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        time.sleep(2)
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_8']['content'])
        self.assertEqual(custom["datatype"], "comments")
        self.assertEqual(custom["name"], "Custom Comment 人物")
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)
        # edit custom column
        self.edit_book(3, custom_content={"Custom Comment 人物": "<strong>Test</strong>"})
        time.sleep(2)
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_8']['content'])
        self.assertEqual(custom["#value#"], "<p><strong>Test</strong></p>")
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={"Custom Comment 人物": ''})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_8']['content'])
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)

    def test_backup_change_custom_categories(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_9']['content'])
        self.assertEqual(custom["datatype"], "text")
        self.assertEqual(custom["name"], "Custom categories\|, 人物")
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)
        self.assertEqual(custom["is_multiple"], "|")
        self.assertEqual(custom["is_multiple2"], {"cache_to_list": "|", "ui_to_list": ",", "list_to_ui": ", "})
        # edit custom column
        self.edit_book(3, custom_content={"Custom categories\|, 人物": "Kulo, Smudo"})
        time.sleep(2)
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_9']['content'])
        self.assertCountEqual(custom["#value#"], ["Kulo", "Smudo"])
        self.assertEqual(custom["#extra#"], None)
        self.assertEqual(custom["is_multiple"], "|")
        self.assertEqual(custom["is_multiple"], "|")
        self.assertEqual(custom["is_multiple2"], {"cache_to_list": "|", "ui_to_list": ",", "list_to_ui": ", "})
        self.edit_book(3, custom_content={"Custom categories\|, 人物": ''})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_9']['content'])
        self.assertEqual(custom["is_multiple"], "|")
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)
        self.assertEqual(custom["is_multiple2"], {"cache_to_list": "|", "ui_to_list": ",", "list_to_ui": ", "})

    def test_backup_change_custom_Enum(self):
        meta_path = os.path.join(TEST_DB, "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_6']['content'])
        self.assertEqual(custom["datatype"], "enumeration")
        self.assertEqual(custom["name"], "Custom 人物 Enum")
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)
        self.assertEqual(custom["display"], {"enum_colors": [],
                                             "enum_values": ["Alfa", "人物", "Huji"],
                                             "description": "Enum Colum 人物",
                                             "use_decorations": 0})
        # edit custom column
        self.edit_book(3, custom_content={"Custom 人物 Enum": "Huji"})
        time.sleep(2)
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_6']['content'])
        self.assertEqual(custom["#value#"], "Huji")
        self.assertEqual(custom["#extra#"], None)
        self.assertEqual(custom["display"], {"enum_colors": [],
                                             "enum_values": ["Alfa", "人物", "Huji"],
                                             "description": "Enum Colum 人物",
                                             "use_decorations": 0})
        self.edit_book(3, custom_content={"Custom 人物 Enum": ''})
        time.sleep(2)
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_6']['content'])
        self.assertEqual(custom["#value#"], None)
        self.assertEqual(custom["#extra#"], None)

    def test_upload_book(self):
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        epub_file = os.path.join(base_path, 'files', 'book.epub')
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.restart_calibre_web()
        meta_path = os.path.join(TEST_DB, details['author'][0], details['title']+ " (15)", "metadata.opf")
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['title'], details['title'])
        self.delete_book(details['id'])
        self.fill_basic_config({'config_uploading': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
