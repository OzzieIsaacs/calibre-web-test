# -*- coding: utf-8 -*-

import unittest
import time
import threading
from helper_ui import ui_class
from testconfig import TEST_DB, VENV_PYTHON, CALIBRE_WEB_PATH, BOOT_TIME
from helper_func import startup, debug_startup, get_Host_IP, add_dependency, remove_dependency, kill_old_cps
from selenium.webdriver.common.by import By
import re
import os
from helper_ldap import TestLDApServer

class test_ldap_login(unittest.TestCase, ui_class):

    p=None
    driver = None
    kobo_adress = None
    dep_line = ["flask-simpleldap"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dep_line, cls.__name__)

        try:
            #server = TestLDApServer(config=1, port=3268, encrypt=None)
            #server.start()
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,'config_login_type':'Use LDAP Authentication'})
        except Exception as e:
            cls.driver.quit()
            cls.p.terminate()
            kill_old_cps()

    @classmethod
    def tearDownClass(cls):
        cls.p.terminate()
        cls.driver.quit()
        # close the browser window and stop calibre-web
        remove_dependency(cls.dep_line)

    def test_invalid_LDAP(self):
        # leave hostname empty and password empty
        self.fill_basic_config({'config_ldap_provider_url':''})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('LDAP Provider' in message.text)
        # leave administrator empty
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1', 'config_ldap_serv_username': ''})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Service Account' in message.text)
        self.fill_basic_config({'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Service Account' in message.text)
        # leave DN empty
        self.fill_basic_config({'config_ldap_serv_password': 'secret', 'config_ldap_dn': ''})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('DN' in message.text)
        # leave user object empty
        self.fill_basic_config({'config_ldap_dn': 'ou=people,dc=calibreweb,dc=com', 'config_ldap_user_object': ''})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('User Object' in message.text)
        # leave user object without %s
        self.fill_basic_config({'config_ldap_user_object': '(&(objectClass=person)(uid=seven))'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('%s' in message.text)
        # leave user object with unequal praenthesis
        self.fill_basic_config({'config_ldap_user_object': '(&(objectClass=person)(uid=%s)'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Parenthesis' in message.text)
        # leave groupOject filter without %s
        self.fill_basic_config({'config_ldap_user_object': '(&(objectClass=person)(uid=%s)',
                                'config_ldap_group_object_filter': '(&(objectClass=groupofnames)(group=cps)9'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('%s' in message.text)
        # leave groupOject filter unequal praenthesis
        self.fill_basic_config({'config_ldap_group_object_filter': '(&(objectClass=groupofnames)(group=%s)'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Parenthesis' in message.text)
        self.fill_basic_config({'config_ldap_group_object_filter': '(&(objectClass=groupofnames)(group=%s))'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_ldap_encryption': 'SSL', 'ldap-cert-settings': 'nofile'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Certificate Location' in message.text)
        self.fill_basic_config({'config_ldap_encryption': 'None', 'ldap-cert-settings': ''})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))


    def test_LDAP_fallback_Login(self):
        self.logout()
        self.login("admin", "admin123")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))

    def test_LDAP_login(self):
        # configure ldap correct
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
                                'config_ldap_dn': 'ou=people,dc=calibreweb,dc=com',
                                'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com',
                                'config_ldap_serv_password': 'secret',
                                'config_ldap_user_object': '(uid=%s)',
                                'config_ldap_group_object_filter': '',
                                'config_ldap_openldap': 1
                                })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # create new user
        # give user password different form ldap
        self.create_user('user0',{'email':'user0@exi.com','password':'1234'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # logout
        self.logout()
        # try login -> LDAP not reachable
        self.login('user0','terces')
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('LDAP Server' in message.text)
        # start ldap
        server = TestLDApServer(config=1, port=3268, encrypt=None)
        server.start()
        # try login, wrong password
        self.login('user0', 'terce')
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        # login
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # logout
        self.logout()
        # try login fallback password -> fail
        self.login('user0', '1234')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        # login as admin
        self.login('admin','admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        # delete user
        self.edit_user('user0', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # logout
        self.logout()
        # try login LDAP password -> fail
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        # stop ldap
        server.stop_LdapServer()

    def test_LDAP_import(self):
        # change user create template
        # start import
        # ldap not reachable
        # start ldap with no groups
        # start import -> no user found
        # stop/start ldap with groupofnames, 1 email adress
        # start import -> all user imported
        # check access right of user match template access rights
        # stop/start ldap with poxixusergroup, no email, 2 email adresses
        # start import -> all user imported
        # check email adresses are correct imported
        # stop/start ldap with missing user, already existing user
        # start import -> error, user missing, user already exisiting
        pass

    def test_LDAP_SSL(self):
        # configure ssl LDAP
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
                                'config_ldap_dn': 'ou=people,dc=calibreweb,dc=com',
                                'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com',
                                'config_ldap_serv_password': 'secret',
                                'config_ldap_user_object': '(uid=%s)',
                                'config_ldap_group_object_filter': '',
                                'config_ldap_openldap': 1,
                                'config_ldap_encryption': 'SSL'
                                })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # create new user
        # give user password different form ldap
        self.create_user('user0',{'email':'user0@exi.com','password':'1235'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # start SSl LDAP
        server = TestLDApServer(config=1, port=3268, encrypt="SSL")
        server.start()
        # logout
        self.logout()
        # login as LDAP user
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # logout
        self.logout()
        # login as admin
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        # configure nonssl LDAP
        self.fill_basic_config({'config_ldap_encryption': 'None'})
        time.sleep(BOOT_TIME)
        # logout
        self.logout()
        # try login -> not reachable
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        # login admin
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.edit_user('user0', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # stop ldap
        server.stop_LdapServer()

    def test_LDAP_STARTTLS(self):
        # configure LDAP STARTTLS
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
                                'config_ldap_dn': 'ou=people,dc=calibreweb,dc=com',
                                'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com',
                                'config_ldap_serv_password': 'secret',
                                'config_ldap_user_object': '(uid=%s)',
                                'config_ldap_group_object_filter': '',
                                'config_ldap_openldap': 1,
                                'config_ldap_encryption': 'TLS'
                                })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # create user
        self.create_user('user0',{'email':'user0@exi.com','password':'1236'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # start SSl LDAP
        server = TestLDApServer(config=1, port=3268, encrypt="TLS")
        server.start()
        # logout
        self.logout()
        # login as LDAP user
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # logout
        self.logout()
        # login as admin
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        # configure nonssl LDAP
        self.fill_basic_config({'config_ldap_encryption': 'None'})
        time.sleep(BOOT_TIME)
        # logout
        self.logout()
        # try login -> not reachable
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        # login admin
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        # configure ssl LDAP
        self.fill_basic_config({'config_ldap_encryption': 'SSL'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # logout
        self.logout()
        # try login -> not reachable
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        # login admin
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.fill_basic_config({'config_ldap_encryption': 'TLS','config_ldap_openldap':0})
        time.sleep(BOOT_TIME)
        self.logout()
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.edit_user('user0', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # stop ldap
        server.stop_LdapServer()
