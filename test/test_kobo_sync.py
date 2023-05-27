#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import unittest
import requests

from helper_ui import ui_class
from config_test import TEST_DB, base_path, BOOT_TIME
from helper_func import startup, get_Host_IP, add_dependency, remove_dependency
from selenium.webdriver.common.by import By
from helper_func import save_logfiles
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestKoboSync(unittest.TestCase, ui_class):

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
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB, 'config_log_level': 'DEBUG', 'config_kobo_sync':1,
                                          'config_kepubifypath': "",
                                          'config_kobo_proxy':0}, host=host, env={"APP_MODE": "test"})
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
        if TestKoboSync.syncToken:
            return TestKoboSync.data
        # change book 5 to have unicode char in title author, description
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'description':u'b物',
                                'bookAuthor':u'John Döe执 & Mon Go',
                                'book_title': u'testbook执',
                                'publisher': u'Publish执',
                                'series': u'O0ü 执',
                                'series_index': '1.5',
                                'tags': u'O0ü 执, kobok'
                                })
        # generate payload for auth request
        payload = {
            "AffiliateName": "Kobo",
            "AppVersion": "4.19.14123",
            "ClientKey": "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMzc1",
            "DeviceId": "lnez00rs6cox274bx8c97kyr67ga3tnn0c1745tbjd9rmsmcywxmmcrw2zcayu6d",
            "PlatformId": "00000000-0000-0000-0000-000000000375",
            "UserKey": "12345678-9012-abcd-efgh-a7b6c0d8e7f2"
        }
        r = requests.post(self.kobo_adress+'/v1/auth/device', json=payload)
        self.assertEqual(r.status_code, 200)
        # request init request to get metadata format
        TestKoboSync.header = {
            'Authorization': 'Bearer ' + r.json()['AccessToken'],
            'Content-Type': 'application/json'
        }
        expectUrl = '/'.join(self.kobo_adress.split('/')[0:-2])
        session = requests.session()
        r = session.get(self.kobo_adress+'/v1/initialization', headers=TestKoboSync.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        # Check cover links
        self.assertEqual(len(r.json()), 1)
        self.assertEqual(r.json()['Resources']['image_host'], expectUrl)
        self.assertEqual(self.kobo_adress+"/{ImageId}/{width}/{height}/{Quality}/isGreyscale/image.jpg",
                         r.json()['Resources']['image_url_quality_template'])
        self.assertEqual(self.kobo_adress + "/{ImageId}/{width}/{height}/false/image.jpg",
                         r.json()['Resources']['image_url_template'])
        # perform user profile request
        r = session.get(self.kobo_adress+'/v1/user/profile', headers=TestKoboSync.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})
        # perform benefits request
        r = session.get(self.kobo_adress+'/v1/user/loyalty/benefits', headers=TestKoboSync.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'Benefits': {}})
        # perform analytics request
        r = session.get(self.kobo_adress+'/v1/analytics/gettests', headers=TestKoboSync.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'Result': 'Success', 'TestKey': '', 'Tests': {}})

        # perform sync request
        bood_uuid = '8f1b72c1-e9a4-4212-b538-8e4f4837d201'
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        data = {}
        while True:
            r = session.get(self.kobo_adress+'/v1/library/sync', params=params, headers=TestKoboSync.syncToken, timeout=10)
            self.assertEqual(r.status_code, 200)
            data = r.json()
            TestKoboSync.data = data
            TestKoboSync.syncToken = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
            # data = new_data
            if not 'x-kobo-sync' in r.headers:
                break
        self.assertEqual(len(data), 4, "4 Books should have valid kobo formats (epub, epub3, kebub)")
        self.assertGreaterEqual(2, len(data[3]['NewEntitlement']['BookMetadata']['DownloadUrls']), data)
        try:
            self.assertEqual(data[3]['NewEntitlement']['BookMetadata']['DownloadUrls'][1]['Format'], 'EPUB')
            self.assertEqual(data[3]['NewEntitlement']['BookMetadata']['DownloadUrls'][1]['Size'], 6720)
            self.assertEqual(data[3]['NewEntitlement']['BookMetadata']['DownloadUrls'][1]['Url'],
                             self.kobo_adress + "/download/5/epub")
            self.assertEqual(data[3]['NewEntitlement']['BookMetadata']['Contributors'], ['John Döe执', 'Mon Go'])
            self.assertEqual(data[3]['NewEntitlement']['BookMetadata']['CoverImageId'], bood_uuid)
            self.assertEqual('<p>b物</p>', data[3]['NewEntitlement']['BookMetadata']['Description'])
            self.assertEqual(data[3]['NewEntitlement']['BookMetadata']['Language'], 'en')
            self.assertEqual(data[3]['NewEntitlement']['BookMetadata']['Series']['Name'], 'O0ü 执')
            self.assertEqual(data[3]['NewEntitlement']['BookMetadata']['Series']['NumberFloat'], 1.5)
        except Exception as e:
            print(data)
            self.assertFalse(e, data)
        # ToDo: What shall it look like?
        #self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['Series']['Number'], 1)
        # ToDo What to expect
        # self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['PublicationDate'], '2017-01-19 00:00:00')
        self.assertEqual(data[3]['NewEntitlement']['BookMetadata']['Publisher']['Name'],
                         'Publish执')
        self.assertEqual(data[3]['NewEntitlement']['BookMetadata']['Title'],
                         'testbook执')
        self.assertEqual(data[3]['NewEntitlement']['BookEntitlement']['Created'],
                         '2017-01-20T20:00:15Z') # 'Tue, 05 Jul 2016 19:30:06 GMT'
        # check none series index is filled with number
        self.assertEqual(data[2]['NewEntitlement']['BookMetadata']['Series']['Number'], 1)
        # moving date
        #self.assertEqual(data[0]['NewEntitlement']['BookEntitlement']['LastModified'],
        #                 '2019-01-12T11:18:51Z') # 'Mon, 02 Apr 2018 16:35:50 GMT'
        # ToDo Check Reading state
        # self.assertEqual(data[0]['NewEntitlement']['ReadingState'], '')
        # perform image request of first book
        r = session.get(self.kobo_adress+'/' + bood_uuid + '/100/100/false/image.jpg', headers=TestKoboSync.header,
                        timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(16790, len(r.content))
        # perform image request of unknown book
        r = session.get(self.kobo_adress+'/100129102/100/100/false/image.jpg', headers=TestKoboSync.header, timeout=10)
        self.assertEqual(r.status_code, 404)
        # self.assertEqual(r.json(), {})

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
        r = session.get(self.kobo_adress+'/v1/analytics/get', headers=TestKoboSync.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})

        # perform nextread request
        r = session.get(self.kobo_adress + '/v1/products/2fe593b7-1389-4478-b66f-f07bf4c4d5b0/nextread',
                        headers=TestKoboSync.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})
        session.close()
        return data

    def sync_kobo(self):
        changeSession = requests.session()
        r = changeSession.get(self.kobo_adress+'/v1/initialization', headers=TestKoboSync.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        data = {}
        index = 0
        while True:
            r = changeSession.get(self.kobo_adress+'/v1/library/sync', params=params, headers=TestKoboSync.syncToken, timeout=10)
            self.assertEqual(r.status_code, 200)
            new_data = r.json()
            TestKoboSync.data = data
            TestKoboSync.syncToken = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
            if not 'x-kobo-sync' in r.headers:
                if not index:
                    TestKoboSync.data = new_data
                    data = new_data
                break
            index += 1
            data = new_data
        changeSession.close()
        return data


    def test_sync_invalid(self):
        payload = {
            "AffiliateName": "Kobo",
            "AppVersion": "4.19.14123",
            "ClientKey": "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMzc1",
            "DeviceId": "lnez00rs6cox274bx8c97kyr67ga3tnn0c1745tbjd9rmsmcywxmmcrw2zcayu6d",
            "PlatformId": "00000000-0000-0000-0000-000000000375",
            "UserKey": "12345678-9012-abcd-efgh-a7b6c0d8e7f2"
        }
        r = requests.post(self.kobo_adress+'x/v1/auth/device', json=payload, timeout=10)
        self.assertEqual(r.status_code, 401)
        header = {
            'Authorization': 'Bearer ' + '123456789',
            'Content-Type': 'application/json'
        }
        session = requests.session()
        r = session.get(self.kobo_adress+'x/v1/initialization', headers=header, timeout=10)
        self.assertEqual(r.status_code, 401)
        session.close()


    def test_sync_unchanged(self):
        self.inital_sync()

        # append synctoken to headers and start over again
        newSession = requests.session()
        r = newSession.get(self.kobo_adress+'/v1/initialization', headers=TestKoboSync.header, timeout=10)
        self.assertEqual(r.status_code, 200)
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        r = newSession.get(self.kobo_adress+'/v1/library/sync', params=params, headers=TestKoboSync.syncToken, timeout=10)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])
        newSession.close()
        TestKoboSync.syncToken = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}

    def test_sync_upload(self):
        self.inital_sync()
        # Upload new book
        # sync and get this book and nothing else
        self.fill_basic_config({'config_uploading':1})
        time.sleep(10)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.epub')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)

        # append synctoken to headers and start over again
        data = self.sync_kobo()
        self.assertEqual(1, len(data))
        self.assertEqual(['Noname 23'], data[0]['NewEntitlement']['BookMetadata']['Contributors'])
        self.assertEqual('book9', data[0]['NewEntitlement']['BookMetadata']['Title'])
        self.delete_book(15)


    def test_sync_changed_book(self):
        self.inital_sync()
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': u'testbook1'})
        time.sleep(2)

        # sync and get this book as changed entitlement instead of new one
        data = self.sync_kobo()
        self.assertEqual(1, len(data))
        self.assertTrue('ChangedEntitlement' in data[0])
        self.assertEqual(data[0]['ChangedEntitlement']['BookMetadata']['Title'],
                         'testbook1')

        # sync and no book
        data = self.sync_kobo()
        self.assertEqual(0, len(data))


    def test_sync_shelf(self):
        self.inital_sync()
        # create private shelf
        # self.edit_user('admin',{'edit_shelf_role': 1})
        self.create_shelf('adminShelf', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # sync, check shelf is synced-> empty
        data = self.sync_kobo()
        self.assertEqual(1, len(data))
        self.assertTrue('NewTag' in data[0])
        self.assertEqual('adminShelf', data[0]['NewTag']['Tag']['Name'])
        self.assertEqual('UserTag', data[0]['NewTag']['Tag']['Type'])
        self.assertEqual([], data[0]['NewTag']['Tag']['Items'])
        # create additional public shelf
        self.create_user('user0', {'password': '1234AbC*!', 'email': 'a@b.com', 'edit_shelf_role': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('user0', '1234AbC*!')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_shelf('adminShelf', True)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_shelf('userShelf', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('admin', 'admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # sync, check shelf is not synced
        data = self.sync_kobo()
        self.assertEqual(0, len(data))
        # delete private shelf
        self.delete_shelf("adminShelf")
        data = self.sync_kobo()
        self.assertEqual(1, len(data))
        self.assertTrue('Id' in data[0]['DeletedTag']['Tag'])


        books = self.get_books_displayed()
        self.get_book_details(int(books[1][0]['id']))   # book no. 13
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'adminShelf')]")).click()
        # sync, check public shelf is not synced -> 0 entry
        time.sleep(2)
        data = self.sync_kobo()
        self.assertEqual(0, len(data))
        # create new private shelf, add book, sync and check if book is in shelf
        self.create_shelf('privateShelf', False)
        self.goto_page('nav_new')
        data = self.sync_kobo()
        self.assertEqual(1, len(data))  # check new Tag is synced
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][0]['id']))   # book no. 13
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'privateShelf')]")).click()
        # ToDo works by change, because old entry is first one, click is independent of text
        self.check_element_on_page((By.XPATH, "//*[@id='remove-from-shelves']//a")).click()
        time.sleep(3)
        data = self.sync_kobo()
        self.assertEqual(1, len(data), data)
        self.assertEqual('privateShelf', data[0]['ChangedTag']['Tag']['Name'])
        self.assertEqual(1, len(data[0]['ChangedTag']['Tag']['Items']))
        tagId = data[0]['ChangedTag']['Tag']['Id']
        # Try to change name of shelf with wrong Id
        newSession = requests.session()
        newSession.get(self.kobo_adress+'/v1/initialization', headers=TestKoboSync.header)

        r = newSession.put(self.kobo_adress+'/v1/library/tags/'+tagId + '1',
                           headers=TestKoboSync.syncToken, data={'Name':'test'})
        self.assertEqual(404, r.status_code)

        # Try to change name of shelf with wrong Payload
        r = newSession.put(self.kobo_adress+'/v1/library/tags/'+tagId, json={'Nam':'test'})
        self.assertEqual(400, r.status_code)

        # Change name of shelf and check afterwards
        r = newSession.put(self.kobo_adress+'/v1/library/tags/'+tagId, json={'Name':'test'})
        self.assertEqual(200, r.status_code)
        self.goto_page('nav_new')
        shelfnames = self.list_shelfs()
        self.assertEqual('adminShelf (Public)', shelfnames[0]['name'])
        self.assertEqual('test', shelfnames[1]['name'])
        # Try to delete name of shelf with wrong Id
        r = newSession.delete(self.kobo_adress+'/v1/library/tags/'+tagId + '1')
        self.assertEqual(404, r.status_code)

        # Delete name of shelf
        r = newSession.delete(self.kobo_adress+'/v1/library/tags/'+  tagId)
        self.assertEqual(200, r.status_code)
        self.goto_page('nav_new')
        shelfnames = self.list_shelfs()
        self.assertEqual('adminShelf (Public)', shelfnames[0]['name'])
        self.assertEqual(1, len(shelfnames))

        # create shelf with empty payload
        r = newSession.post(self.kobo_adress + '/v1/library/tags')
        self.assertEqual(400, r.status_code)

        # create shelf with empty name and Items
        r = newSession.post(self.kobo_adress + '/v1/library/tags', json={'Name':'', 'Items': []})
        self.assertEqual(400, r.status_code)

        # create shelf with empty name and Items
        Item1 = {'Type': 'ProductRevisionTagItem', 'RevisionId':'8f1b72c1-e9a4-4212-b538-8e4f4837d201'}
        ItemDefect = {'Typ': 'ProductRevisionTagItem', 'RevisionId': '1'}
        r = newSession.post(self.kobo_adress + '/v1/library/tags', json={'Name':'执', 'Items':[ItemDefect]})
        self.assertEqual(201, r.status_code)    # malformed Items are silently denied
        r = newSession.post(self.kobo_adress + '/v1/library/tags', json={'Name': 'Success', 'Items': [Item1]})
        self.assertEqual(201, r.status_code)
        self.goto_page('nav_new')
        self.list_shelfs(u'Success')['ele'].click()
        books = self.get_shelf_books_displayed()
        self.assertEqual(1, len(books))
        self.assertEqual('5', books[0]['id'])

        #create 2 shelfs with identical names
        r = newSession.post(self.kobo_adress + '/v1/library/tags', json={'Name': 'Dup1', 'Items': []})
        self.assertEqual(201, r.status_code)
        r = newSession.post(self.kobo_adress + '/v1/library/tags', json={'Name': 'Dup1', 'Items': [Item1]})
        self.assertEqual(201, r.status_code)
        self.goto_page('nav_new')
        self.list_shelfs(u'Dup1')['ele'].click()
        books = self.get_shelf_books_displayed()
        self.assertEqual(1, len(books))
        self.assertEqual('5', books[0]['id'])

        # logout, login new user, create shelf for new user
        # self.logout()
        # self.login('user0','123AbC*!')
        # self.create_shelf('new_user', True)
        # data = self.sync_kobo() # sync to get id of shelf
        # self.change_shelf('new_user', public=0)

        # ToDo:
        # request new user shelf -> error
        # request delete of new user shelf via kobo-> error
        # r = requests.put(self.kobo_adress+'/v1/library/tags/'+tagId, headers=self.syncToken, data={'Name':'test'})
        # self.assertEqual(401, r.status_code)

        # logout
        # self.logout()
        # self.login('admin','admin123')
        newSession.close()
        # delete user
        self.edit_user('user0', {'delete': 1})
        shelfs = self.list_shelfs()
        for shelf in shelfs:
            self.delete_shelf(shelf['name'])
        # final sync
        time.sleep(2)
        self.sync_kobo()


    def test_shelves_add_remove_books(self):
        self.inital_sync()
        # create private shelf
        newSession = requests.session()
        newSession.get(self.kobo_adress+'/v1/initialization', headers=TestKoboSync.header)

        r = newSession.post(self.kobo_adress + '/v1/library/tags', json={'Name': 'BooksAdd', 'Items': []})
        self.assertEqual(201, r.status_code)
        tagId = r.json()
        # sync, check shelf is synced-> empty
        data = self.sync_kobo()

        Item1 = {'Type': 'ProductRevisionTagItem', 'RevisionId':'8f1b72c1-e9a4-4212-b538-8e4f4837d201'}
        ItemDefect = {'Typ': 'ProductRevisionTagItem', 'RevisionId': '1'}

        # post empty request
        request_header = {"Content-Type": "application/json; charset=utf-8"}
        r = newSession.post(self.kobo_adress + '/v1/library/tags/' + tagId + '/items', headers=request_header)
        self.assertEqual(400, r.status_code)
        r = newSession.post(self.kobo_adress + '/v1/library/tags/' + tagId + '/items', json={'Item': []})
        self.assertEqual(400, r.status_code)
        r = newSession.post(self.kobo_adress + '/v1/library/tags/1234/items', json={'Items': [ItemDefect]})
        self.assertEqual(404, r.status_code)
        r = newSession.post(self.kobo_adress + '/v1/library/tags/' + tagId + '/items', json={'Items': [ItemDefect]})
        self.assertEqual(201, r.status_code)
        self.goto_page('nav_new')
        self.list_shelfs(u'BooksAdd')['ele'].click()
        books = self.get_shelf_books_displayed()
        self.assertEqual(0, len(books))

        r = newSession.post(self.kobo_adress + '/v1/library/tags/' + tagId + '/items', json={'Items': [Item1]})
        self.assertEqual(201, r.status_code)
        self.goto_page('nav_new')
        self.list_shelfs(u'BooksAdd')['ele'].click()
        books = self.get_shelf_books_displayed()
        self.assertEqual(1, len(books))
        self.assertEqual('5', books[0]['id'])

        # Delete books from shelf
        r = newSession.post(self.kobo_adress + '/v1/library/tags/' + tagId + '/items/delete', headers=request_header)
        self.assertEqual(400, r.status_code)
        r = newSession.post(self.kobo_adress + '/v1/library/tags/' + tagId + '/items/delete', json={'Item': []})
        self.assertEqual(400, r.status_code)
        r = newSession.post(self.kobo_adress + '/v1/library/tags/1234/items/delete', json={'Items': [ItemDefect]})
        self.assertEqual(404, r.status_code)
        r = newSession.post(self.kobo_adress + '/v1/library/tags/' + tagId + '/items/delete', json={'Items': [ItemDefect]})
        self.assertEqual(200, r.status_code)
        self.goto_page('nav_new')
        self.list_shelfs(u'BooksAdd')['ele'].click()
        books = self.get_shelf_books_displayed()
        self.assertEqual(1, len(books))

        r = newSession.post(self.kobo_adress + '/v1/library/tags/' + tagId + '/items/delete', json={'Items': [Item1]})
        self.assertEqual(200, r.status_code)
        self.goto_page('nav_new')
        self.list_shelfs(u'BooksAdd')['ele'].click()
        books = self.get_shelf_books_displayed()
        self.assertEqual(0, len(books))
        newSession.close()

        shelfs = self.list_shelfs()
        for shelf in shelfs:
            self.delete_shelf(shelf['name'])
        time.sleep(2)
        # final sync
        self.sync_kobo()


    def test_sync_reading_state(self):
        self.inital_sync()
        # reading state
        newSession = requests.session()
        r = newSession.get(self.kobo_adress+'/v1/initialization', headers=TestKoboSync.header)

        r = newSession.get(self.kobo_adress + '/v1/library/77/state')
        self.assertEqual(200, r.status_code)
        self.assertEqual({}, r.json())

        # book no 5
        r = newSession.get(self.kobo_adress + '/v1/library/8f1b72c1-e9a4-4212-b538-8e4f4837d201/state')
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual('8f1b72c1-e9a4-4212-b538-8e4f4837d201', data[0]['EntitlementId'])
        self.assertEqual('ReadyToRead', data[0]['StatusInfo']['Status'])

        headers = {"Content-Type": "application/json; charset=utf-8"}
        r = newSession.put(self.kobo_adress + '/v1/library/8f1b72c1-e9a4-4212-b538-8e4f4837d201/state', headers=headers)
        self.assertEqual(400, r.status_code)
        postData = {
            "ReadingStates":[{
                "CurrentBookmark": {
                    "ProgressPercent":'40',
                    "ContentSourceProgressPercent": '20',
                    "Location": {
                        "Value":'10',
                        "Type": 'Unknown',
                        "Source": 'Unknown'
                    }
                },
                "Statistics": {
                    "SpentReadingMinutes": '100',
                    "RemainingTimeMinutes": '20'
                },
                "StatusInfo": {
                    "Status":'Reading'
                }
            }]
        }
        r = newSession.put(self.kobo_adress + '/v1/library/8f1b72c1-e9a4-4212-b538-8e4f4837d201/state',
                           json=postData)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual('Success', data['RequestResult'])
        self.assertEqual('Success', data['UpdateResults'][0]['StatisticsResult']['Result'])

        postData['ReadingStates'][0]['CurrentBookmark']['ProgressPercent'] = 'Nijik'
        r = newSession.put(self.kobo_adress + '/v1/library/8f1b72c1-e9a4-4212-b538-8e4f4837d201/state',
                           json=postData)
        self.assertEqual(400, r.status_code)
        postData['ReadingStates'][0]['CurrentBookmark']['ProgressPercent'] = '30'
        postData['ReadingStates'][0]['Statistics']['SpentReadingMinutes'] = 'gigj'
        r = newSession.put(self.kobo_adress + '/v1/library/8f1b72c1-e9a4-4212-b538-8e4f4837d201/state',
                           json=postData)
        self.assertEqual(400, r.status_code)

        newSession.close()

        shelfs = self.list_shelfs()
        for shelf in shelfs:
            self.delete_shelf(shelf['name'])

        # final sync
        time.sleep(2)
        self.sync_kobo()

    def test_kobo_about(self):
        self.assertTrue(self.goto_page('nav_about'))

    def test_book_download(self):
        data = self.inital_sync()
        downloadSession = requests.session()
        r = downloadSession.get(self.kobo_adress+'/v1/initialization', headers=TestKoboSync.header)
        self.assertEqual(r.status_code, 200)
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        r = downloadSession.get(self.kobo_adress+'/v1/library/sync', params=params, headers=TestKoboSync.syncToken)
        self.assertEqual(r.status_code, 200)
        TestKoboSync.syncToken = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
        self.assertGreaterEqual(2, len(data[0]['NewEntitlement']['BookMetadata']['DownloadUrls']), data)
        try:
            download = downloadSession.get(data[0]['NewEntitlement']['BookMetadata']['DownloadUrls'][1]['Url'], headers=TestKoboSync.header)
            self.assertEqual(200, download.status_code)
            self.assertEqual('application/epub+zip', download.headers['Content-Type'])
            downloadSession.close()
        except Exception as e:
            print(e)
            self.assertFalse(e, data)

    def test_kobo_sync_selected_shelfs(self):
        data = self.inital_sync()
        self.assertEqual(4, len(data))
        self.change_visibility_me({"kobo_only_shelves_sync": 1})
        # create private Shelf without sync, add book to it
        self.create_shelf("Unsyncd_shelf", sync=0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'Unsyncd_shelf')]")).click()

        self.assertEqual(0, len(self.sync_kobo()))

        self.create_shelf("syncd_shelf_u1", sync=1)
        self.get_book_details(10)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'syncd_shelf_u1')]")).click()
        data3 = self.sync_kobo()  # 1 book synced, reading state changed as book was modified due to adding to shelf(?)
        self.assertIn("NewTag", data3[1])
        self.assertIn("NewEntitlement", data3[0])
        self.create_user('kobosync', {'password': '123AbC*!', 'email': 'da@b.com', "kobo_only_shelves_sync": 1})
        user_settings = self.get_user_settings('kobosync')
        self.assertTrue(user_settings["kobo_only_shelves_sync"])
        # check kobo only
        self.logout()
        self.login("kobosync","123AbC*!")
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

    def test_kobo_upload_book(self):
        self.inital_sync()
        self.fill_basic_config({'config_uploading': 1})
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        self.edit_user('admin', {'upload_role': 1})
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.epub')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(3)
        data = self.sync_kobo()
        print(data) # todo check result

    def test_kobo_limit(self):
        host = 'http://' + get_Host_IP() + ':8083'
        payload = {
            "AffiliateName": "Kobo",
            "AppVersion": "4.19.14123",
            "ClientKey": "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMzc1",
            "DeviceId": "lnez00rs6cox274bx8c97kyr67ga3tnn0c1745tbjd9rmsmcywxmmcrw2zcayu6d",
            "PlatformId": "00000000-0000-0000-0000-000000000375",
            "UserKey": "12345678-9012-abcd-efgh-a7b6c0d8e7f2"
        }
        # request several times the same endpoint with different hashes within one minute, from same ip address
        for i in range(1, 4):
            r = requests.post(host + '/kobo/tesit/v1/auth/device', json=payload)
            self.assertEqual(401, r.status_code)
        # after x tries get 429
        r = requests.post(host + '/kobo/tesit/v1/auth/device', json=payload)
        self.assertEqual(429, r.status_code)
        # try to use working endpoint not working
        r = requests.post(self.kobo_adress + '/v1/auth/device', json=payload)
        self.assertEqual(429, r.status_code)
        # wait one minute
        time.sleep(61)
        # access wrong endpoint again -> error 401
        r = requests.post(host + '/kobo/tesit/v1/auth/device', json=payload)
        self.assertEqual(401, r.status_code)
        # access right endpoint -> working
        r = requests.post(self.kobo_adress + '/v1/auth/device', json=payload)
        self.assertEqual(200, r.status_code)
        # switch of limit, logout
        self.fill_basic_config({"config_ratelimiter": 0})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        # request several times the same endpoint with different hashes within one minute, from same ip address -> working all the time
        for i in range(1, 5):
            r = requests.post(host + '/kobo/tesit/v1/auth/device', json=payload)
            self.assertEqual(401, r.status_code)
        r = requests.post(self.kobo_adress + '/v1/auth/device', json=payload)
        self.assertEqual(200, r.status_code)
        # switch on limit again
        self.login("admin", "admin123")
        self.fill_basic_config({"config_ratelimiter":1, 'config_public_reg':0})
        time.sleep(BOOT_TIME)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
