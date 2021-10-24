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
    syncToken = None
    header = None
    json_line = ["jsonschema"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.json_line, cls.__name__)


        try:
            host = 'http://' + get_Host_IP() + ':8083'
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB, 'config_kobo_sync':1,
                                          'config_kepubifypath': "",
                                          'config_kobo_proxy':0}, host=host)
            add_books(os.path.join(TEST_DB, "metadata.db"), 120)
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

    def inital_sync(self):
        if TestKoboSyncBig.syncToken:
            return TestKoboSyncBig.data
        # generate payload for auth request
        payload = {
            "AffiliateName": "Kobo",
            "AppVersion": "4.19.14123",
            "ClientKey": "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMzc1",
            "DeviceId": "lnez00rs6cox274bx8c97kyr67ga3tnn0c1745tbjd9rmsmcywxmmcrw2zcayu6d",
            "PlatformId": "00000000-0000-0000-0000-000000000375",
            "UserKey": "12345678-9012-abcd-efgh-a7b6c0d8e7f2"
        }
        r = requests.post(self.kobo_adress + '/v1/auth/device', json=payload)
        self.assertEqual(r.status_code, 200)
        # request init request to get metadata format
        TestKoboSyncBig.header = {
            'Authorization': 'Bearer ' + r.json()['AccessToken'],
            'Content-Type': 'application/json'
        }
        expectUrl = '/'.join(self.kobo_adress.split('/')[0:-2])
        session = requests.session()
        r = session.get(self.kobo_adress+'/v1/initialization', headers=TestKoboSyncBig.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        # Check cover links
        self.assertEqual(len(r.json()), 1)
        self.assertEqual(r.json()['Resources']['image_host'], expectUrl)
        self.assertEqual(self.kobo_adress+"/{ImageId}/{width}/{height}/{Quality}/isGreyscale/image.jpg",
                         r.json()['Resources']['image_url_quality_template'])
        self.assertEqual(self.kobo_adress + "/{ImageId}/{width}/{height}/false/image.jpg",
                         r.json()['Resources']['image_url_template'])
        # perform user profile request
        r = session.get(self.kobo_adress+'/v1/user/profile', headers=TestKoboSyncBig.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})
        # perform benefits request
        r = session.get(self.kobo_adress+'/v1/user/loyalty/benefits', headers=TestKoboSyncBig.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})
        # perform analytics request
        r = session.get(self.kobo_adress+'/v1/analytics/gettests', headers=TestKoboSyncBig.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})

        # perform sync request
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        data = list()
        while True:
            r = session.get(self.kobo_adress+'/v1/library/sync',
                            params=params,
                            headers=TestKoboSyncBig.syncToken,
                            timeout=10)
            self.assertEqual(r.status_code, 200)
            data.append(r.json())
            TestKoboSyncBig.data = data
            TestKoboSyncBig.syncToken = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
            if not 'x-kobo-sync' in r.headers:
                break

        # perform whishlist request
        params = {'PageSize': '30', 'PageIndex': '0'}
        r = session.get(self.kobo_adress+'/v1/user/wishlist', params=params, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})

        # perform recommendation request
        params = {'page_index': '0', 'page_size': '50'}
        r = session.get(self.kobo_adress+'/v1/user/recommendations', params=params, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})
        # perform analytics request
        r = session.get(self.kobo_adress+'/v1/analytics/get', headers=TestKoboSyncBig.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})
        session.close()
        self.assertEqual(len(data[0]), 100)
        self.assertEqual(len(data[1]), 24)  # 120 new and 4 original books
        return data

    def sync_kobo(self):
        changeSession = requests.session()
        r = changeSession.get(self.kobo_adress+'/v1/initialization', headers=TestKoboSyncBig.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        data = list()
        while True:
            r = changeSession.get(self.kobo_adress+'/v1/library/sync', params=params,
                                  headers=TestKoboSyncBig.syncToken,
                                  timeout=10)
            self.assertEqual(r.status_code, 200)
            data.append(r.json())
            TestKoboSyncBig.data = data
            TestKoboSyncBig.syncToken = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
            if not 'x-kobo-sync' in r.headers:
                break
        changeSession.close()
        return data

    def test_sync_changed_book(self):
        self.inital_sync()
        # append synctoken to headers and start over again
        newSession = requests.session()
        r = newSession.get(self.kobo_adress+'/v1/initialization', headers=TestKoboSyncBig.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        r = newSession.get(self.kobo_adress+'/v1/library/sync', params=params,
                           headers=TestKoboSyncBig.syncToken,
                           timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])
        newSession.close()
        TestKoboSyncBig.syncToken = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
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
        # create private Shelf without sync, add book to it
        self.create_shelf("Unsyncd_shelf", sync=0)
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
        self.assertIn("NewTag", data3[2])
        self.assertIn("NewEntitlement", data3[0])
        self.create_user('kobosync', {'password': '123', 'email': 'da@b.com', "kobo_only_shelves_sync": 1})
        user_settings = self.get_user_settings('kobosync')
        self.assertTrue(user_settings["kobo_only_shelves_sync"])
        # check kobo only
        self.logout()
        self.login("kobosync","123")
        # 2.user erzeuge neuen shelf mit sync füge Bücher hinzu
        self.create_shelf("syncd_shelf_u2", sync=1)
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'syncd_shelf_u2')]")).click()
        self.logout()
        self.login("admin","admin123")
        self.assertEqual(0, len(self.sync_kobo()))  # nothing synced

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

