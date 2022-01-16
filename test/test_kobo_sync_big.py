#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import unittest
import requests
import json

from helper_ui import ui_class
from config_test import TEST_DB, base_path
from helper_func import startup, debug_startup, get_Host_IP, add_dependency, remove_dependency
from helper_db import add_books
from selenium.webdriver.common.by import By
from helper_func import save_logfiles
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestKoboSyncBig(unittest.TestCase, ui_class):

    p = None
    driver = None
    kobo_adress = None
    syncToken = dict()
    header = dict()
    data = dict()
    json_line = ["jsonschema"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.json_line, cls.__name__)


        try:
            host = 'http://' + get_Host_IP() + ':8083'
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_kobo_sync': 1,
                                          'config_kepubifypath': "",
                                          # 'config_log_level': 'DEBUG',
                                          'config_kobo_proxy': 0}, host=host)
            add_books(os.path.join(TEST_DB, "metadata.db"), 1520)    #1520
            time.sleep(3)
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
            cls.goto_page('user_setup')
            cls.check_element_on_page((By.ID, "config_create_kobo_token")).click()
            link = cls.check_element_on_page((By.CLASS_NAME, "well"))
            cls.kobo_adress = host + '/kobo/' + re.findall(".*/kobo/(.*)", link.text)[0]
            cls.check_element_on_page((By.ID, "kobo_close")).click()
            cls.driver.get('http://127.0.0.1:8083')
            cls.login('admin', 'admin123')
            time.sleep(2)
        except Exception as e:
            print(e)
            cls.driver.quit()
            cls.p.terminate()
            cls.p.poll()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        cls.driver.quit()
        cls.p.terminate()
        # close the browser window and stop calibre-web
        remove_dependency(cls.json_line)
        save_logfiles(cls, cls.__name__)

    def inital_sync(self, user_id=None):
        koboaddress = user_id or self.kobo_adress
        if TestKoboSyncBig.syncToken.get(koboaddress):
            return TestKoboSyncBig.data.get(koboaddress)
        # generate payload for auth request
        payload = {
            "AffiliateName": "Kobo",
            "AppVersion": "4.19.14123",
            "ClientKey": "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMzc1",
            "DeviceId": "lnez00rs6cox274bx8c97kyr67ga3tnn0c1745tbjd9rmsmcywxmmcrw2zcayu6d",
            "PlatformId": "00000000-0000-0000-0000-000000000375",
            "UserKey": "12345678-9012-abcd-efgh-a7b6c0d8e7f2"
        }
        r = requests.post(koboaddress + '/v1/auth/device', json=payload, timeout=1000)
        self.assertEqual(r.status_code, 200)
        # request init request to get metadata format
        TestKoboSyncBig.header[koboaddress] = {
            'Authorization': 'Bearer ' + r.json()['AccessToken'],
            'Content-Type': 'application/json'
        }
        expectUrl = '/'.join(koboaddress.split('/')[0:-2])
        session = requests.session()
        r = session.get(koboaddress+'/v1/initialization', headers=TestKoboSyncBig.header.get(koboaddress), timeout=10)
        self.assertEqual(r.status_code, 200)
        # Check cover links
        self.assertEqual(len(r.json()), 1)
        self.assertEqual(r.json()['Resources']['image_host'], expectUrl)
        self.assertEqual(koboaddress + "/{ImageId}/{width}/{height}/{Quality}/isGreyscale/image.jpg",
                         r.json()['Resources']['image_url_quality_template'])
        self.assertEqual(koboaddress + "/{ImageId}/{width}/{height}/false/image.jpg",
                         r.json()['Resources']['image_url_template'])
        # perform user profile request
        r = session.get(koboaddress + '/v1/user/profile', headers=TestKoboSyncBig.header.get(koboaddress), timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})
        # perform benefits request
        r = session.get(koboaddress + '/v1/user/loyalty/benefits', headers=TestKoboSyncBig.header.get(koboaddress), timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'Benefits': {}})
        # perform analytics request
        r = session.get(koboaddress + '/v1/analytics/gettests', headers=TestKoboSyncBig.header.get(koboaddress), timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'Result': 'Success', 'TestKey': '', 'Tests': {}})

        # perform sync request
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        data = list()
        while True:
            r = session.get(koboaddress + '/v1/library/sync',
                            params=params,
                            headers=TestKoboSyncBig.syncToken.get(koboaddress),
                            timeout=10000)
            self.assertEqual(r.status_code, 200)
            data.append(r.json())
            TestKoboSyncBig.data[koboaddress] = data
            TestKoboSyncBig.syncToken[koboaddress] = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
            if not 'x-kobo-sync' in r.headers:
                break

        # perform whishlist request
        params = {'PageSize': '30', 'PageIndex': '0'}
        r = session.get(koboaddress + '/v1/user/wishlist', params=params, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})

        # perform recommendation request
        params = {'page_index': '0', 'page_size': '50'}
        r = session.get(koboaddress + '/v1/user/recommendations', params=params, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})
        # perform analytics request
        r = session.get(koboaddress + '/v1/analytics/get', headers=TestKoboSyncBig.header.get(koboaddress), timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})
        session.close()
        self.assertEqual(100, len(data[0]))
        self.assertEqual(24, len(data[-1]))  # 120 new and 4 original books
        return data

    def sync_kobo(self, user_id=None):
        koboaddress = user_id or self.kobo_adress
        changeSession = requests.session()
        r = changeSession.get(koboaddress + '/v1/initialization', headers=TestKoboSyncBig.header.get(koboaddress)
                              , timeout=10)
        self.assertEqual(r.status_code, 200)
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        data = list()
        while True:
            r = changeSession.get(koboaddress + '/v1/library/sync', params=params,
                                  headers=TestKoboSyncBig.syncToken.get(koboaddress),
                                  timeout=10000)
            self.assertEqual(r.status_code, 200)
            data.append(r.json())
            TestKoboSyncBig.data[koboaddress] = data
            TestKoboSyncBig.syncToken[koboaddress] = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
            if not 'x-kobo-sync' in r.headers:
                break
        changeSession.close()
        return data

    def test_sync_changed_book(self):
        self.inital_sync()
        # append synctoken to headers and start over again
        newSession = requests.session()
        r = newSession.get(self.kobo_adress+'/v1/initialization', headers=TestKoboSyncBig.header.get(self.kobo_adress),
                           timeout=10)
        self.assertEqual(r.status_code, 200)
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        r = newSession.get(self.kobo_adress+'/v1/library/sync', params=params,
                           headers=TestKoboSyncBig.syncToken.get(self.kobo_adress),
                           timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])
        newSession.close()
        TestKoboSyncBig.syncToken[self.kobo_adress] = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': u'testbook1'})
        time.sleep(2)

        # sync and get this book as changed entitlement instead of new one
        data = self.sync_kobo()
        self.assertEqual(1, len(data))
        self.assertTrue('ChangedEntitlement' in data[0][0])
        self.assertEqual(data[0][0]['ChangedEntitlement']['BookMetadata']['Title'],
                         'testbook1')
        # sync and no book
        data = self.sync_kobo()
        self.assertEqual(0, len(data[0]))

    def test_sync_shelf(self):
        self.inital_sync()
        # create private shelf
        self.create_shelf('syncShelf', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # sync, check shelf is synced-> empty
        data = self.sync_kobo()
        self.assertEqual(1, len(data))
        self.assertEqual(1, len(data[0]))
        self.assertTrue('NewTag' in data[0][0])
        self.assertEqual('syncShelf', data[0][0]['NewTag']['Tag']['Name'])
        self.assertEqual('UserTag', data[0][0]['NewTag']['Tag']['Type'])
        self.assertEqual([], data[0][0]['NewTag']['Tag']['Items'])
        # sync again, nothing more synced
        data = self.sync_kobo()
        self.assertEqual(0, len(data[0]))

        # add 105 books to shelf
        for i in range(15, 120):
            self.get_book_details(i)
            self.check_element_on_page((By.ID, "add-to-shelf")).click()
            self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'syncShelf')]")).click()
        time.sleep(3)
        data = self.sync_kobo()
        self.assertEqual(len(data[0][0]['ChangedTag']['Tag']['Items']), 105)
        # remove 103 books to shelf
        for i in range(15, 118):
            self.get_book_details(i)
            self.check_element_on_page((By.XPATH, "//*[@id='remove-from-shelves']//a")).click()
        # sync, 2 books remaining
        data = self.sync_kobo()
        self.assertEqual(len(data[0][0]['ChangedTag']['Tag']['Items']), 2)

        shelfs = self.list_shelfs()
        for shelf in shelfs:
            self.delete_shelf(shelf['name'])
        # final sync
        time.sleep(2)
        data = self.sync_kobo()
        self.assertEqual(1, len(data[0]))
        self.assertTrue('DeletedTag' in data[0][0])
        data = self.sync_kobo()
        self.assertEqual(0, len(data[0]))

    def test_sync_reading_state(self):
        self.inital_sync()
        # add 105 books read state in UI
        for i in range(15, 120):
            self.get_book_details(i)
            self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        # reading state
        data = self.sync_kobo()
        self.assertEqual(len(data[0]), 100)
        self.assertEqual(len(data[1]), 5)  # 120 new and 4 original books
        self.assertIn('ChangedReadingState', data[0][0])
        # add 105 books read state in UI
        for i in range(15, 118):
            self.get_book_details(i)
            self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        data = self.sync_kobo()
        self.assertEqual(len(data[0]), 100)
        self.assertEqual(len(data[1]), 3)  # 120 new and 4 original books
        self.assertIn('ChangedReadingState', data[0][0])
        time.sleep(2)
        data = self.sync_kobo()
        self.assertEqual(0, len(data[0]))

    def test_kobo_sync_selected_shelfs(self):
        self.inital_sync()
        self.change_visibility_me({"kobo_only_shelves_sync": 1})
        time.sleep(40)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # create private Shelf without sync, add book to it
        self.create_shelf("Unsyncd_shelf", sync=0)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'Unsyncd_shelf')]")).click()
        data = self.sync_kobo()
        self.assertEqual(0, len(data[0]))

        self.create_shelf("syncd_shelf_u1", sync=1)
        # add 105 books to shelf
        for i in range(15, 120):
            self.get_book_details(i)
            self.check_element_on_page((By.ID, "add-to-shelf")).click()
            self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'syncd_shelf_u1')]")).click()

        data3 = self.sync_kobo()  # 1 book synced, reading state changed as book was modified due to adding to shelf(?)
        self.assertIn("NewTag", data3[0][-1])
        # self.assertFalse('DeletedTag' in data[0][-2])
        self.assertIn("NewEntitlement", data3[0][0])
        self.create_user('kobosync', {'password': '123', 'email': 'da@b.com', "kobo_only_shelves_sync": 1})
        user_settings = self.get_user_settings('kobosync')
        self.assertTrue(user_settings["kobo_only_shelves_sync"])
        # check kobo only
        self.logout()
        self.login("kobosync","123")
        # 2.user creates new shelf and adds books
        self.create_shelf("syncd_shelf_u2", sync=1)
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'syncd_shelf_u2')]")).click()
        self.logout()
        self.login("admin","admin123")
        self.assertEqual(0, len(self.sync_kobo()[0]))  # nothing synced

        # Cleanup
        self.change_visibility_me({"kobo_only_shelves_sync": 0})
        self.delete_shelf('Unsyncd_shelf')
        self.delete_shelf('syncd_shelf_u1')
        self.edit_user('kobosync', {'delete': 1})

        # unarchive books
        self.get_book_details(10)
        self.check_element_on_page((By.XPATH, "//*[@id='archived_cb']")).click()
        self.get_book_details(9)
        self.check_element_on_page((By.XPATH, "//*[@id='archived_cb']")).click()
        self.get_book_details(8)
        self.check_element_on_page((By.XPATH, "//*[@id='archived_cb']")).click()
        self.get_book_details(5)
        self.check_element_on_page((By.XPATH, "//*[@id='archived_cb']")).click()
        for i in range(15, 134):
            self.get_book_details(i)
            self.check_element_on_page((By.XPATH, "//*[@id='archived_cb']")).click()

        self.sync_kobo()

    def test_kobo_sync_multi_user(self):
        # create 2 users
        self.create_user('user1', {'password': '123', 'email': 'ada@b.com', "edit_role":1, "download_role": 1})
        self.create_user('user2', {'password': '321', 'email': 'aba@b.com', "edit_role":1, "download_role": 1})
        host = 'http://' + get_Host_IP() + ':8083'
        self.driver.get(host)   # still logged in
        # create links for both users
        self.navigate_to_user("user1")
        self.check_element_on_page((By.ID, "config_create_kobo_token")).click()
        link = self.check_element_on_page((By.CLASS_NAME, "well"))
        user1_kobo = host + '/kobo/' + re.findall(".*/kobo/(.*)", link.text)[0]
        self.check_element_on_page((By.ID, "kobo_close")).click()
        time.sleep(1) # wait for dialog to close
        self.goto_page("nav_new")   # otherwise there is a chance that page change is not detected
        self.navigate_to_user("user2")
        self.check_element_on_page((By.ID, "config_create_kobo_token")).click()
        link = self.check_element_on_page((By.CLASS_NAME, "well"))
        user2_kobo = host + '/kobo/' + re.findall(".*/kobo/(.*)", link.text)[0]
        self.check_element_on_page((By.ID, "kobo_close")).click()
        # sync user 1
        # check number of books synced (-> is done in inital_sync)
        self.inital_sync(user1_kobo)
        # sync user 2
        # check number of books synced (-> is done in inital_sync)
        self.inital_sync(user2_kobo)
        # change one book
        self.get_book_details(104, host)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': u'Nonomatics'})
        # sync both user -> both get the new book synced
        data1 = self.sync_kobo(user1_kobo)
        data2 = self.sync_kobo(user2_kobo)
        self.assertEqual(1, len(data1[0]))
        self.assertEqual(1, len(data2[0]))
        self.assertIn('ChangedEntitlement', data1[0][0])
        self.assertIn('ChangedEntitlement', data2[0][0])
        # upload one book
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        new_epub_file = os.path.join(base_path, 'files', 'book.epub')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(new_epub_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(1)
        book_details = self.get_book_details(-1, host)
        # sync both user -> both get the new book synced
        data1 = self.sync_kobo(user1_kobo)
        data2 = self.sync_kobo(user2_kobo)
        self.assertEqual(1, len(data1[0]))
        self.assertEqual(1, len(data2[0]))
        self.assertIn('NewEntitlement', data1[0][0])
        self.assertIn('NewEntitlement', data2[0][0])

        self.fill_basic_config({'config_uploading': 0})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # delete book to make book count as before
        self.delete_book(book_details['id'], host)
        data1 = self.sync_kobo(user1_kobo)
        data2 = self.sync_kobo(user2_kobo)
        self.assertEqual(0, len(data1[0]))
        self.assertEqual(0, len(data2[0]))
        # archive one book for user 1 in cw (is archived last_modified value?)
        self.logout()
        self.login("user1", "123")
        self.get_book_details(110, host)
        self.check_element_on_page((By.XPATH, "//*[@id='archived_cb']")).click()
        # sync books for both user -> only archived for user1
        data1 = self.sync_kobo(user1_kobo)
        data2 = self.sync_kobo(user2_kobo)
        self.assertEqual(1, len(data1[0]))
        self.assertEqual(0, len(data2[0]))
        self.assertIn('ChangedEntitlement', data1[0][0])
        self.logout()
        # archive one book for user 2 on kobo
        self.login("user2", "321")
        self.get_book_details(140, host)
        self.check_element_on_page((By.XPATH, "//*[@id='archived_cb']")).click()
        self.logout()
        # sync books for both user -> only archived for user2
        data1 = self.sync_kobo(user1_kobo)
        data2 = self.sync_kobo(user2_kobo)
        self.assertEqual(0, len(data1[0]))
        self.assertEqual(1, len(data2[0]))
        self.assertIn('ChangedEntitlement', data2[0][0])
        # create shelf for one user add books
        # sync books for both user -> only changed for user1
        self.login("user1", "123")
        self.create_shelf('syncShelf', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(122, host)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'syncShelf')]")).click()
        self.get_book_details(55, host)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'syncShelf')]")).click()
        self.logout()
        data1 = self.sync_kobo(user1_kobo)
        data2 = self.sync_kobo(user2_kobo)
        self.assertEqual(1, len(data1[0]))
        self.assertEqual(0, len(data2[0]))
        self.assertIn('NewTag', data1[0][0])
        self.assertEqual(2, len(data1[0][0]['NewTag']['Tag']['Items']))
        # switch user2 to sync selected shelfs and add books
        self.login("user2", "321")
        self.create_shelf('syncShelf2', False)
        self.get_book_details(122, host)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'syncShelf2')]")).click()
        self.get_book_details(56, host)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'syncShelf2')]")).click()
        self.change_visibility_me({"kobo_only_shelves_sync": 1})
        time.sleep(40)   # ToDo: Revert to 40
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.change_shelf('syncShelf2', sync=1)
        self.logout()
        # sync books for both user -> only changed for user2
        data1 = self.sync_kobo(user1_kobo)
        data2 = self.sync_kobo(user2_kobo)
        self.assertEqual(0, len(data1[0]))
        self.assertEqual(3, len(data2[0]))
        self.assertTrue('NewTag' in data2[0][-1])
        self.assertFalse('DeletedTag' in data2[0][-2])
        self.assertEqual(2, len(data2[0][2]['NewTag']['Tag']['Items']))

        # Todo Fix and check user2 sync result
        self.login("admin", "admin123")
        self.edit_user("user1", {"delete":1})
        self.edit_user("user2", {"delete":1})
        self.driver.get('http://127.0.0.1:8083') # still logged in
