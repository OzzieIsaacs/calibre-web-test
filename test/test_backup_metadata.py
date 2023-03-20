#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from datetime import datetime, date
from unittest import TestCase
import time
import glob
from bs4 import BeautifulSoup
import codecs
import json

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB, base_path, BOOT_TIME
from helper_func import startup, add_dependency, remove_dependency
from helper_func import save_logfiles


def read_opf_metadata(filename):
    result = {}
    with codecs.open(filename, "r", "utf-8") as f:
        soup = BeautifulSoup(f.read(), "xml")
    result['identifier'] = soup.findAll("identifier")
    cover = soup.find("reference")
    result['cover'] = cover.attrs if cover else ""
    title = soup.find("dc:title")
    result['title'] = title.contents[0] if title else ""
    author = soup.findAll("dc:creator")
    result['author'] = [a.contents[0] for a in author]
    result['author_attr'] = [a.attrs for a in author]
    contributor = soup.find("dc:contributor")
    if contributor:
        result['contributor'] = contributor.contents
        result['contributor_attr'] = contributor.attrs
    else:
        result['contributor'] = ""
        result['contributor_attr'] = ""
    result['pub_date'] = datetime.strptime(soup.find("dc:date").contents[0], "%Y-%m-%dT%H:%M:%S")
    language = soup.findAll("dc:language")
    result['language'] = [lang.contents[0] for lang in language] if language else []
    publisher = soup.find("dc:publisher")
    result['publisher'] = publisher.contents[0] if publisher else ""
    tags = soup.findAll("dc:subject")
    result['tags'] = [t.contents[0] for t in tags] if tags else []
    comment = soup.find("dc:description")
    result['description'] = comment.contents[0] if comment else ""
    series_index = soup.find("meta", {"name": "calibre:series_index"})
    result['series_index'] = series_index.attrs if series_index else ""
    author_link_map = soup.find("meta", {"name": "calibre:author_link_map"})
    result['author_link_map'] = author_link_map.attrs if author_link_map else ""
    series = soup.find("meta", {"name": "calibre:series"})
    result['series'] = series.attrs if series else ""
    rating = soup.find("meta", {"name": "calibre:rating"})
    result['rating'] = rating.attrs if rating else ""
    result['timestamp'] = datetime.strptime(soup.find("meta", {"name": "calibre:timestamp"}).attrs['content'],
                                            "%Y-%m-%dT%H:%M:%S")
    title_sort = soup.find("meta", {"name": "calibre:title_sort"})
    result['title_sort'] = title_sort.attrs if title_sort else ""
    custom_1 = soup.find("meta", {"name": "calibre:user_metadata:#cust1"})
    result['custom_1'] = custom_1.attrs if custom_1 else ""
    custom_2 = soup.find("meta", {"name": "calibre:user_metadata:#cust2"})
    result['custom_2'] = custom_2.attrs if custom_2 else ""
    custom_3 = soup.find("meta", {"name": "calibre:user_metadata:#cust3"})
    result['custom_3'] = custom_3.attrs if custom_3 else ""
    custom_4 = soup.find("meta", {"name": "calibre:user_metadata:#cust4"})
    result['custom_4'] = custom_4.attrs if custom_4 else ""
    custom_5 = soup.find("meta", {"name": "calibre:user_metadata:#cust5"})
    result['custom_5'] = custom_5.attrs if custom_5 else ""
    custom_6 = soup.find("meta", {"name": "calibre:user_metadata:#cust6"})
    result['custom_6'] = custom_6.attrs if custom_6 else ""
    custom_7 = soup.find("meta", {"name": "calibre:user_metadata:#cust7"})
    result['custom_7'] = custom_7.attrs if custom_7 else ""
    custom_8 = soup.find("meta", {"name": "calibre:user_metadata:#cust8"})
    result['custom_8'] = custom_8.attrs if custom_8 else ""
    custom_9 = soup.find("meta", {"name": "calibre:user_metadata:#cust9"})
    result['custom_9'] = custom_9.attrs if custom_9 else ""
    return result


@unittest.SkipTest
class TestBackupMetadata(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, env={"APP_MODE": "test"})
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_backup_all(self):
        # backup all drücken
        ref = self.check_tasks()
        self.queue_metadata_backup()
        count, tasks = self.check_tasks(ref)
        self.assertEqual(1, count)
        self.restart_calibre_web()
        res = self.check_tasks()
        self.assertEqual(1, len(res))
        # schauen das alle opd dateien vorhanden sind
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

    def test_backup_change_book_seriesindex(self):
        meta_path = os.path.join(TEST_DB, "Frodo Beutlin", "Der Buchtitel (1)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check seriesindex content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        # edit seriesindex
        self.assertEqual(metadata['series_index'], "")
        self.assertEqual(metadata['series'], "")
        self.edit_book(1, content={'series_index':'1.53'})
        # restart cw
        self.restart_calibre_web()
        # check seriesindex content of metadata.opf file -> as long as no series is set, the index is not present
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['series_index'], "")
        self.assertEqual(metadata['series'], "")
        self.edit_book(1, content={'series':'test'})
        # restart cw
        self.restart_calibre_web()
        # check seriesindex content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['series_index']['content'], "1.53")
        self.assertEqual(metadata['series']['content'], "test")
        self.edit_book(1, content={'series': 'tEst', 'series_index':'1.0'})
        # restart cw
        self.restart_calibre_web()
        # check seriesindex content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['series']['content'], "tEst")
        self.assertEqual(metadata['series_index']['content'], "1.0")
        self.edit_book(1, content={'series': 't,st'})
        # restart cw
        self.restart_calibre_web()
        # check seriesindex content of metadata.opf file
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
        self.restart_calibre_web()
        # check seriesindex content of metadata.opf file
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
        self.restart_calibre_web()
        # check title content of metadata.opf file
        metadata = read_opf_metadata(os.path.join(TEST_DB, "John Döe", "The bok Lo,执,1u (7)", "metadata.opf"))
        self.assertEqual(metadata['title'], 'The bok Lo,执|1u')
        self.edit_book(7, content={'title': 'Buuko'})

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
        self.restart_calibre_web()
        # check author content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(["Frodo Beutlin","Norbert Halagal", "Hector Gonçalves"], metadata['author'])
        self.assertEqual("Beutlin, Frodo & Halagal, Norbert & Gonçalves, Hector", metadata['author_attr'][0]['opf:file-as'])
        self.edit_book(1, content={'bookAuthor': 'Hector Gonçalves'})
        self.restart_calibre_web()
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
        # edit Publisher
        self.edit_book(4, content={'tags': 'Lo执|1u'})
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertEqual(metadata['tags'], ['Lo执|1u'])
        self.edit_book(4, content={'tags': 'Ku,kOl'})
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertCountEqual(metadata['tags'], ['Ku','kOl'])
        self.edit_book(4, content={'tags': ''})

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
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertCountEqual(metadata['language'], ["eng", "deu"])
        self.edit_book(3, content={'languages': 'Italian'})
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
        self.restart_calibre_web()
        # check ratings content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertCountEqual(metadata['rating']['content'], "6")
        self.edit_book(3, content={'rating': 0})
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
        self.restart_calibre_web()
        # check description content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        self.assertCountEqual(metadata['description'], "<p><strong>Test</strong></p>")
        self.edit_book(3, content={'description': ""})
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
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
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_1']['content'])
        self.assertEqual(custom["#value#"], True)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Bool 1 Ä': 'No'})
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_1']['content'])
        self.assertEqual(custom["#value#"], False)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Bool 1 Ä': ''})
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
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_5']['content'])
        self.assertEqual(custom["#value#"], 3.33)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Float 人物': '-34'})
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_5']['content'])
        self.assertEqual(custom["#value#"], -34.0)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Float 人物': ''})
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
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_4']['content'])
        self.assertEqual(custom["#value#"], 213213123)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Integer 人物': '-34213213123'})
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_4']['content'])
        self.assertEqual(custom["#value#"], -34213213123)
        self.assertEqual(custom["#extra#"], -None)
        self.edit_book(3, custom_content={'Custom Integer 人物': ''})
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
        self.restart_calibre_web()
        # check custom column content of metadata.opf file
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_3']['content'])
        self.assertEqual(custom["#value#"], 7)
        self.assertEqual(custom["#extra#"], None)
        self.edit_book(3, custom_content={'Custom Rating 人物': ''})
        self.restart_calibre_web()
        metadata = read_opf_metadata(meta_path)
        custom = json.loads(metadata['custom_3']['content'])
        #self.assertEqual(custom["#value#"], None)
        #self.assertEqual(custom["#extra#"], None)

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

    def test_gdrive(self):
        pass
        # repeat all tests on gdrive