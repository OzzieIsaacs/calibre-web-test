# -*- coding: utf-8 -*-

import unittest
from selenium.webdriver.common.by import By

from helper_func import save_logfiles
import time
import re
import requests
from helper_ui import ui_class
from helper_ui import RESTRICT_TAG_ME, RESTRICT_COL_USER
from config_test import TEST_DB
# from parameterized import parameterized_class
from helper_func import startup, debug_startup


RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


class TestCalibreWebVisibilitys(unittest.TestCase, ui_class):

    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB}, index=INDEX, env = {"APP_MODE": "test"})
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:" + PORTS[0])
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_checked_logged_in(self):
        # get the search textbox
        self.assertTrue(self.check_element_on_page((By.NAME, 'query')))

    def test_about(self):
        self.goto_page('nav_about')
        self.assertTrue(self.check_element_on_page((By.ID, 'libs')))

    # Checks if random book section is available in all sidebar menus
    def test_random_books_available(self):
        # check random books shown in new section
        self.goto_page('nav_new')
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # check random books shown in category section
        list_element = self.goto_page('nav_cat')
        self.assertIsNotNone(list_element)
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # check random books shown in series section
        self.goto_page('nav_serie')
        list_element = self.get_list_books_displayed()
        self.assertIsNotNone(list_element)
        list_element[0]['ele'].click()

        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # check random books NOT shown in author section
        list_element = self.goto_page('nav_author')
        self.assertIsNotNone(list_element)
        list_element[0].click()
        self.driver.implicitly_wait(5)
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))

        # check random books shown in language section
        list_element = self.goto_page('nav_lang')
        self.assertIsNotNone(list_element)
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # check random books shown in hot section
        list_element = self.goto_page('nav_author')
        self.assertIsNotNone(list_element)
        self.goto_page('nav_hot')
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # check random books shown in publisher section
        list_element = self.goto_page('nav_publisher')
        self.assertIsNotNone(list_element)
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))

        # Check random menu is in sidebar
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))

        # Check no random books in random section
        self.assertTrue(self.goto_page('nav_rand'))
        self.assertFalse(self.check_element_on_page((By.ID, "books_rand")))

    # checks if message for empty email working, sets e-mail for admin
    def test_user_email_available(self):
        self.driver.find_element(By.ID, "top_user").click()
        self.check_element_on_page((By.ID, "email"))
        # WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "email")))
        submit = self.driver.find_element(By.ID, "user_submit")
        self.driver.find_element(By.ID, "email").clear()
        self.driver.find_element(By.ID, "email").send_keys("alfa@web.de")
        submit.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertIsNotNone(self.driver.find_element(By.NAME, "show_32"))
        self.assertIsNotNone(self.driver.find_element(By.NAME, "show_16"))
        self.assertIsNotNone(self.driver.find_element(By.NAME, "show_2"))
        self.assertIsNotNone(self.driver.find_element(By.NAME, "show_4"))
        self.assertIsNotNone(self.driver.find_element(By.NAME, "show_8"))

    # checks if admin can configure sidebar for random view
    def test_user_visibility_sidebar(self):
        self.goto_page('user_setup')
        self.change_user({'show_32': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_new")
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in category section
        list_element = self.goto_page("nav_cat")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books shown in series section
        self.goto_page("nav_serie")
        list_element = self.get_list_books_displayed()
        self.assertIsNotNone(list_element)
        list_element[0]['ele'].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in author section
        list_element = self.goto_page("nav_author")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in publisher section
        list_element = self.goto_page("nav_publisher")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in language section
        list_element = self.goto_page("nav_lang")
        list_element[0].click()
        self.assertTrue(self.check_element_on_page((By.ID, "books")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in hot section
        self.goto_page("nav_hot")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in best rated section
        self.goto_page("nav_rated")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in read section
        self.goto_page("nav_read")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # check random books not shown in unread section
        self.goto_page("nav_unread")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        # Go to admin section and re enable show random view
        self.goto_page('user_setup')
        self.change_user({'show_32': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    # Test if user can change visibility of sidebar view best rated books
    def test_admin_change_visibility_rated(self):
        self.goto_page('user_setup')
        self.change_user({'show_128': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rated")))
        self.change_user({'show_128': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))
        order = {'new': (10,),
                 'old': (10,),
                 'asc': (10,),
                 'desc': (10,),
                 'auth_az': (10,),
                 'auth_za': (10,),
                 'pub_new': (10,),
                 'pub_old': (10,)
                 }
        self.verify_order("nav_rated", order=order)
        self.check_element_on_page((By.ID, "new")).click()

    # Test if user can change visibility of sidebar view read and unread books
    def test_admin_change_visibility_read(self):
        self.goto_page('user_setup')
        self.change_user({'show_256': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_read")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_unread")))
        self.change_user({'show_256': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))
        values = self.get_book_details(8)
        self.assertFalse(values['read'])
        read = self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']"))
        self.assertTrue(read)
        read.click()
        values = self.get_book_details()
        self.assertTrue(values['read'])
        self.goto_page('nav_read')
        books = self.get_books_displayed()
        self.assertEqual(1, len(books[1]))
        self.assertEqual('Read Books (1)',
                         self.check_element_on_page((By.XPATH, "//*[@class='discover load-more']/H2")).text)
        self.goto_page('nav_unread')
        books = self.get_books_displayed()
        self.assertEqual(10, len(books[1]))
        self.assertEqual('Unread Books (10)',
                         self.check_element_on_page((By.XPATH, "//*[@class='discover load-more']/H2")).text)
        self.get_book_details(8)
        self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        order = {'new': (13, 12, 11, 10),
                 'old': (1, 3, 4, 5),
                 'asc': (12, 13, 9, 10),
                 'desc': (4, 5, 3, 7),
                 'auth_az': (8, 1, 5, 7),
                 'auth_za': (10, 4, 12, 3),
                 'pub_new': (7, 5, 1, 3),
                 'pub_old': (1, 3, 4, 8)
                 }
        self.verify_order("nav_unread", order=order)
        self.check_element_on_page((By.ID, "new")).click()

    # checks if admin can change user language
    def test_admin_change_visibility_language(self):
        self.goto_page('user_setup')
        self.change_user({'show_2': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_lang")))
        self.change_user({'show_2': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))
        order = {'new': (10, 9, 5, 1),
                 'old': (1, 5, 9, 10),
                 'asc': (9, 10, 1, 5),
                 'desc': (5, 1, 10, 9),
                 'auth_az': (1, 5, 9, 10),
                 'auth_za': (10, 9, 5, 1),
                 'pub_new': (5, 1, 9, 10),
                 'pub_old': (1, 9, 10, 5)
                 }
        self.verify_order("nav_lang", 0, order=order)
        self.check_element_on_page((By.ID, "new")).click()

    # checks if admin can change hot books
    def test_admin_change_visibility_hot(self):
        self.goto_page('user_setup')
        self.change_user({'show_16': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_hot")))
        self.change_user({'show_16': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))
        order = {'new': (1, 2, 3, 4, 5, 6),
                 'old': (1, 2, 3, 4, 5, 6),
                 'asc': (1, 2, 3, 4, 5, 6),
                 'desc': (1, 2, 3, 4, 5, 6),
                 'auth_az': (1, 2, 3, 4, 5, 6),
                 'auth_za': (1, 2, 3, 4, 5, 6),
                 'pub_new': (1, 2, 3, 4, 5, 6),
                 'pub_old': (1, 2, 3, 4, 5, 6)
                 }

    # checks if admin can change random books
    def test_admin_change_visibility_random(self):
        self.goto_page('user_setup')
        self.change_user({'show_32': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.change_user({'show_32': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_rand")
        self.assertEqual(11, len(self.get_books_displayed()[1]))

    # checks if admin can change series
    def test_admin_change_visibility_series(self):
        self.goto_page('user_setup')
        self.change_user({'show_4': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_serie")))
        self.change_user({'show_4': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))
        order = {'new': (7, 3),
                 'old': (3, 7),
                 'asc': (7, 3),
                 'desc': (3, 7),
                 'auth_az': (7, 3),
                 'auth_za': (3, 7),
                 'pub_new': (7, 3),
                 'pub_old': (3, 7),
                 'series_asc': (3, 7),
                 'series_desc': (7, 3)
                 }
        self.verify_order("nav_serie", 0, order=order)
        self.check_element_on_page((By.ID, "new")).click()

    # checks if admin can change publisher
    def test_admin_change_visibility_publisher(self):
        self.goto_page('user_setup')
        self.change_user({'show_4096': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_publisher")))
        self.change_user({'show_4096': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))
        order = {'new': (5,),
                 'old': (5,),
                 'asc': (5,),
                 'desc': (5,),
                 'auth_az': (5,),
                 'auth_za': (5,),
                 'pub_new': (5,),
                 'pub_old': (5,),
                 }
        self.verify_order("nav_publisher", 1, order=order)
        self.check_element_on_page((By.ID, "new")).click()

    # checks if admin can change ratings
    def test_admin_change_visibility_rating(self):
        self.goto_page('user_setup')
        self.change_user({'show_8192': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rate")))
        self.change_user({'show_8192': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rate")))
        order = {'new': (7,),
                 'old': (7,),
                 'asc': (7,),
                 'desc': (7,),
                 'auth_az': (7,),
                 'auth_za': (7,),
                 'pub_new': (7,),
                 'pub_old': (7,),
                 }
        self.verify_order("nav_rate", 1, order=order)
        self.check_element_on_page((By.ID, "new")).click()

    # checks if admin can change fileFormats
    def test_admin_change_visibility_file_formats(self):
        self.goto_page('user_setup')
        self.change_user({'show_16384': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_format")))
        self.change_user({'show_16384': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))
        order = {'new': (10, 9, 8, 5),
                 'old': (5, 8, 9, 10),
                 'asc': (9, 10, 8, 5),
                 'desc': (5, 8, 10, 9),
                 'auth_az': (8, 5, 9, 10),
                 'auth_za': (10, 9, 5, 8),
                 'pub_new': (5, 8, 9, 10),
                 'pub_old': (8, 9, 10, 5)  # books 8,9,10 are all of same date (0101) -> 2nd order according to id in database
                 }
        self.verify_order("nav_format", 1, order=order)
        self.check_element_on_page((By.ID, "new")).click()

    # checks if admin can change fileFormats
    def test_admin_change_visibility_archived(self):
        self.goto_page('user_setup')
        self.change_user({'show_32768': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_archived")))
        self.change_user({'show_32768': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_archived")))

    # checks if admin can change author
    # testcase always failed for unknown reason, therefore sleep calls ToDo: Why failed??
    def test_admin_change_visibility_authors(self):
        # maybe button not visible, and therefore click isn't working?
        time.sleep(5)
        self.goto_page('user_setup')
        time.sleep(5)
        self.change_user({'show_64': 0, 'email': 'a@f.de'})
        time.sleep(5)
        self.change_user({'show_64': 0, 'email': 'a@f.de'})
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_author")))
        self.change_user({'show_64': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))
        order = {'new': (7, 5),
                 'old': (5, 7),
                 'asc': (7, 5),
                 'desc': (5, 7),
                 'pub_new': (7, 5),
                 'pub_old': (5, 7)
                 }
        self.verify_order("nav_author", 2, order=order)
        self.check_element_on_page((By.ID, "new")).click()

    # checks if admin can change categories
    def test_admin_change_visibility_category(self):
        self.goto_page('user_setup')
        self.change_user({'show_8': 0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # Category not visible
        self.assertFalse(self.check_element_on_page((By.ID, "nav_cat")))
        self.change_user({'show_8': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))

    # checks if admin can change its own password
    def test_admin_change_password(self):
        self.change_current_user_password("123AbC*!")
        self.logout()
        self.assertFalse(self.login("admin", "admin123"))
        self.assertTrue(self.login("admin", "123AbC*!"))
        # remove password restrictions
        self.fill_basic_config({'config_password_policy':0})
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.change_current_user_password("admin123"))
        # reenable  password restrictions
        self.fill_basic_config({'config_password_policy':1})
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))


    # checks if admin can enter edit email-server settings
    def test_admin_SMTP_Settings(self):
        # goto email server setup page
        self.goto_page("mail_server")
        # return to admin page by changing nothing
        submit = self.check_element_on_page((By.NAME, "submit"))
        self.assertTrue(submit)
        submit.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        back = self.check_element_on_page((By.ID, "email_back"))
        self.assertTrue(back)
        back.click()
        self.assertTrue(self.check_element_on_page((By.ID, "admin_edit_email")))

    # checks if admin can add a new user
    def test_admin_add_user(self):
        # goto admin page
        self.goto_page("create_user")
        # goto back to admin page
        self.driver.find_element(By.ID, "back").click()
        new_user = self.check_element_on_page((By.ID, "admin_new_user"))
        if new_user:
            row_count = len(self.get_user_list())
            self.assertEqual(row_count, 1)
            # goto add user page
            self.create_user(None, {'email': 'alfa@web.com'})
            self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
            self.create_user('User', {'email': 'alfa@web.com'})
            self.assertTrue(self.check_element_on_page((By.ID, "flash_danger")))
            self.create_user('User', {'password': u"Guêst123AbC*!", 'email': 'alfa@web.com'})
            self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
            # check if on admin page
            self.goto_page("admin_setup")
            if self.check_element_on_page((By.ID, "admin_new_user")):
                row_count = len(self.get_user_list())
                self.assertEqual(row_count, 2)
                return
        self.assertIsNone("Error creating new users")

    def test_change_title(self):
        self.fill_view_config({'config_calibre_web_title': 'Lü 执'})
        self.goto_page('nav_new')
        self.assertEqual('Lü 执', self.check_element_on_page((By.CLASS_NAME, "navbar-brand")).text)


    def test_search_string(self):
        self.assertEqual(7, len(self.adv_search({'title': ' book '})))
        self.adv_search({'title': 'Hallo'}, get=False)
        field = self.check_element_on_page((By.ID, "query"))
        self.assertEqual('', field.get_attribute('value'))
        self.search('Hallo')
        field = self.check_element_on_page((By.ID, "query"))
        self.assertEqual('Hallo', field.get_attribute('value'))

    def test_search_order(self):
        self.search('book')
        order = {'new': (13, 12, 11, 10),
                 'old': (5, 8, 9, 10),
                 'asc': (12, 13, 9, 10),
                 'desc': (5, 11, 8, 10),
                 'auth_az': (8, 5, 11, 13),
                 'auth_za': (10, 12, 9, 13),
                 'pub_new': (5, 9 , 10, 11),
                 'pub_old': (8, 12, 13, 9)
                 }
        self.verify_order("search", order=order)
        self.search('book')
        order = {'new': (13, 12, 11, 10),
                 'old': (5, 8, 9, 10),
                 'asc': (12, 13, 9, 10),
                 'desc': (5, 11, 8, 10),
                 'auth_az': (8, 5, 11, 13),
                 'auth_za': (10, 12, 9, 13),
                 'pub_new': (5, 9 , 10, 11),
                 'pub_old': (8, 12, 13, 9)
                 }
        self.verify_order("search", order=order)
        self.check_element_on_page((By.ID, "new")).click()

    def test_search_functions(self):
        r = requests.session()
        login_page = r.get('http://127.0.0.1:{}/login'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:{}/login'.format(PORTS[0]), data=payload)
        resp = r.get('http://127.0.0.1:{}/search'.format(PORTS[0]))
        self.assertEqual(200, resp.status_code)
        resp = r.get('http://127.0.0.1:{}/advsearch'.format(PORTS[0]))
        self.assertEqual(200, resp.status_code)
        r.close()

    def test_restrict_tags(self):
        # create shelf with Genot content
        elements = self.adv_search('', get=True)
        self.assertEqual(len(elements['include_tags']), 1)
        self.assertEqual(len(elements['exclude_tags']), 1)
        self.create_shelf('restrict', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][0]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'restrict')]")).click()
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][1]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'restrict')]")).click()
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][4]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'restrict')]")).click()
        self.goto_page('nav_new')
        self.list_shelfs('restrict')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books), 3)
        restricts = self.list_restrictions(RESTRICT_TAG_ME)
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('Genot', allow=False)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.list_shelfs('restrict')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books), 3)
        restricts = self.list_restrictions(RESTRICT_TAG_ME)
        self.assertEqual(len(restricts), 1)
        self.delete_restrictions('d0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        restricts = self.list_restrictions(RESTRICT_TAG_ME)
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('Gênot', allow=False)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.list_shelfs('restrict')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books), 2)
        self.check_element_on_page((By.ID, "order_shelf")).click()
        order = self.get_order_shelf_list()
        self.assertEqual(len(order), 3)
        elements = self.adv_search('', get=True)
        self.assertEqual(len(elements['include_tags']), 0)
        self.assertEqual(len(elements['exclude_tags']), 0)
        self.assertEqual(len(self.adv_search({'title': 'book10'})), 0)
        self.assertEqual(len(self.adv_search({'authors': 'Lulu de Marco'})), 0)
        self.assertEqual(len(self.search('Lulu de Marco')), 0)
        self.assertEqual(len(self.search('book10')), 0)
        self.assertEqual(len(self.search('Gênot')), 0)
        self.goto_page('nav_new')
        self.assertEqual(len(self.get_books_displayed()[1]), 7)
        self.list_restrictions(RESTRICT_TAG_ME)
        self.delete_restrictions('d0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        close.click()
        time.sleep(2)
        self.delete_shelf("restrict")

    def test_allow_tags(self):
        self.create_shelf('allow', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][0]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'allow')]")).click()
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][1]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'allow')]")).click()
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][2]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'allow')]")).click()
        self.goto_page('nav_new')
        self.list_shelfs('allow')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books), 3)
        restricts = self.list_restrictions(RESTRICT_TAG_ME)
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('Genot', allow=True)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.list_shelfs('allow')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books), 0)
        restricts = self.list_restrictions(RESTRICT_TAG_ME)
        self.assertEqual(len(restricts), 1)
        self.delete_restrictions('a0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        restricts = self.list_restrictions(RESTRICT_TAG_ME)
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('Gênot', allow=True)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.list_shelfs('allow')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books), 2)
        self.check_element_on_page((By.ID, "order_shelf")).click()
        order = self.get_order_shelf_list()
        self.assertEqual(len(order), 3)
        elements = self.adv_search('', get=True)
        self.assertEqual(len(elements['include_tags']), 1)
        self.assertEqual(len(elements['exclude_tags']), 1)
        self.assertEqual(len(elements['include_serie']), 1)
        self.assertEqual(len(elements['exclude_serie']), 1)
        self.assertEqual(len(elements['include_language']), 2)
        self.assertEqual(len(elements['exclude_language']), 2)
        self.assertEqual(len(elements['include_extension']), 3)
        self.assertEqual(len(elements['exclude_extension']), 3)
        self.assertEqual(len(self.adv_search({'title': 'book10'})), 1)
        self.assertEqual(len(self.adv_search({'title': 'Der Buchtitel'})), 0)
        self.assertEqual(len(self.adv_search({'authors': 'Peter Parker'})), 1)
        self.assertEqual(len(self.search('Lulu de Marco')), 1)
        self.assertEqual(len(self.search('book10')), 1)
        self.assertEqual(len(self.search('Gênot')), 4)
        self.assertEqual(len(self.search('Loko')), 0)
        self.assertEqual(len(self.search('Der Buchtitel')), 0)
        self.goto_page('nav_new')
        self.assertEqual(len(self.get_books_displayed()[1]), 4)
        self.list_restrictions(RESTRICT_TAG_ME)
        self.delete_restrictions('a0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        close.click()
        time.sleep(2)
        self.delete_shelf(u'allow')

    def test_restrict_columns(self):
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": 'test'})
        self.edit_book(11, custom_content={"Custom Text 人物 *'()&": 'test'})
        self.edit_book(1, custom_content={"Custom Text 人物 *'()&": 'test'})
        self.edit_book(9, custom_content={"Custom Text 人物 *'()&": 'test'})
        restricts = self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('testo', allow=False)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 11)
        restricts = self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.assertEqual(len(restricts), 1)
        self.delete_restrictions('d0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        restricts = self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('test', allow=False)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 11)
        self.fill_view_config({'config_restricted_column': "Custom Text 人物 *'()&"})
        elements = self.adv_search('', get=True)
        self.assertEqual(len(elements['include_tags']), 1)
        self.assertEqual(len(elements['exclude_tags']), 1)
        self.assertEqual(len(elements['include_serie']), 1)
        self.assertEqual(len(elements['exclude_serie']), 1)
        self.assertEqual(len(elements['include_language']), 2)
        self.assertEqual(len(elements['exclude_language']), 2)
        self.assertEqual(len(elements['include_extension']), 4)
        self.assertEqual(len(elements['exclude_extension']), 4)
        self.assertEqual(len(self.adv_search({'title': 'Buchtitel'})), 0)
        self.assertEqual(len(self.adv_search({"custom_column_10": 'test'})), 0)
        self.assertEqual(len(self.adv_search({'authors': 'Peter Parker'})), 1)
        self.assertEqual(len(self.search('Lulu de Marco')), 1)
        self.assertEqual(len(self.search('Loko')), 0)
        self.assertEqual(len(self.search('Gênot')), 2)
        self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.delete_restrictions('d0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        close.click()
        time.sleep(2)
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(11, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(9, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(1, custom_content={"Custom Text 人物 *'()&": ''})
        self.fill_view_config({'config_restricted_column': "None"})

    def test_allow_columns(self):
        self.fill_view_config({'config_restricted_column': "Custom Text 人物 *'()&"})
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": 'allow'})
        self.edit_book(11, custom_content={"Custom Text 人物 *'()&": 'allow'})
        self.edit_book(1, custom_content={"Custom Text 人物 *'()&": 'allow'})
        self.edit_book(9, custom_content={"Custom Text 人物 *'()&": 'allow'})
        restricts = self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.assertEqual(len(restricts), 0)
        time.sleep(1)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 11)
        self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.add_restrictions('allow', allow=True)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 4)
        elements = self.adv_search('', get=True)
        self.assertEqual(len(elements['include_tags']), 1)
        self.assertEqual(len(elements['exclude_tags']), 1)
        self.assertEqual(len(elements['include_serie']), 1)
        self.assertEqual(len(elements['exclude_serie']), 1)
        self.assertEqual(len(elements['include_language']), 1)
        self.assertEqual(len(elements['exclude_language']), 1)
        self.assertEqual(len(elements['include_extension']), 3)
        self.assertEqual(len(elements['exclude_extension']), 3)
        self.assertEqual(len(self.adv_search({'title': 'Buchtitel'})), 1)
        self.assertEqual(len(self.adv_search({"custom_column_10": 'Allow'})), 4)
        self.assertEqual(len(self.adv_search({'authors': 'Peter Parker'})), 1)
        self.assertEqual(len(self.search('Lulu de Marco')), 0)
        self.assertEqual(len(self.search('Loko')), 1)
        self.assertEqual(len(self.search('Genot')), 2)
        books = self.get_shelf_books_displayed()
        self.assertEqual(books[0]['id'], '11')
        self.check_element_on_page((By.ID, "old")).click()
        books = self.get_shelf_books_displayed()
        self.assertEqual(books[0]['id'], '10')
        self.check_element_on_page((By.ID, "new")).click()

        self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.delete_restrictions('a0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        close.click()
        time.sleep(2)
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(11, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(1, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(9, custom_content={"Custom Text 人物 *'()&": ''})
        self.fill_view_config({'config_restricted_column': "None"})
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 11)

    def test_link_column_to_read_status(self):
        self.goto_page("nav_author")
        list_element = self.get_list_books_displayed()
        self.assertIsNotNone(list_element)
        list_element[0]['ele'].click()
        self.check_element_on_page((By.ID, "new")).click()
        search = self.adv_search('', get=True)
        self.assertTrue(search['cust_columns']['Custom Bool 1 Ä'])
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Bool 1 Ä': u'No'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Bool 1 Ä': u'Yes'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        details = self.get_book_details(5)
        self.assertEqual(details['cust_columns'][0]['value'], 'remove')
        details = self.get_book_details(7)
        self.assertEqual(details['cust_columns'][0]['value'], 'ok')
        self.goto_page("nav_read")
        list_element = self.get_books_displayed()
        self.assertEqual(len(list_element[1]), 0)
        self.goto_page("nav_unread")
        list_element = self.get_books_displayed()
        self.assertEqual(len(list_element[1]), 11)
        self.fill_view_config({'config_read_column': "Custom Bool 1 Ä"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page("nav_read")
        list_element = self.get_books_displayed()
        self.assertEqual(len(list_element[1]), 1)
        # check read mark visible in read view
        self.assertTrue(list_element[1][0]['read'])
        # check read mark visible in author view
        list_element[1][0]['author_ele'][0].click()
        author = self.get_books_displayed()
        self.assertTrue(author[1][0]['read'])
        self.assertFalse(author[1][1]['read'])
        # check read mark visible in series view
        author[1][0]['series_ele'].click()
        series = self.get_books_displayed()
        self.assertTrue(series[1][0]['read'])
        self.assertFalse(series[1][1]['read'])
        # check read mark visible in normal book view
        self.goto_page("nav_new")
        books = self.get_books_displayed()
        self.assertTrue(books[1][6]['read'])
        self.assertFalse(books[1][5]['read'])
        # check read mark visible in discovery view
        self.goto_page("nav_rand")
        books = self.get_books_displayed()
        found = 0
        for book in books[1]:
            if book['read'] == True:
                found = 1
                break
        self.assertEqual(1, found)
        # check read mark visible in search view
        search = self.search("Djüngel")
        self.assertTrue(search[0]['read'])
        self.assertFalse(search[1]['read'])
        # check read mark visible in shelf view
        self.create_shelf("linked_read")
        self.get_book_details(7)
        time.sleep(2)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'linked_read')]")).click()
        self.list_shelfs("linked_read")['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertTrue(shelf_books[0]['read'])
        self.delete_shelf("linked_read")
        self.goto_page("nav_unread")
        list_element = self.get_books_displayed()
        self.assertEqual(len(list_element[1]), 10)
        self.assertEqual(len(self.adv_search({"read_status": "Yes"})), 1)
        self.assertEqual(len(self.adv_search({"read_status": "No"})), 1)
        self.assertEqual(len(self.adv_search({"title": "book", "read_status": "No"})), 1)
        self.assertEqual(len(self.adv_search({"title": "book", "read_status": "Empty"})), 6)
        self.assertEqual(len(self.adv_search({"title": "Buu", "read_status": "Yes"})), 1)
        details = self.get_book_details(5)
        self.assertFalse(details['read'])
        self.assertEqual(len(details['cust_columns']), 0)
        details = self.get_book_details(7)
        self.assertTrue(details['read'])
        self.assertEqual(len(details['cust_columns']), 0)
        details = self.get_book_details(9)
        self.assertFalse(details['read'])
        self.assertEqual(len(details['cust_columns']), 0)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.check_element_on_page((By.ID, "custom_column_3"))

        search = self.adv_search('', get=True)
        self.assertFalse('Custom Bool 1 Ä' in search['cust_columns'],
                         'Bool column linked to read function, should not visible')
        self.fill_view_config({'config_read_column': ""})
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Bool 1 Ä': u''})
        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Bool 1 Ä': u''})

    def test_request_link_column_to_read_status(self):
        r = requests.session()
        login_page = r.get('http://127.0.0.1:{}/login'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"",
                   'next':"/", "remember_me":"on", "csrf_token": token.group(1)}
        result = r.post('http://127.0.0.1:{}/login'.format(PORTS[0]), data=payload)
        self.assertEqual(200, result.status_code)
        config_page = r.get('http://127.0.0.1:{}/admin/viewconfig'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', config_page.text)
        payload = {"config_read_column": "-1", "csrf_token": token.group(1)}
        result = r.post('http://127.0.0.1:{}/admin/viewconfig'.format(PORTS[0]), data=payload)
        self.assertTrue("flash_danger" in result.text)
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', result.text)
        payload = {"config_read_column": "2", "csrf_token": token.group(1)}
        result = r.post('http://127.0.0.1:{}/admin/viewconfig'.format(PORTS[0]), data=payload)
        self.assertTrue("flash_danger" in result.text)
        r.close()

    def test_read_status_visible(self):
        self.get_book_details(7)
        self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()
        self.assertEqual(len(self.adv_search({"read_status": "Yes"})), 1)
        self.assertEqual(len(self.adv_search({"read_status": "No"})), 10)
        self.goto_page("nav_read")
        list_element = self.get_books_displayed()
        self.assertEqual(len(list_element[1]), 1)
        # check read mark visible in read view
        self.assertTrue(list_element[1][0]['read'])
        # check read mark visible in author view
        list_element[1][0]['author_ele'][0].click()
        author = self.get_books_displayed()
        self.assertTrue(author[1][0]['read'])
        self.assertFalse(author[1][1]['read'])
        # check read mark visible in series view
        author[1][0]['series_ele'].click()
        series = self.get_books_displayed()
        self.assertTrue(series[1][0]['read'])
        self.assertFalse(series[1][1]['read'])
        # check read mark visible in normal book view
        self.goto_page("nav_new")
        books = self.get_books_displayed()
        self.assertTrue(books[1][6]['read'])
        self.assertFalse(books[1][5]['read'])
        # check read mark visible in discovery view
        self.goto_page("nav_rand")
        books = self.get_books_displayed()
        found = 0
        for book in books[1]:
            if book['read'] == True:
                found = 1
                break
        self.assertEqual(1, found)
        # check read mark visible in search view
        search = self.search("Djüngel")
        self.assertTrue(search[0]['read'])
        self.assertFalse(search[1]['read'])
        # check read mark visible in shelf view
        self.create_shelf("linked_read")
        self.get_book_details(7)
        time.sleep(2)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'linked_read')]")).click()
        self.list_shelfs("linked_read")['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertTrue(shelf_books[0]['read'])
        self.delete_shelf("linked_read")
        self.get_book_details(7)
        self.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']")).click()


    def test_hide_custom_column(self):
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Bool 1 Ä': u'No',
                                       'Custom Rating 人物': 5,
                                       'Custom Integer 人物': 1,
                                       r'Custom categories\|, 人物': 'Test',
                                       'Custom Float 人物': '3.5',
                                       'Custom 人物 Enum': 'Alfa',
                                       'Custom Text 人物 *\'()&': 'Tedo'
                                       })
        details = self.get_book_details(5)
        self.assertEqual(details['cust_columns'][0]['value'], '5')
        self.assertEqual(details['cust_columns'][1]['value'], 'remove')
        self.assertEqual(details['cust_columns'][2]['value'], '1')
        self.assertEqual(details['cust_columns'][3]['value'], 'Test')
        self.assertEqual(details['cust_columns'][4]['value'], '3.50')
        self.assertEqual(details['cust_columns'][5]['value'], 'Alfa')
        self.assertEqual(details['cust_columns'][6]['value'], 'Tedo')
        search = self.adv_search('', get=True)
        self.assertTrue(search['cust_columns']['Custom Rating 人物'])
        self.assertTrue(search['cust_columns']['Custom Bool 1 Ä'])
        self.assertTrue(search['cust_columns']['Custom Integer 人物'])
        self.assertTrue(search['cust_columns'][r'Custom categories\|, 人物'])
        self.assertTrue(search['cust_columns']['Custom Float 人物'])
        self.assertTrue(search['cust_columns']['Custom 人物 Enum'])
        self.assertTrue(search['cust_columns']['Custom Text 人物 *\'()&'])
        self.fill_view_config({'config_columns_to_ignore': "^Custom"})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        search = self.adv_search('', get=True)
        self.assertFalse(search['cust_columns'].get('Custom Rating 人物'))
        self.assertFalse(search['cust_columns'].get('Custom Bool 1 Ä'))
        self.assertFalse(search['cust_columns'].get('Custom Integer 人物'))
        self.assertFalse(search['cust_columns'].get(r'Custom categories\|, 人物'))
        self.assertFalse(search['cust_columns'].get('Custom Float 人物'))
        self.assertFalse(search['cust_columns'].get('Custom 人物 Enum'))
        self.assertFalse(search['cust_columns'].get('Custom Text 人物 *\'()&'))
        details = self.get_book_details(5)
        self.assertFalse(details.get('cust_columns'))
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Bool 1 Ä': u'',
                                       'Custom Rating 人物': '',
                                       'Custom Integer 人物': '',
                                       r'Custom categories\|, 人物': '',
                                       'Custom Float 人物': '',
                                       'Custom 人物 Enum': '',
                                       'Custom Text 人物 *\'()&': ''
                                       })
        self.fill_view_config({'config_columns_to_ignore': ""})

    def test_authors_max_settings(self):
        self.create_shelf('Author', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        details = self.get_book_details(1)
        self.assertEqual(len(details['author']), 4)
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        shelf_list = self.driver.find_elements(By.XPATH, "//ul[@id='add-to-shelves']/li")
        self.assertEqual(1, len(shelf_list))
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'Author')]")).click()
        self.goto_page('nav_new')
        list_element = self.get_books_displayed()
        self.assertEqual(len(list_element[1][10]['author']), 4)
        self.list_shelfs('Author')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books[0]['author']), 4)
        result = self.search('Yang')
        self.assertEqual(len(result[0]['author']), 4)
        self.fill_view_config({'config_authors_max': "2"})

        details = self.get_book_details(1)
        self.assertEqual(len(details['author']), 4)
        self.goto_page('nav_new')
        list_element = self.get_books_displayed()
        self.assertEqual(len(list_element[1][10]['author']), 3)
        self.assertEqual(list_element[1][10]['author'][2], '(...)')

        self.list_shelfs('Author')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books[0]['author']), 3)

        result = self.search('Yang')
        self.assertEqual(len(result[0]['author']), 3)
        self.assertEqual(result[0]['author'][2], '(...)')

        # delete Shelf
        self.delete_shelf(u'Author')
        self.fill_view_config({'config_authors_max': "0"})
        result = self.search('Yang')
        self.assertEqual(len(result[0]['author']), 4)

    def test_archive_books(self):
        # check archive book visible in book details
        details = self.get_book_details(5)
        self.assertIsNotNone(details['archived'])
        self.assertFalse(details['archived'])
        # tick archive book in book details
        self.check_element_on_page((By.XPATH, "//*[@id='archived_cb']")).click()
        details = self.get_book_details(5)
        self.assertTrue(details['archived'])
        # check one book in archive section
        self.goto_page('nav_archived')
        list_element = self.get_books_displayed()
        self.assertEqual(len(list_element[1]), 1)
        # check book with archive set is accessible
        details = self.get_book_details(5)
        self.assertEqual('testbook', details['title'])
        # try to edit book
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "title")))
        # check right cover of book is visible
        r = requests.session()
        login_page = r.get('http://127.0.0.1:{}/login'.format(PORTS[0]))
        token = re.search('<input type="hidden" name="csrf_token" value="(.*)">', login_page.text)
        payload = {'username': 'admin', 'password': 'admin123', 'submit': "", 'next': "/", "remember_me": "on", "csrf_token": token.group(1)}
        r.post('http://127.0.0.1:{}/login'.format(PORTS[0]), data=payload)
        resp = r.get('http://127.0.0.1:{}/cover/{}'.format(PORTS[0], list_element[1][0]['id']))
        self.assertEqual('16790', resp.headers['Content-Length'])
        r.close()
        # check archive book visible in search result
        self.assertEqual(len(self.search('testbook')), 1)
        # check archive book visible in advanced search result
        self.assertEqual(len(self.adv_search({'title': 'testbook'})), 1)
        # set archive book section invisible
        self.goto_page('user_setup')
        self.change_user({'show_32768': 0})
        # check book with archive set should be visible again
        details = self.get_book_details(5)
        # check archive book invisible in book details
        self.assertIsNone(details['archived'])
        # check archive book visible in search result
        self.assertEqual(len(self.search('testbook')), 1)
        # check archive book visible in advanced search result
        self.assertEqual(len(self.adv_search({'title': 'testbook'})), 1)
        # revert changes
        self.goto_page('user_setup')
        self.change_user({'show_32768': 1})
        self.get_book_details(5)
        self.check_element_on_page((By.XPATH, "//*[@id='archived_cb']")).click()

    def test_save_views_recent(self):
        self.goto_page('nav_new')
        self.check_element_on_page((By.ID, "desc")).click()
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['id'], '4')
        self.goto_page('nav_hot')
        time.sleep(2)
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(books[1][0]['id'], '4')
