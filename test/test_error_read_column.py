# -*- coding: utf-8 -*-

from base_test import ParallelTestCase
import os

from selenium.webdriver.common.by import By
import time
from helper_db import delete_cust_class
from helper_func import startup
from helper_ui import RESTRICT_COL_USER


class TestErrorReadColumn(ParallelTestCase):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': cls.temp_dir},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):        
        cls.driver.get("http://127.0.0.1:" + cls.worker_port)
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        super().tearDownClass()

    def test_invalid_custom_read_column(self):
        self.fill_view_config({'config_read_column': "Custom Bool 1 Ä"})
        self.get_book_details(10)
        self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        delete_cust_class(os.path.join(self.temp_dir, "metadata.db"), 3)
        self.restart_calibre_web()
        self.goto_page("nav_read")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.goto_page("nav_new")
        self.goto_page("nav_unread")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.adv_search({"read_status": "Yes"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.adv_search({"read_status": "No"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.get_book_details(5)
        self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.get_book_details(5)
        self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.fill_view_config({'config_read_column': ""})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))

    def test_invalid_custom_column(self):
        self.fill_view_config({'config_restricted_column': "Custom Text 人物 *'()&"})
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": 'test'})
        restricts = self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('test', allow=False)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        delete_cust_class(os.path.join(self.temp_dir, "metadata.db"), 10)
        self.restart_calibre_web()
        self.goto_page("nav_read")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.goto_page("nav_new")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.goto_page("nav_lang")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
        self.fill_view_config({'config_restricted_column': "None"})
