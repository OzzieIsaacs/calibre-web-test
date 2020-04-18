# -*- coding: utf-8 -*-

import unittest
import requests
from helper_ui import ui_class
from testconfig import TEST_DB, VENV_PYTHON, CALIBRE_WEB_PATH
from helper_func import startup, debug_startup, get_Host_IP, add_dependency, remove_dependency, kill_old_cps
from selenium.webdriver.common.by import By
# from helper_environment import environment
import re
import time

class test_kobo_sync(unittest.TestCase, ui_class):

    p=None
    driver = None
    kobo_adress = None
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
            time.sleep(2)
            # print(cls.kobo_adress)

        except:
            cls.driver.quit()
            cls.p.terminate()
            kill_old_cps()

    @classmethod
    def tearDownClass(cls):
        cls.stop_calibre_web()
        cls.p.terminate()
        cls.driver.quit()
        # close the browser window and stop calibre-web
        remove_dependency(cls.json_line)

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

    def test_check_sync(self):
        # get the search textbox
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
        header ={
            'Authorization': 'Bearer ' + r.json()['AccessToken'],
            'Content-Type': 'application/json'
         }
        expectUrl = '/'.join(self.kobo_adress.split('/')[0:-2])
        session = requests.session()
        r = session.get(self.kobo_adress+'/v1/initialization', headers=header)
        self.assertEqual(r.status_code,200)
        self.assertEqual(len(r.json()),1)
        self.assertEqual(r.json()['Resources']['image_host'], expectUrl)
        self.assertEqual(r.json()['Resources']['image_url_quality_template'], self.kobo_adress+"/{ImageId}/{width}/{height}/image.jpg")
        self.assertEqual(r.json()['Resources']['image_url_template'], self.kobo_adress + "/{ImageId}/{width}/{height}/image.jpg")
        r = session.get(self.kobo_adress+'/v1/user/profile', headers=header)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), {})
        r = session.get(self.kobo_adress+'/v1/user/loyalty/benefits', headers=header)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), {})
        r = session.get(self.kobo_adress+'/v1/analytics/gettests', headers=header)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), {})
        params = {'Filter': 'All', 'DownloadUrlFilter': 'Generic,Android', 'PrioritizeRecentReads':'true'}
        r = session.get(self.kobo_adress+'/v1/library/sync', params=params)
        self.assertEqual(r.status_code,200)
        data=r.json()
        self.assertEqual(len(data), 4, "4 Books should have valid kobo formats (epub, epub3, kebub)")
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['DownloadUrls'][1]['Format'], 'EPUB')
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['DownloadUrls'][1]['Size'], 6720)
        self.assertEqual(data[0]['NewEntitlement']['BookMetadata']['DownloadUrls'][1]['Url'],
                         expectUrl + "/download/5/epub")
        params = {'PageSize': '30', 'PageIndex': '0'}
        r = session.get(self.kobo_adress+'/v1/user/wishlist', params=params)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(),{})
        params = {'page_index': '0', 'page_size': '50'}
        r = session.get(self.kobo_adress+'/v1/user/recommendations', params=params)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), {})
        r = session.get(self.kobo_adress+'/v1/analytics/get', headers=header)
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json(), {})
        session.close()

    def test_kobo_about(self):
        self.assertTrue(self.goto_page('nav_about'))