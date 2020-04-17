# -*- coding: utf-8 -*-

import unittest
import time
from helper_ui import ui_class
from testconfig import TEST_DB, VENV_PYTHON, CALIBRE_WEB_PATH, BOOT_TIME
from helper_func import startup, debug_startup, get_Host_IP, add_dependency, remove_dependency, kill_old_cps
from selenium.webdriver.common.by import By
from helper_ldap import TestLDApServer


class test_ldap_login(unittest.TestCase, ui_class):

    p=None
    driver = None
    kobo_adress = None
    dep_line = ["Flask-SimpleLDAP", "python-ldap"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dep_line, cls.__name__)

        try:
            cls.server = TestLDApServer(config=1, port=3268, encrypt=None)
            cls.server.start()
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,'config_login_type':'Use LDAP Authentication'})
            print('stop in setup')
            cls.server.stopListen()
        except Exception as e:
            cls.driver.quit()
            cls.p.terminate()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop_LdapServer()
        cls.p.terminate()
        cls.driver.quit()
        # close the browser window and stop calibre-web
        remove_dependency(cls.dep_line)

    @classmethod
    def tearDown(cls):
        try:
            cls.server.stopListen()
        except Exception as e:
            print(e)

    def test_invalid_LDAP(self):
        # set to default
        self.fill_basic_config({'config_ldap_provider_url': 'example.org',
                                'config_ldap_port': '389',
                                'config_ldap_dn': 'dc=example,dc=org',
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
        self.assertTrue('Service Account' in message.text)
        self.fill_basic_config({'config_ldap_serv_username': 'cn=root,dc=calibreweb,dc=com'})
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
        # leave groupOject filter unequal praenthesis
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
        self.fill_basic_config({'config_ldap_cert_path': 'nofile'})
        message= self.check_element_on_page((By.ID, "flash_alert"))
        self.assertTrue(message)
        self.assertTrue('Certificate Location' in message.text)
        self.fill_basic_config({'config_ldap_cert_path': ''})
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
        self.server.stopListen()
        self.login('admin','admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        # stop ldap

    def test_LDAP_import(self):
        # configure LDAP
        self.fill_basic_config({'config_ldap_provider_url': '127.0.0.1',
                                'config_ldap_port': '3268',
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
        users = ['执一','Mümmy']
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
        self.assertEqual(rights['show_512'], 1)
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
        self.edit_user('执一', {'show_512':0,'show_16':1,'passwd_role':0,'upload_role':1})
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
        self.assertEqual(rights['show_512'],0)
        self.assertEqual(rights['show_16'], 1)
        self.assertEqual(rights['passwd_role'], 0)
        self.assertEqual(rights['upload_role'], 1)

        self.edit_user('Mümmy', {'delete': 1})
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