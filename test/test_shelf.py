#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from selenium.webdriver.common.by import By
import time
from ui_helper import ui_class
from testconfig import TEST_DB
from func_helper import is_port_in_use
from parameterized import parameterized_class
from func_helper import startup

'''@parameterized_class([
   { "py_version": u'/usr/bin/python'},
   { "py_version": u'/usr/bin/python3'},
],names=('Python27','Python36'))'''
class test_shelf(unittest.TestCase, ui_class):
    p=None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version,{'config_calibre_dir':TEST_DB}, request=True)
            cls.create_user('shelf', {'edit_shelf_role':1, 'password':'123', 'email':'a@b.com'})
            cls.edit_user('admin',{'edit_shelf_role':1, 'email':'e@fe.de'})
        except:
            if is_port_in_use(8083):
                print('port in use')
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.kill()

    def tearDown(self):
        if not self.check_user_logged_in('admin'):
            self.logout()
            self.login('admin','admin123')
        while True:
            shelfs = self.list_shelfs()
            if not len(shelfs):
                break
            try:
                shelfs[0]['ele'].click()
                self.check_element_on_page((By.ID, "delete_shelf")).click()
                self.check_element_on_page((By.ID, "confirm")).click()
            except:
                pass

    def test_private_shelf(self):
        self.goto_page('create_shelf')
        self.create_shelf('Pü 执',False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('shelf','123')
        # other user can't see shelf
        self.assertFalse(len(self.list_shelfs()))
        # self.assertFalse(self.driver.find_elements_by_xpath( "//a/span[@class='glyphicon glyphicon-list']//ancestor::a"))
        # other user is not able to add books
        self.driver.get("http://127.0.0.1:8083/shelf/add/1/1")
        self.assertTrue(self.check_element_on_page((By.ID, "flash_alert")))
        self.logout()
        self.login('admin','admin123')
        books = self.get_books_displayed()
        # books[1][0].click()
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
        self.logout()
        self.login('admin','admin123')
        # go to shelf page
        self.list_shelfs(u'Pü 执')['ele'].click()
        self.check_element_on_page((By.ID, "delete_shelf")).click()
        self.check_element_on_page((By.ID, "confirm")).click()
        # shelf is gone
        self.assertFalse(len(self.list_shelfs()))

    def test_public_shelf(self):
        self.goto_page('create_shelf')
        self.create_shelf('Gü 执',True)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.logout()
        self.login('shelf','123')
        # other user can see shelf
        shelfs = self.list_shelfs(u'Gü 执')
        self.assertTrue(shelfs)
        # other user is able to add books
        self.driver.get("http://127.0.0.1:8083/shelf/add/1/" + shelfs['id'])
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
        self.list_shelfs(u'Gü 执')['ele'].click()
        # self.check_element_on_page((By.XPATH, "//a/span[@class='glyphicon glyphicon-list']")).click()
        self.check_element_on_page((By.ID, "delete_shelf"))
        shelf_books = self.get_books_displayed()
        # No random books displayed, 2 books in shelf
        self.assertTrue(len(shelf_books[0]) == 2)
        self.assertTrue(len(shelf_books[1]) == 0)
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
        self.list_shelfs(u'Gü 执')[0]['ele'].click()
        self.check_element_on_page((By.ID, "delete_shelf"))
        shelf_books = self.get_books_displayed()
        # No random books displayed, 3 books in shelf
        self.assertTrue(len(shelf_books[0]) == 3)
        self.assertTrue(len(shelf_books[1]) == 0)

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
    # @unittest.expectedFailure
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
        test= self.list_shelfs('order')[0]['ele'].click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(shelf_books[0]['id'], '13')
        self.assertEqual(shelf_books[1]['id'], '11')
        self.assertEqual(shelf_books[2]['id'], '9')
        self.check_element_on_page((By.ID, "order_shelf")).click()
        order = self.get_order_shelf_list()
        self.driver.request('POST', 'http://127.0.0.1:8083/shelf/order/1',
                                          data={"9": "1","11": "2","13": "3"})
        self.driver.refresh() # reload page

        self.check_element_on_page((By.ID, "shelf_back")).click()
        shelf_books = self.get_shelf_books_displayed()
        self.assertEqual(shelf_books[0]['id'], '9')
        self.assertEqual(shelf_books[1]['id'], '11')
        self.assertEqual(shelf_books[2]['id'], '13')

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
        self.list_shelfs('shelf_public')[0]['ele'].click()
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
        self.list_shelfs('shelf_private')['ele'].click()
        del_shelf = self.check_element_on_page((By.ID, "delete_shelf"))
        del_shelf.click()
        self.check_element_on_page((By.ID, "confirm")).click()
        self.logout()
        self.login('admin','admin123')
        self.assertTrue(self.list_shelfs('shelf_public'))

    # Add shelf with extra long name
    def test_shelf_long_name(self):
        self.create_shelf('Halllalalalal1l1ll2332434llsfllsdfglsdflglfdglfdlgldfsglsdlgrtfgsdfvxccbbsgtsvxv', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.assertTrue(self.list_shelfs('Halllalalalal1l1ll2332434llsfllsdfgls[..]'))


    # Change database
    @unittest.skip("Change Database Not Implemented")
    def test_shelf_database_change(self):
        self.create_shelf('order', False)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))