#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium.webdriver.common.by import By
import time
from helper_ui import ui_class
from config_test import TEST_DB, BOOT_TIME
from helper_func import startup
# from parameterized import parameterized_class
import requests
from helper_func import save_logfiles


class TestShelf(unittest.TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version,{'config_calibre_dir':TEST_DB})
            cls.create_user('shelf', {'edit_shelf_role':1, 'password':'123', 'email':'a@b.com'})
            cls.edit_user('admin',{'edit_shelf_role':1, 'email':'e@fe.de'})
        except Exception:
            cls.driver.quit()
            cls.p.terminate()

    @classmethod
    def tearDownClass(cls):
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin','admin123')
        shelfs = self.list_shelfs()
        if not len(shelfs):
            return
        try:
            for shelf in shelfs:
                self.delete_shelf(shelf['name'])
        except Exception:
            pass

    def test_private_shelf(self):
        self.goto_page('create_shelf')
        self.create_shelf('Pü 执',False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('shelf','123')
        # other user can't see shelf
        self.assertFalse(len(self.list_shelfs()))
        # other user is not able to add books
        self.driver.get("http://127.0.0.1:8083/shelf/add/1/1")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.logout()
        self.login('admin','admin123')
        books = self.get_books_displayed()
        details = self.get_book_details(int(books[1][0]['id']))
        self.assertFalse(details['del_shelf'])
        self.assertTrue(details['add_shelf'])
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'P')]")).click()
        self.assertTrue(self.check_element_on_page((By.XPATH, "//*[@id='remove-from-shelves']//a")))

        # check shelf still invisible
        self.logout()
        self.login('shelf','123')
        # other user can't see shelf
        self.assertFalse(len(self.list_shelfs()))
        # other user is not able to add books
        self.driver.get("http://127.0.0.1:8083/shelf/add/1/1")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.create_shelf('Pü 执', False)
        self.assertTrue(len(self.list_shelfs()))
        self.logout()
        self.login('admin','admin123')
        # go to shelf page and delete shelf
        self.delete_shelf('Pü 执')
        # shelf is gone
        self.assertFalse(len(self.list_shelfs()))

    def test_public_shelf(self):
        self.goto_page('create_shelf')
        self.create_shelf('Gü 执',True)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('shelf','123')
        # other user can see shelf
        shelfs = self.list_shelfs(u'Gü 执 (Public)')
        self.assertTrue(shelfs)
        # other user is able to add books
        self.driver.get("http://127.0.0.1:8083/shelf/add/" + shelfs['id'] + '/1')
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        time.sleep(2)
        # 2nd way to add book
        books = self.get_books_displayed()
        details = self.get_book_details(int(books[1][0]['id']))
        self.assertFalse(details['del_shelf'])
        self.assertTrue(details['add_shelf'])
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'G')]")).click()
        self.assertTrue(self.check_element_on_page((By.XPATH, "//*[@id='remove-from-shelves']//a")))
        # goto shelf
        self.list_shelfs(u'Gü 执 (Public)')['ele'].click()
        self.check_element_on_page((By.ID, "delete_shelf"))
        shelf_books = self.get_shelf_books_displayed()
        # No random books displayed, 2 books in shelf
        self.assertTrue(len(shelf_books) == 2)
        self.create_shelf('Gü 执', True)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.create_shelf('Gü 执', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        shelfs=self.list_shelfs()
        self.assertEqual(shelfs[0]['name'],'Gü 执 (Public)') # Public shelf of admin
        self.assertEqual(shelfs[0]['public'], True)
        self.assertEqual(shelfs[1]['name'], 'Gü 执')         # Private shelf of shelf123
        self.assertEqual(shelfs[1]['public'], False)
        self.logout()
        self.login('admin','admin123')
        books = self.get_books_displayed()
        details = self.get_book_details(int(books[1][1]['id']))
        self.assertFalse(details['del_shelf'])
        self.assertTrue(details['add_shelf'])
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'G')]")).click()
        self.assertTrue(self.check_element_on_page((By.XPATH, "//*[@id='remove-from-shelves']//a")))
        # go to shelf page
        self.list_shelfs(u'Gü 执 (Public)')['ele'].click()
        self.check_element_on_page((By.ID, "delete_shelf"))
        shelf_books = self.get_shelf_books_displayed()
        # No random books displayed, 3 books in shelf
        self.assertTrue(len(shelf_books) == 3)

    # rename shelfs, duplicate shelfs are prevented and books can be added and deleted to shelf
    # capital letters and lowercase letters
    def test_rename_shelf(self):
        self.create_shelf('Lolo', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # add book to shelf
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][0]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'Lolo')]")).click()
        # goto shelf and edit name of shelf
        self.list_shelfs('Lolo')['ele'].click()
        edit=self.check_element_on_page((By.ID, "edit_shelf"))
        self.assertTrue(edit)
        edit.click()
        title=self.check_element_on_page((By.ID, "title"))
        self.assertTrue(title)
        title.clear()
        title.send_keys('Lolu')
        submit = self.check_element_on_page((By.ID, "submit"))
        submit.click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # create 2nd shelf
        self.create_shelf('Lolo', False)
        # goto 2nd shelf and try to rename to name of shelf one
        self.list_shelfs('Lolo')['ele'].click()
        # shelfs[0].click()
        edit=self.check_element_on_page((By.ID, "edit_shelf"))
        self.assertTrue(edit)
        edit.click()
        title=self.check_element_on_page((By.ID, "title"))
        self.assertTrue(title)
        title.clear()
        title.send_keys('Lolu')
        submit = self.check_element_on_page((By.ID, "submit"))
        submit.click()
        # can't rename shelf to same name of other shelf
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.logout()
        # logout and try to create another shelf with same name, even if user can't see shelfs name
        self.login('shelf','123')
        self.create_shelf('Lolu', True)
        # can't rename shelf to same name of other shelf, even if invisible
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('admin','admin123')
        self.list_shelfs('Lolo')['ele'].click()
        edit=self.check_element_on_page((By.ID, "edit_shelf"))
        self.assertTrue(edit)
        edit.click()
        title=self.check_element_on_page((By.ID, "title"))
        self.assertTrue(title)
        title.clear()
        title.send_keys('admin')
        submit = self.check_element_on_page((By.ID, "submit"))
        submit.click()

    # delete book of shelf in database, shelf can still be accesssed
    def test_delete_book_of_shelf(self):
        self.create_shelf('Delete', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # add book to shelf
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][7]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'Delete')]")).click()
        # ToDo: Delete Book
        self.list_shelfs('Delete')['ele'].click()
        shelf_books = self.get_books_displayed()

    # Add muliple books to shelf and arrange the order
    def test_arrange_shelf(self):
        # coding = utf-8
        self.create_shelf('order', True)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][0]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'order')]")).click()
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][2]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'order')]")).click()
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][4]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'order')]")).click()
        self.goto_page('nav_new')
        self.list_shelfs('order (Public)')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(shelf_books[0]['id'], '13')
        self.assertEqual(shelf_books[1]['id'], '11')
        self.assertEqual(shelf_books[2]['id'], '9')
        self.check_element_on_page((By.ID, "order_shelf")).click()
        self.get_order_shelf_list()
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        r.post('http://127.0.0.1:8083/shelf/order/1', data={"9": "1","11": "2","13": "3"})
        self.driver.refresh() # reload page
        self.check_element_on_page((By.ID, "shelf_back")).click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(shelf_books[0]['id'], '9')
        self.assertEqual(shelf_books[1]['id'], '11')
        self.assertEqual(shelf_books[2]['id'], '13')
        r.close()

    # change shelf from public to private type
    def test_public_private_shelf(self):
        self.create_shelf('shelf_public', True)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.create_shelf('shelf_private', False)
        # change private to public
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.list_shelfs('shelf_private')['ele'].click()
        edit_shelf = self.check_element_on_page((By.ID, "edit_shelf"))
        edit_shelf.click()
        public=self.check_element_on_page((By.NAME, "is_public"))
        self.assertFalse(public.is_selected())
        public.click()
        self.check_element_on_page((By.ID, "submit")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        # change public to private
        self.list_shelfs('shelf_public (Public)')['ele'].click()
        edit_shelf = self.check_element_on_page((By.ID, "edit_shelf"))
        edit_shelf.click()
        public=self.check_element_on_page((By.NAME, "is_public"))
        self.assertTrue(public.is_selected())
        public.click()
        self.check_element_on_page((By.ID, "submit")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        # logout and try to create another shelf with same name, even if user can't see shelfs name
        self.login('shelf','123')
        self.delete_shelf('shelf_private (Public)')
        self.logout()
        self.login('admin','admin123')
        self.assertTrue(self.list_shelfs('shelf_public'))

    # Add shelf with extra long name
    def test_shelf_long_name(self):
        self.create_shelf('Halllalalalal1l1ll2332434llsfllsdfglsdflglfdglfdlgldfsglsdlgrtfgsdfvxccbbsgtsvxv', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.list_shelfs('Halllalalalal1l1ll2332434llsfllsdfgls[..]'))

    def test_shelf_action_non_shelf_edit_role(self):
        # remove edit role from admin account
        self.edit_user('admin', {'edit_shelf_role': 0, 'email': 'e@fe.de'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # create user with edit_shlefs role
        self.create_user('user0', {'edit_shelf_role': 1, 'password': '1234', 'email': 'a1@b.com'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('user0','1234')
        self.create_shelf('noright', True)
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][2]['id']))
        # Add book to shelf
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        shelf_list = self.driver.find_elements_by_xpath("//ul[@id='add-to-shelves']/li")
        self.assertEqual(1, len(shelf_list))
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'noright')]")).click()
        self.assertFalse(self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'noright')]")))
        # Remove book from shelf
        remove = self.check_element_on_page((By.XPATH, "//*[@id='remove-from-shelves']//a"))
        self.assertTrue(remove)
        remove.click()
        # Add book to shelf again
        self.assertFalse(self.check_element_on_page((By.XPATH, "//*[@id='remove-from-shelves']//a")))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'noright')]")).click()
        #logout and login admin again
        self.logout()
        self.login('admin', 'admin123')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][2]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        self.assertFalse(self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'noright')]")))
        remove = self.check_element_on_page((By.XPATH, "//*[@id='remove-from-shelves']//a"))
        self.assertTrue(remove)
        remove.click()
        self.assertTrue(self.check_element_on_page((By.XPATH, "//*[@id='remove-from-shelves']//a")))
        self.edit_user('user0', {'delete': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.edit_user('admin', {'edit_shelf_role': 1})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    def test_add_shelf_from_search(self):
        self.create_shelf('search', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.search('Döe')
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        shelf_list = self.driver.find_elements_by_xpath("//ul[@id='add-to-shelves']/li")
        self.assertEqual(1, len(shelf_list))
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'search')]")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # self.assertFalse(self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'search')]")))
        self.list_shelfs('search')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books), 2)
        self.delete_shelf()

    def test_shelf_anonymous(self):
        # Enable Anonymous browsing and create shelf
        self.fill_basic_config({'config_anonbrowse': 1})
        time.sleep(BOOT_TIME)
        self.create_shelf('anon', True)

        # Add Book to shelf
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.get_book_details(int(books[1][2]['id']))
        self.check_element_on_page((By.ID, "add-to-shelf")).click()
        shelf_list = self.driver.find_elements_by_xpath("//ul[@id='add-to-shelves']/li")
        self.assertEqual(1, len(shelf_list))
        self.check_element_on_page((By.XPATH, "//ul[@id='add-to-shelves']/li/a[contains(.,'anon')]")).click()
        # Check if book is in shelf
        self.list_shelfs('anon (Public)')['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books), 1)
        # Logout and check anonymous user can see book in shelf
        self.logout()
        all_shelfs = self.list_shelfs()
        anon_shelf = [el for el in all_shelfs if 'anon' in el['name']]
        self.assertEqual(1, len(anon_shelf))
        anon_shelf[0]['ele'].click()
        self.assertFalse(self.check_element_on_page((By.ID, "edit_shelf")))
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(len(shelf_books), 1)

        self.goto_page('nav_new')
        self.get_book_details(int(books[1][1]['id']))
        self.assertFalse(self.check_element_on_page((By.ID, "add-to-shelf")))

        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        # make shelf private
        self.list_shelfs(u'anon (Public)')['ele'].click()
        edit_shelf = self.check_element_on_page((By.ID, "edit_shelf"))
        edit_shelf.click()
        public=self.check_element_on_page((By.NAME, "is_public"))
        self.assertTrue(public.is_selected())
        public.click()
        self.check_element_on_page((By.ID, "submit")).click()
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        # logout and check if anonymous user can see still see shelf (should not)
        self.logout()
        self.assertFalse(self.list_shelfs('anon'))
        # login delete shelf and remove anonbrowser setting
        self.check_element_on_page((By.ID, "top_user")).click()
        self.login('admin', 'admin123')
        self.fill_basic_config({'config_anonbrowse': 0})
        self.logout()
        # Check with deactivated anonymous browsing access to private shelfs not possible
        self.driver.get('http://127.0.0.1:8083/shelf/' + anon_shelf[0]['id'])
        self.assertEqual(self.driver.title, u'Calibre-Web | Login')
        self.login('admin', 'admin123')
        self.delete_shelf(u'anon')

    # Change database
    @unittest.skip("Change Database Not Implemented")
    def test_shelf_database_change(self):
        self.create_shelf('order', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

    # Change database
    @unittest.skip("Change Database Not Implemented")
    def test_shelf_database_change(self):
        self.create_shelf('order', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
