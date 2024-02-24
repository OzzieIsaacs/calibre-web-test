
from unittest import TestCase


import time

from helper_ui import ui_class
from config_test import TEST_DB, base_path, BOOT_TIME, SPLIT_LIB
from helper_func import startup
from helper_func import save_logfiles



RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


class TestSplitLibrary(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls,
                    cls.py_version,
                    {'config_calibre_dir': TEST_DB},
                    port=PORTS[0],
                    index=INDEX,
                    env={"APP_MODE": "test"},
                    split=True,
                    lib_path=SPLIT_LIB
                    )
            time.sleep(3)
            cls.fill_db_config({'config_calibre_split': 1, 'config_calibre_split_dir': SPLIT_LIB})
            time.sleep(3)
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

    # check cover visible
    # check thumbnail generation working
    def test_cover(self):
        tasks = self.check_tasks()
        pass

    # check ebook can be converted
    def test_convert_ebook(self):
        pass

    # check ebook can be emailed
    def test_email_ebook(self):
        pass

    # check kobo sync working
    def test_kobo(self):
        pass

    # check book can be renamed and is still found
    def test_change_ebook(self):
        pass

    def test_upload_ebook(self):
        pass