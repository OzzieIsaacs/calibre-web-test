#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from base_test import ParallelTestCase
import time
import unittest
import shutil

from config_test import base_path
from helper_func import startup, add_dependency, remove_dependency
from helper_gdrive import prepare_gdrive, connect_gdrive
import datetime


@unittest.skipIf(not os.path.exists(os.path.join(base_path, "files", "client_secrets.json")) or
                 not os.path.exists(os.path.join(base_path, "files", "gdrive_credentials")),
                 "client_secrets.json and/or gdrive_credentials file is missing")
class TestBackupMetadataGdrive(ParallelTestCase):
    resource_lock = "gdrive"
    p=None
    driver = None
    dependency = ["oauth2client", "PyDrive2", "PyYAML", "google-api-python-client", "httplib2"]


    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version,
                    {'config_calibre_dir': cls.temp_dir},
                    only_metadata=True,
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    lib_dest=cls.temp_dir,
                    env={"APP_MODE": "test","CALIBRE_PORT": cls.worker_port}
                    )
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
        cls.driver.get("http://127.0.0.1:"+ cls.worker_port)
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()

        src1 = os.path.join(cls.app_dir, "client_secrets.json")
        src = os.path.join(cls.app_dir, "gdrive_credentials")
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
        super().tearDownClass()

    def test_backup_gdrive(self):
        fs = connect_gdrive("test")
        remote_meta = os.path.join("test", "Asterix Lionherd", "comicdemo (3)", "metadata.opf")
        # generate all metadata.opf files
        self.queue_metadata_backup()
        self.restart_calibre_web()
        # check tags content of metadata.opf file
        time.sleep(20)
        self.assertTrue(fs.isfile(remote_meta.replace('\\', '/')))
