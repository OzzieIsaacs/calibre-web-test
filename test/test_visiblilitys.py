# -*- coding: utf-8 -*-

import unittest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from ui_helper import ui_class
from ui_helper import RESTRICT_TAG_ME, RESTRICT_COL_ME, RESTRICT_TAG_USER, RESTRICT_COL_USER
from testconfig import TEST_DB
from parameterized import parameterized_class
from func_helper import startup, debug_startup

'''
ToDOs: suche:
buchtitel (leerzeichen, unicode zeichen, kein treffer)
author (nachname, „name, vorname“, vornname jeweils mit unicode, kein treffer)
serie (leerzeichen, unicode, kein treffer)
ergebnis zu shelf hinzufügen (kein ergebnis vorhanden, public shelf, private shelf, buch schon vorhanden, kein shelf vorhanden)
'''


'''@parameterized_class([
   { "py_version": u'/usr/bin/python'},
   { "py_version": u'/usr/bin/python3'},
],names=('Python27','Python36'))'''
class calibre_web_visibilitys(unittest.TestCase, ui_class):

    p=None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB})
        except:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.kill()

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
        list_element = self.goto_page('nav_serie')
        self.assertIsNotNone(list_element)
        list_element[0].click()
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

    # checks if message for empty email working, sets e-mail for admin
    def test_user_email_available(self):
        self.driver.find_element_by_id("top_user").click()
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "email")))
        #emailcontent = self.driver.find_element_by_id("email").get_attribute("value")
        submit=self.driver.find_element_by_id("submit")
        #self.assertEqual(emailcontent,u'')
        #submit.click()
        self.driver.find_element_by_id("email").clear()
        self.driver.find_element_by_id("email").send_keys("alfa@web.de")
        submit.click()
        WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        self.assertIsNotNone(self.driver.find_element_by_id("flash_success"))
        self.assertIsNotNone(self.driver.find_element_by_name("show_32"))
        self.assertIsNotNone(self.driver.find_element_by_name("show_16"))
        self.assertIsNotNone(self.driver.find_element_by_name("show_2"))
        self.assertIsNotNone(self.driver.find_element_by_name("show_4"))
        self.assertIsNotNone(self.driver.find_element_by_name("show_8"))

    # checks if admin can configure sidebar for random view
    def test_user_visibility_sidebar(self):
        self.goto_page('user_setup')
        self.change_user({'show_32':0})
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
        list_element = self.goto_page("nav_serie")
        list_element[0].click()
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
        # check random books not shown in sorted section
        '''self.driver.find_element_by_id("nav_sort").click()
        self.goto_page("nav_sort_old")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_sort_new")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_sort_asc")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))
        self.goto_page("nav_sort_desc")
        self.assertTrue(self.check_element_on_page((By.ID, "books_rand")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rand")))'''
        # Go to admin section and reenable show random view
        self.goto_page('user_setup')
        self.change_user({'show_32':1})
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rand")))
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    # Test if user can change visibility of sidebar view sorted
    '''def test_admin_change_visibility_sorted(self):
        self.goto_page('user_setup')
        self.change_user({'show_sorted':0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_sort")))
        self.change_user({'show_sorted': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_sort")))'''

    # Test if user can change visibility of sidebar view best rated books
    def test_admin_change_visibility_rated(self):
        self.goto_page('user_setup')
        self.change_user({'show_128':0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rated")))
        self.change_user({'show_128': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rated")))

    # Test if user can change visibility of sidebar view read and unread books
    def test_admin_change_visibility_read(self):
        self.goto_page('user_setup')
        self.change_user({'show_256':0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_read")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_unread")))
        self.change_user({'show_256': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_read")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_unread")))

    # checks if admin can change user language
    def test_admin_change_visibility_language(self):
        self.goto_page('user_setup')
        self.change_user({'show_2':0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_lang")))
        self.change_user({'show_2': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_lang")))

    # checks if admin can change hot books
    def test_admin_change_visibility_hot(self):
        self.goto_page('user_setup')
        self.change_user({'show_16':0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_hot")))
        self.change_user({'show_16': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_hot")))

    # checks if admin can change series
    def test_admin_change_visibility_series(self):
        self.goto_page('user_setup')
        self.change_user({'show_4':0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_serie")))
        self.change_user({'show_4': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_serie")))

    # checks if admin can change publisher
    def test_admin_change_visibility_publisher(self):
        self.goto_page('user_setup')
        self.change_user({'show_4096':0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_publisher")))
        self.change_user({'show_4096': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_publisher")))


    # checks if admin can change ratings
    def test_admin_change_visibility_rating(self):
        self.goto_page('user_setup')
        self.change_user({'show_8192':0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_rate")))
        self.change_user({'show_8192': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_rate")))


    # checks if admin can change fileformats
    def test_admin_change_visibility_file_formats(self):
        self.goto_page('user_setup')
        self.change_user({'show_16384':0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_format")))
        self.change_user({'show_16384': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_format")))

    # checks if admin can change author
    # testcase always failed for unknown reason, therefor sleep calls ToDo: Why failed??
    def test_admin_change_visibility_authors(self):
        # maybe button not visible, and therefore click isn't working?
        time.sleep(5)
        self.goto_page('user_setup')
        time.sleep(5)
        self.change_user({'show_64':0,'email':'a@f.de'})
        time.sleep(5)
        self.change_user({'show_64': 0, 'email': 'a@f.de'})
        time.sleep(5)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertFalse(self.check_element_on_page((By.ID, "nav_author")))
        self.change_user({'show_64': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_author")))

    # checks if admin can change categories
    def test_admin_change_visibility_category(self):
        self.goto_page('user_setup')
        self.change_user({'show_8':0})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # Category not visible
        self.assertFalse(self.check_element_on_page((By.ID, "nav_cat"))) # self.driver.find_elements_by_id("nav_author").__len__())
        self.change_user({'show_8': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.check_element_on_page((By.ID, "nav_cat")))

    # checks if admin can change its own password
    def test_admin_change_password(self):
        self.change_current_user_password("1234")
        self.logout()
        self.assertFalse(self.login("admin","admin123"))
        self.assertTrue(self.login("admin", "1234"))
        self.assertTrue(self.change_current_user_password("admin123"))

    # checks if admin can enter edit email-server settings
    def test_admin_SMTP_Settings(self):
        # goto email server setup page
        self.goto_page("mail_server")
        # return to admin page by changing nothing
        submit = self.check_element_on_page((By.NAME, "submit"))
        self.assertTrue(submit)
        submit.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        back = self.check_element_on_page((By.ID, "back"))
        self.assertTrue(back)
        back.click()
        self.assertTrue(self.check_element_on_page((By.ID, "admin_edit_email")))


    # checks if admin can add a new user
    def test_admin_add_user(self):
        # goto admin page
        self.goto_page("create_user")
        # goto back to admin page
        self.driver.find_element_by_id("back").click()
        new_user = self.check_element_on_page((By.ID, "admin_new_user"))
        if new_user:
            row_count = len(self.get_user_list())
            self.assertEqual(row_count,2)
            # goto add user page
            self.create_user(None, {'email': 'alfa@web.com'})
            self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
            self.create_user('User', {'email': 'alfa@web.com'})
            self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
            self.create_user('User', {'password':u"Guêst",'email': 'alfa@web.com'})
            self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
            # check if on admin page
            if self.check_element_on_page((By.ID, "admin_new_user")):
                row_count = len(self.get_user_list())
                self.assertEqual(row_count,3)
                return
        self.assertIsNone("Error creating new users")

    # checks if admin can change user language
    '''def test_admin_alter_user(self):
        pass'''

    def test_restrict_tags(self):
        # create shelf with Genot content
        elements=self.adv_search('',get=True)
        self.assertEqual(len(elements['include_tags']),1)
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
        self.assertEqual(len(shelf_books),3)
        restricts = self.list_restrictions(RESTRICT_TAG_ME)
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('Genot',allow=False)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.list_shelfs('restrict')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books),3)
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
        elements=self.adv_search('',get=True)
        self.assertEqual(len(elements['include_tags']),0)
        self.assertEqual(len(elements['exclude_tags']), 0)
        self.assertEqual(len(self.adv_search({'book_title':'book10'})),0)
        self.assertEqual(len(self.adv_search({'bookAuthor': 'Lulu de Marco'})), 0)
        self.assertEqual(len(self.search('Lulu de Marco')), 0)
        self.assertEqual(len(self.search('book10')), 0)
        self.assertEqual(len(self.search('Gênot')), 0)
        self.goto_page('nav_new')
        self.assertEqual(len(self.get_books_displayed()[1]), 7)
        restricts = self.list_restrictions(RESTRICT_TAG_ME)
        self.delete_restrictions('d0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        close.click()
        time.sleep(2)
        shelfs = self.list_shelfs()
        shelfs[0]['ele'].click()
        self.check_element_on_page((By.ID, "delete_shelf")).click()
        self.check_element_on_page((By.ID, "confirm")).click()

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
        self.assertEqual(len(shelf_books),3)
        restricts = self.list_restrictions(RESTRICT_TAG_ME)
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('Genot',allow=True)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.list_shelfs('allow')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books),0)
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
        elements=self.adv_search('',get=True)
        self.assertEqual(len(elements['include_tags']), 1)
        self.assertEqual(len(elements['exclude_tags']), 1)
        self.assertEqual(len(elements['include_serie']), 1)
        self.assertEqual(len(elements['exclude_serie']), 1)
        self.assertEqual(len(elements['include_language']), 2)
        self.assertEqual(len(elements['exclude_language']), 2)
        self.assertEqual(len(elements['include_extension']), 3)
        self.assertEqual(len(elements['exclude_extension']), 3)
        self.assertEqual(len(self.adv_search({'book_title':'book10'})),1)
        self.assertEqual(len(self.adv_search({'book_title': 'Der Buchtitel'})), 0)
        self.assertEqual(len(self.adv_search({'bookAuthor': 'Peter Parker'})), 1)
        self.assertEqual(len(self.search('Lulu de Marco')), 1)
        self.assertEqual(len(self.search('book10')), 1)
        self.assertEqual(len(self.search('Gênot')), 4)
        self.assertEqual(len(self.search('Loko')), 0)
        self.assertEqual(len(self.search('Der Buchtitel')), 0)
        self.goto_page('nav_new')
        self.assertEqual(len(self.get_books_displayed()[1]), 4)
        restricts = self.list_restrictions(RESTRICT_TAG_ME)
        self.delete_restrictions('a0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        close.click()
        time.sleep(2)
        shelfs = self.list_shelfs()
        shelfs[0]['ele'].click()
        self.check_element_on_page((By.ID, "delete_shelf")).click()
        self.check_element_on_page((By.ID, "confirm")).click()

    def test_restrict_columns(self):
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&":'test'})
        self.edit_book(11, custom_content={"Custom Text 人物 *'()&": 'test'})
        self.edit_book(1, custom_content={"Custom Text 人物 *'()&": 'test'})
        self.edit_book(9, custom_content={"Custom Text 人物 *'()&": 'test'})
        restricts = self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.assertEqual(len(restricts), 0)
        self.add_restrictions('testo',allow=False)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]),11)
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
        self.fill_view_config({'config_restricted_column':"Custom Text 人物 *'()&"})
        elements=self.adv_search('',get=True)
        self.assertEqual(len(elements['include_tags']), 1)
        self.assertEqual(len(elements['exclude_tags']), 1)
        self.assertEqual(len(elements['include_serie']), 1)
        self.assertEqual(len(elements['exclude_serie']), 1)
        self.assertEqual(len(elements['include_language']), 2)
        self.assertEqual(len(elements['exclude_language']), 2)
        self.assertEqual(len(elements['include_extension']), 4)
        self.assertEqual(len(elements['exclude_extension']), 4)
        self.assertEqual(len(self.adv_search({'book_title':'Buchtitel'})),0)
        self.assertEqual(len(self.adv_search({'bookAuthor': 'Peter Parker'})), 1)
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
        self.edit_book(8, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(3, custom_content={"Custom Text 人物 *'()&": ''})
        self.fill_view_config({'config_restricted_column': "None"})

    def test_allow_columns(self):
        self.fill_view_config({'config_restricted_column':"Custom Text 人物 *'()&"})
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": 'allow'})
        self.edit_book(11, custom_content={"Custom Text 人物 *'()&": 'allow'})
        self.edit_book(1, custom_content={"Custom Text 人物 *'()&": 'allow'})
        self.edit_book(9, custom_content={"Custom Text 人物 *'()&": 'allow'})
        restricts = self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.assertEqual(len(restricts), 0)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]),11)
        self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.add_restrictions('allow', allow=True)
        close = self.check_element_on_page((By.ID, "restrict_close"))
        self.assertTrue(close)
        close.click()
        time.sleep(2)
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 4)
        elements=self.adv_search('', get=True)
        self.assertEqual(len(elements['include_tags']), 1)
        self.assertEqual(len(elements['exclude_tags']), 1)
        self.assertEqual(len(elements['include_serie']), 1)
        self.assertEqual(len(elements['exclude_serie']), 1)
        self.assertEqual(len(elements['include_language']), 1)
        self.assertEqual(len(elements['exclude_language']), 1)
        self.assertEqual(len(elements['include_extension']), 3)
        self.assertEqual(len(elements['exclude_extension']), 3)
        self.assertEqual(len(self.adv_search({'book_title':'Buchtitel'})),1)
        self.assertEqual(len(self.adv_search({'bookAuthor': 'Peter Parker'})), 1)
        self.assertEqual(len(self.search('Lulu de Marco')), 0)
        self.assertEqual(len(self.search('Loko')), 1)
        self.assertEqual(len(self.search('Genot')), 2)
        self.list_restrictions(RESTRICT_COL_USER, username="admin")
        self.delete_restrictions('a0')
        close = self.check_element_on_page((By.ID, "restrict_close"))
        close.click()
        time.sleep(2)
        self.edit_book(10, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(11, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(8, custom_content={"Custom Text 人物 *'()&": ''})
        self.edit_book(3, custom_content={"Custom Text 人物 *'()&": ''})
        self.fill_view_config({'config_restricted_column': "None"})
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual(len(books[1]), 11)
