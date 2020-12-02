# -*- coding: utf-8 -*-

import unittest
import socket
import time
import re
import os
import shutil
from helper_ui import ui_class
from config_test import TEST_DB, BOOT_TIME, CALIBRE_WEB_PATH, base_path
from helper_func import startup, debug_startup, add_dependency, remove_dependency, get_Host_IP
from selenium.webdriver.common.by import By
from helper_ldap import TestLDAPServer
import requests
from helper_func import save_logfiles


class TestLdapLogin(unittest.TestCase, ui_class):

    p = None
    driver = None
    kobo_adress = None
    if os.name == 'nt':
        dep_line = ["local|LDAP_WHL|python-ldap", "jsonschema", "Flask-SimpleLDAP"]
    else:
        dep_line = ["Flask-SimpleLDAP", "python-ldap", "jsonschema"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dep_line, cls.__name__)

        try:
            cls.server = TestLDAPServer(config=4, port=3268, encrypt=None)
            cls.server.start()
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,'config_login_type':'Use LDAP Authentication'})
            # print('stop in setup')
            cls.server.stopListen()
        except Exception as e:
            cls.driver.quit()
            cls.p.terminate()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop_LdapServer()
        cls.stop_calibre_web()
        cls.p.terminate()
        cls.driver.quit()
        # close the browser window and stop calibre-web
        remove_dependency(cls.dep_line)
        save_logfiles(cls.__name__)

    @classmethod
    def tearDown(cls):
        try:
            cls.server.stopListen()
        except Exception as e:
            print(e)

    def inital_sync(self, kobo_adress):
        # generate payload for auth request
        payload = {
            "AffiliateName": "Kobo",
            "AppVersion": "4.19.14123",
            "ClientKey": "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMzc1",
            "DeviceId": "lnez00rs6cox274bx8c97kyr67ga3tnn0c1745tbjd9rmsmcywxmmcrw2zcayu6d",
            "PlatformId": "00000000-0000-0000-0000-000000000375",
            "UserKey": "12345678-9012-abcd-efgh-a7b6c0d8e7f2"
        }
        r = requests.post(kobo_adress+'/v1/auth/device', json=payload)
        self.assertEqual(r.status_code, 200)
        # request init request to get metadata format
        header = {
            'Authorization': 'Bearer ' + r.json()['AccessToken'],
            'Content-Type': 'application/json'
        }
        session = requests.session()
        r = session.get(kobo_adress+'/v1/initialization', headers=header)
        self.assertEqual(r.status_code, 200)
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        r = session.get(self.kobo_adress+'/v1/library/sync', params=params)
        self.assertEqual(r.status_code, 200)
        # syncToken = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
        Item1 = {'Type': 'ProductRevisionTagItem', 'RevisionId':'8f1b72c1-e9a4-4212-b538-8e4f4837d201'}
        r = session.post(self.kobo_adress + '/v1/library/tags', json={'Name': 'Success', 'Items': [Item1]})
        self.assertEqual(201, r.status_code)
        session.close()



    def test_invalid_LDAP(self):
        # set to default
        self.fill_basic_config({'config_ldap_provider_url': 'example.org',
                                'config_ldap_port': '389',
                                'config_ldap_dn': 'dc=example,dc=org',
                                'config_ldap_authentication' : 'Simple',
                                'config_ldap_serv_username': 'cn=admin,dc=example,dc=org',
                                'config_ldap_serv_password': '1',
                                'config_ldap_user_object': 'uid=%s',
                                'config_ldap_group_object_filter': '(&(objectclass=posixGroup)(cn=%s))',
                                'config_ldap_openldap': 1,
                                'config_ldap_encryption': 'None',
                                'config_ldap_group_name': 'calibreweb',
                                'config_ldap_group_members_field': 'memberUid'
                                })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # leave hostname empty and password empty
        self.fill_basic_config({'config_ldap_provider_url':''})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('LDAP Provider' in message.text)
        # leave administrator empty
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1', 'config_ldap_serv_username': ''})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Password' in message.text)
        # leave administrator empty and change to Unauthenticated
        self.fill_basic_config({'config_ldap_authentication': 'Unauthenticated'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Service Account' in message.text)
        # leave administrator empty and change to Unauthenticated
        self.fill_basic_config({'config_ldap_authentication': 'Anonymous'})
        message= self.check_element_on_page((By.ID, "flash_success"))
        time.sleep(BOOT_TIME)
        self.fill_basic_config({'config_ldap_authentication': 'Simple',
                                'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com'})
        # it can't be assured that password is empty if other tests run before
        time.sleep(BOOT_TIME)
        #message= self.check_element_on_page((By.ID, "flash_alert"))
        #self.assertTrue(message)
        #self.assertTrue('Service Account' in message.text)
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
        self.fill_basic_config({'config_ldap_user_object': '(&(objectClass=person)(uid=%s))',
                                'config_ldap_group_object_filter': '(&(objectClass=groupofnames)(group=cps))'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('%s' in message.text)
        # leave groupObject filter unequal praenthesis
        self.fill_basic_config({'config_ldap_group_object_filter': '(&(objectClass=groupofnames)(group=%s)'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Parenthesis' in message.text)
        self.fill_basic_config({'config_ldap_group_object_filter': '(&(objectClass=groupofnames)(group=%s))'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        self.fill_basic_config({'config_ldap_encryption': 'SSL'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        self.fill_basic_config({'config_ldap_cacert_path': 'nofile'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Location is not Valid' in message.text)
        self.fill_basic_config({'config_ldap_cacert_path': '', 'config_ldap_cert_path': 'nofile'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Location is not Valid' in message.text)
        self.fill_basic_config({'config_ldap_cert_path': '', 'config_ldap_key_path': 'nofile'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Location is not Valid' in message.text)
        self.fill_basic_config({'config_ldap_cacert_path': '',
                                'config_ldap_key_path': '',
                                'config_ldap_cert_path': ''})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        self.fill_basic_config({'config_ldap_encryption': 'None'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)


    def test_LDAP_fallback_Login(self):
        self.logout()
        self.login("admin", "admin123")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))

    def test_LDAP_login(self):
        # configure ldap correct
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
                                'config_ldap_authentication': 'Simple',
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
        self.server.relisten(config=1, port=3268, encrypt=None)
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

        #login as admin
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
        self.server.stopListen()
        self.login('admin','admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))

    def test_LDAP_import(self):
        # configure LDAP
        # ToDo: configuration of different authentication settings
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
                                'config_ldap_authentication': 'Simple',
                                'config_ldap_dn': 'dc=calibreweb,dc=com',
                                'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com',
                                'config_ldap_serv_password': 'secret',
                                'config_ldap_user_object': '(uid=%s)',
                                'config_ldap_group_object_filter': '',
                                'config_ldap_openldap': 1,
                                'config_ldap_encryption': 'None'
                                })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # change user create template
        self.fill_view_config({'show_16384': 0,'show_2': 0,'show_16': 0, 'show_8192': 0, 'show_256': 0,
                               'download_role': 1, 'delete_role':1, 'passwd_role':1})
        # start import
        self.goto_page('admin_setup')
        imprt = self.check_element_on_page((By.ID, "import_ldap_users"))
        self.assertTrue(imprt)
        imprt.click()
        # ldap not reachable
        time.sleep(3)
        self.assertTrue('Error:' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(2)
        # start ldap with no groups
        self.server.relisten(config=1, port=3268, encrypt=None)
        # print('new setup config 1')
        time.sleep(3)
        # start import -> no user found
        self.goto_page('admin_setup')
        imprt = self.check_element_on_page((By.ID, "import_ldap_users"))
        self.assertTrue(imprt)
        imprt.click()
        time.sleep(3)
        self.assertTrue('not all' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(2)
        # stop/start ldap with groupofnames, 1 email adress, wrong group name, member name
        self.server.relisten(config=2, port=3268, encrypt=None)
        # print('new setup config 2')
        time.sleep(5)
        self.fill_basic_config({'config_ldap_group_object_filter': '(& (objectclass=groupofnames)(cn=%s))',
                                'config_ldap_group_name':'cbs','config_ldap_group_members_field':'memper'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        imprt = self.check_element_on_page((By.ID, "import_ldap_users"))
        self.assertTrue(imprt)
        imprt.click()
        time.sleep(3)
        self.assertTrue('No user' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(2)
        # setup wrong group name
        self.fill_basic_config({'config_ldap_group_name':'cbs','config_ldap_group_members_field':'member'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        imprt = self.check_element_on_page((By.ID, "import_ldap_users"))
        self.assertTrue(imprt)
        imprt.click()
        time.sleep(3)
        self.assertTrue('No user' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(2)
        # start import -> all user imported
        self.fill_basic_config({'config_ldap_group_name':'cps','config_ldap_group_members_field':'member'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        imprt = self.check_element_on_page((By.ID, "import_ldap_users"))
        self.assertTrue(imprt)
        imprt.click()
        time.sleep(3)
        self.assertTrue('Successfully Imported' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(2)

        userlist = self.get_user_list()
        self.assertEqual(len(userlist),3)
        users = ['执一','Mümmy 7']
        self.assertTrue(all(elem in userlist for elem in users))

        # check access right of user match template access rights
        rights = self.get_user_settings('执一')
        self.assertEqual(rights['show_16384'],0)
        self.assertEqual(rights['show_2'],0)
        self.assertEqual(rights['show_16'], 0)
        self.assertEqual(rights['show_8192'], 0)
        self.assertEqual(rights['show_256'], 0)
        self.assertEqual(rights['download_role'], 1)
        self.assertEqual(rights['delete_role'], 1)
        self.assertEqual(rights['passwd_role'], 1)
        self.assertEqual(rights['upload_role'], 0)
        self.assertEqual(rights['edit_shelf_role'], 0)
        self.assertEqual(rights['show_4'], 1)
        self.assertEqual(rights['show_4096'], 1)
        self.assertEqual(rights['email'], 'onny@beta.org')
        self.assertEqual(rights['kindle_mail'], '')

        self.logout()
        # try login LDAP password
        self.login('执一', 'eekretsay')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('admin','admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))

        # change one user visibility and do reimport of users
        self.edit_user('执一', {'show_256':0,'show_16':1,'passwd_role':0,'upload_role':1})
        self.goto_page('admin_setup')
        imprt = self.check_element_on_page((By.ID, "import_ldap_users"))
        self.assertTrue(imprt)
        imprt.click()
        time.sleep(3)
        self.assertTrue('Failed to Create' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(2)
        # check access right of user still match changed rights
        rights = self.get_user_settings('执一')
        self.assertEqual(rights['show_256'],0)
        self.assertEqual(rights['show_16'], 1)
        self.assertEqual(rights['show_4096'], 1)
        self.assertEqual(rights['passwd_role'], 0)
        self.assertEqual(rights['upload_role'], 1)

        self.edit_user('Mümmy 7', {'delete': 1})
        self.edit_user('执一', {'delete': 1})
        # stop/start ldap with poxixusergroup, no email, 2 email adresses
        # print('new setup config 3')
        self.server.relisten(config=3, port=3268, encrypt=None)
        time.sleep(3)
        self.fill_basic_config({'config_ldap_group_object_filter': '(& (objectclass=posixGroup)(cn=%s))',
                                'config_ldap_group_name':'cps','config_ldap_group_members_field':'memberuid'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # start import -> all user imported
        self.goto_page('admin_setup')
        imprt = self.check_element_on_page((By.ID, "import_ldap_users"))
        self.assertTrue(imprt)
        imprt.click()
        time.sleep(3)
        self.assertTrue('Successfully Imported' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(2)
        # Check email adresses are correct imported
        User1rights = self.get_user_settings('user01')
        self.assertEqual(User1rights['kindle_mail'],'user01@gamma.org')
        self.assertEqual(User1rights['email'], 'user01@beta.com')
        User2rights = self.get_user_settings('user12')
        self.assertEqual(User2rights['email'],'user12@email.com')
        self.assertEqual(User2rights['kindle_mail'], '')
        self.edit_user('user01', {'delete': 1})
        self.edit_user('user12', {'delete': 1})

        # stop/start ldap with missing user, wrong entry (no uid field, wrong dn field)
        self.server.relisten(config=4, port=3268, encrypt=None)
        # print('new setup config 4')
        self.fill_basic_config({'config_ldap_group_object_filter': '(& (objectclass=groupofnames)(cn=%s))',
                                'config_ldap_group_members_field':'member'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # start import -> error
        self.goto_page('admin_setup')
        imprt = self.check_element_on_page((By.ID, "import_ldap_users"))
        self.assertTrue(imprt)
        imprt.click()
        time.sleep(3)
        self.assertTrue('One LDAP User' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(2)

        # connect with wrong encryption
        self.fill_basic_config({'config_ldap_encryption':'SSL'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        imprt = self.check_element_on_page((By.ID, "import_ldap_users"))
        self.assertTrue(imprt)
        imprt.click()
        time.sleep(3)
        self.assertTrue('Error:' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(2)
        self.edit_user('user0', {'delete': 1})

        # connect with wrong encryption
        self.fill_basic_config({'config_ldap_openldap':0,'config_ldap_encryption':'None'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        imprt = self.check_element_on_page((By.ID, "import_ldap_users"))
        self.assertTrue(imprt)
        imprt.click()
        time.sleep(3)
        # This time OpenLDAP config has no influence
        self.assertTrue('One LDAP User' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(2)


    def test_LDAP_SSL(self):
        # configure ssl LDAP
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
                                'config_ldap_authentication': 'Simple',
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
        self.server.relisten(config=1, port=3268, encrypt="SSL")
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
        self.server.stopListen()

    # @unittest.skip('Unknown how to test certificate')
    def test_LDAP_SSL_CERTIFICATE(self):
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH, 'files'), ignore_errors=True)
        os.makedirs(os.path.join(CALIBRE_WEB_PATH, 'files'))
        for f in ['ca.cert.pem', 'client.crt', 'client.key']:
            dest = os.path.join(CALIBRE_WEB_PATH, 'files', f)
            src = os.path.join(base_path, 'files', f)
            shutil.copy(src, dest)

        real_ca_file = os.path.join(CALIBRE_WEB_PATH, 'files', 'ca.cert.pem')
        real_cert_file = os.path.join(CALIBRE_WEB_PATH, 'files', 'client.crt')
        real_key_file = os.path.join(CALIBRE_WEB_PATH, 'files', 'client.key')

        # configure ssl LDAP
        self.fill_basic_config({'config_ldap_provider_url': socket.gethostname(),
                                'config_ldap_port': '3268',
                                'config_ldap_authentication': 'Simple',
                                'config_ldap_dn': 'ou=people,dc=calibreweb,dc=com',
                                'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com',
                                'config_ldap_serv_password': 'secret',
                                'config_ldap_user_object': '(uid=%s)',
                                'config_ldap_group_object_filter': '',
                                'config_ldap_openldap': 1,
                                'config_ldap_encryption': 'SSL',
                                'config_ldap_cacert_path': real_ca_file,
                                'config_ldap_cert_path': real_cert_file,
                                'config_ldap_key_path': real_key_file
                                })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # create new user
        # give user password different form ldap
        self.create_user('user0',{'email':'user0@exi.com','password':'1235'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # start SSl LDAP
        self.server.relisten(config=1, port=3268, encrypt="SSL", validate=True)
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
        # configure no certificate LDAP
        self.fill_basic_config({'config_ldap_cacert_path': '',
                                'config_ldap_key_path': '',
                                'config_ldap_cert_path': ''})
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
        self.server.stopListen()
        os.unlink(real_ca_file)
        os.unlink(real_cert_file)
        os.unlink(real_key_file)


    def test_LDAP_STARTTLS(self):
        # configure LDAP STARTTLS
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
                                'config_ldap_authentication': 'Simple',
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
        self.server.relisten(config=1, port=3268, encrypt="TLS")
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
        # try login without openLDAP config
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.fill_basic_config({'config_ldap_encryption': 'TLS','config_ldap_openldap':0})
        time.sleep(BOOT_TIME)
        self.logout()
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))

        # check login with wrong user object string
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.fill_basic_config({'config_ldap_user_object': 'uis%s','config_ldap_openldap':1})
        time.sleep(BOOT_TIME)
        self.logout()
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))

        # check login with wrong dn string
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.fill_basic_config({'config_ldap_user_object': 'uis=%s',
                                'config_ldap_dn':'ou=people,dc=calibrweb,dc=com'})
        time.sleep(BOOT_TIME)
        self.logout()
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))

        # check login with wrong admins password
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.fill_basic_config({'config_ldap_serv_password': 'sercet',
                                'config_ldap_dn':'ou=people,dc=calibreweb,dc=com'})
        time.sleep(BOOT_TIME)
        self.logout()
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))

        # check login with wrong admins name
        # ToDo:
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.fill_basic_config({'config_ldap_serv_password': 'secret',
                                'config_ldap_serv_username':'cn=rot,dc=calibreweb,dc=com'})
        time.sleep(BOOT_TIME)
        self.logout()
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))

        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.edit_user('user0', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # stop ldap
        self.server.stopListen()

    def test_ldap_about(self):
        self.assertTrue(self.goto_page('nav_about'))

    def test_ldap_authentication(self):
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
                                'config_ldap_authentication': 'Anonymous',
                                'config_ldap_dn': 'ou=people,dc=calibreweb,dc=com',
                                'config_ldap_user_object': 'uid=%s',
                                'config_ldap_group_object_filter': '',
                                'config_ldap_openldap': 1,
                                'config_ldap_encryption': 'None'
                                })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # create user
        self.create_user('user0',{'email':'user0@exi.com','password':'1236'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

        self.server.relisten(config=1, port=3268, encrypt=None, auth=0)
        # logout
        self.logout()
        # login as LDAP user
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # logout
        self.logout()

        # Change server to min unauthenticated
        self.server.relisten(config=1, port=3268, encrypt=None, auth=1)
        # login as LDAP user
        self.login('user0', 'terces')
        message=self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('admin login' in message.text)
        # login as admin
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        # change config to Unauthenticated
        self.fill_basic_config({'config_ldap_authentication': 'Unauthenticated',
                                'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # logout
        self.logout()
        # login as LDAP user
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # logout
        self.logout()
        # Change server to min authenticate
        self.server.relisten(config=1, port=3268, encrypt=None, auth=2)

        # login as LDAP user
        self.login('user0', 'terces')
        message = self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('admin login' in message.text)
        # login as admin

        # login as admin
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        # change config to Unauthenticated
        self.fill_basic_config({'config_ldap_authentication': 'Simple',
                                'config_ldap_serv_password': 'secret'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)

        self.logout()
        # login as LDAP user
        self.login('user0', 'terces')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        # login as admin
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.edit_user('user0', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # stop ldap
        self.server.stopListen()

    def test_ldap_opds_download_book(self):
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
                                'config_ldap_authentication': 'Simple',
                                'config_ldap_dn': 'ou=people,dc=calibreweb,dc=com',
                                'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com',
                                'config_ldap_serv_password': 'secret',
                                'config_ldap_user_object': '(uid=%s)',
                                'config_ldap_group_object_filter': '',
                                'config_ldap_openldap': 1
                                })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # start ldap
        self.server.relisten(config=2, port=3268, encrypt=None)
        # create new user
        self.create_user('执一',{'email':'use10@oxi.com','password':'1234', 'download_role': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()

        r = requests.get('http://127.0.0.1:8083/opds', auth=('admin', 'admin123'))
        self.assertEqual(401, r.status_code)
        # try to login with wron password for user
        r = requests.get('http://127.0.0.1:8083/opds', auth=('执一'.encode('utf-8'), 'wrong'))
        self.assertEqual(401, r.status_code)
        # login user and check content
        r = requests.get('http://127.0.0.1:8083/opds', auth=('执一'.encode('utf-8'), 'eekretsay'))
        self.assertEqual(200, r.status_code)
        elements = self.get_opds_index(r.text)
        r = requests.get('http://127.0.0.1:8083' + elements['Recently added Books']['link'], auth=('执一'.encode('utf-8'), 'eekretsay'))
        entries = self.get_opds_feed(r.text)
        # check download book
        r = requests.get('http://127.0.0.1:8083' + entries['elements'][0]['download'], auth=('执一'.encode('utf-8'), 'eekretsay'))
        self.assertEqual(len(r.content), 28590)
        self.assertEqual(r.headers['Content-Type'], 'application/pdf')
        # login admin and remove download role from 执一
        self.login("admin", "admin123")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.edit_user('执一', {'download_role': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        # try to download book without download rights
        r = requests.get('http://127.0.0.1:8083'+ entries['elements'][0]['download'], auth=('执一'.encode('utf-8'), 'terces'))
        self.assertEqual(401, r.status_code)
        # stop ldap
        self.server.stopListen()
        time.sleep(3)
        # try to login without ldap reachable
        r = requests.get('http://127.0.0.1:8083/opds', auth=('执一'.encode('utf-8'), 'eekretsay'))
        self.assertEqual(424, r.status_code)

        # login admin and delete user0
        self.login("admin", "admin123")
        self.edit_user('执一', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_ldap_opds_anonymous(self):
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
                                'config_ldap_authentication': 'Simple',
                                'config_ldap_dn': 'ou=people,dc=calibreweb,dc=com',
                                'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com',
                                'config_ldap_serv_password': 'secret',
                                'config_ldap_user_object': '(uid=%s)',
                                'config_ldap_group_object_filter': '',
                                'config_ldap_openldap': 1
                                })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # enable anonymous browsing
        self.fill_basic_config({'config_anonbrowse': 1})
        time.sleep(BOOT_TIME)
        # start ldap
        self.server.relisten(config=2, port=3268, encrypt=None)


        self.logout()
        r = requests.get('http://127.0.0.1:8083/opds')
        self.assertEqual(200, r.status_code)
        elements = self.get_opds_index(r.text)

        self.login("admin", "admin123")
        self.fill_basic_config({'config_anonbrowse': 0})

    def test_ldap_kobo_sync(self):
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
                                'config_ldap_authentication': 'Simple',
                                'config_ldap_dn': 'ou=people,dc=calibreweb,dc=com',
                                'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com',
                                'config_ldap_serv_password': 'secret',
                                'config_ldap_user_object': '(uid=%s)',
                                'config_ldap_group_object_filter': '',
                                'config_ldap_openldap': 1
                                })
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(BOOT_TIME)
        # start ldap
        self.server.relisten(config=2, port=3268, encrypt=None)
        # create new user
        self.create_user('执一',{'email':'use10@oxi.com','password':'1234', 'download_role': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        host = 'http://' + get_Host_IP() + ':8083'
        self.fill_basic_config({'config_kobo_sync': 1})
        time.sleep(BOOT_TIME)
        self.logout()
        self.driver.get(host)
        self.login('执一','eekretsay')
        self.goto_page('user_setup')
        self.check_element_on_page((By.ID, "config_create_kobo_token")).click()
        link = self.check_element_on_page((By.CLASS_NAME, "well"))
        self.kobo_adress = host + '/kobo/' + re.findall(".*/kobo/(.*)", link.text)[0]
        self.check_element_on_page((By.ID, "kobo_close")).click()
        time.sleep(2)
        self.logout()
        self.inital_sync(self.kobo_adress)

        self.login("admin", "admin123")
        self.edit_user('执一', {'delete': 1})
        self.fill_basic_config({'config_kobo_sync': 0})


