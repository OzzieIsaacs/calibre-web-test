# -*- coding: utf-8 -*-

import unittest
from base_test import ParallelTestCase, acquire_resource, release_resource
import os
import time
import shutil
import re
import requests
import subprocess

from helper_func import get_Host_IP, kill_dead_cps, copy_calibre_web_for_test
from subproc_wrapper import process_open
from config_test import BOOT_TIME, base_path
from helper_func import wait_for_reboot
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException


class TestCli(ParallelTestCase):


    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        copy_calibre_web_for_test(cls.app_dir)
        cls.driver = webdriver.Firefox()
        cls.driver.maximize_window()
        # shutil.rmtree(cls.temp_dir, ignore_errors=True)
        shutil.copytree(os.path.join(base_path, 'Calibre_db'), cls.temp_dir, dirs_exist_ok=True)
        cls.port = acquire_resource("port")
        cls.env = os.environ.copy()
        cls.env.update({
            "APP_MODE": "test",
            "CALIBRE_PORT": cls.worker_port
        })

    def setUp(self):
        os.chdir(base_path)
        try:
            os.remove(os.path.join(self.app_dir, 'app.db'))
        except Exception:
            pass

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(no=True)
        release_resource("port", cls.port)
        try:
            os.chmod(os.path.join(cls.app_dir, "exclude.txt"), 0o644)
        except Exception:
            pass
        os.chmod(os.path.join(cls.app_dir, "cps", "templates", "tasks.html"), 0o644)
        os.chmod(os.path.join(cls.app_dir, "cps", "static"), 0o755)
        os.chmod(os.path.join(cls.app_dir, "cps", "static", "js", "main.js"), 0o644)
        # close the browser window
        os.chdir(base_path)
        cls.driver.quit()
        try:
            shutil.rmtree(os.path.join(cls.app_dir, u'hü lo'), ignore_errors=True)
            os.remove(os.path.join(cls.app_dir, 'app.db'))
        except Exception:
            pass

    def tearDown(self):
        super().tearDown()
        try:
            new_db = os.path.join(self.app_dir, 'hü go.app')
            os.remove(new_db)
        except Exception:
            pass
        kill_dead_cps(self.worker_port)

    def check_password_change(self, parameter, expectation):
        p = process_open([self.py_version, "-B", 'cps.py', "-s", parameter], [1], env=self.env)
        nextline = ""
        try:
            nextline, __ = p.communicate(timeout=BOOT_TIME)
        except subprocess.TimeoutExpired:
            self.log("timeout")
            p.kill()
            p.communicate()
        self.assertTrue(re.findall(expectation, nextline), nextline)

    def test_cli_different_folder(self):
        os.chdir(self.app_dir)
        self.p = process_open([self.py_version,  "-B", u'cps.py'], [1], env=self.env)
        wait_for_reboot(f"http://127.0.0.1:{self.worker_port}")
        os.chdir(os.path.dirname(__file__))
        try:
            # create a new Firefox session
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:" + self.worker_port)

            # Wait for config screen to show up
            self.fill_db_config({'config_calibre_dir': self.temp_dir})

            # wait for cw to reboot
            wait_for_reboot("http://127.0.0.1:" + self.worker_port)

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
        try:
            self.p.terminate()
            self.p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.communicate()

    def test_cli_different_settings_database(self):
        new_db = os.path.join(self.app_dir, 'hü go.app')
        self.p = process_open([self.py_version, "-B",  os.path.join(self.app_dir, u'cps.py'),
                               '-p', new_db], [1, 3], env=self.env)
        os.chdir(os.path.dirname(__file__))
        wait_for_reboot(f"http://127.0.0.1:{self.worker_port}")
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
        self.driver.get("http://127.0.0.1:" + self.worker_port)

        # Wait for config screen to show up
        self.check_element_on_page((By.ID, "username"))
        self.fill_db_config({'config_calibre_dir': self.temp_dir})
        self.assertTrue(self.check_element_on_page((By.ID, "calibre_modal_path")))

        # wait for cw to reboot
        time.sleep(2)

        # Wait for config screen with login button to show up
        self.stop_calibre_web(self.p)
        try:
            self.p.terminate()
            self.p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.communicate()

        self.assertTrue(os.path.isfile(new_db), "New settingsfile location not accepted")
        os.remove(new_db)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass

    def test_cli_SSL_files(self):
        os.chdir(os.path.dirname(__file__))
        shutil.rmtree(os.path.join(self.app_dir, 'hü lo'), ignore_errors=True)
        path_like_file = self.app_dir
        only_path = self.app_dir + os.sep
        real_key_file = os.path.join(self.app_dir, 'hü lo', 'lö g.key')
        real_crt_file = os.path.join(self.app_dir, 'hü lo', 'lö g.crt')
        p = process_open([self.py_version, "-B", os.path.join(self.app_dir, u'cps.py'),
                          '-c', path_like_file], [1, 3], env=self.env)
        nextline = ""
        try:
            nextline, __ = p.communicate(timeout=BOOT_TIME)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

        self.assertIsNotNone(re.findall('Certfilepath is invalid. Exiting', nextline))
        try:
            p.terminate()
            p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

        p = process_open([self.py_version, "-B", os.path.join(self.app_dir, u'cps.py'),
                          '-k', path_like_file], [1, 3], env=self.env)
        try:
            nextline, __ = p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

        self.assertIsNotNone(re.findall('Keyfilepath is invalid. Exiting', nextline))
        try:
            p.terminate()
            p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

        p = process_open([self.py_version, "-B", os.path.join(self.app_dir, u'cps.py'),
                          '-c', only_path], [1, 3], env=self.env)
        try:
            nextline, __ = p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()
        self.assertIsNotNone(re.findall('Certfilepath is invalid. Exiting', nextline))

        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py'),
                          '-k', only_path], [1, 3], env=self.env)
        try:
            nextline, __ = p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()
        self.assertIsNotNone(re.findall('Keyfilepath is invalid. Exiting', nextline))
        try:
            p.terminate()
            p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py'),
                         '-c', real_crt_file], (1, 3), env=self.env)
        try:
            p.terminate()
            nexline, __ = p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()
        self.assertIsNotNone(re.findall('Certfilepath is invalid. Exiting', nextline))
        try:
            p.terminate()
            p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

        p = process_open([self.py_version, "-B", os.path.join(self.app_dir, u'cps.py'),
                         '-k', real_key_file], (1, 3), env=self.env)
        try:
            p.terminate()
            nexline, __ = p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()
        self.assertIsNotNone(re.findall('Keyfilepath is invalid. Exiting', nextline))
        try:
            p.terminate()
            p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

        os.makedirs(os.path.join(self.app_dir, 'hü lo'))
        with open(real_key_file, 'wb') as fout:
            fout.write(os.urandom(124))
        with open(real_crt_file, 'wb') as fout:
            fout.write(os.urandom(124))

        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py'),
                         '-c', real_crt_file], (1, 3), env=self.env)
        nextline = ""
        try:
            nextline, __ = p.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()
        self.assertIsNotNone(re.findall('Certfile and Keyfile have to be used together. Exiting', nextline))

        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py'),
                         '-k', real_key_file], (1, 3), env=self.env)
        nextline = ""
        try:
            nextline, __ = p.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

        self.assertIsNotNone(re.findall('Certfile and Keyfile have to be used together. Exiting', nextline))

        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py'),
                         '-c', real_crt_file, '-k', real_key_file], (1, 3, 5), env=self.env)

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
            self.driver.get("https://127.0.0.1:" + self.worker_port)
            self.assertIsNone("Error", "HTTPS Connection could established with wrong key/cert file")
        except WebDriverException as e:
            self.assertIsNotNone(re.findall('Reached error page: about:neterror?nssFailure', e.msg))
        try:
            p.terminate()
            p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

        shutil.rmtree(os.path.join(self.app_dir, 'hü lo'), ignore_errors=True)
        shutil.copytree('./files', os.path.join(self.app_dir, 'hü lo'))
        real_crt_file = os.path.join(self.app_dir, 'hü lo', 'server.crt')
        real_key_file = os.path.join(self.app_dir, 'hü lo', 'server.key')
        p = process_open([self.py_version, "-B", os.path.join(self.app_dir, u'cps.py'),
                         '-c', real_crt_file, '-k', real_key_file], (1, 3, 5), env=self.env)
        if p.poll() is not None:
            self.assertIsNone('Fail', 'Unexpected error')
        time.sleep(10)

        # navigate to the application home page
        try:
            self.driver.get("https://127.0.0.1:" + self.worker_port)
        except WebDriverException:
            self.assertIsNone("Error", "HTTPS Connection could not established with key/cert file")

        shutil.rmtree(os.path.join(self.app_dir, 'hü lo'), ignore_errors=True)
        self.assertTrue(self.check_element_on_page((By.ID, "username")))
        try:
            p.terminate()
            nexline, __ = p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

    def test_bind_to_single_interface(self):
        address = get_Host_IP()
        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py'), '-i',
                          'http://'+address], [1], env=self.env)
        nextline = ""
        try:
            nextline, __ = p.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

        self.assertIsNotNone(re.search('illegal IP address string', nextline))
        # os.remove(os.path.join(self.app_dir, 'app.db'))
        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py'), '-i', address], [1], env=self.env)
        wait_for_reboot(f"http://{address}:{self.worker_port}")

        # navigate to the application home page
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        try:
            error = ""
            # Should not listen on 127.0.0.1, therefore error
            self.driver.get("http://127.0.0.1:" + self.worker_port)
        except WebDriverException as e:
            error = e.msg
        self.assertTrue(re.findall(r'Reached error page:\sabout:neterror\?e=connectionFailure', error))
        try:
            self.driver.get("http://" + address + ":" + self.worker_port)
        except WebDriverException:
            self.assertIsNone('Limit listening address not working')
        self.assertTrue(self.check_element_on_page((By.ID, "username")))
        try:
            p.terminate()
            p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

    @unittest.skip("Opsolete")
    def test_environ_port_setting(self):
        my_env = os.environ.copy()
        my_env["CALIBRE_PORT"] = self.port
        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py')], [1], env=my_env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)

        # navigate to the application home page
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        try:
            error = ""
            self.driver.get("http://127.0.0.1:" + self.port)
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
        os.chdir(self.app_dir)
        p1 = process_open([self.py_version,  "-B", u'cps.py'], [1], env=self.env)
        wait_for_reboot("http:127.0.0.1:" + self.worker_port)
        p2 = process_open([self.py_version,  "-B", u'cps.py'], [1], env=self.env)
        result = 0
        try:
            result = p2.wait(timeout=BOOT_TIME)
            p2.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            p2.kill()
            p2.communicate()
            self.assertTrue('2nd process not terminated, port is already in use')
        self.assertEqual(result, 1)

        try:
            p1.terminate()
            p1.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p1.kill()
            p1.communicate()

    # start calibre-web in process A.
    # Start calibre-web in process B.
    # Check process B terminates with exit code 1
    # stop process A
    def test_settingsdb_not_writeable(self):
        # check unconfigured database
        os.chdir(self.app_dir)
        p1 = process_open([self.py_version,  "-B", u'cps.py'], [1], env=self.env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        try:
            wait_for_reboot("http://127.0.0.1:" + self.worker_port)
            p1.terminate()
            p1.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p1.kill()
            p1.communicate()
        os.chmod("app.db", 0o400)
        p2 = process_open([self.py_version,  "-B", u'cps.py'], [1], env=self.env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        try:
            wait_for_reboot("http://127.0.0.1:" + self.worker_port)
            p2.terminate()
            p2.communicate(timeout=4)
            result = p2.wait(2)
        except subprocess.TimeoutExpired:
            p2.kill()
            p2.communicate()
            self.assertTrue('2nd process not terminated, port is already in use')
        self.assertEqual(result, 2)
        os.chmod("app.db", 0o644)
        # configure and check again
        p1 = process_open([self.py_version,  "-B", u'cps.py'], [1], env=self.env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        try:
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:" + self.worker_port)

            # Wait for config screen to show up
            self.fill_db_config({'config_calibre_dir': self.temp_dir})

            # wait for cw to reboot
            time.sleep(2)
        except Exception:
            self.assertFalse(True, "Inital config failed with nonwriteable database")
        try:
            p1.terminate()
            p1.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p1.kill()
            p1.communicate()

        os.chmod("app.db", 0o400)
        p2 = process_open([self.py_version,  "-B", u'cps.py'], [1], env=self.env)
        try:
            wait_for_reboot("http://127.0.0.1:" + self.worker_port)
            p2.terminate()
            p2.communicate(timeout=4)
            result = p2.wait(2)
        except subprocess.TimeoutExpired:
            p2.kill()
            p2.communicate()
            self.assertTrue('2nd process not terminated, port is already in use')
        self.assertEqual(result, 2)
        os.chmod("app.db", 0o644)
        os.chdir(base_path)

    def test_change_password(self):
        os.chdir(self.app_dir)
        self.check_password_change("admin:aDmin12!", "Password for user 'admin' changed")
        self.check_password_change("admin:aDm:in12", "Password for user 'admin' changed")
        self.check_password_change("admin.kolo", "No valid 'username:password.*")
        self.check_password_change("admin:aDm:in12", "Password for user 'admin' changed")
        self.check_password_change("admin:", "Empty password")
        p1 = process_open([self.py_version,  "-B", u'cps.py'], [1], env=self.env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        try:
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:" + self.worker_port)

            # Wait for config screen to show up
            self.login("admin", "aDm:in12")
            time.sleep(1)
            self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
            self.fill_db_config({'config_calibre_dir': self.temp_dir})
            self.assertTrue(self.check_element_on_page((By.ID, "flash_success"), timeout=BOOT_TIME))
            # wait for cw to reboot
            # self.driver.get("http://127.0.0.1:" + self.worker_port)
            self.logout()
            time.sleep(1)

        except Exception as e:
            self.assertFalse(e)
        self.check_password_change("admin:@hukl123AbC*!", "Password for user 'admin' changed")
        if os.name != "nt":
            self.assertFalse(self.login("admin", "admin123"))
            self.assertTrue(self.login("admin", "@hukl123AbC*!"))
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_db_config({'config_calibre_dir': self.temp_dir})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success"), timeout=BOOT_TIME))
        self.check_password_change("admin:admin123", "Password doesn't comply with password")
        self.fill_basic_config({"config_password_policy": 0})
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        p1.terminate()
        try:
            p1.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p1.kill()
            p1.communicate()
        os.remove("app.db")

    def help_dry_run(self):
        p1 = process_open([self.py_version, "-B", u'cps.py', "-d"], [1], env=self.env)
        output = list()
        while p1.poll() is None:
            output.append(p1.stdout.readline())
        self.assertEqual(0, p1.returncode)
        p1.stdout.close()
        p1.stderr.close()
        p1.kill()
        return "".join(output)

    def test_dryrun_update(self):
        os.chdir(self.app_dir)
        # check empty file
        output = self.help_dry_run()
        self.assertTrue("Finished" in output)
        # check missing file
        exclude = os.path.join(self.app_dir, "exclude.txt")
        if os.path.exists(exclude):
            os.remove(exclude)
        output = self.help_dry_run()
        self.assertTrue("file list for updater not found" in output)
        # check no permission for file
        with open(os.path.join(self.app_dir, "exclude.txt"), "w") as f:
            f.write("")
        os.chmod(os.path.join(self.app_dir, "exclude.txt"), 0o040)
        output = self.help_dry_run()
        self.assertTrue("file list for updater not found" in output)
        os.chmod(os.path.join(self.app_dir, "exclude.txt"), 0o644)

        # check empty file
        with open(os.path.join(self.app_dir, "exclude.txt"), "w") as f:
            f.write("")
        output = self.help_dry_run()
        self.assertTrue("Finished" in output)

        # check file with spaces is found
        with open(os.path.join(self.app_dir, "exclude.txt"), "w") as f:
            f.write(" cps.py ")
        output = self.help_dry_run()
        self.assertFalse("cps.py" in output)

        # check file with backslash is found
        with open(os.path.join(self.app_dir, "exclude.txt"), "w") as f:
            f.write(" \\cps.py ")
        output = self.help_dry_run()
        self.assertFalse("cps.py" in output)

        # check file with double backslash is found
        with open(os.path.join(self.app_dir, "exclude.txt"), "w") as f:
            f.write(" \\\\cps.py ")
        output = self.help_dry_run()
        self.assertFalse("cps.py" in output)

        # check file with double backslash is found
        with open(os.path.join(self.app_dir, "exclude.txt"), "w") as f:
            f.write("invalid_strange_pfile.pi")
        output = self.help_dry_run()
        self.assertTrue("invalid_strange_pfile.pi" in output)

        # check file with " and mixed path separators is not found
        with open(os.path.join(self.app_dir, "exclude.txt"), "w") as f:
            f.write(r' "cps\static/favicon.ico" ')
        output = self.help_dry_run()
        self.assertFalse("favicon.ico" in output)

        # check file with 2 lines
        with open(os.path.join(self.app_dir, "exclude.txt"), "w") as f:
            f.write(' "\\cps\\static/favicon.ico"\ncps.py ')
        output = self.help_dry_run()
        self.assertFalse("favicon.ico" in output)
        self.assertFalse("cps.py" in output)

        # Delete exclude file content
        with open(os.path.join(self.app_dir, "exclude.txt"), "w") as f:
            f.write("")

    def test_no_database(self):
        # check unconfigured database
        os.chdir(self.app_dir)
        p1 = process_open([self.py_version, u'cps.py'], [1], env=self.env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        try:
            # navigate to the application home page
            self.driver.get("http://127.0.0.1:" + self.worker_port)
            # Wait for config screen to show up
            self.fill_db_config({'config_calibre_dir': self.temp_dir})
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
        os.rename(os.path.join(self.temp_dir, "metadata.db"), os.path.join(self.temp_dir, "_metadata.db"))
        self.restart_calibre_web()
        self.goto_page("user_setup")
        database_dir = self.check_element_on_page((By.ID, "config_calibre_dir"))
        self.assertTrue(database_dir)
        self.assertEqual(self.temp_dir, database_dir.get_attribute("value"))
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
        self.assertEqual(self.temp_dir, database_dir.get_attribute("value"))
        os.rename(os.path.join(self.temp_dir, "_metadata.db"), os.path.join(self.temp_dir, "metadata.db"))
        self.check_element_on_page((By.ID, "db_submit")).click()
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        # check shelf is still there
        self.list_shelfs("database")['ele'].click()
        book_shelf = self.get_shelf_books_displayed()
        self.assertEqual(1, len(book_shelf))
        # copy database to different location, move location, check shelf is still there
        alt_location = os.path.abspath(os.path.join(self.temp_dir, "..", "alternate"))
        os.makedirs(alt_location, exist_ok=True)
        shutil.copy(os.path.join(self.temp_dir, "metadata.db"), os.path.join(alt_location, "metadata.db"))
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
        os.chdir(os.path.dirname(self.app_dir))
        logdir = os.path.join(self.app_dir, 'logdir')
        log_file = os.path.join(logdir, "test.log")
        shutil.rmtree(logdir, ignore_errors=True)
        os.makedirs(logdir)
        p = process_open([self.py_version, "-B", os.path.join(self.app_dir, u'cps.py'),
                          '-o'], [1], env=self.env)
        time.sleep(1)
        # output = list()
        output = p.stderr.readlines()
        lines = "".join(output)
        self.assertTrue("usage: cps.py" in lines, lines)
        try:
            p.terminate()
            p.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p.kill()
            p.communicate()

        # stream log
        p3 = process_open([self.py_version, "-B", os.path.join(self.app_dir, u'cps.py'),
                          '-o', "/dev/stdout"], [1], env=self.env)
        output = list()
        for i in range (0,7):
            output.append(p3.stdout.readline())
            time.sleep(1)
        lines = "".join(output)
        try:
            p3.terminate()
            p3.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p3.kill()
            p3.communicate()

        self.assertTrue("Starting Calibre Web..." in lines, lines)

        # logfile not writeable        
        if os.path.exists(os.path.join(self.app_dir, "calibre-web.log")):
            os.unlink(os.path.join(self.app_dir, "calibre-web.log"))
        rights = os.stat(logdir).st_mode & 0o777
        os.chmod(logdir, 0o500)
        self.assertFalse(os.path.exists(os.path.join(self.app_dir, "calibre-web.log")))
        
        p1 = process_open([self.py_version, "-B", os.path.join(self.app_dir, u'cps.py'),
                          '-o', log_file], [1], env=self.env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        self.assertTrue(os.path.exists(os.path.join(self.app_dir, "calibre-web.log")))
        try:
            p1.terminate()
            p1.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p1.kill()
            p1.communicate()

        os.chmod(logdir, rights)
        self.assertFalse(os.path.exists(log_file))

        # check logfile in gui = param change logfile in gui -> after reboot the commandline logfile
        p2 = process_open([self.py_version, "-B", os.path.join(self.app_dir, u'cps.py'),
                          '-o', log_file], [1], env=self.env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + self.worker_port)
        # Wait for config screen to show up
        self.fill_db_config({'config_calibre_dir': self.temp_dir})
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.fill_basic_config({'config_logfile': os.path.join(self.app_dir, "new.log")})
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success"),timeout=BOOT_TIME))
        old_size = os.path.getsize(log_file)
        self.restart_calibre_web()
        self.assertGreater(os.path.getsize(log_file)-1000, old_size)
        self.assertFalse(os.path.exists(os.path.join(self.app_dir, "new.log")))
        try:
            p2.terminate()
            p2.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            p2.kill()
            p2.communicate()
        shutil.rmtree(logdir, ignore_errors=True)

    def test_enable_reconnect(self):
        my_env = dict(self.env, CALIBRE_RECONNECT="1")
        # my_env["CALIBRE_RECONNECT"] = '1'
        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py')], [1], env=my_env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + self.worker_port)
        # Wait for config screen to show up
        self.fill_db_config({'config_calibre_dir': self.temp_dir})
        # wait for cw to reboot
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        r = requests.get("http://127.0.0.1:" + self.worker_port + "/reconnect")
        self.assertEqual(200, r.status_code)
        self.assertDictEqual({}, r.json())
        self.stop_calibre_web(p)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py')], [1], env=self.env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)

        r = requests.get("http://127.0.0.1:" + self.worker_port + "/reconnect")
        self.assertEqual(404, r.status_code)
        self.stop_calibre_web(p)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py'), "-r"], [1], env=self.env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)

        r = requests.get("http://127.0.0.1:" + self.worker_port + "/reconnect")
        self.assertEqual(200, r.status_code)
        self.assertDictEqual({}, r.json())
        self.stop_calibre_web(p)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        os.remove(os.path.join(self.app_dir, u'app.db'))

    def test_writeonly_static_files(self):
        p = process_open([self.py_version,  "-B", os.path.join(self.app_dir, u'cps.py')], [1], env=self.env)
        wait_for_reboot("http://127.0.0.1:" + self.worker_port)
        # navigate to the application home page
        self.driver.get("http://127.0.0.1:" + self.worker_port)
        # Wait for config screen to show up
        self.fill_db_config({'config_calibre_dir': self.temp_dir})
        # wait for cw to reboot
        time.sleep(2)
        self.assertTrue(self.check_element_on_page((By.ID, 'flash_success')))
        # readonly template "tasks.html"
        mode = os.path.join(self.app_dir, "cps", "themes", "standard", "templates", "tasks.html")
        os.chmod(mode, 0o200)
        r = requests.session()
        login_page = r.get('http://127.0.0.1:{}/login'.format(self.worker_port))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:{}/login'.format(self.worker_port), data=payload)
        resp = r.get("http://127.0.0.1:" + self.worker_port + "/tasks")
        self.assertEqual(403, resp.status_code)
        os.chmod(mode, 0o644)
        resp = r.get("http://127.0.0.1:" + self.worker_port + "/tasks")
        self.assertEqual(200, resp.status_code)
        # readonly "static" folder
        mode = os.path.join(self.app_dir, "cps", "static")
        os.chmod(mode, 0o200)
        resp = r.get("http://127.0.0.1:" + self.worker_port + "/static/js/main.js")
        self.assertEqual(404, resp.status_code)
        resp = r.get("http://127.0.0.1:" + self.worker_port + "/tasks")
        self.assertEqual(200, resp.status_code)
        os.chmod(mode, 0o755)
        resp = r.get("http://127.0.0.1:" + self.worker_port + "/static/js/main.js")
        self.assertEqual(200, resp.status_code)
        # readonly "main.js" folder
        mode = os.path.join(self.app_dir, "cps", "static", "js", "main.js")
        os.chmod(mode, 0o200)
        resp = r.get("http://127.0.0.1:" + self.worker_port + "/static/js/main.js")
        self.assertEqual(500, resp.status_code)
        resp = r.get("http://127.0.0.1:" + self.worker_port + "/tasks")
        self.assertEqual(200, resp.status_code)
        os.chmod(mode, 0o644)
        resp = r.get("http://127.0.0.1:" + self.worker_port + "/static/js/main.js")
        self.assertEqual(200, resp.status_code)

        self.stop_calibre_web(p)
        try:
            self.driver.switch_to.alert.accept()
        except Exception:
            pass
        os.remove(os.path.join(self.app_dir, u'app.db'))
