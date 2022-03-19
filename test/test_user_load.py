#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import time
import re
import requests
import random
import threading
from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB
from helper_func import startup, debug_startup
from helper_func import save_logfiles
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def user_change(user, result, index):
    r = requests.session()
    login_page = r.get('http://127.0.0.1:8083/login')
    token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
    payload = {'username': user, 'password': "1234", 'submit': "", 'next': "/", "csrf_token": token.group(1)}
    r.post('http://127.0.0.1:8083/login', data=payload)
    # random.seed(123)
    for i in range(0, 200):
        time.sleep(random.random() * 0.05)
        parameter = int(random.uniform(2, 260))
        me_page = r.get('http://127.0.0.1:8083/me')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', me_page.text)
        user_load = {'name': user,
                    'email': 'alfa' + re.findall("user(\d+)", user)[0] + '@email.com',
                    'password': "",
                    'locale': "en",
                    'default_language': "all",
                    "csrf_token": token.group(1)
                    }
        for bit_shift in range(1, 16):
            if (parameter >> bit_shift) & 1:
                user_load['show_'+ str(1 << bit_shift)] = "on"

        resp = r.post('http://127.0.0.1:8083/me', data=user_load)
        if resp.status_code != 200 or "flash_danger" in resp.text:
            print('Error: ' + user)
            result[index] = False
            return
    r.close()
    print('Finished: ' + user)
    result[index] = True
    return


class TestUserLoad(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_access_log': 1},
                    env={"APP_MODE": "test"})
            time.sleep(3)
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
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
        login_page = r.get('http://127.0.0.1:8083/login')
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:8083/login', data=payload)
        for i in range(0, user_count):
            new_user_page = r.get('http://127.0.0.1:8083/admin/user/new')
            token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', new_user_page.text)
            user_load = {'name': 'user' + str(i),
                        'email': 'alfa' + str(i) + '@email.com',
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
                        'edit_role': "on",
                        "csrf_token": token.group(1)
                        }
            resp = r.post('http://127.0.0.1:8083/admin/user/new', data=user_load)
            self.assertEqual(resp.status_code, 200)
        r.close()
        threads = [None] * user_count
        results = [None] * user_count
        for i in range(0, user_count):
            threads[i] = threading.Thread(target=user_change, args=('user'+str(i), results, i))
            threads[i].start()
        # time.sleep(400)
        for i in range(0, user_count):
            threads[i].join()
            self.assertTrue(results[i])
