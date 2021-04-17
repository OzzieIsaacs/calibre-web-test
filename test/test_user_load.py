#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase, skip
import os
import time
import requests
import random
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from helper_ui import ui_class
from config_test import TEST_DB, base_path
from helper_func import startup, debug_startup, add_dependency, remove_dependency
from helper_func import save_logfiles

def user_change(user):
    r = requests.session()
    payload = {'username': user, 'password': "1234", 'submit': "", 'next': "/"}
    r.post('http://127.0.0.1:8083/login', data=payload)
    # random.seed(123)
    for i in range(0, 200):
        time.sleep(random.random() * 0.05)
        parameter = int(random.uniform(2, 260))
        userload = {'name': user,
                    'email': "",
                    'password': "",
                    'locale': "en",
                    'default_language': "all",
                    }
        for bit_shift in range(1, 16):
            if (parameter >> bit_shift) & 1:
                userload['show_'+ str(1 << bit_shift)] = "on"
        resp = r.post('http://127.0.0.1:8083/me', data=userload)
        if resp.status_code != 200:
            print('Error: ' + user)
            break
    r.close()
    print('Finished: ' + user)


class TestUserLoad(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_access_log': 1})
            time.sleep(3)
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.stop_calibre_web()
        except:
            cls.driver.get("http://127.0.0.1:8083")
            time.sleep()
            try:
                cls.stop_calibre_web()
            except:
                pass
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)


    # goto books list, check content of table
    # delete one book
    # change no of books per page to 5
    # goto page 2 check content
    def test_user_change_vis(self):
        user_count = 30
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        for i in range(0, user_count):
            userload = {'name': 'user' + str(i),
                        'email': str(i) + 'alfa@email.com',
                        'password': "1234",
                        'locale': "en",
                        'default_language': "all",
                        'show_16': "on",
                        'show_65536': "on",
                        'show_128': "on",
                        'show_256': "on",
                        'show_32': "on",
                        'show_8': "on",
                        'show_4': "on",
                        'show_64': "on",
                        'show_4096': "on",
                        'show_2': "on",
                        'show_8192': "on",
                        'edit_role': "on"
                        }
            resp = r.post('http://127.0.0.1:8083/admin/user/new', data=userload)
            self.assertEqual(resp.status_code, 200)
        r.close()
        for i in range(0, user_count):
            threading.Thread(target=user_change, args=('user'+str(i),)).start()
        time.sleep(400)
