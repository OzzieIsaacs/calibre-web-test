#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
import os
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import shutil
from ui_helper import ui_class
from subproc_wrapper import process_open
from testconfig import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME
from email_convert_helper import Gevent_SMPTPServer, CredentialValidator
import email_convert_helper
from parameterized import parameterized_class

'''@parameterized_class([
   { "py_version": u'python'},
   { "py_version": u'python3'},
],names=('Python27','Python36'))'''
@unittest.skipIf(email_convert_helper.is_calibre_not_present(),"Skipping convert, calibre not found")
class test_ebook_convert(unittest.TestCase, ui_class):
    p=None
    driver = None
    email_server = None
    py_version = 'python'

    @classmethod
    def setUpClass(cls):
        print('test_ebook_convert')
        # start email server
        cls.email_server = Gevent_SMPTPServer(
            ('127.0.0.1', 1025),
            only_ssl=False,
            credential_validator=CredentialValidator(),
            timeout=10
        )
        cls.email_server.start()

        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH,'app.db'))
        except:
            pass
        shutil.rmtree(TEST_DB,ignore_errors=True)
        shutil.copytree('./Calibre_db', TEST_DB)
        try:
            cls.p = process_open([cls.py_version, os.path.join(CALIBRE_WEB_PATH,u'cps.py')],(1),sout=None)

            # create a new Firefox session
            cls.driver = webdriver.Firefox()
            # time.sleep(15)
            cls.driver.implicitly_wait(BOOT_TIME)
            print('Calibre-web started')

            cls.driver.maximize_window()

            # navigate to the application home page
            cls.driver.get("http://127.0.0.1:8083")

            # Wait for config screen to show up
            cls.fill_initial_config({'config_calibre_dir':TEST_DB, 'config_converterpath':email_convert_helper.calibre_path(),
                                     'config_ebookconverter':'converter2'})

            # wait for cw to reboot
            time.sleep(BOOT_TIME)

            # Wait for config screen with login button to show up
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.NAME, "login")))
            login_button = cls.driver.find_element_by_name("login")
            login_button.click()

            # login
            cls.login("admin", "admin123")
            cls.edit_user('admin', {'email': 'a5@b.com','kindle_mail': 'a1@b.com'})
            cls.setup_server(True, {'mail_server':'127.0.0.1', 'mail_port':'1025',
                                'mail_use_ssl':'None','mail_login':'name@host.com','mail_password':'1234',
                                'mail_from':'name@host.com'})
            time.sleep(2)
        except:
            cls.driver.quit()
            cls.p.terminate()
    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        cls.email_server.stop()
        time.sleep(2)
        cls.p.kill()

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin','admin123')


    # deactivate converter and check send to kindle and convert are not visible anymore
    def test_convert_deactivate(self):
        self.fill_basic_config({'config_ebookconverter': 'converter0'})
        self.goto_page('nav_about')
        self.assertFalse(self.check_element_on_page((By.XPATH,"//tr/th[text()='Calibre converter']/following::td[1]")))
        details = self.get_book_details(5)
        self.assertFalse(details['kindlebtn'])
        vals = self.get_convert_book(5)
        self.assertFalse(vals['btn_from'])
        self.assertFalse(vals['btn_to'])
        self.fill_basic_config({'config_ebookconverter': 'converter2'})

    # Set excecutable to wrong exe and start convert
    # set excecutable not existing and start convert
    # set excecutable non excecutable and start convert
    def test_convert_wrong_excecutable(self):
        task_len = len(self.check_tasks())
        self.fill_basic_config({'config_converterpath':'/opt/calibre/ebook-polish'})
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH,"//tr/th[text()='Calibre converter']/following::td[1]"))
        self.assertEqual(element.text,'not installed')
        details = self.get_book_details(5)
        self.assertEqual(len(details['kindle']),1)
        # ToDo: check convert function
        vals = self.get_convert_book(5)

        # ToDo: change behavior convert should only be visible if ebookconverter has valid entry
        self.fill_basic_config({'config_converterpath':'/opt/calibre/kuku'})
        details = self.get_book_details(5)
        self.assertEqual(len(details['kindle']),1)
        details['kindlebtn'].click()
        # conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        # self.assertTrue(conv)
        # conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='Calibre converter']/following::td[1]"))
        self.assertEqual(element.text, 'not installed')
        # ToDo: check convert function
        vals = self.get_convert_book(5)
        # self.assertFalse(vals['btn_from'])
        # self.assertFalse(vals['btn_to'])

        nonexec = os.path.join(CALIBRE_WEB_PATH,'app.db')
        self.fill_basic_config({'config_converterpath': nonexec})
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='Calibre converter']/following::td[1]"))
        self.assertEqual(element.text, 'Excecution permissions missing')
        details = self.get_book_details(5)
        self.assertEqual(len(details['kindle']),1)
        details['kindlebtn'].click()
        # conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        # self.assertTrue(conv)
        # conv.click()
        # ToDo: check convert function
        vals = self.get_convert_book(5)
        i = 0
        while i < 10:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 2:
                if ret[-1]['result'] ==  'Finished' or ret[-1]['result'] ==  'Failed':
                    break
            i += 1
        self.assertEqual(len(ret),(task_len+2) % 20)
        if len(ret) > 1:
            self.assertEqual(ret[-2]['result'], 'Failed')
        self.assertEqual(ret[-1]['result'], 'Failed')
        self.fill_basic_config({'config_converterpath': email_convert_helper.calibre_path()})


    # set parameters for convert ( --margin-right 11.9) and start conversion -> conversion okay
    # set parameters for convert ( --margin-righ) and start conversion -> conversion failed
    # remove parameters for conversion
    def test_convert_parameter(self):
        task_len = len(self.check_tasks())
        self.fill_basic_config({'config_calibre': '--margin-right 11.9'})
        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('LIT')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(4)
        ret = self.check_tasks()
        self.assertEqual(len(ret) - 1, task_len)
        self.assertEqual(ret[-1]['result'], 'Finished')

        self.fill_basic_config({'config_calibre': '--margin-rght 11.9'})
        vals = self.get_convert_book(8)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('LRF')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(4)
        ret = self.check_tasks()
        self.assertEqual(len(ret) - 2, task_len)
        self.assertEqual(ret[-1]['result'], 'Failed')
        self.fill_basic_config({'config_calibre': ''})

    # press send to kindle for not converted book
    # wait for finished
    # check email received
    def test_convert_email(self):
        self.setup_server(True, {'mail_password': '10234', 'mail_use_ssl':'None'})
        task_len = len(self.check_tasks())
        details = self.get_book_details(9)
        self.assertEqual(len(details['kindle']),1)
        details['kindlebtn'].click()
        # conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].getchildren()[0].tail))
        # self.assertTrue(conv)
        # conv.click()
        i = 0
        while i < 10:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 2:
                if ret[-1]['result'] ==  'Finished' or ret[-1]['result'] ==  'Failed':
                    break
            i += 1
        self.assertEqual(ret[-2]['result'], 'Finished')
        self.assertEqual(ret[-1]['result'], 'Finished')
        self.setup_server(True, {'mail_password': '1234'})


    # check visiblility kindle button for user with not set kindle-email
    # create user -> no kindle email
    # logout, login new user
    # check button send to kindle not visible
    def test_kindle_send_not_configured(self):
        self.create_user('kindle', {'password': '123', 'email': 'a@b.com', 'edit_role':1})
        self.logout()
        self.login('kindle', '123')
        details = self.get_book_details(5)
        self.assertIsNone(details['kindlebtn'])
        self.logout()
        self.login('admin', 'admin123')

    # check conversion and email started and conversion fails
    # move valid file to invalid filename and create random file with extension for conversion
    # start conversion. Check conversion fails
    # delete ranom file and move invalid filename back to vaild filename
    # convert valid file
    def test_convert_failed_and_email(self):
        orig_file = os.path.join(TEST_DB, u'Leo Baskerville/book8 (8)',
                                 u'book8 - Leo Baskerville.epub').encode('UTF-8')
        moved_file = os.path.join(TEST_DB, u'Leo Baskerville/book8 (8)',
                                 u'book8.epub').encode('UTF-8')
        os.rename(orig_file,moved_file)
        with open(orig_file, 'wb') as fout:
            fout.write(os.urandom(124))
        self.setup_server(True, {'mail_password': '10234'})
        task_len = len(self.check_tasks())
        details = self.get_book_details(8)
        self.assertEqual(len(details['kindle']),1)
        details['kindlebtn'].click()
        # conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][1].text))
        # self.assertTrue(conv)
        # conv.click()
        i = 0
        while i < 10:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 1:
                if ret[-1]['result'] ==  'Finished' or ret[-1]['result'] ==  'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Failed')
        self.setup_server(True, {'mail_password': '1234'})
        os.remove(orig_file)
        os.rename(moved_file, orig_file)


    # convert everything to everything
    # start conversion of mobi -> azw3
    # start conversion of epub -> pdf
    # start conversion of epub -> txt
    # start conversion of epub -> fb2
    # start conversion of epub -> lit
    # start conversion of epub -> html
    # start conversion of epub -> rtf
    # start conversion of epub -> odt
    # start conversion of azw3 -> mobi
    # create user
    # logout
    # check conversion result for non admin user -> nothing visible
    # start conversion for non admin user
    # check conversion result for non admin user -> own conversion visible without username
    # logout
    # login as admin
    # check conversion result conversion of other user visible
    def test_convert_only(self):
        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('AZW3')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('EPUB')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('TXT')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('FB2')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('LIT')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('MOBI')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('HTMLZ')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

        self.create_user('solo', {'password': '123', 'email': 'a@b.com', 'edit_role':1})
        time.sleep(2)
        ret = self.check_tasks()
        self.assertEqual(ret[-6]['result'], 'Finished')
        self.assertEqual(ret[-5]['result'], 'Finished')
        self.assertEqual(ret[-4]['result'], 'Finished')
        self.assertEqual(ret[-3]['result'], 'Finished')
        self.assertEqual(ret[-2]['result'], 'Finished')
        self.assertEqual(ret[-1]['result'], 'Finished')
        memory = len(ret)

        self.logout()
        self.login('solo', '123')
        ret = self.check_tasks()
        self.assertEqual(0, len(ret))

        vals = self.get_convert_book(7)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('PDF')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('RTF')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(10)
        ret = self.check_tasks()
        self.assertEqual(ret[-1]['result'], 'Finished')

        self.logout()
        self.login('admin', 'admin123')
        ret = self.check_tasks()
        self.assertEqual(memory+1, len(ret))


    # start conversion of epub -> mobi
    # wait for finished
    # start sending e-mail
    # check email received
    # check filename
    def test_email_only(self):
        self.setup_server(True, {'mail_use_ssl':'None','mail_password':'10234'})
        task_len = len(self.check_tasks())
        vals = self.get_convert_book(5)
        select = Select(vals['btn_from'])
        select.select_by_visible_text('EPUB')
        select = Select(vals['btn_to'])
        select.select_by_visible_text('MOBI')
        self.driver.find_element_by_id("btn-book-convert").click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 10:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 1:
                if ret[-1]['result'] ==  'Finished' or ret[-1]['result'] ==  'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Finished')
        details = self.get_book_details(5)
        details['kindlebtn'].click()
        # conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        # self.assertTrue(conv)
        # conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 10:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 2:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Finished')
        self.assertGreaterEqual(self.email_server.message_size,30700)
        self.setup_server(False, {'mail_password':'1234'})


    # check behavior for failed email (size)
    # conversion okay, email failed
    def test_email_failed(self):
        self.setup_server(False, {'mail_password': '10234'})
        task_len = len(self.check_tasks())
        details = self.get_book_details(5)
        self.email_server.set_return_value(552)
        # = '552 Requested mail action aborted: exceeded storage allocation'
        details['kindlebtn'].click()
        # conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][1].text))
        # self.assertTrue(conv)
        # conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 10:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Failed')
        self.email_server.set_return_value(0)
        self.setup_server(False, {'mail_password':'1234'})


    # check behavior for failed server setup (STARTTLS)
    def test_STARTTLS_smtp_setup_error(self):
        task_len = len(self.check_tasks())
        self.setup_server(False, {'mail_use_ssl':'STARTTLS','mail_password':'10234'})
        details = self.get_book_details(7)
        details['kindlebtn'].click()
        conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        self.assertTrue(conv)
        conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 10:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Failed')

    # check behavior for failed server setup (SSL)
    def test_SSL_smtp_setup_error(self):
        task_len = len(self.check_tasks())
        self.setup_server(False, {'mail_use_ssl':'SSL/TLS','mail_password':'10234'})
        details = self.get_book_details(7)
        details['kindlebtn'].click()
        conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        self.assertTrue(conv)
        conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        i = 0
        while i < 10:
            time.sleep(2)
            ret = self.check_tasks()
            if len(ret) - task_len == 1:
                if ret[-1]['result'] == 'Finished' or ret[-1]['result'] == 'Failed':
                    break
            i += 1
        self.assertEqual(ret[-1]['result'], 'Failed')
