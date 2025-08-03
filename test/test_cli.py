#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
import time
import shutil
import re
import requests

from helper_ui import ui_class
from helper_func import get_Host_IP, kill_dead_cps, save_logfiles
from subproc_wrapper import process_open
from config_test import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME, base_path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

RESOURCES = {'ports': 2}

PORTS = ['8083', '8082']
INDEX = ""

class TestCli(unittest.TestCase, ui_class):
    driver = None

    @classmethod
    def setUpClass(cls):
        # startup function is not called, therefore direct print
        print("\n%s - %s: " % (cls.py_version, cls.__name__))
        cls.driver = webdriver.Firefox()
        cls.driver.implicitly_wait(10)
        cls.driver.maximize_window()
        shutil.rmtree(TEST_DB, ignore_errors=True)
        shutil.copytree(os.path.join(base_path, 'Calibre_db'), TEST_DB)

    def setUp(self):
        os.chdir(base_path)
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH + INDEX, 'app.db'))
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        os.chmod(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), 0o644)
        os.chmod(os.path.join(CALIBRE_WEB_PATH, "cps", "templates", "tasks.html"), 0o644)
        os.chmod(os.path.join(CALIBRE_WEB_PATH, "cps", "static"), 0o755)
        os.chmod(os.path.join(CALIBRE_WEB_PATH, "cps", "static", "js", "main.js"), 0o644)
        # close the browser window
        os.chdir(base_path)
        kill_dead_cps()
        cls.driver.quit()
        try:
            shutil.rmtree(os.path.join(CALIBRE_WEB_PATH + INDEX, u'hü lo'), ignore_errors=True)
            os.remove(os.path.join(CALIBRE_WEB_PATH + INDEX, 'app.db'))
        except Exception:
            pass
        save_logfiles(cls, cls.__name__)

    def tearDown(self):
        try:
            new_db = os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü go.app')
            os.remove(new_db)
        except Exception:
            pass

    def check_password_change(self, parameter, expectation):
        p = process_open([self.py_version, "-B", 'cps.py', "-s", parameter], [1])
        time.sleep(3)
        if p.poll() is None:
            p.kill()
        nextline = p.communicate()[0]
        self.assertTrue(re.findall(expectation, nextline), nextline)
        p.terminate()
        p.stdout.close()
        p.stderr.close()

    def test_cli_different_folder(self):
        os.chdir(CALIBRE_WEB_PATH + INDEX)
        self.p = process_open([self.py_version,  "-B", u'cps.py'], [1])
        os.chdir(os.path.dirname(__file__))
        try:
            # create a new Firefox session
            time.sleep(15)
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:" + PORTS[0])

            # Wait for config screen to show up
            self.fill_db_config({'config_calibre_dir': TEST_DB})

            # wait for cw to reboot
            time.sleep(BOOT_TIME)

            # Wait for config screen with login button to show up
            login_button = self.check_element_on_page((By.NAME, "login"))
            self.assertTrue(login_button)
            login_button.click()

            # login
            self.login("admin", "admin123")
            time.sleep(3)
            self.assertTrue(self.check_element_on_page((By.NAME, "query")))
            self.stop_calibre_web(self.p)

        except Exception:
            pass
        self.p.stdout.close()
        self.p.stderr.close()
        self.p.terminate()

    def test_cli_different_settings_database(self):
        new_db = os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü go.app')
        self.p = process_open([self.py_version, "-B",  os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                               '-p', new_db], [1, 3])

        time.sleep(15)
        # navigate to the application home page
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        self.driver.refresh()
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        self.driver.get("http://127.0.0.1:" + PORTS[0])

        # Wait for config screen to show up
        self.check_element_on_page((By.ID, "username"))
        self.fill_db_config({'config_calibre_dir': TEST_DB})
        self.assertTrue(self.check_element_on_page((By.ID, "calibre_modal_path")))

        # wait for cw to reboot
        time.sleep(2)

        # Wait for config screen with login button to show up
        self.stop_calibre_web(self.p)
        self.p.stdout.close()
        self.p.stderr.close()
        self.p.terminate()
        time.sleep(3)
        self.assertTrue(os.path.isfile(new_db), "New settingsfile location not accepted")
        os.remove(new_db)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass

    def test_cli_SSL_files(self):
        os.chdir(os.path.dirname(__file__))
        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo'), ignore_errors=True)
        path_like_file = CALIBRE_WEB_PATH + INDEX
        only_path = CALIBRE_WEB_PATH + INDEX + os.sep
        real_key_file = os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo', 'lö g.key')
        real_crt_file = os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo', 'lö g.crt')
        p = process_open([self.py_version, "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                          '-c', path_like_file], [1, 3])
        time.sleep(2)
        nextline = p.communicate()[0]
        if p.poll() is None:
            p.kill()
        self.assertIsNotNone(re.findall('Certfilepath is invalid. Exiting', nextline))
        p.terminate()
        p.stdout.close()
        p.stderr.close()

        p = process_open([self.py_version, "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                          '-k', path_like_file], [1, 3])
        time.sleep(2)
        nextline = p.communicate()[0]
        if p.poll() is None:
            p.kill()
        self.assertIsNotNone(re.findall('Keyfilepath is invalid. Exiting', nextline))
        p.terminate()
        p.stdout.close()
        p.stderr.close()

        p = process_open([self.py_version, "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                          '-c', only_path], [1, 3])
        time.sleep(2)
        nextline = p.communicate()[0]
        if p.poll() is None:
            p.kill()
        self.assertIsNotNone(re.findall('Certfilepath is invalid. Exiting', nextline))

        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                          '-k', only_path], [1, 3])
        time.sleep(2)
        nextline = p.communicate()[0]
        if p.poll() is None:
            p.kill()
        self.assertIsNotNone(re.findall('Keyfilepath is invalid. Exiting', nextline))
        p.terminate()
        p.stdout.close()
        p.stderr.close()

        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                         '-c', real_crt_file], (1, 3))
        time.sleep(2)
        if p.poll() is None:
            p.kill()
        nextline = p.communicate()[0]
        self.assertIsNotNone(re.findall('Certfilepath is invalid. Exiting', nextline))
        p.terminate()
        p.stdout.close()
        p.stderr.close()

        p = process_open([self.py_version, "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                         '-k', real_key_file], (1, 3))
        time.sleep(2)
        if p.poll() is None:
            p.kill()
        nextline = p.communicate()[0]
        self.assertIsNotNone(re.findall('Keyfilepath is invalid. Exiting', nextline))
        p.terminate()
        p.stdout.close()
        p.stderr.close()

        os.makedirs(os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo'))
        with open(real_key_file, 'wb') as fout:
            fout.write(os.urandom(124))
        with open(real_crt_file, 'wb') as fout:
            fout.write(os.urandom(124))

        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                         '-c', real_crt_file], (1, 3))
        time.sleep(2)
        if p.poll() is None:
            p.kill()
        nextline = p.communicate()[0]
        self.assertIsNotNone(re.findall('Certfile and Keyfile have to be used together. Exiting', nextline))
        p.terminate()
        p.stdout.close()
        p.stderr.close()

        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                         '-k', real_key_file], (1, 3))
        time.sleep(2)
        if p.poll() is None:
            p.kill()
        nextline = p.communicate()[0]
        self.assertIsNotNone(re.findall('Certfile and Keyfile have to be used together. Exiting', nextline))
        p.terminate()
        p.stdout.close()
        p.stderr.close()

        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                         '-c', real_crt_file, '-k', real_key_file], (1, 3, 5))

        if p.poll() is not None:
            self.assertIsNone('Fail', 'Unexpected error')
            p.kill()
        p.terminate()
        p.stdout.close()
        p.stderr.close()

        time.sleep(10)
        p.poll()

        # navigate to the application home page
        try:
            self.driver.get("https://127.0.0.1:" + PORTS[0])
            self.assertIsNone("Error", "HTTPS Connection could established with wrong key/cert file")
        except WebDriverException as e:
            self.assertIsNotNone(re.findall('Reached error page: about:neterror?nssFailure', e.msg))
        p.kill()
        p.stdout.close()
        p.stderr.close()

        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo'), ignore_errors=True)
        shutil.copytree('./files', os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo'))
        real_crt_file = os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo', 'server.crt')
        real_key_file = os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo', 'server.key')
        p = process_open([self.py_version, "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                         '-c', real_crt_file, '-k', real_key_file], (1, 3, 5))
        if p.poll() is not None:
            self.assertIsNone('Fail', 'Unexpected error')
        time.sleep(10)

        # navigate to the application home page
        try:
            self.driver.get("https://127.0.0.1:" + PORTS[0])
        except WebDriverException:
            self.assertIsNone("Error", "HTTPS Connection could not established with key/cert file")

        shutil.rmtree(os.path.join(CALIBRE_WEB_PATH + INDEX, 'hü lo'), ignore_errors=True)
        self.assertTrue(self.check_element_on_page((By.ID, "username")))
        p.terminate()
        p.stdout.close()
        p.stderr.close()
        time.sleep(3)
        p.poll()

    def test_bind_to_single_interface(self):
        address = get_Host_IP()
        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'), '-i', 'http://'+address], [1])
        time.sleep(2)
        if p.poll() is None:
            p.kill()
        nextline = p.stdout.readline()
        p.stdout.close()
        p.stderr.close()

        # nextline = p.communicate()[0]
        self.assertIsNotNone(re.search('illegal IP address string', nextline))
        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'), '-i', address], [1])

        time.sleep(BOOT_TIME)
        # navigate to the application home page
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        try:
            error = ""
            self.driver.get("http://127.0.0.1:" + PORTS[0])
        except WebDriverException as e:
            error = e.msg
        self.assertTrue(re.findall(r'Reached error page:\sabout:neterror\?e=connectionFailure', error))
        try:
            self.driver.get("http://" + address + ":" + PORTS[0])
        except WebDriverException:
            self.assertIsNone('Limit listening address not working')
        self.assertTrue(self.check_element_on_page((By.ID, "username")))
        p.stdout.close()
        p.stderr.close()
        p.terminate()
        time.sleep(3)
        p.poll()

    def test_environ_port_setting(self):
        my_env = os.environ.copy()
        my_env["CALIBRE_PORT"] = PORTS[1]
        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py')], [1], env=my_env)

        time.sleep(BOOT_TIME)
        # navigate to the application home page
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        try:
            error = ""
            self.driver.get("http://127.0.0.1:" + PORTS[1])
        except WebDriverException as e:
            error = e.msg
        self.assertFalse(re.findall(r'Reached error page:\sabout:neterror\?e=connectionFailure', error))
        self.assertTrue(self.check_element_on_page((By.ID, "username")))
        p.terminate()
        time.sleep(3)
        p.poll()

    # start calibre-web in process A.
    # Start calibre-web in process B.
    # Check process B terminates with exit code 1
    # stop process A
    def test_already_started(self):
        os.chdir(CALIBRE_WEB_PATH + INDEX)
        p1 = process_open([self.py_version,  "-B", u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        p2 = process_open([self.py_version,  "-B", u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        time.sleep(2)
        result = p2.poll()
        if result is None:
            p2.terminate()
            self.assertTrue('2nd process not terminated, port is already in use')
        self.assertEqual(result, 1)
        p1.terminate()
        time.sleep(3)
        p1.poll()
        p1.stdout.close()
        p1.stderr.close()
        p2.stdout.close()
        p2.stderr.close()

    # start calibre-web in process A.
    # Start calibre-web in process B.
    # Check process B terminates with exit code 1
    # stop process A
    def test_settingsdb_not_writeable(self):
        # check unconfigured database
        os.chdir(CALIBRE_WEB_PATH + INDEX)
        p1 = process_open([self.py_version,  "-B", u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        p1.terminate()
        p1.stdout.close()
        p1.stderr.close()
        time.sleep(BOOT_TIME)
        p1.poll()
        os.chmod("app.db", 0o400)
        p2 = process_open([self.py_version,  "-B", u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        result = p2.poll()
        if result is None:
            p2.terminate()
            p2.poll()
            self.assertTrue('2nd process not terminated, port is already in use')
        p2.stdout.close()
        p2.stderr.close()
        self.assertEqual(result, 2)
        os.chmod("app.db", 0o644)
        # configure and check again
        p1 = process_open([self.py_version,  "-B", u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        try:
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:" + PORTS[0])

            # Wait for config screen to show up
            self.fill_db_config({'config_calibre_dir': TEST_DB})

            # wait for cw to reboot
            time.sleep(2)
        except Exception:
            self.assertFalse(True, "Inital config failed with nonwriteable database")
        p1.terminate()
        p1.stdout.close()
        p1.stderr.close()
        time.sleep(BOOT_TIME)
        p1.poll()
        os.chmod("app.db", 0o400)
        p2 = process_open([self.py_version,  "-B", u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        result = p2.poll()
        if result is None:
            p2.terminate()
            p2.poll()
            self.assertTrue('2nd process not terminated, port is already in use')
        p2.stdout.close()
        p2.stderr.close()
        self.assertEqual(result, 2)
        os.chmod("app.db", 0o644)
        os.chdir(base_path)

    def test_change_password(self):
        os.chdir(CALIBRE_WEB_PATH + INDEX)
        self.check_password_change("admin:aDmin12!", "Password for user 'admin' changed")
        self.check_password_change("admin:aDm:in12", "Password for user 'admin' changed")
        self.check_password_change("admin.kolo", "No valid 'username:password.*")
        self.check_password_change("admin:aDm:in12", "Password for user 'admin' changed")
        self.check_password_change("admin:", "Empty password")
        p1 = process_open([self.py_version,  "-B", u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        try:
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:" + PORTS[0])

            # Wait for config screen to show up
            self.login("admin", "aDm:in12")
            self.fill_db_config({'config_calibre_dir': TEST_DB})
            # wait for cw to reboot
            time.sleep(2)
            self.logout()

        except Exception as e:
            self.assertFalse(e)
        self.check_password_change("admin:@hukl123AbC*!", "Password for user 'admin' changed")
        if os.name != "nt":
            self.assertFalse(self.login("admin", "admin123"))
            self.assertTrue(self.login("admin", "@hukl123AbC*!"))
        self.fill_basic_config({"config_password_policy": 0})
        time.sleep(BOOT_TIME)
        self.check_password_change("admin:admin123", "Password for user 'admin' changed")
        p1.terminate()
        time.sleep(3)
        p1.stdout.close()
        p1.stderr.close()
        os.remove("app.db")

    def help_dry_run(self):
        p1 = process_open([self.py_version, "-B", u'cps.py', "-d"], [1])
        output = list()
        while p1.poll() is None:
            output.append(p1.stdout.readline())
        self.assertEqual(0, p1.returncode)
        p1.stdout.close()
        p1.stderr.close()
        p1.kill()
        return "".join(output)

    def test_dryrun_update(self):
        os.chdir(CALIBRE_WEB_PATH + INDEX)
        # check empty file
        output = self.help_dry_run()
        self.assertTrue("Finished" in output)
        # check missing file
        os.remove(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"))
        output = self.help_dry_run()
        self.assertTrue("file list for updater not found" in output)
        # check no permission for file
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), "w") as f:
            f.write("")
        os.chmod(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), 0o040)
        output = self.help_dry_run()
        self.assertTrue("file list for updater not found" in output)
        os.chmod(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), 0o644)

        # check empty file
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), "w") as f:
            f.write("")
        output = self.help_dry_run()
        self.assertTrue("Finished" in output)

        # check file with spaces is found
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), "w") as f:
            f.write(" cps.py ")
        output = self.help_dry_run()
        self.assertFalse("cps.py" in output)

        # check file with backslash is found
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), "w") as f:
            f.write(" \\cps.py ")
        output = self.help_dry_run()
        self.assertFalse("cps.py" in output)

        # check file with double backslash is found
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), "w") as f:
            f.write(" \\\\cps.py ")
        output = self.help_dry_run()
        self.assertFalse("cps.py" in output)

        # check file with double backslash is found
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), "w") as f:
            f.write("invalid_strange_pfile.pi")
        output = self.help_dry_run()
        self.assertTrue("invalid_strange_pfile.pi" in output)

        # check file with " and mixed path separators is not found
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), "w") as f:
            f.write(r' "cps\static/favicon.ico" ')
        output = self.help_dry_run()
        self.assertFalse("favicon.ico" in output)

        # check file with 2 lines
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), "w") as f:
            f.write(r' "\cps\static/favicon.ico"\ncps.py ')
        output = self.help_dry_run()
        self.assertFalse("favicon.ico" in output)
        self.assertFalse("cps.py" in output)

        # Delete exclude file content
        with open(os.path.join(CALIBRE_WEB_PATH + INDEX, "exclude.txt"), "w") as f:
            f.write("")

    def test_no_database(self):
        # check unconfigured database
        os.chdir(CALIBRE_WEB_PATH + INDEX)
        p1 = process_open([self.py_version, u'cps.py'], [1])
        time.sleep(BOOT_TIME)
        try:
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:" + PORTS[0])
            # Wait for config screen to show up
            self.fill_db_config({'config_calibre_dir': TEST_DB})
            # wait for cw to reboot
            time.sleep(5)
            self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        except Exception:
            self.assertFalse(True, "Inital config failed with normal database")
        # create shelf, add book to shelf
        self.create_shelf("database")
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        self.get_book_details(1)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'database')]")).click()
        self.list_shelfs("database")['ele'].click()
        book_shelf = self.get_shelf_books_displayed()
        self.assertEqual(1, len(book_shelf))
        # rename database file and restart
        os.rename(os.path.join(TEST_DB, "metadata.db"), os.path.join(TEST_DB, "_metadata.db"))
        self.restart_calibre_web()
        self.goto_page("user_setup")
        database_dir = self.check_element_on_page((By.ID, "config_calibre_dir"))
        self.assertTrue(database_dir)
        self.assertEqual(TEST_DB, database_dir.get_attribute("value"))
        self.check_element_on_page((By.ID, "config_back")).click()
        time.sleep(2)
        self.check_element_on_page((By.ID, "config_calibre_dir"))
        self.check_element_on_page((By.ID, "db_submit")).click()
        time.sleep(1)
        confirm = self.check_element_on_page((By.ID, 'invalid_confirm'))
        self.assertTrue(confirm)
        confirm.click()
        time.sleep(1)
        database_dir = self.check_element_on_page((By.ID, "config_calibre_dir"))
        self.assertTrue(database_dir)
        self.assertEqual(TEST_DB, database_dir.get_attribute("value"))
        os.rename(os.path.join(TEST_DB, "_metadata.db"), os.path.join(TEST_DB, "metadata.db"))
        self.check_element_on_page((By.ID, "db_submit")).click()
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        # check shelf is still there
        self.list_shelfs("database")['ele'].click()
        book_shelf = self.get_shelf_books_displayed()
        self.assertEqual(1, len(book_shelf))
        # copy database to different location, move location, check shelf is still there
        alt_location = os.path.abspath(os.path.join(TEST_DB, "..", "alternate"))
        os.makedirs(alt_location, exist_ok=True)
        shutil.copy(os.path.join(TEST_DB, "metadata.db"), os.path.join(alt_location, "metadata.db"))
        self.fill_db_config({'config_calibre_dir': alt_location})
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        # check shelf is still there
        self.list_shelfs("database")['ele'].click()
        book_shelf = self.get_shelf_books_displayed()
        self.assertEqual(1, len(book_shelf))
        # Fails on Samba drive, because file is new created before return of command
        shutil.rmtree(alt_location, ignore_errors=True)
        self.list_shelfs("database")['ele'].click()
        element = self.check_element_on_page((By.XPATH, '//*[@title="Return to Database config"]'))
        self.assertTrue(element)
        element.click()
        self.assertTrue(self.check_element_on_page((By.ID, 'config_calibre_dir')))
        self.stop_calibre_web(p1)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        shutil.rmtree(alt_location, ignore_errors=True)

    def test_logfile(self):
        # no logfile parameter
        os.chdir(os.path.dirname(CALIBRE_WEB_PATH + INDEX))
        logdir = os.path.join(CALIBRE_WEB_PATH + INDEX, 'logdir')
        log_file = os.path.join(logdir, "test.log")
        shutil.rmtree(logdir, ignore_errors=True)
        os.makedirs(logdir)
        p = process_open([self.py_version, "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                          '-o'], [1])        
        time.sleep(1)
        # output = list()
        output = p.stderr.readlines()
        lines = "".join(output)
        self.assertTrue("usage: cps.py" in lines, lines)
        p.terminate()
        p.stdout.close()
        p.stderr.close()

        # stream log
        p3 = process_open([self.py_version, "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                          '-o', "/dev/stdout"], [1])
        output = list()
        for i in range (0,7):
            #while p.poll() is not None:
            output.append(p3.stdout.readline())
            time.sleep(1)
        lines = "".join(output)
        p3.terminate()
        p3.stdout.close()
        p3.stderr.close()
        p3.kill()
        self.assertTrue("Starting Calibre Web..." in lines, lines)

        # logfile not writeable        
        if os.path.exists(os.path.join(CALIBRE_WEB_PATH + INDEX, "calibre-web.log")):
            os.unlink(os.path.join(CALIBRE_WEB_PATH + INDEX, "calibre-web.log"))
        rights = os.stat(logdir).st_mode & 0o777
        os.chmod(logdir, 0o500)
        self.assertFalse(os.path.exists(os.path.join(CALIBRE_WEB_PATH + INDEX, "calibre-web.log")))
        
        p1 = process_open([self.py_version, "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                          '-o', log_file], [1])
        time.sleep(BOOT_TIME)
        self.assertTrue(os.path.exists(os.path.join(CALIBRE_WEB_PATH + INDEX, "calibre-web.log")))
        p1.terminate()
        p1.stdout.close()
        p1.stderr.close()
        p1.kill()

        os.chmod(logdir, rights)
        self.assertFalse(os.path.exists(log_file))

        # check logfile in gui = param change logfile in gui -> after reboot the commandline logfile
        p2 = process_open([self.py_version, "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'),
                          '-o', log_file], [1])
        time.sleep(BOOT_TIME)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + PORTS[0])
        # Wait for config screen to show up
        self.fill_db_config({'config_calibre_dir': TEST_DB})
        # wait for cw to reboot
        time.sleep(2)
        self.fill_basic_config({'config_logfile': os.path.join(CALIBRE_WEB_PATH + INDEX, "new.log")})
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        old_size = os.path.getsize(log_file)
        self.restart_calibre_web()
        self.assertGreater(os.path.getsize(log_file)-1000, old_size)
        self.assertFalse(os.path.exists(os.path.join(CALIBRE_WEB_PATH + INDEX, "new.log")))
        p2.terminate()
        p2.stdout.close()
        p2.stderr.close()
        p2.kill()
        shutil.rmtree(logdir, ignore_errors=True)

    def test_enable_reconnect(self):
        my_env = os.environ.copy()
        my_env["CALIBRE_RECONNECT"] = '1'
        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py')], [1], env=my_env)
        time.sleep(BOOT_TIME)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + PORTS[0])
        # Wait for config screen to show up
        self.fill_db_config({'config_calibre_dir': TEST_DB})
        # wait for cw to reboot
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        r = requests.get("http://127.0.0.1:" + PORTS[0] + "/reconnect")
        self.assertEqual(200, r.status_code)
        self.assertDictEqual({}, r.json())
        self.stop_calibre_web(p)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        my_env = os.environ.copy()
        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py')], [1], env=my_env)
        time.sleep(BOOT_TIME)
        r = requests.get("http://127.0.0.1:" + PORTS[0] + "/reconnect")
        self.assertEqual(404, r.status_code)
        self.stop_calibre_web(p)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py'), "-r"], [1])
        time.sleep(BOOT_TIME)
        r = requests.get("http://127.0.0.1:" + PORTS[0] + "/reconnect")
        self.assertEqual(200, r.status_code)
        self.assertDictEqual({}, r.json())
        self.stop_calibre_web(p)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        os.remove(os.path.join(CALIBRE_WEB_PATH, u'app.db'))

    def test_writeonly_static_files(self):
        p = process_open([self.py_version,  "-B", os.path.join(CALIBRE_WEB_PATH + INDEX, u'cps.py')], [1])
        time.sleep(BOOT_TIME)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + PORTS[0])
        # Wait for config screen to show up
        self.fill_db_config({'config_calibre_dir': TEST_DB})
        # wait for cw to reboot
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        # readonly template "tasks.html"
        mode = os.path.join(CALIBRE_WEB_PATH, "cps", "templates", "tasks.html")
        os.chmod(mode, 0o200)
        r = requests.session()
        login_page = r.get('http://127.0.0.1:{}/login'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:{}/login'.format(PORTS[0]), data=payload)
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/tasks")
        self.assertEqual(403, resp.status_code)
        os.chmod(mode, 0o644)
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/tasks")
        self.assertEqual(200, resp.status_code)
        # readonly "static" folder
        mode = os.path.join(CALIBRE_WEB_PATH, "cps", "static")
        os.chmod(mode, 0o200)
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/static/js/main.js")
        self.assertEqual(404, resp.status_code)
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/tasks")
        self.assertEqual(200, resp.status_code)
        os.chmod(mode, 0o755)
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/static/js/main.js")
        self.assertEqual(200, resp.status_code)
        # readonly "main.js" folder
        mode = os.path.join(CALIBRE_WEB_PATH, "cps", "static", "js", "main.js")
        os.chmod(mode, 0o200)
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/static/js/main.js")
        self.assertEqual(500, resp.status_code)
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/tasks")
        self.assertEqual(200, resp.status_code)
        os.chmod(mode, 0o644)
        resp = r.get("http://127.0.0.1:" + PORTS[0] + "/static/js/main.js")
        self.assertEqual(200, resp.status_code)

        self.stop_calibre_web(p)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        os.remove(os.path.join(CALIBRE_WEB_PATH + INDEX, u'app.db'))
