#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import unittest
from unittest import TestCase
import time
import glob
from diffimg import diff
from io import BytesIO

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup, add_dependency, remove_dependency
from helper_func import save_logfiles

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

    def test_backup_change_book_title(self):
        pass

    def test_backup_change_book_author(self):
        pass

    def test_backup_change_book_series(self):
        pass

    def test_backup_change_book_seriesindex(self):
        pass

    def test_backup_change_book_publisher(self):
        pass

    def test_backup_change_book_publishing_date(self):
        pass

    def test_backup_change_book_tags(self):
        pass

    def test_backup_change_book_custom_bool(self):
        pass

    def test_backup_change_book_read_status(self):
        pass

    def test_grdive(self):
        pass
        # repeat all tests on gdrive