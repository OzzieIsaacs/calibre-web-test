# -*- coding: utf-8 -*-

import os
import time
import unittest
import shutil
import requests

from helper_ui import ui_class
from config_test import TEST_DB, BOOT_TIME, CALIBRE_WEB_PATH
from helper_func import startup
from helper_func import count_files
from helper_proxy import Proxy, val
from selenium.webdriver.common.by import By
from zipfile import ZipFile, ZipInfo
from helper_func import save_logfiles


RESOURCES = {'ports': 2}

PORTS = ['8083', '8080']
INDEX = ""


class TestUpdater(unittest.TestCase, ui_class):
    p = None
    driver = None
    proxy = None

    @classmethod
    def setUpClass(cls):
        if cls.copy_cw():
            thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH + INDEX, 'cps', 'cache', 'thumbnails')
            shutil.rmtree(thumbnail_cache_path, ignore_errors=True)
            cls.proxy = Proxy()
            cls.proxy.start()
            pem_file = os.path.join(os.path.expanduser('~'), '.mitmproxy', 'mitmproxy-ca-cert.pem')
            my_env = os.environ.copy()
            my_env["http_proxy"] = 'http://localhost:' + PORTS[1]
            my_env["https_proxy"] = 'http://localhost:'  + PORTS[1]
            my_env["REQUESTS_CA_BUNDLE"] = pem_file
            my_env["APP_MODE"] = "test"
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, port=PORTS[0], index=INDEX, env=my_env)
        else:
            cls.assertTrue(False, "Target Directory present")

    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        try:
            cls.stop_calibre_web()
        except:
            cls.driver.get("http://127.0.0.1:" + PORTS[0])
            time.sleep(2)
            try:
                cls.stop_calibre_web()
            except:
                pass
        cls.driver.quit()
        cls.proxy.stop_proxy()
        cls.p.terminate()
        try:
            save_logfiles(cls, cls.__name__)
        except:
            pass
        # Move original image back in place
        cls.return_cw()
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH + INDEX, 'cps', 'cache', 'thumbnails')
        shutil.rmtree(thumbnail_cache_path, ignore_errors=True)

    def tearDown(self):
        os.chmod(os.path.join(CALIBRE_WEB_PATH + INDEX, "cps"), 0o764)
        os.chmod(os.path.join(CALIBRE_WEB_PATH + INDEX, "cps", "web.py"), 0o766)
        if not self.check_user_logged_in('admin'):
            try:
                self.logout()
            except:
                self.driver.get("http://127.0.0.1:" + PORTS[0])
                time.sleep(3)
                self.logout()
            self.login('admin', 'admin123')

    def check_updater(self, responsetext, className, timeout=0.5):
        updater = self.check_element_on_page((By.ID, "check_for_update"))
        updater.click()
        time.sleep(timeout)
        self.assertTrue(responsetext in self.check_element_on_page((By.ID, "message")).text)
        self.assertTrue(self.check_element_on_page((By.CLASS_NAME, className)))
        self.check_element_on_page((By.CLASS_NAME, "close")).click()

    @classmethod
    def copy_cw(cls):
        if os.path.isdir(CALIBRE_WEB_PATH + INDEX + '_2'):
            shutil.rmtree(CALIBRE_WEB_PATH + INDEX + '_2', ignore_errors=True)
        if not os.path.isdir(CALIBRE_WEB_PATH + INDEX + '_2'):
            shutil.copytree(CALIBRE_WEB_PATH + INDEX, CALIBRE_WEB_PATH + INDEX + '_2')
            with ZipFile('cps_copy.zip', 'w') as zipObj:
                zipfolder = ZipInfo(os.path.join('calibre-web-0.6.6' + "/"))
                zipObj.writestr(zipfolder, "")
                # Add customized readmie file to check if files are going to be replaces ToDo
                # zipObj.write(os.path.join(CALIBRE_WEB_PATH + '_2', 'cps.py'), arcname='README.md')
                # Iterate over all the files in directory, add everything except .pyc files from cps folder as
                # relative paths
                for folderName, subfolders, filenames in os.walk(os.path.join(CALIBRE_WEB_PATH + INDEX + '_2', 'cps')):
                    for filename in filenames:
                        if os.path.splitext(filename)[1] != '.pyc':
                            filePath = os.path.join(folderName, filename)
                            zipObj.write(filePath, os.path.join('calibre-web-0.6.6',
                                                                os.path.relpath(filePath, CALIBRE_WEB_PATH + INDEX + '_2')))
                zipObj.write(os.path.join(CALIBRE_WEB_PATH + INDEX + '_2', 'cps.py'), arcname='calibre-web-0.6.6/cps.py')
                return True
        else:
            print('target directory already existing')
            return False

    @classmethod
    def return_cw(cls):
        if os.path.isdir(CALIBRE_WEB_PATH + INDEX + '_2'):
            if os.name != 'nt':
                shutil.rmtree(CALIBRE_WEB_PATH + INDEX, ignore_errors=True)
                shutil.move(CALIBRE_WEB_PATH + INDEX + '_2', CALIBRE_WEB_PATH)
            else:
                # On windows the Test folder is locked, as the testoutput is going to be written to it
                # special treatment
                try:
                    shutil.rmtree(CALIBRE_WEB_PATH + INDEX, ignore_errors=True)
                    shutil.copytree(CALIBRE_WEB_PATH + INDEX + '_2', CALIBRE_WEB_PATH,  dirs_exist_ok=True)
                except Exception as e:
                    print(e)
                try:
                    shutil.rmtree(CALIBRE_WEB_PATH + INDEX + '_2', ignore_errors=True)
                except Exception as e:
                    print(e)
        try:
            os.remove(os.path.join(os.getcwd(),'cps_copy.zip'))
        except Exception:
            pass

    def test_check_update_stable_errors(self):
        self.fill_basic_config({'config_updatechannel': 'Stable'})
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        update_table = self.check_element_on_page((By.ID, "current_version")).find_elements(By.TAG_NAME, 'td')
        # self.assertEqual(update_table[0].text,'')  # ToDo Check current version correct
        self.assertEqual(update_table[1].text, 'Current Version')
        version = [int(x) for x in (update_table[0].text.rstrip(' Beta')).split('.')]
        beta = 'Beta' in update_table[0].text
        version3 = [version[0], version[1], version[2]+2]
        version2 = [version[0], version[1], version[2]+1]
        version1 = [version[0], version[1], version[2]]
        val.set_Version([version3, version2, version1])
        val.set_type(['Timeout'])
        self.check_updater('Timeout',  "alert", 13)
        val.set_type(['HTTPError'])
        self.check_updater('404',  "alert")
        val.set_type(['ConnectionError'])
        self.check_updater('Connection',  "alert")
        val.set_type(['GeneralError'])
        self.check_updater('General',  "alert")
        val.set_type(['MissingTagName'])
        self.check_updater('Unexpected',  "alert")
        val.set_type(['MissingBody'])
        self.check_updater('Unexpected',  "alert", )
        val.set_type(['MissingZip'])
        self.check_updater('Unexpected',  "alert")

    def test_check_update_stable_versions(self):
        self.fill_basic_config({'config_updatechannel': 'Stable'})
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        update_table = self.check_element_on_page((By.ID, "current_version")).find_elements(By.TAG_NAME, 'td')
        # ToDo Check current version correct
        self.assertEqual(update_table[1].text, 'Current Version')
        version = [int(x) for x in (update_table[0].text.rstrip(' Beta')).split('.')]
        beta = 'Beta' in update_table[0].text
        version3 = [version[0], version[1], version[2]+2]
        version2 = [version[0], version[1], version[2]+1]
        version1 = [version[0], version[1], version[2]]
        val.set_Version([version3, version2, version1])
        val.set_type([None])
        self.check_updater('{}.{}.{}'.format(*version3), "alert-warning")
        self.assertTrue(self.check_element_on_page((By.ID, "perform_update")))
        self.goto_page('admin_setup')

        # We are equal to newest release
        version3 = [version[0], version[1], version[2]]
        version2 = [version[0], version[1], version[2]-1]
        version1 = [version[0], version[1], version[2]-2]
        val.set_Version([version3, version2, version1])
        if beta:
            self.check_updater('{}.{}.{}'.format(*version3), "alert-warning")
        else:
            self.check_updater('latest version installed', "alert-success")
        self.goto_page('admin_setup')

        # We are last release before new minor release -> update to newest version
        version3 = [version[0], version[1]+2, version[2]]
        version2 = [version[0], version[1]+1, version[2]]
        version1 = [version[0], version[1], version[2]]
        val.set_Version([version3, version2, version1])
        self.check_updater('{}.{}.{}'.format(*version3),  "alert-warning")
        self.goto_page('admin_setup')

        # We are last release before new major release -> update to new major version
        version3 = [version[0]+2, version[1], version[2]]
        version2 = [version[0]+1, version[1], version[2]]
        version1 = [version[0], version[1], version[2]]
        val.set_Version([version3, version2, version1])
        self.check_updater('{}.{}.{}'.format(*version2),  "alert-warning")
        self.goto_page('admin_setup')

        # We are not last release before new major release -> update to last minor version
        version3 = [version[0]+1, version[1], version[2]]
        version2 = [version[0], version[1]+1, version[2]]
        version1 = [version[0], version[1], version[2]+1]
        val.set_Version([version3, version2, version1])
        self.check_updater('{}.{}.{}'.format(*version2),  "alert-warning")
        self.goto_page('admin_setup')

        # Only new major releases available -> update to lowest available major version
        version3 = [version[0]+1, 2, 0]
        version2 = [version[0]+1, 0, version[2]+1]
        version1 = [version[0]+1, 0, version[2]]
        val.set_Version([version3, version2, version1])
        self.check_updater('{}.{}.{}'.format(*version1),  "alert-warning")

    def test_check_update_nightly_errors(self):
        self.fill_basic_config({'config_updatechannel': 'Nightly'})
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        update_table = self.check_element_on_page((By.ID, "current_version")).find_elements(By.TAG_NAME, 'td')
        # self.assertEqual(update_table[0],'')  # ToDo Check current version correct
        self.assertEqual(update_table[1].text, 'Current Version')
        val.set_type(['Timeout'])
        self.check_updater('Timeout', "alert", 13)

        val.set_type(['HTTPError'])
        self.check_updater('404', "alert")

        val.set_type(['ConnectionError'])
        self.check_updater('Connection', "alert")

        val.set_type(['GeneralError'])
        self.check_updater('General', "alert")

        val.set_type(['MissingObject'])
        self.check_updater('Unexpected', "alert")

        val.set_type(['MissingSha'])
        self.check_updater('Unexpected', "alert")

        val.set_type(['MissingUrl'])
        self.check_updater('Unexpected', "alert")

    def test_check_update_nightly_request_errors(self):
        self.fill_basic_config({'config_updatechannel': 'Nightly'})
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        update_table = self.check_element_on_page((By.ID, "current_version")).find_elements(By.TAG_NAME, 'td')
        # self.assertEqual(update_table[0],'')  # ToDo Check current version correct
        self.assertEqual(update_table[1].text, 'Current Version')
        val.set_type([None, 'Timeout'])
        self.check_updater('Timeout', "alert", 13)

        val.set_type([None, 'HTTPError'])
        self.check_updater('404', "alert")

        val.set_type([None, 'ConnectionError'])
        time.sleep(0.5)
        self.check_updater('Connection', "alert")

        val.set_type([None, 'GeneralError'])
        self.check_updater('General', "alert")

        val.set_type([None, 'MissingComitter'])
        self.check_updater('Could not fetch', "alert")

        val.set_type([None, 'MissingMessage'])
        self.check_updater('Could not fetch', "alert")

        val.set_type([None, 'MissingSha'])
        self.check_updater('Could not fetch', "alert")

        val.set_type([None, 'MissingParents'])
        self.check_updater('new update', "alert-warning")

    @unittest.skip('Takes too long')
    def test_perform_update_timeout(self):
        self.fill_basic_config({'config_updatechannel': 'Stable'})
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        update_table = self.check_element_on_page((By.ID, "current_version")).find_elements(By.TAG_NAME, 'td')
        version = [int(x) for x in (update_table[0].text.rstrip(' Beta')).split('.')]
        version3 = [version[0], version[1], version[2] + 2]
        version2 = [version[0], version[1], version[2] + 1]
        version1 = [version[0], version[1], version[2]]
        val.set_Version([version3, version2, version1])
        self.goto_page('admin_setup')
        val.set_type([None])
        updater = self.check_element_on_page((By.ID, "check_for_update"))
        updater.click()
        val.set_type(['Timeout'])
        performUpdate = self.check_element_on_page((By.ID, "perform_update"))
        performUpdate.click()
        time.sleep(11)
        self.assertTrue('Timeout' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()

    def test_perform_update_stable_errors(self):
        self.fill_basic_config({'config_updatechannel': 'Stable'})
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        update_table = self.check_element_on_page((By.ID, "current_version")).find_elements(By.TAG_NAME, 'td')
        version = [int(x) for x in (update_table[0].text.rstrip(' Beta')).split('.')]
        version3 = [version[0], version[1], version[2] + 2]
        version2 = [version[0], version[1], version[2] + 1]
        version1 = [version[0], version[1], version[2]]
        val.set_Version([version3, version2, version1])
        self.goto_page('admin_setup')
        val.set_type([None])
        time.sleep(5)
        updater = self.check_element_on_page((By.ID, "check_for_update"))
        self.assertTrue(updater)
        updater.click()
        time.sleep(5)
        val.set_type(['HTTPError'])
        time.sleep(4)
        performUpdate = self.check_element_on_page((By.ID, "perform_update"))
        self.assertTrue(performUpdate)
        performUpdate.click()
        time.sleep(5)
        self.assertTrue('HTTP Error' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(3)
        val.set_type([None])
        time.sleep(5)
        updater = self.check_element_on_page((By.ID, "check_for_update"))
        self.assertTrue(updater)
        updater.click()
        time.sleep(5)
        val.set_type(['ConnectionError'])
        time.sleep(5)
        performUpdate = self.check_element_on_page((By.ID, "perform_update"))
        self.assertTrue(performUpdate)
        performUpdate.click()
        time.sleep(5)
        self.assertTrue('Connection' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(3)
        val.set_type([None])
        time.sleep(5)
        updater = self.check_element_on_page((By.ID, "check_for_update"))
        self.assertTrue(updater)
        updater.click()
        time.sleep(5)
        val.set_type(['GeneralError'])
        time.sleep(5)
        performUpdate = self.check_element_on_page((By.ID, "perform_update"))
        self.assertTrue(performUpdate)
        performUpdate.click()
        time.sleep(5)
        self.assertTrue('General' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(3)

    def test_perform_update(self):
        self.fill_basic_config({'config_updatechannel': 'Stable'})
        time.sleep(BOOT_TIME)
        self.fill_thumbnail_config({'schedule_generate_book_covers': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.restart_calibre_web()
        time.sleep(3)
        thumbnail_cache_path = os.path.join(CALIBRE_WEB_PATH + INDEX, 'cps', 'cache', 'thumbnails')
        self.assertTrue(os.path.isdir(thumbnail_cache_path))
        self.assertEqual(20, count_files(thumbnail_cache_path))
        self.goto_page('admin_setup')
        update_table = self.check_element_on_page((By.ID, "current_version")).find_elements(By.TAG_NAME, 'td')
        version = [int(x) for x in (update_table[0].text.rstrip(' Beta')).split('.')]
        version3 = [version[0], version[1], version[2] + 2]
        version2 = [version[0], version[1], version[2] + 1]
        version1 = [version[0], version[1], version[2]]
        val.set_Version([version3, version2, version1])

        val.set_type([None])
        time.sleep(0.5)
        updater = self.check_element_on_page((By.ID, "check_for_update"))
        updater.click()
        time.sleep(2)
        performUpdate = self.check_element_on_page((By.ID, "perform_update"))
        performUpdate.click()
        loop = 3
        while loop:
            time.sleep(20)
            button = self.check_element_on_page((By.ID, "DialogFinished"))
            if not button.is_displayed():
                loop -= 1
            else:
                break
        if button:
            button.click()
        else:
            self.driver.get("http://127.0.0.1:" + PORTS[0])
        time.sleep(3)
        # Check all relevant files are kept, venv folder
        self.assertTrue(os.path.isdir(os.path.join(CALIBRE_WEB_PATH + INDEX, "venv")))
        self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH + INDEX, "calibre-web.log")))
        self.assertTrue(os.path.isfile(os.path.join(CALIBRE_WEB_PATH + INDEX, "app.db")))
        self.assertTrue(os.path.isdir(thumbnail_cache_path))
        self.assertEqual(30, count_files(thumbnail_cache_path))
        self.fill_thumbnail_config({'schedule_generate_book_covers': 0})
        # ToDo: Additional folders, additional files

    # check cps files not writebale
    @unittest.skipIf(os.name=="nt", "Test isn't running on Windows")
    def test_update_write_protect(self):
        self.fill_basic_config({'config_updatechannel': 'Stable'})
        time.sleep(BOOT_TIME)
        self.goto_page('admin_setup')
        update_table = self.check_element_on_page((By.ID, "current_version")).find_elements(By.TAG_NAME, 'td')
        version = [int(x) for x in (update_table[0].text.rstrip(' Beta')).split('.')]
        version3 = [version[0], version[1], version[2] + 2]
        version2 = [version[0], version[1], version[2] + 1]
        version1 = [version[0], version[1], version[2]]
        val.set_Version([version3, version2, version1])
        os.chmod(os.path.join(CALIBRE_WEB_PATH + INDEX, "cps"), 0o400)
        val.set_type([None])
        time.sleep(0.5)
        updater = self.check_element_on_page((By.ID, "check_for_update"))
        updater.click()
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "message")))
        performUpdate = self.check_element_on_page((By.ID, "perform_update"))
        performUpdate.click()
        time.sleep(30)
        self.assertTrue('Update failed' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(3)
        os.chmod(os.path.join(CALIBRE_WEB_PATH + INDEX, "cps"), 0o764)
        # Only change permission of single file
        os.chmod(os.path.join(CALIBRE_WEB_PATH + INDEX, "cps", "web.py"), 0o400)
        updater = self.check_element_on_page((By.ID, "check_for_update"))
        updater.click()
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "message")))
        performUpdate = self.check_element_on_page((By.ID, "perform_update"))
        performUpdate.click()
        time.sleep(30)
        # Update fails due to missing write permission on web.py
        self.assertTrue('Update failed' in self.check_element_on_page((By.ID, "DialogContent")).text)
        self.check_element_on_page((By.ID, "DialogFinished")).click()
        time.sleep(3)
        os.chmod(os.path.join(CALIBRE_WEB_PATH + INDEX, "cps", "web.py"), 0o766)

    def test_reconnect_database(self):
        self.driver.get("http://127.0.0.1:" + PORTS[0])
        self.reconnect_database()
        self.assertTrue(self.check_element_on_page((By.ID, "check_for_update")))
        # deactivated by default
        resp = requests.get('http://127.0.0.1:{}/reconnect'.format(PORTS[0]))
        self.assertEqual(404, resp.status_code)
        # self.assertDictEqual({}, resp.json())
