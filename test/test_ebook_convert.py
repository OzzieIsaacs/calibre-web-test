#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium import webdriver
import os
import sys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import shutil
from ui_helper import ui_class
from subproc_wrapper import process_open
from testconfig import CALIBRE_WEB_PATH, TEST_DB
from secure_smtpd import SMTPServer
import threading
import asyncore

'''
use secure-smtp
'''


class CredentialValidator(object):

    def validate(self, username, password):
        if username == 'name@host.com' and password == '10234':
            return True
        return False


class threaded_SMPTPServer(SMTPServer, threading.Thread):

    def __init__(self, *args, **kwargs):
        SMTPServer.__init__(self, *args, **kwargs)
        self._stopevent = threading.Event()
        threading.Thread.__init__(self)
        self.status = 1

    def process_message(self, peer, mailfrom, rcpttos, message_data):
        print(message_data)

    def run(self):
        asyncore.loop()
        while self.status:
            time.sleep(1)
        print('email server stopps')

    def stop(self):
        self.status = 0
        self.close()


def is_calibre_not_present():
    if calibre_path():
        return False
    else:
        return True

def calibre_path():
    if sys.platform == "win32":
        calibre_path = ["C:\\program files\calibre\calibre-convert.exe", "C:\\program files(x86)\calibre\calibre-convert.exe"]
    else:
        calibre_path = ["/opt/calibre/ebook-convert"]
    for element in calibre_path:
        if os.path.isfile(element):
            return element
    return None


class SSLSMTPServer(SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, message_data):
        print(message_data)


@unittest.skipIf(is_calibre_not_present(),"Skipping convert, calibre not found")
class test_ebook_convert(unittest.TestCase, ui_class):
    p=None
    driver = None
    email_server = None

    @classmethod
    def setUpClass(cls):
        # start email server
        cls.email_server = threaded_SMPTPServer(
            # cls,
            ('127.0.0.1', 1025),
            None,
            require_authentication=True,
            use_ssl=True,
            certfile='SSL/ssl.crt',
            keyfile='SSL/ssl.key',
            credential_validator=CredentialValidator(),
        )
        cls.email_server.start()

        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH,'app.db'))
        except:
            pass
        shutil.rmtree(TEST_DB,ignore_errors=True)
        shutil.copytree('./Calibre_db', TEST_DB)
        cls.p = process_open([u"python", os.path.join(CALIBRE_WEB_PATH,u'cps.py')],(1))

        # create a new Firefox session
        cls.driver = webdriver.Firefox()
        # time.sleep(15)
        cls.driver.implicitly_wait(5)
        print('Calibre-web started')

        cls.driver.maximize_window()

        # navigate to the application home page
        cls.driver.get("http://127.0.0.1:8083")

        # Wait for config screen to show up
        cls.fill_initial_config({'config_calibre_dir':TEST_DB, 'config_converterpath':calibre_path(),
                                 'config_ebookconverter':'converter2'})

        # wait for cw to reboot
        time.sleep(5)

        # Wait for config screen with login button to show up
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.NAME, "login")))
        login_button = cls.driver.find_element_by_name("login")
        login_button.click()

        # login
        cls.login("admin", "admin123")
        cls.edit_user('admin', {'email': 'a5@b.com','kindle_mail': 'a1@b.com'})
        cls.setup_server(True, {'mail_server':'127.0.0.1', 'mail_port':'1025',
                            'mail_use_ssl':'SSL/TLS','mail_login':'name@host.com','mail_password':'1234',
                            'mail_from':'name@host.com'})
        # print('configured')


    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        cls.email_server.stop()

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin','admin123')

    # Set excecutable to wrong exe and start convert
    # set excecutable not existing and start convert
    # set excecutable non excecutable and start convert
    # @unittest.skip("Not Implemented")
    def test_convert_wrong_excecutable(self):
        self.fill_basic_config({'config_converterpath':'/opt/calibre/ebook-polish'})
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH,"//tr/th[text()='Calibre converter']/following::td[1]"))
        self.assertEqual(element.text,'not installed')
        details = self.get_book_details(5)
        # ToDo: change behavior convert should only be visible if ebookconverter has valid entry
        self.assertEqual(len(details['kindle']),2)

        self.fill_basic_config({'config_converterpath':'/opt/calibre/kuku'})
        details = self.get_book_details(5)
        self.assertEqual(len(details['kindle']),2)
        details['kindlebtn'].click()
        conv = self.check_element_on_page((By.LINK_TEXT, details['kindle'][0].text))
        self.assertTrue(conv)
        conv.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_about')
        element = self.check_element_on_page((By.XPATH, "//tr/th[text()='Calibre converter']/following::td[1]"))
        self.assertEqual(element.text, 'not installed')
        ret = self.check_tasks()
        print('a')

    # deactivate converter and check send to kindle and convert are not visible anymore
    @unittest.skip("Not Implemented")
    def test_convert_deactivate(self):
        self.assertIsNone('Not Implemented')

    # set parameters for convert and start conversion
    @unittest.skip("Not Implemented")
    def test_convert_parameter(self):
        self.assertIsNone('Not Implemented')

    # convert everything to everything
    # start conversion of azw3 -> mobi
    # start conversion of mobi -> azw3
    # start conversion of epub -> pdf
    # start conversion of epub -> txt
    # start conversion of epub -> fb2
    # start conversion of epub -> lit
    # start conversion of epub -> html
    # start conversion of epub -> rtf
    # start conversion of epub -> odt
    # create user
    # logout
    # check conversion result for non admin user -> nothing visible
    # start conversion for non admin user
    # check conversion result for non admin user -> own conversion visible without username
    # logout
    # login as admin
    # check conversion result conversion of other user visible
    @unittest.skip("Not Implemented")
    def test_convert_only(self):
        self.assertIsNone('Not Implemented')

    # start conversion of epub -> mobi
    # wait for finished
    # start sending e-mail
    # check email received
    @unittest.skip("Not Implemented")
    def test_email_only(self):
        self.assertIsNone('Not Implemented')

    # press send to kindle for not converted book
    # wait for finished
    # check email received
    @unittest.skip("Not Implemented")
    def test_convert_email(self):
        self.assertIsNone('Not Implemented')

    # check visiblility kindle button for user with not set kindle-email
    @unittest.skip("Not Implemented")
    def test_kindle_send_not_configured(self):
        self.assertIsNone('Not Implemented')

    # check behavior for failed email (size)
    # conversion okay, email failed
    @unittest.skip("Not Implemented")
    def test_email_failed(self):
        self.assertIsNone('Not Implemented')

    # check conversion and email started and conversion failes
    @unittest.skip("Not Implemented")
    def test_convert_failed_and_email(self):
        self.assertIsNone('Not Implemented')

    # check behavior for failed server setup (non-SSL)
    @unittest.skip("Not Implemented")
    def test_smtp_setup_error(self):
        self.assertIsNone('Not Implemented')

    # check behavior for failed server setup (SSL)
    @unittest.skip("Not Implemented")
    def test_SSL_smtp_setup_error(self):
        self.assertIsNone('Not Implemented')

    # check behavior for failed server setup (STARTTLS)
    @unittest.skip("Not Implemented")
    def test_STARTTLS_smtp_setup_error(self):
        self.assertIsNone('Not Implemented')
