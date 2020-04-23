# -*- coding: utf-8 -*-

import unittest
import requests
from helper_ui import ui_class
from testconfig import TEST_DB, VENV_PYTHON, CALIBRE_WEB_PATH, base_path
from helper_func import startup, debug_startup, get_Host_IP, add_dependency, remove_dependency, kill_old_cps
from selenium.webdriver.common.by import By
import os
import re
import time

class test_kobo_sync(unittest.TestCase, ui_class):

    p=None
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
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB,'config_kobo_sync':1,
                                                'config_kobo_proxy':0}, host= host)
            cls.goto_page('user_setup')
            cls.check_element_on_page((By.ID, "config_create_kobo_token")).click()
            link = cls.check_element_on_page((By.CLASS_NAME, "well"))
            cls.kobo_adress = host + '/kobo/' + re.findall(".*/kobo/(.*)",link.text)[0]
            cls.check_element_on_page((By.ID, "kobo_close")).click()
            cls.driver.get('http://127.0.0.1:8083')
            cls.login('admin','admin123')
            time.sleep(2)
        except:
            cls.driver.quit()
            cls.p.terminate()
            cls.p.poll()

    @classmethod
    def tearDownClass(cls):
        cls.stop_calibre_web()
        cls.driver.quit()
        # cls.p.terminate()
        # close the browser window and stop calibre-web
        remove_dependency(cls.json_line)

    def inital_sync(self):
        if self.syncToken:
            return
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
        payload={
            "AffiliateName": "Kobo",
            "AppVersion": "4.19.14123",
            "ClientKey": "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMzc1",
            "DeviceId": "lnez00rs6cox274bx8c97kyr67ga3tnn0c1745tbjd9rmsmcywxmmcrw2zcayu6d",
            "PlatformId": "00000000-0000-0000-0000-000000000375",
            "UserKey": "12345678-9012-abcd-efgh-a7b6c0d8e7f2"
        }
        r = requests.post(self.kobo_adress+'/v1/auth/device', json=payload)
        self.assertEqual(r.status_code,200)
        # request init request to get metadata format
        self.header ={
            'Authorization': 'Bearer ' + r.json()['AccessToken'],
            'Content-Type': 'application/json'
         }
        expectUrl = '/'.join(self.kobo_adress.split('/')[0:-2])
        session = requests.session()
        r = session.get(self.kobo_adress+'/v1/initialization', headers=self.header)
        self.assertEqual(r.status_code,200)
        # Check cover links
        self.assertEqual(len(r.json()),1)
        self.assertEqual(r.json()['Resources']['image_host'], expectUrl)
        self.assertEqual(self.kobo_adress+"/{ImageId}/{width}/{height}/{Quality}/isGreyscale/image.jpg",
                         r.json()['Resources']['image_url_quality_template'])
        self.assertEqual(self.kobo_adress + "/{ImageId}/{width}/{height}/false/image.jpg",
                         r.json()['Resources']['image_url_template'])
        # perform user profile request
        r = session.get(self.kobo_adress+'/v1/user/profile', headers=self.header)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), {})
        # perform benefits request
        r = session.get(self.kobo_adress+'/v1/user/loyalty/benefits', headers=self.header)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), {})
        # perform analytics request
        r = session.get(self.kobo_adress+'/v1/analytics/gettests', headers=self.header)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), {})

        # perform sync request
        bood_uuid = '8f1b72c1-e9a4-4212-b538-8e4f4837d201'
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        r = session.get(self.kobo_adress+'/v1/library/sync', params=params)
        self.assertEqual(r.status_code,200)
        data=r.json()
        self.syncToken = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
        self.assertEqual(len(data), 4, "4 Books should have valid kobo formats (epub, epub3, kebub)")
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['DownloadUrls'][1]['Format'], 'EPUB')
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['DownloadUrls'][1]['Size'], 6720)
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['DownloadUrls'][1]['Url'],
                         expectUrl + "/download/5/epub")
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['Contributors'],
                         'John Döe执')
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['CoverImageId'],
                         bood_uuid)
        self.assertTrue('<p>b物</p>', data[0]['NewEntitlement']['BookMetadata']['Description'])
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['Language'],
                         'en')
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['Series']['Name'],
                         'O0ü 执')
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['Series']['NumberFloat'],
                         1.5)
        # ToDo: What shall it look like?
        #self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['Series']['Number'], 1)
        # ToDo What to expect
        # self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['PublicationDate'], '2017-01-19 00:00:00')
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['Publisher']['Name'],
                         'Publish执')
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['Title'],
                         'testbook执')
        self.assertEqual(data[0]['NewEntitlement']['BookEntitlement']['Created'],
                         '2017-01-20T20:00:15Z') # 'Tue, 05 Jul 2016 19:30:06 GMT'
        # moving date
        #self.assertEqual(data[0]['NewEntitlement']['BookEntitlement']['LastModified'],
        #                 '2019-01-12T11:18:51Z') # 'Mon, 02 Apr 2018 16:35:50 GMT'
        # ToDo Check Reading state
        # self.assertEqual(data[0]['NewEntitlement']['ReadingState'], '')
        # perform image request of first book
        r = session.get(self.kobo_adress+'/' + bood_uuid + '/100/100/false/image.jpg', headers=self.header)
        self.assertEqual(r.status_code,200)
        self.assertEqual(16790, len(r.content))
        # perform image request of unknown book
        r = session.get(self.kobo_adress+'/100129102/100/100/false/image.jpg', headers=self.header)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), {})

        # perform whishlist request
        params = {'PageSize': '30', 'PageIndex': '0'}
        r = session.get(self.kobo_adress+'/v1/user/wishlist', params=params)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(),{})

        # perform recommendation request
        params = {'page_index': '0', 'page_size': '50'}
        r = session.get(self.kobo_adress+'/v1/user/recommendations', params=params)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), {})
        # perform analytics request
        r = session.get(self.kobo_adress+'/v1/analytics/get', headers=self.header)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), {})

        # perform nextread request
        r = session.get(self.kobo_adress + '/11fb0e29-aa28-4ab8-83be-19b161cd6a2d,2fe593b7-1389-4478-b66f-f07bf4c4d5b0/nextread',
                        headers=self.header)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {})
        session.close()

    def sync_kobo(self):
        changeSession = requests.session()
        r = changeSession.get(self.kobo_adress+'/v1/initialization', headers=self.header)
        self.assertEqual(r.status_code,200)
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        r = changeSession.get(self.kobo_adress+'/v1/library/sync', params=params, headers=self.syncToken)
        self.assertEqual(r.status_code,200)
        self.syncToken = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}
        data = r.json()
        changeSession.close()
        return data


    def test_sync_invalid(self):
        payload={
            "AffiliateName": "Kobo",
            "AppVersion": "4.19.14123",
            "ClientKey": "MDAwMDAwMDAtMDAwMC0wMDAwLTAwMDAtMDAwMDAwMDAwMzc1",
            "DeviceId": "lnez00rs6cox274bx8c97kyr67ga3tnn0c1745tbjd9rmsmcywxmmcrw2zcayu6d",
            "PlatformId": "00000000-0000-0000-0000-000000000375",
            "UserKey": "12345678-9012-abcd-efgh-a7b6c0d8e7f2"
        }
        r = requests.post(self.kobo_adress+'x/v1/auth/device', json=payload)
        self.assertEqual(r.status_code, 401)
        header ={
            'Authorization': 'Bearer ' + '123456789',
            'Content-Type': 'application/json'
         }
        session = requests.session()
        r = session.get(self.kobo_adress+'x/v1/initialization', headers=header)
        self.assertEqual(r.status_code, 401)
        self.syncToken = None


    def test_sync_unchanged(self):
        self.inital_sync()

        # append synctoken to headers and start over again
        newSession = requests.session()
        r = newSession.get(self.kobo_adress+'/v1/initialization', headers=self.header)
        self.assertEqual(r.status_code,200)
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        r = newSession.get(self.kobo_adress+'/v1/library/sync', params=params, headers=self.syncToken)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), [])
        newSession.close()
        self.syncToken = {'x-kobo-synctoken': r.headers['x-kobo-synctoken']}

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
        self.assertEqual('Unknown', data[0]['NewEntitlement']['BookMetadata']['Contributors'])
        self.assertEqual('book', data[0]['NewEntitlement']['BookMetadata']['Title'])
        # self.assertEqual(None , data[0]['NewEntitlement']['BookMetadata']['Publisher']['Name'])
        self.delete_book(15)


    def test_sync_changed_book(self):
        self.inital_sync()
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': u'testbook1'})

        # sync and get this book as changed entitlement instead of new one
        data = self.sync_kobo()
        self.assertEqual(1, len(data))
        self.assertTrue('ChangedEntitlement' in data[0])
        self.assertEqual(data[0]['ChangedEntitlement']['BookMetadata']['Title'],
                         'testbook1')


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
        self.create_user('user0', {'password': '1234', 'email': 'a@b.com', 'edit_shelf_role': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('user0','1234')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_shelf('adminShelf', True)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_shelf('userShelf', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('admin','admin123')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # sync, check shelf is not synced
        data = self.sync_kobo()
        self.assertEqual(0, len(data))
        # delete private shelf
        self.list_shelfs(u'adminShelf')['ele'].click()
        self.check_element_on_page((By.ID, "delete_shelf")).click()
        self.check_element_on_page((By.ID, "confirm")).click()
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][0]['id']))   # book no. 13
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'adminShelf')]")).click()
        # sync, check public shelf is synced -> 1 entry
        data = self.sync_kobo()
        self.assertEqual(1, len(data))

        # request delete shelf from kobo -> Shelf is deleted in UI, references are removed
        # request wrong named shelf -> error
        # create user,
        # logout, login new user, create shelf for new user
        self.logout()
        self.login('user0','1234')
        self.create_shelf('new_user', False)
        # request new user shelf -> error
        # request delete of new user shelf via kobo-> error
        # logout
        self.logout()
        self.login('admin','admin123')
        # delete all shelfs
        # delete user

    def test_sync_reading_state(self):
        self.inital_sync()
        # reading state






    def test_kobo_about(self):
        self.assertTrue(self.goto_page('nav_about'))