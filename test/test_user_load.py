# -*- coding: utf-8 -*-

from base_test import ParallelTestCase, log_message
import time
import re
import requests
import random
import threading

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from helper_func import startup


def user_change(user, worker_port, result, index):
    r = requests.session()
    login_page = r.get('http://127.0.0.1:{}/login'.format(worker_port))
    token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
    payload = {'username': user, 'password': "123AbC*!", 'submit': "", 'next': "/", "csrf_token": token.group(1)}
    r.post('http://127.0.0.1:{}/login'.format(worker_port), data=payload)
    # random.seed(123)
    for i in range(0, 200):
        time.sleep(random.random() * 0.05)
        parameter = int(random.uniform(2, 260))
        me_page = r.get('http://127.0.0.1:{}/me'.format(worker_port))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', me_page.text)
        user_load = {'name': user,
                    'email': 'alfa' + re.findall(r"user(\d+)", user)[0] + '@email.com',
                    'password': "",
                    'locale': "en",
                    'default_language': "all",
                    "csrf_token": token.group(1)
                    }
        for bit_shift in range(1, 16):
            if (parameter >> bit_shift) & 1:
                user_load['show_'+ str(1 << bit_shift)] = "on"

        resp = r.post('http://127.0.0.1:{}/me'.format(worker_port), data=user_load)
        if resp.status_code != 200 or "flash_danger" in resp.text:
            log_message('Error: ' + user, class_name="TestUserLoad")
            result[index] = False
            return
    r.close()
    log_message('Finished: ' + user, class_name="TestUserLoad")
    result[index] = True
    return


class TestUserLoad(ParallelTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': cls.temp_dir, 'config_access_log': 1},
                    port=cls.worker_port,
                    app_dir=cls.app_dir,
                    env={"APP_MODE": "test", "CALIBRE_PORT": cls.worker_port},
                    lib_dest=cls.temp_dir)
            time.sleep(3)
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    # goto books list, check content of table
    # delete one book
    # change no of books per page to 5
    # goto page 2 check content
    def test_user_change_vis(self):
        user_count = 30
        r = requests.session()
        login_page = r.get('http://127.0.0.1:{}/login'.format(self.worker_port))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:{}/login'.format(self.worker_port), data=payload)
        for i in range(0, user_count):
            new_user_page = r.get('http://127.0.0.1:{}/admin/user/new'.format(self.worker_port))
            token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', new_user_page.text)
            user_load = {'name': 'user' + str(i),
                        'email': 'alfa' + str(i) + '@email.com',
                        'password': "123AbC*!",
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
            resp = r.post('http://127.0.0.1:{}/admin/user/new'.format(self.worker_port), data=user_load)
            self.assertEqual(resp.status_code, 200)
        r.close()
        threads = [None] * user_count
        results = [None] * user_count
        for i in range(0, user_count):
            threads[i] = threading.Thread(target=user_change, args=('user'+str(i), self.worker_port, results, i))
            threads[i].start()
        # time.sleep(400)
        for i in range(0, user_count):
            threads[i].join()
            self.assertTrue(results[i])
