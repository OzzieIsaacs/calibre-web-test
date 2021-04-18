#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase, skip
import os
import time
import requests
import random
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from helper_ui import ui_class
from config_test import TEST_DB, base_path
from helper_func import startup, debug_startup
from helper_func import save_logfiles

def user_change(user):
    r = requests.session()
    payload = {'username': user, 'password': "1234", 'submit': "", 'next': "/"}
    r.post('http://127.0.0.1:8083/login', data=payload)
    # random.seed(123)
    for i in range(0, 200):
        time.sleep(random.random() * 0.05)
        parameter = int(random.uniform(2, 260))
        userload = {'name': user,
                    'email': "",
                    'password': "",
                    'locale': "en",
                    'default_language': "all",
                    }
        for bit_shift in range(1, 16):
            if (parameter >> bit_shift) & 1:
                userload['show_'+ str(1 << bit_shift)] = "on"
        resp = r.post('http://127.0.0.1:8083/me', data=userload)
        if resp.status_code != 200:
            print('Error: ' + user)
            break
    r.close()
    print('Finished: ' + user)


class TestUserList(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            debug_startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB})
            time.sleep(3)
            # cls.mass_create_users(1)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        try:
            pass # cls.stop_calibre_web()
        except:
            #cls.driver.get("http://127.0.0.1:8083")
            #time.sleep()
            try:
                cls.stop_calibre_web()
            except:
                pass
        # close the browser window and stop calibre-web
        cls.driver.quit()
        #cls.p.terminate()
        #save_logfiles(cls, cls.__name__)

    def check_search(self, bl, term, count, column, value):
        bl['search'].clear()
        bl['search'].send_keys(term)
        bl['search'].send_keys(Keys.RETURN)
        time.sleep(1)
        bl = self.get_user_table(-1)
        self.assertEqual(count, len(bl['table']))
        self.assertEqual(value, bl['table'][0][column]['text'])
        return bl

    @classmethod
    def mass_create_users(cls, count):
        cls.create_user('no_one', {'password': '1234', 'email': 'muki1al@b.com', 'kindle_mail': 'muki1al@b.com'})
        cls.create_user('no_two', {'password': '1234', 'email': 'muki2al@b.com', "download_role": 1, "locale":"Deutsch"})
        cls.create_user('no_three', {'password': '1234', 'email': 'muki3al@b.com', 'kindle_mail': 'm11uklial@bds.com'})
        cls.create_user('no_four', {'password': '1234', 'email': 'muki4al@b.com', "download_role": 1, 'show_16': 1, "upload_role":1})
        cls.create_user('no_5', {'password': '1234', 'email': 'muki5al@b.com', 'kindle_mail': 'muki5al@bad.com'})
        cls.create_user('no_6', {'password': '1234', 'email': 'muki6al@b.com', "edit_role": 1, "locale":"Italiano", 'show_16': 1})
        cls.create_user('no_1', {'password': '1234', 'email': 'muki7al@b.com', "locale": "Polski", "passwd_role":1})
        cls.create_user('1_no', {'password': '1234', 'email': 'muki8al@b.com', 'kindle_mail': 'muki8al@bcd.com', "admin_role":1})
        cls.create_user('2_no', {'password': '1234', 'email': 'muki9al@b.com', "edit_role": 1, 'default_language': "English"})
        cls.create_user('3_no', {'password': '1234', 'email': 'muki10al@b.com', 'kindle_mail': 'muki1al@b.com', 'default_language': "Norwegian Bokmål"})
        for i in range(0, count):
            cls.create_user('user_' + str(count), {'password': '1234', 'email': str(count) + 'al@b.com'})

    def test_user_list_edit_button(self):
        ul = self.get_user_table(2)
        self.assertEqual("3_no", ul['table'][0]['Username']['text'])
        ul['table'][0]['Edit']['element'].click()
        name = self.check_element_on_page((By.ID, "name"))
        self.assertEqual("3_no", name.get_attribute('value'))
        self.check_element_on_page((By.ID, "back")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "user_delete_selection")), "Press cancel in User edit leads not back to user table")

    # change visibility of some columns
    # goto other page, return to books list, check if visibility is same
    def test_list_visibility(self):
        ul = self.get_user_table(1)
        self.assertTrue(ul['column'])
        ul['column'].click()
        self.assertEqual(33, len(ul['column_elements']))
        self.assertEqual(34, len(ul['table'][0]))
        for indx, element in enumerate(ul['column_elements']):
            if element.is_selected():
                if not ul['column_texts'][indx].text in ul['table'][0]:
                    self.assertTrue("role_" + ul['column_texts'][indx].text in ul['table'][0])
        ul['column_elements'][0].click()
        ul['column_elements'][1].click()
        ul['column_elements'][2].click()
        ul['column_elements'][3].click()
        ul['column_elements'][4].click()
        ul['column_elements'][5].click()
        ul['column_elements'][6].click()
        ul['column_elements'][7].click()
        ul['column_elements'][8].click()
        ul['column_elements'][9].click()
        ul['column_elements'][10].click()
        ul = self.get_user_table(2)
        self.assertTrue(ul['column'])
        ul['column'].click()
        self.assertEqual(33, len(ul['column_elements']))
        self.assertEqual(23, len(ul['table'][0]))
        self.assertFalse(ul['column_elements'][0].is_selected())
        self.assertFalse(ul['column_elements'][1].is_selected())
        self.assertFalse(ul['column_elements'][2].is_selected())
        self.assertFalse(ul['column_elements'][3].is_selected())
        self.assertFalse(ul['column_elements'][4].is_selected())
        self.assertFalse(ul['column_elements'][5].is_selected())
        self.assertFalse(ul['column_elements'][6].is_selected())
        self.assertFalse(ul['column_elements'][7].is_selected())
        self.assertFalse(ul['column_elements'][8].is_selected())
        self.assertFalse(ul['column_elements'][9].is_selected())
        self.assertFalse(ul['column_elements'][10].is_selected())
        ul['column_elements'][0].click()
        ul['column_elements'][1].click()
        ul['column_elements'][2].click()
        ul['column_elements'][3].click()
        ul['column_elements'][4].click()
        ul['column_elements'][5].click()
        ul['column_elements'][6].click()
        ul['column_elements'][7].click()
        ul['column_elements'][8].click()
        ul['column_elements'][9].click()
        ul['column_elements'][10].click()
        ul = self.get_user_table(1)
        self.assertEqual(34, len(ul['table'][0]))

    def test_user_list_edit_name(self):
        ul = self.get_user_table(1)
        self.assertTrue("no_one", ul['table'][1]['Username']['text'])
        self.edit_table_element(ul['table'][1]['Username']['element'], "nu_one")
        ul = self.get_user_table(-1)
        self.assertEqual("nu_one", ul['table'][1]['Username']['text'])
        self.edit_table_element(ul['table'][1]['Username']['element'], "no_two")
        self.assertTrue("already taken" in self.check_element_on_page((By.XPATH,
                                                          "//div[contains(@class,'editable-error-block')]")).text)
        self.check_element_on_page((By.XPATH, "//button[contains(@class,'editable-cancel')]")).click()

        self.edit_table_element(ul['table'][1]['Username']['element'], "")
        self.assertTrue("This Field is Required" in self.check_element_on_page((By.XPATH,
                                                          "//div[contains(@class,'editable-error-block')]")).text)
        self.check_element_on_page((By.XPATH, "//button[contains(@class,'editable-cancel')]")).click()
        self.edit_table_element(ul['table'][1]['Username']['element'], "no_one")
        ul = self.get_user_table(-1)
        self.assertTrue("no_one", ul['table'][1]['Username']['text'])


    def test_user_list_edit_email(self):
        ul = self.get_user_table(1)
        self.assertTrue("muki1al@b.com", ul['table'][1]['E-mail Address']['text'])
        self.edit_table_element(ul['table'][1]['E-mail Address']['element'], "nuki1al@b.com")
        ul = self.get_user_table(-1)
        self.assertEqual("nuki1al@b.com", ul['table'][1]['E-mail Address']['text'])
        self.edit_table_element(ul['table'][1]['E-mail Address']['element'], "no_email")
        self.assertTrue("Invalid e-mail" in self.check_element_on_page((By.XPATH,
                                                          "//div[contains(@class,'editable-error-block')]")).text)
        self.check_element_on_page((By.XPATH, "//button[contains(@class,'editable-cancel')]")).click()

        self.edit_table_element(ul['table'][1]['E-mail Address']['element'], "muki2al@b.com")
        self.assertTrue("existing account" in self.check_element_on_page((By.XPATH,
                                                          "//div[contains(@class,'editable-error-block')]")).text)
        self.check_element_on_page((By.XPATH, "//button[contains(@class,'editable-cancel')]")).click()
        self.edit_table_element(ul['table'][1]['E-mail Address']['element'], "")
        self.assertTrue("This Field is Required" in self.check_element_on_page((By.XPATH,
                                                          "//div[contains(@class,'editable-error-block')]")).text)
        self.check_element_on_page((By.XPATH, "//button[contains(@class,'editable-cancel')]")).click()
        self.edit_table_element(ul['table'][1]['E-mail Address']['element'], " kin@de.de ")
        ul = self.get_user_table(-1)
        self.assertEqual("kin@de.de", ul['table'][1]['E-mail Address']['text'])
        self.edit_table_element(ul['table'][1]['E-mail Address']['element'], "muki1al@b.com")
        ul = self.get_user_table(-1)
        self.assertTrue("muki1al@b.com", ul['table'][1]['E-mail Address']['text'])

    def test_user_list_edit_kindle(self):
        ul = self.get_user_table(1)
        self.assertTrue("muki1al@b.com", ul['table'][1]['Kindle E-mail']['text'])
        self.edit_table_element(ul['table'][1]['Kindle E-mail']['element'], "nuki1al@b.com")
        ul = self.get_user_table(-1)
        self.assertEqual("nuki1al@b.com", ul['table'][1]['Kindle E-mail']['text'])
        self.edit_table_element(ul['table'][1]['Kindle E-mail']['element'], "no_email")
        self.assertTrue("Invalid e-mail" in self.check_element_on_page((By.XPATH,
                                                          "//div[contains(@class,'editable-error-block')]")).text)
        self.check_element_on_page((By.XPATH, "//button[contains(@class,'editable-cancel')]")).click()
        self.edit_table_element(ul['table'][1]['Kindle E-mail']['element'], "")
        ul = self.get_user_table(-1)
        self.assertEqual("+", ul['table'][1]['Kindle E-mail']['text'])
        self.edit_table_element(ul['table'][1]['Kindle E-mail']['element'], "muki1al@b.com")
        ul = self.get_user_table(-1)
        self.assertTrue("muki1al@b.com", ul['table'][1]['Kindle E-mail']['text'])

    def test_user_list_edit_locale(self):
        ul = self.get_user_table(1)
        self.assertTrue("English", ul['table'][1]['Locale']['text'])
        self.edit_table_select(ul['table'][1]['Locale']['element'], "Hungarian")
        ul = self.get_user_table(-1)
        self.assertEqual("Hungarian", ul['table'][1]['Locale']['text'])
        self.edit_table_select(ul['table'][1]['Locale']['element'], "Dutch", True)
        self.assertEqual("Hungarian", ul['table'][1]['Locale']['element'].text)
        # ToDo Mass Edit
        self.assertEqual("Locale", ul['header'][5]['text'])
        self.assertFalse(ul['header'][5]['element'].is_enabled())
        self.edit_table_select(ul['table'][1]['Locale']['element'], "English")
        ul = self.get_user_table(-1)
        self.assertTrue("English", ul['table'][1]['Locale']['text'])

    def test_user_list_edit_language(self):
        ul = self.get_user_table(1)
        self.assertTrue("Show All", ul['table'][1]['Visible Book Languages']['text'])
        self.edit_table_select(ul['table'][1]['Visible Book Languages']['element'], "English")
        ul = self.get_user_table(-1)
        self.assertEqual("English", ul['table'][1]['Visible Book Languages']['text'])
        self.edit_table_select(ul['table'][1]['Visible Book Languages']['element'], "Norwegian Bokmål", True)
        self.assertEqual("English", ul['table'][1]['Locale']['element'].text)
        # ToDo Mass Edit
        self.assertEqual("Visible Book Languages", ul['header'][6]['text'])
        self.assertFalse(ul['header'][6]['element'].is_enabled())
        self.edit_table_select(ul['table'][1]['Visible Book Languages']['element'], "Show All")
        ul = self.get_user_table(-1)
        self.assertTrue("Show All", ul['table'][1]['Locale']['text'])

    @skip("Not Implemented")
    def test_user_list_denied_tags(self):
        pass

    def test_user_list_admin_role(self):
        ul = self.get_user_table(1)
        self.assertEqual("", ul['table'][1]['role_Admin']['text'])
        self.assertFalse(ul['table'][1]['role_Admin']['element'].is_selected())
        self.assertTrue(ul['table'][0]['role_Admin']['element'].is_selected())
        self.assertTrue(ul['table'][8]['role_Admin']['element'].is_selected())
        ul['table'][8]['role_Admin']['element'].click()
        ul = self.get_user_table(-1)
        self.assertFalse(ul['table'][8]['role_Admin']['element'].is_selected())

        ul['table'][0]['role_Admin']['element'].click()
        ul = self.get_user_table(-1)
        self.assertTrue(ul['table'][0]['role_Admin']['element'].is_selected())
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))
        # ToDo: remove admin rights from current user
        ul['table'][8]['role_Admin']['element'].click()

    def test_user_list_download_role(self):
        ul = self.get_user_table(1)
        self.assertEqual("", ul['table'][1]['role_Download']['text'])
        self.assertFalse(ul['table'][1]['role_Download']['element'].is_selected())
        self.assertTrue(ul['table'][0]['role_Download']['element'].is_selected())
        self.assertTrue(ul['table'][4]['role_Download']['element'].is_selected())
        ul['table'][4]['role_Download']['element'].click()
        ul = self.get_user_table(-1)
        self.assertFalse(ul['table'][4]['role_Download']['element'].is_selected())
        ul['table'][0]['role_Download']['element'].click()
        ul = self.get_user_table(-1)
        self.assertFalse(ul['table'][0]['role_Download']['element'].is_selected())
        # ToDo: Mass change elements
        # Restore default
        ul['table'][4]['role_Download']['element'].click()
        ul = self.get_user_table(-1)
        ul['table'][0]['role_Download']['element'].click()

    def test_user_list_edit_visiblility(self):
        ul = self.get_user_table(1)
        self.assertEqual("", ul['table'][1]['Show category selection']['text'])
        self.assertTrue(ul['table'][1]['Show category selection']['element'].is_selected())
        self.assertTrue(ul['table'][0]['Show category selection']['element'].is_selected())
        self.assertTrue(ul['table'][4]['Show category selection']['element'].is_selected())
        ul['table'][4]['Show category selection']['element'].click()
        ul = self.get_user_table(-1)
        self.assertFalse(ul['table'][4]['Show category selection']['element'].is_selected())
        ul['table'][0]['Show category selection']['element'].click()
        ul = self.get_user_table(-1)
        self.assertFalse(ul['table'][0]['Show category selection']['element'].is_selected())
        # ToDo: Mass change elements
        # Restore default
        ul['table'][4]['Show category selection']['element'].click()
        ul = self.get_user_table(-1)
        ul['table'][0]['Show category selection']['element'].click()

    def test_user_list_search(self):
        ul = self.get_user_table(1)
        self.assertEqual(10, len(ul['table']))
        self.assertEqual(4, len(ul['pagination']))
        ul = self.check_search(ul, "u1", 1, "Username", "u1")
        ul = self.check_search(ul, "B.cOm", 10, "E-mail Address", "a5@b.com")
        self.check_search(ul, "a1@", 1, "Kindle E-mail", "a1@b.com")

    def test_user_list_sort(self):
        ul = self.get_user_table(1)
        self.assertEqual("Username", ul['header'][2]['text'])
        ul['header'][2]['sort'].click()
        ul = self.get_user_table(-1)
        self.assertEqual("1_no", ul['table'][0]['Username']['text'])
        ul['header'][2]['sort'].click()
        ul = self.get_user_table(-1)
        self.assertEqual("ü执1", ul['table'][0]['Username']['text'])
        self.assertEqual("E-mail Address", ul['header'][3]['text'])
        ul['header'][3]['sort'].click()
        ul = self.get_user_table(-1)
        self.assertEqual("1al@b.com", ul['table'][0]['E-mail Address']['text'])
        ul['header'][3]['sort'].click()
        ul = self.get_user_table(-1)
        self.assertEqual("muki9al@b.com", ul['table'][0]['E-mail Address']['text'])
        self.assertEqual("Kindle E-mail", ul['header'][4]['text'])
        ul['header'][4]['sort'].click()
        ul = self.get_user_table(-1)
        self.assertEqual("+", ul['table'][0]['Kindle E-mail']['text'])
        self.assertEqual("a1@b.com", ul['table'][8]['Kindle E-mail']['text'])
        ul['header'][4]['sort'].click()
        ul = self.get_user_table(-1)
        self.assertEqual("muki8al@bcd.com", ul['table'][0]['Kindle E-mail']['text'])
        self.assertEqual("Locale", ul['header'][5]['text'])
        ul['header'][5]['sort'].click()
        ul = self.get_user_table(-1)
        self.assertEqual("German", ul['table'][0]['Locale']['text'])
        ul['header'][5]['sort'].click()
        ul = self.get_user_table(-1)
        self.assertEqual("Polish", ul['table'][0]['Locale']['text'])
        self.assertEqual("Visible Book Languages", ul['header'][6]['text'])
        ul['header'][6]['sort'].click()
        ul = self.get_user_table(-1)
        self.assertEqual("Show All", ul['table'][0]['Visible Book Languages']['text'])
        ul['header'][6]['sort'].click()
        ul = self.get_user_table(-1)
        self.assertEqual("Norwegian Bokmål", ul['table'][0]['Visible Book Languages']['text'])

    def test_user_list_guest_edit(self):
        self.fill_basic_config({'config_anonbrowse': 1})
        ul = self.get_user_table(2)
        self.assertEqual(3, len(ul['table']))
        ul = self.get_user_table(1)
        self.assertEqual("Guest", ul['table'][1]['Username']['text'])
        self.assertFalse(ul['table'][1]['Delete User']['element'].is_displayed())
        self.assertTrue("disabled" in ul['table'][1]['Username']['element'].get_attribute('class'))
        self.assertEqual("", ul['table'][1]['Locale']['text'])
        self.assertFalse(ul['table'][1]['Delete User']['element'].is_displayed())
        ul['table'][1]['role_Admin']['element'].click()
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))
        ul = self.get_user_table(-1)
        self.assertEqual("", ul['table'][1]['Locale']['text'])
        self.assertFalse(ul['table'][1]['Delete User']['element'].is_displayed())
        ul['table'][1]['role_Change Password']['element'].click()
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))
        ul = self.get_user_table(-1)
        ul['table'][1]['role_Edit Public Shelfs']['element'].click()
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_danger')))
        self.fill_basic_config({'config_anonbrowse': 0})
