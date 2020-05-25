#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase, skip
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from helper_ui import ui_class
from config_test import TEST_DB, base_path
from parameterized import parameterized_class
from helper_func import startup, debug_startup, add_dependency, remove_dependency
import requests

'''@parameterized_class([
   { "py_version": u'/usr/bin/python'},
   { "py_version": u'/usr/bin/python3'}
],names=('Python27','Python36'))'''
class test_edit_books(TestCase, ui_class):
    p=None
    driver = None
    dependencys = ['Pillow','lxml']
    # py_version = u'/usr/bin/python3'

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependencys, cls.__name__)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir':TEST_DB})
            time.sleep(3)
        except Exception as e:
            cls.driver.quit()
            cls.p.kill()


    @classmethod
    def tearDownClass(cls):
        remove_dependency(cls.dependencys)
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        # cls.p.kill()

    # goto Book 1
    # Change Title with unicode chars
    # save title, go to show books page
    # check title
    # edit title with spaces on beginning
    # save title, stay on page
    # check title correct, check folder name correct, old folder deleted
    # edit title remove title
    # save title
    # check title correct (Unknown)
    # change title to something where the title regex matches
    # check title correct, check if book correct in order of a-z books
    # add files to folder of book
    # change title of book,
    # check folder moves completly with all files
    # delete complete folder
    # change title of book
    # error metadata should occour
    # delete cover file
    # change title of book
    # metadata error does not occour
    # Test Capital letters and lowercase characters
    # booktitle with ,;|
    def test_edit_title(self):
        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title':u'O0ü 执'})
        values=self.get_book_details()
        self.assertEqual(u'O0ü 执',values['title'])
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB,values['author'][0],'O0u Zhi (4)')))
        self.assertFalse(os.path.isdir(os.path.join(TEST_DB, values['author'][0],
                                                  'Very long extra super turbo cool tit (4)')))
        self.check_element_on_page((By.ID, "edit_book")).click()
        with open(os.path.join(TEST_DB,values['author'][0],'O0u Zhi (4)','test.dum'), 'wb') as fout:
            fout.write(os.urandom(124))
        self.edit_book(content={'book_title':u' O0ü 执'},detail_v=True)
        title = self.check_element_on_page((By.ID, "book_title"))
        # calibre strips spaces in beginning
        self.assertEqual(u'O0ü 执', title.get_attribute('value'))
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB,values['author'][0],'O0u Zhi (4)')))
        self.edit_book(content={'book_title':u'O0ü name'},detail_v=True)
        title = self.check_element_on_page((By.ID, "book_title"))
        # calibre strips spaces in the end
        self.assertEqual(u'O0ü name', title.get_attribute('value'))
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB,values['author'][0],'O0u name (4)')))
        self.assertFalse(os.path.isdir(os.path.join(TEST_DB, values['author'][0], 'O0u Zhi (4)')))
        self.edit_book(content={'book_title':''})
        values=self.get_book_details()
        os.path.join(TEST_DB,values['author'][0],'Unknown')
        self.assertEqual('Unknown', values['title'])
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB,values['author'][0],'Unknown (4)')))
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title':'The camicdemo'})
        values=self.get_book_details()
        os.path.join(TEST_DB,values['author'][0],'The camicdemo')
        self.assertEqual('The camicdemo',values['title'])
        self.goto_page('nav_new')
        books = self.get_books_displayed()
        self.assertEqual('The camicdemo', books[1][8]['title'])
        file_path=os.path.join(TEST_DB, values['author'][0], 'The camicdemo (4)')
        not_file_path = os.path.join(TEST_DB, values['author'][0], 'camicdemo')
        os.renames(file_path, not_file_path)
        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': u'Not found'})
        self.check_element_on_page((By.ID,'flash_alert'))
        title = self.check_element_on_page((By.ID, "book_title"))
        # calibre strips spaces in the end
        self.assertEqual('The camicdemo', title.get_attribute('value'))
        os.renames(not_file_path, file_path)
        # missing cover file is not detected, and cover file is moved
        cover_file=os.path.join(TEST_DB, values['author'][0], 'The camicdemo (4)','cover.jpg')
        not_cover_file = os.path.join(TEST_DB, values['author'][0], 'The camicdemo (4)','no_cover.jpg')
        os.renames(cover_file, not_cover_file)
        self.edit_book(content={'book_title': u'No Cover'},detail_v=True)
        title = self.check_element_on_page((By.ID, "book_title"))
        self.assertEqual('No Cover', title.get_attribute('value'))
        cover_file=os.path.join(TEST_DB, values['author'][0], 'No Cover (4)','cover.jpg')
        not_cover_file = os.path.join(TEST_DB, values['author'][0], 'No Cover (4)','no_cover.jpg')
        os.renames(not_cover_file, cover_file)
        self.edit_book(content={'book_title': u'Pipo|;.:'},detail_v=True)
        title = self.check_element_on_page((By.ID, "book_title"))
        self.assertEqual(u'Pipo|;.:', title.get_attribute('value'))
        self.edit_book(content={'book_title': u'Very long extra super turbo cool title without any issue of displaying including ö utf-8 characters'})
        ele=self.check_element_on_page((By.ID, "title"))
        self.assertEqual(ele.text, u'Very long extra super turbo cool title without any issue of ...')
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'book_title': u'book6'})



    # goto Book 2
    # Change Author with unicode chars
    # save book, go to show books page
    # check Author
    # edit Author with spaces on beginning (Single name)
    # save book, stay on page
    # check Author correct, check folder name correct, old folder deleted (last book of author)
    # edit Author of book 7, book 2 and 7 have same author now
    # check authorfolder has 2 subfolders
    # change author of book 2
    # save book, stay on page
    # check Author correct, check folder name correct, old folder still existing (not last book of author)
    # edit Author remove Author
    # save book, stay on page
    # check Author correct (Unknown)
    # edit Author, add 2nd not existing author
    # save book, stay on page
    # check Authors correct
    # Author Alfa Alfa & Beta Beta (where is book saved?) -> Alfa Alfa
    # Author Beta Beta & Alfa Alfa (where is book saved?) -> Beta Beta
    # change author to something with ',' in it
    # save book, stay on page
    # check author correct, check if author correct in order authors (author sort should be 2nd 1st)
    # change author to something with '|' in it
    # save book, stay on page
    # check author correct (what is correct)???
    # add files to folder of author
    # change author of book,
    # check folder moves completly with all files
    # remove folder permissions
    # change author of book
    # error should occour
    # remove folder of author
    # change author of book
    # error should occour
    # Test Capital letters and lowercase characters
    def test_edit_author(self):
        self.get_book_details(8)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor':u'O0ü 执'})
        values=self.get_book_details()
        self.assertEqual(u'O0ü 执',values['author'][0])
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB,'O0u Zhi','book8 (8)')))
        self.assertFalse(os.path.isdir(os.path.join(TEST_DB, 'Leo Baskerville',
                                                  'book8 (8)')))
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor':u' O0ü name '},detail_v=True)
        author = self.check_element_on_page((By.ID, "bookAuthor"))
        # calibre strips spaces in the end
        self.assertEqual(u'O0ü name', author.get_attribute('value'))
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB,'O0u name','book8 (8)')))
        self.edit_book(content={'bookAuthor':''})
        values=self.get_book_details()
        os.path.join(TEST_DB,'Unknown','book8 (8)')
        self.assertEqual('Unknown', values['author'][0])
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB,values['author'][0],'book8 (8)')))
        self.check_element_on_page((By.ID, "edit_book")).click()
        # Check authorsort
        self.edit_book(content={'bookAuthor':'Marco, Lulu de'})
        values=self.get_book_details()
        os.path.join(TEST_DB,values['author'][0],'book8 (8)')
        self.assertEqual(values['author'][0],'Marco, Lulu de')
        list_element = self.goto_page('nav_author')
        # ToDo check names of List elements
        self.get_book_details(8)
        self.check_element_on_page((By.ID, "edit_book")).click()

        self.edit_book(content={'bookAuthor': 'Sigurd Lindgren'},detail_v=True)
        author = self.check_element_on_page((By.ID, "bookAuthor")).get_attribute('value')
        self.assertEqual(u'Sigurd Lindgren', author)
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB, author, 'book8 (8)')))
        self.edit_book(content={'bookAuthor': 'Sigurd Lindgren&Leo Baskerville'}, detail_v=True)
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB, 'Sigurd Lindgren', 'book8 (8)')))
        self.assertFalse(os.path.isdir(os.path.join(TEST_DB, 'Leo Baskerville', 'book8 (8)')))
        author = self.check_element_on_page((By.ID, "bookAuthor"))
        self.assertEqual(u'Sigurd Lindgren & Leo Baskerville', author.get_attribute('value'))
        self.edit_book(content={'bookAuthor': ' Leo Baskerville & Sigurd Lindgren '}, detail_v=True)
        self.assertFalse(os.path.isdir(os.path.join(TEST_DB, 'Sigurd Lindgren', 'book8 (8)')))
        self.assertTrue(os.path.isdir(os.path.join(TEST_DB, 'Leo Baskerville', 'book8 (8)')))
        self.edit_book(content={'bookAuthor': 'Pipo| Pipe'}, detail_v=True)
        author = self.check_element_on_page((By.ID, "bookAuthor"))
        self.assertEqual(u'Pipo, Pipe', author.get_attribute('value'))
        list_element = self.goto_page('nav_author')

        file_path=os.path.join(TEST_DB, 'Pipo, Pipe', 'book8 (8)')
        not_file_path = os.path.join(TEST_DB, 'Pipo, Pipe', 'nofolder')
        os.renames(file_path, not_file_path)
        self.get_book_details(8)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'bookAuthor': u'Not found'})
        self.check_element_on_page((By.ID,'flash_alert'))
        author = self.check_element_on_page((By.ID, "bookAuthor"))
        self.assertEqual('Pipo, Pipe', author.get_attribute('value'))
        os.renames(not_file_path, file_path)
        self.edit_book(content={'bookAuthor': 'Leo Baskerville'}, detail_v=True)

    # series with unicode spaces, ,|,
    def test_edit_series(self):
        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':u'O0ü 执'})
        values=self.get_book_details()
        self.assertEqual(u'O0ü 执',values['series'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':u'Alf|alfa, Kuko'})
        values=self.get_book_details()
        self.assertEqual(u'Alf|alfa, Kuko',values['series'])
        list_element = self.goto_page('nav_serie')
        self.assertEqual(list_element[0].text, u'Alf|alfa, Kuko')

        self.get_book_details(9)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':''})
        values=self.get_book_details()
        self.assertFalse('series' in values)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':'Loko'},detail_v=True)
        series = self.check_element_on_page((By.ID, "series"))
        self.assertEqual(u'Loko', series.get_attribute('value'))

        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':u'loko'})
        values=self.get_book_details()
        self.assertEqual(u'loko',values['series'])
        list_element = self.goto_page('nav_serie')
        self.assertEqual(list_element[1].text, u'loko')

        self.get_book_details(4)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series':u'Loko','series_index':'1.0'})
        values=self.get_book_details()
        self.assertEqual(u'Loko', values['series'])
        self.check_element_on_page((By.XPATH, "//*[contains(@href,'series')]/ancestor::p/a")).click()
        books=self.get_books_displayed()
        self.assertEqual(len(books[1]),2)
        books[1][0]['ele'].click()
        ele=self.check_element_on_page((By.ID, "title"))
        self.assertEqual(u'book6', ele.text)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'series': u''})


    def test_edit_category(self):
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':u'O0ü 执'})
        values=self.get_book_details()
        self.assertEqual(len(values['tag']),1)
        self.assertEqual(u'O0ü 执',values['tag'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':u'Alf|alfa'})
        values=self.get_book_details()
        self.assertEqual(u'Alf|alfa',values['tag'][0])
        list_element = self.goto_page('nav_cat')
        self.assertEqual(list_element[0].text, u'Alf|alfa')

        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':''})
        values=self.get_book_details()
        self.assertEqual(len(values['tag']), 0)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':u' Gênot & Peter '},detail_v=True)
        tags = self.check_element_on_page((By.ID, "tags"))
        self.assertEqual(u'Gênot & Peter', tags.get_attribute('value'))

        self.edit_book(content={'tags':u' Gênot , Peter '})
        values = self.get_book_details()
        self.assertEqual(u'Gênot',values['tag'][0])
        self.assertEqual(u'Peter', values['tag'][1])

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':u'gênot'})
        values = self.get_book_details()
        self.assertEqual(u'gênot',values['tag'][0])
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'tags':'Gênot'})


    def test_edit_publisher(self):
        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':u'O0ü 执'})
        values=self.get_book_details()
        self.assertEqual(len(values['publisher']),1)
        self.assertEqual(u'O0ü 执',values['publisher'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':u'Beta|,Bet'})
        values=self.get_book_details()
        self.assertEqual(u'Beta|,Bet',values['publisher'][0])
        list_element = self.goto_page('nav_publisher')
        self.assertEqual(list_element[0].text, u'Beta|,Bet', "Publisher Sorted according to name, B before R")

        self.get_book_details(7)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':''})
        values=self.get_book_details()
        self.assertEqual(len(values['publisher']), 0)

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':u' Gênot & Peter '},detail_v=True)
        publisher = self.check_element_on_page((By.ID, "publisher"))
        self.assertEqual(u'Gênot & Peter', publisher.get_attribute('value'))

        self.edit_book(content={'publisher':u' Gênot , Peter '})
        values = self.get_book_details()
        self.assertEqual(u'Gênot , Peter',values['publisher'][0])

        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':u'gênot'})
        values = self.get_book_details()
        self.assertEqual(u'gênot',values['publisher'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'publisher':u'Gênot'})
        values = self.get_book_details()
        self.assertEqual(u'Gênot', values['publisher'][0])


    # choose language not part ob lib
    def test_edit_language(self):
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages':u'english'})
        values=self.get_book_details()
        self.assertEqual(len(values['languages']),1)
        self.assertEqual('English',values['languages'][0])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages':u'German'})
        values=self.get_book_details()
        self.assertEqual('German',values['languages'][0])
        list_element = self.goto_page('nav_lang')
        self.assertEqual(list_element[2].text, u'German')
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'languages':'German & English'}, detail_v=True)
        self.check_element_on_page((By.ID, 'flash_alert'))
        self.edit_book(content={'languages': 'German, English'})
        self.get_book_details(3)
        values=self.get_book_details()
        self.assertEqual(len(values['languages']),2)
        self.assertEqual('German',values['languages'][1])
        self.assertEqual('English', values['languages'][0])


    # change rating, delete rating
    # check if book with rating of 4 stars appears in list of hot books
    def test_edit_rating(self):
        self.goto_page('nav_rated')
        books=self.get_books_displayed()
        self.assertEqual(1, len(books[1]))
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'rating':4})
        values=self.get_book_details()
        self.assertEqual(4, values['rating'])
        self.goto_page('nav_rated')
        books=self.get_books_displayed()
        self.assertEqual(1, len(books[1]))
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'rating':5})
        values=self.get_book_details()
        self.assertEqual(5, values['rating'])
        self.goto_page('nav_rated')
        books=self.get_books_displayed()
        self.assertEqual(2, len(books[1]))
        self.get_book_details(3)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'rating':0})
        values = self.get_book_details()
        self.assertEqual(0, values['rating'])

    # change comments, add comments, delete comments
    def test_edit_comments(self):
        self.get_book_details(12)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'description':u'bogomirä 人物'})
        values = self.get_book_details()
        self.assertEqual(u'bogomirä 人物', values['comment'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={'description':''})
        values = self.get_book_details()
        self.assertEqual('', values['comment'])

    # change comments, add comments, delete comments
    def test_edit_custom_bool(self):
        self.assertEqual(len(self.adv_search({u'custom_column_3': u'Yes'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Bool 1 Ä':u'Yes'})
        vals = self.get_book_details(5)
        self.assertEqual(u'ok', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_3': u'No'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_3': u'Yes'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Bool 1 Ä': u""})
        vals = self.get_book_details(5)
        self.assertEqual(0,len(vals['cust_columns']))


    def test_edit_custom_rating(self):
        self.assertEqual(len(self.adv_search({u'custom_column_1': u'3'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Rating 人物':'3'})
        vals = self.get_book_details(5)
        self.assertEqual('3', vals['cust_columns'][0]['value'])
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Rating 人物': '6'})
        vals = self.get_book_details(5)
        self.assertEqual('3', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_1': u'4'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_1': u'3'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Rating 人物': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))


    def test_edit_custom_single_select(self):
        self.assertEqual(len(self.adv_search({u'custom_column_9': u'人物'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom 人物 Enum':u'人物'})
        vals = self.get_book_details(5)
        self.assertEqual(u'人物', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_9': u'Alfa'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_9': u'人物'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom 人物 Enum': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))

    # change comments, add comments, delete comments
    def test_edit_custom_text(self):
        self.assertEqual(len(self.adv_search({u'custom_column_10': u'人 Ä'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Text 人物 *\'()&': u'Lulu 人 Ä'})
        vals = self.get_book_details(5)
        self.assertEqual(u'Lulu 人 Ä', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_10': u'Koko'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_10': u'lu'})), 1)
        self.assertEqual(len(self.adv_search({u'custom_column_10': u'人 Ä'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Text 人物 *\'()&': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))

    # change comments, add comments, delete comments
    def test_edit_custom_categories(self):
        self.assertEqual(len(self.adv_search({u'custom_column_6': u'人 Ü'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom categories\|, 人物': u'KuKu 人 Ü'})
        vals = self.get_book_details(5)
        self.assertEqual(u'KuKu 人 Ü', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_6': u'Koko'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_6': u'Ku'})), 1)
        self.assertEqual(len(self.adv_search({u'custom_column_6': u'人 Ü'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom categories\|, 人物': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))


    # change comments, add comments, delete comments
    def test_edit_custom_float(self):
        self.assertEqual(len(self.adv_search({u'custom_column_8': u'-2.5'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Float 人物': u'-2.5'})
        vals = self.get_book_details(5)
        self.assertEqual(u'-2.5', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_8': u'-2.3'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_8': u'-2.5'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Float 人物': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))

    # change comments, add comments, delete comments
    def test_edit_custom_int(self):
        self.assertEqual(len(self.adv_search({u'custom_column_4': u'0'})), 0)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Integer 人物': u'0'})
        vals = self.get_book_details(5)
        self.assertEqual(u'0', vals['cust_columns'][0]['value'])
        self.assertEqual(len(self.adv_search({u'custom_column_4': u'5'})), 0)
        self.assertEqual(len(self.adv_search({u'custom_column_4': u'0'})), 1)
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(custom_content={u'Custom Integer 人物': ''})
        vals = self.get_book_details(5)
        self.assertEqual(0, len(vals['cust_columns']))


    @skip("Not Implemented")
    def test_edit_publishing_date(self):
        self.assertIsNone('Not Implemented')

    def test_typeahead_functions(self):
        req = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        req.post('http://127.0.0.1:8083/login',data=payload)
        r=req.get('http://127.0.0.1:8083/get_languages_json')
        self.assertEqual(200,r.status_code)
        r = req.get('http://127.0.0.1:8083/get_matching_tags')
        self.assertEqual(200, r.status_code)
        r = req.get('http://127.0.0.1:8083/get_series_json')
        self.assertEqual(200, r.status_code)
        r = req.get('http://127.0.0.1:8083/get_tags_json')
        self.assertEqual(200, r.status_code)
        r = req.get('http://127.0.0.1:8083/get_publishers_json')
        self.assertEqual(200, r.status_code)
        r = req.get('http://127.0.0.1:8083/get_authors_json')
        self.assertEqual(200, r.status_code)
        req.close()

    # change comments, add comments, delete comments
    def test_typeahead_language(self):
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        lang = self.check_element_on_page((By.ID, "languages"))
        lang.send_keys(Keys.CONTROL, "a")
        lang.send_keys(Keys.DELETE)
        lang.send_keys('G')
        time.sleep(1)
        typeahead=self.check_element_on_page((By.CLASS_NAME, "tt-dataset-languages"))
        typeahead_set = set(typeahead.text.split("\n"))
        result = set(("German", "Greek; Modern (1453-)", "Ga", "Gayo", "Gbaya (Central African Republic)"))
        self.assertEqual(typeahead_set, result)
        lang.send_keys('a')
        time.sleep(1)
        typeahead_set = set(typeahead.text.split("\n"))
        result = set(("Ga", "Gayo", "Gaelic; Scottish", "Galician", "Ganda"))
        self.assertEqual(typeahead_set, result)
        lang.send_keys('y')
        time.sleep(1)
        typeahead_set= set(typeahead.text.split("\n"))
        result = set(("Gayo","Hiligaynon"))
        self.assertEqual(typeahead_set, result)
        lang.send_keys('o')
        time.sleep(1)
        lang.send_keys(Keys.DOWN)
        lang.send_keys(Keys.RETURN)
        self.check_element_on_page((By.ID, "submit")).click()
        details = self.get_book_details(5)
        self.assertEqual(details['languages'][0], 'Gayo')
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'languages':u'English'})

    def test_typeahead_series(self):
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        lang = self.check_element_on_page((By.ID, "series"))
        lang.send_keys(Keys.CONTROL, "a")
        lang.send_keys(Keys.DELETE)
        lang.send_keys('D')
        time.sleep(1)
        typeahead=self.check_element_on_page((By.CLASS_NAME, "tt-dataset-series"))
        self.assertEqual('Djüngel',typeahead.text)
        lang.send_keys('j')
        time.sleep(1)
        typeahead = self.check_element_on_page((By.CLASS_NAME, "tt-dataset-series"))
        self.assertEqual('Djüngel', typeahead.text)
        lang.send_keys(Keys.DOWN)
        lang.send_keys(Keys.RETURN)
        self.check_element_on_page((By.ID, "submit")).click()
        details = self.get_book_details(5)
        self.assertEqual(details['series'], 'Djüngel')
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'series':u''})

    def test_typeahead_author(self):
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        lang = self.check_element_on_page((By.ID, "bookAuthor"))
        lang.send_keys('&')
        time.sleep(1)
        typeahead = self.check_element_on_page((By.CLASS_NAME, "tt-dataset-authors"))
        typeahead_set = set(typeahead.text.split("\n"))
        result = set(("John Döe & John Döe", "John Döe & Peter Parker", "John Döe & Asterix Lionherd", "John Döe & Frodo Beutlin", "John Döe & Norbert Halagal"))
        self.assertEqual(typeahead_set, result)
        lang.send_keys('ro')
        time.sleep(1)
        typeahead = self.check_element_on_page((By.CLASS_NAME, "tt-dataset-authors"))
        self.assertEqual('John Döe & Frodo Beutlin', typeahead.text)
        lang.send_keys(Keys.DOWN)
        lang.send_keys(Keys.RETURN)
        self.check_element_on_page((By.ID, "submit")).click()
        details = self.get_book_details(5)
        self.assertEqual(details['author'][1], 'Frodo Beutlin')
        self.assertEqual(details['author'][0], 'John Döe')
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'bookAuthor':u'John Döe'})

    def test_typeahead_tag(self):
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        lang = self.check_element_on_page((By.ID, "tags"))
        lang.send_keys(Keys.CONTROL, "a")
        lang.send_keys(Keys.DELETE)
        lang.send_keys('g')
        time.sleep(1)
        typeahead=self.check_element_on_page((By.CLASS_NAME, "tt-dataset-tags"))
        self.assertEqual('Gênot',typeahead.text)
        lang.send_keys('e')
        time.sleep(1)
        typeahead = self.check_element_on_page((By.CLASS_NAME, "tt-dataset-tags"))
        self.assertEqual('Gênot', typeahead.text)
        lang.send_keys(Keys.DOWN)
        lang.send_keys(Keys.RETURN)
        self.check_element_on_page((By.ID, "submit")).click()
        details = self.get_book_details(5)
        self.assertEqual(details['tag'][0], 'Gênot')
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'tags':u''})

    def test_typeahead_publisher(self):
        self.get_book_details(10)
        self.check_element_on_page((By.ID, "edit_book")).click()
        lang = self.check_element_on_page((By.ID, "publisher"))
        lang.send_keys(Keys.CONTROL, "a")
        lang.send_keys(Keys.DELETE)
        lang.send_keys('a')
        time.sleep(1)
        typeahead=self.check_element_on_page((By.CLASS_NAME, "tt-dataset-publishers"))
        self.assertEqual('Randomhäus',typeahead.text)
        lang.send_keys(Keys.DOWN)
        lang.send_keys(Keys.RETURN)
        self.check_element_on_page((By.ID, "submit")).click()
        details = self.get_book_details(10)
        self.assertEqual(details['publisher'][0], 'Randomhäus')
        self.get_book_details(10)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.edit_book(content={u'publisher':u''})

    def test_upload_cover_hdd(self):
        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        jpegcover = os.path.join(base_path, 'files', 'cover.jpg')
        self.edit_book(content={'local_cover': jpegcover})
        self.driver.refresh()
        time.sleep(2)
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = r.get( 'http://127.0.0.1:8083/cover/5')
        with open(jpegcover, 'rb') as reader:
            self.assertEqual(reader.read(),resp.content)

        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        bmpcover = os.path.join(base_path, 'files', 'cover.bmp')
        self.edit_book(content={'local_cover': bmpcover})
        self.assertTrue(self.check_element_on_page((By.CLASS_NAME, "alert")))
        self.driver.refresh()
        time.sleep(2)
        resp = r.get( 'http://127.0.0.1:8083/cover/5')
        with open(jpegcover, 'rb') as reader:
            self.assertEqual(reader.read(), resp.content)

        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        pngcover = os.path.join(base_path, 'files', 'cover.png')
        self.edit_book(content={'local_cover': pngcover})
        self.driver.refresh()
        time.sleep(2)
        resp = r.get( 'http://127.0.0.1:8083/cover/5')
        self.assertEqual('20317',resp.headers['Content-Length'])

        self.get_book_details(5)
        self.check_element_on_page((By.ID, "edit_book")).click()
        pngcover = os.path.join(base_path, 'files', 'cover.webp')
        self.edit_book(content={'local_cover': pngcover})
        self.driver.refresh()
        time.sleep(2)
        resp = r.get( 'http://127.0.0.1:8083/cover/5')
        self.assertEqual('17420',resp.headers['Content-Length'])
        r.close()
        self.assertTrue(False,"Browser-Cache Problem: Old Cover is displayed instead of New Cover")

    # check metadata recognition
    def test_upload_book_pdf(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.pdf')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('book', details['title'])
        self.assertEqual('Unknown', details['author'][0])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = r.get( 'http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('182574',resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()

    # check metadata recognition
    def test_upload_book_fb2(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.fb2')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        # ToDo: check file contents
        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('book', details['title'])
        self.assertEqual('Unknown', details['author'][0])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = r.get( 'http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('182574',resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()

    def test_upload_book_lit(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.lit')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        # ToDo: check file contents
        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('book', details['title'])
        self.assertEqual('Unknown', details['author'][0])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = r.get( 'http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('182574',resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()

    def test_upload_book_mobi(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.mobi')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)
        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('book', details['title'])
        self.assertEqual('Unknown', details['author'][0])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = r.get( 'http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('182574',resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()


    def test_upload_book_epub(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.epub')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)

        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('book9', details['title'])
        self.assertEqual('Noname 23', details['author'][0])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = r.get( 'http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('8936',resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()

    def test_upload_book_cbz(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.cbz')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)

        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('book', details['title'])
        self.assertEqual('Unknown', details['author'][0])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = r.get( 'http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('8936', resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()

    def test_upload_book_cbt(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.cbt')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)

        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('book', details['title'])
        self.assertEqual('Unknown', details['author'][0])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = r.get( 'http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('8936',resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()


    def test_upload_book_cbr(self):
        self.fill_basic_config({'config_uploading':1})
        time.sleep(3)
        self.goto_page('nav_new')
        upload_file = os.path.join(base_path, 'files', 'book.cbr')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(upload_file)

        time.sleep(2)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        details = self.get_book_details()
        self.assertEqual('book', details['title'])
        self.assertEqual('Unknown', details['author'][0])
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = r.get( 'http://127.0.0.1:8083' + details['cover'])
        self.assertEqual('182574',resp.headers['Content-Length'])
        self.fill_basic_config({'config_uploading': 0})
        r.close()

    # download of books
    def test_download_book(self):
        self.goto_page('user_setup')
        book_downloads = self.driver.find_elements_by_class_name("media-object")
        self.assertEqual(0, len(book_downloads))
        self.get_book_details(5)
        element=self.check_element_on_page((By.XPATH, "//*[starts-with(@id,'btnGroupDrop')]"))
        download_link=element.get_attribute("href")
        self.assertTrue(download_link.endswith('/5.epub'),'Download Link has invalid format for kobo browser, has to end with filename')
        r = requests.session()
        payload = {'username': 'admin', 'password': 'admin123', 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login',data=payload)
        resp = r.get(download_link)
        self.assertEqual(resp.headers['Content-Type'],'application/epub+zip')
        self.assertEqual(resp.status_code, 200)
        self.edit_user('admin',{'download_role':0})
        resp = r.get(download_link)
        self.assertEqual(resp.status_code, 403)
        book = self.get_book_details(5)
        self.assertNotIn('download', book)
        self.edit_user('admin', {'download_role': 1})
        r.close()
        self.goto_page('user_setup')
        book_downloads = self.driver.find_elements_by_class_name("media-object")
        self.assertEqual(1, len(book_downloads))
        book_downloads[0].click()
        book = self.get_book_details()
        self.assertEqual('testbook', book['title'])
        # self.assertFalse(self.check_element_on_page((By.XPATH, "//*/h2/div/")))


    # If more than one book has the same: author, tag or series it should be possible to change uppercase
    # letters to lowercase and vice versa. Example:
    # Book1 and Book2 are both part of the series "colLection". Changing the series to 'collection'
    # Expected Behavior: Both books later on are part of the series 'collection'
    @skip("Not Implemented")
    def test_rename_uppercase_lowercase(self):
        pass

    # If authors are: "Claire North & Peter Snoogut" then authorsort should be: "North, Claire & Snoogut, Peter"
    # The files should be saved in ../Claire North/...
    # ------------ nachfolgendes kann man sich sparen ---------
    # the IDs in books_authors links have to be arranged according to sort order of names e.g:
    # before : Claire North (4) Peter Snoogut (100) -> "Peter Snoogut & Claire North"
    # afterwards Claire North (100) Peter Snoogut (4)