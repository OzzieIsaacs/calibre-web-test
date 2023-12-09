#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from datetime import datetime, date
from unittest import TestCase
import time
import glob
import json
import unittest
import shutil

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import CALIBRE_WEB_PATH, TEST_DB, base_path, WAIT_GDRIVE, BOOT_TIME
from helper_func import startup, add_dependency, remove_dependency
from helper_func import save_logfiles, read_opf_metadata
from helper_gdrive import prepare_gdrive, connect_gdrive

RESOURCES = {'ports': 1, "gdrive": True}

PORTS = ['8083']
INDEX = ""


@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
class TestBackupMetadataGdrive(TestCase, ui_class):
    p=None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]


    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependency, cls.__name__)
        prepare_gdrive()
        try:
            src = os.path.join(base_path, "files", "client_secrets.json")
            dst = os.path.join(CALIBRE_WEB_PATH + INDEX, "client_secrets.json")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            # delete settings_yaml file
            set_yaml = os.path.join(CALIBRE_WEB_PATH + INDEX, "settings.yaml")
            if os.path.exists(set_yaml):
                os.unlink(set_yaml)

            # delete gdrive file
            gdrive_db = os.path.join(CALIBRE_WEB_PATH + INDEX, "gdrive.db")
            if os.path.exists(gdrive_db):
                os.unlink(gdrive_db)

            # delete gdrive authenticated file
            src = os.path.join(base_path, 'files', "gdrive_credentials")
            dst = os.path.join(CALIBRE_WEB_PATH + INDEX, "gdrive_credentials")
            os.chmod(src, 0o764)
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.copy(src, dst)

            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, only_metadata=True, index=INDEX, env={"APP_MODE": "test"})
            time.sleep(3)
            cls.fill_db_config({'config_use_google_drive': 1})
            time.sleep(2)
            cls.fill_db_config({'config_google_drive_folder': 'test'})
            time.sleep(2)
            cls.fill_thumbnail_config({'schedule_metadata_backup': 1})
            cls.restart_calibre_web()
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:"+ PORTS[0])
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        remove_dependency(cls.dependency)

        src1 = os.path.join(CALIBRE_WEB_PATH + INDEX, "client_secrets.json")
        src = os.path.join(CALIBRE_WEB_PATH + INDEX, "gdrive_credentials")
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

    def test_backup_gdrive(self):
        fs = connect_gdrive("test")
        remote_meta = os.path.join("test", "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        time.sleep(20)
        self.assertTrue(fs.isfile(remote_meta.replace('\\', '/')))
