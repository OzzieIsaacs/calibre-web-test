# -*- coding: utf-8 -*-

import sys
import unittest
from config_test import CALIBRE_WEB_PATH
from helper_func import save_logfiles

sys.path.append(CALIBRE_WEB_PATH)



class TestCalibreHelper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global helper
        from cps import helper

    def test_check_high23(self):
        self.assertEqual(helper.get_valid_filename(u'²³'), u'23')

    def test_check_doubleS(self):
        self.assertEqual(helper.get_valid_filename(u'§ß'), u'SSss')

    def test_check_umlauts(self):
        self.assertEqual(helper.get_valid_filename(u'ÄÜÖäöü'), u'AUOaou')

    def test_check_chinese_Characters(self):
        self.assertEqual(helper.get_valid_filename(u'执一'), u'Zhi Yi')

    def test_whitespaces(self):
        self.assertEqual(helper.get_valid_filename(u' Alfaman '), u'Alfaman')

    def test_check_finish_Dot(self):
        self.assertEqual(helper.get_valid_filename(u'Nameless.'), u'Nameless_')

    def test_check_Limit_Length(self):
        self.assertEqual(helper.get_valid_filename(u'1234567890123456789012345678901234567890123456789012345678'
                u'901234567890123456789012345678901234567890123456789012345678901234567890'), u'123456789012345678901'
                u'23456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789'
                u'012345678')

    def test_check_char_replacement(self):
        self.assertEqual(helper.get_valid_filename(u'A*B+C:D"E/F<G>H?'), u'A_B_C_D_E_F_G_H_')
        self.assertEqual(helper.get_valid_filename(u'Alfaman| Name'), u'Alfaman, Name')
        self.assertEqual(helper.get_valid_filename(u'**++** Numi **++**'), u'_ Numi _')

    def test_check_deg_eur_replacement(self):
        self.assertEqual(helper.get_valid_filename(u'°€'), u'degEUR')

    def test_author_sort(self):
        self.assertEqual(helper.get_sorted_author(u'Hugo Boss'), u'Boss, Hugo')
        self.assertEqual(helper.get_sorted_author(u'Hugo-Peter Boss'), u'Boss, Hugo-Peter')
        self.assertEqual(helper.get_sorted_author(u'Hugo Peter Boss'), u'Boss, Hugo Peter')
        self.assertEqual(helper.get_sorted_author(u'Hugo Boss-Schnuffel'), u'Boss-Schnuffel, Hugo')

    def test_author_sort_roman(self):
        self.assertEqual(helper.get_sorted_author(u'Hügo Böso I'), u'Böso, Hügo I')
        self.assertEqual(helper.get_sorted_author(u'Hügo Böso II.'), u'Böso, Hügo II.')
        self.assertEqual(helper.get_sorted_author(u'Hügo Böso III'), u'Böso, Hügo III')
        self.assertEqual(helper.get_sorted_author(u'Hügo Böso IV.'), u'Böso, Hügo IV.')

    def test_author_sort_junior(self):
        self.assertEqual(helper.get_sorted_author(u'Herb Suli sr.'), u'Suli, Herb sr.')
        self.assertEqual(helper.get_sorted_author(u'Herb Suli jr.'), u'Suli, Herb jr.')
        self.assertEqual(helper.get_sorted_author(u'Herb Suli jr'), u'Suli, Herb jr')
        self.assertEqual(helper.get_sorted_author(u'Garcia'), u'Garcia')
        self.assertEqual(helper.get_sorted_author(u'Jr.'), u'Jr.')


    def test_author_sort_oneword(self):
        self.assertEqual(helper.get_sorted_author(u'Single'), u'Single')

    def test_author_sort_comma(self):
        self.assertEqual(helper.get_sorted_author(u'Single, name'), u'Single, name')

    def test_split_authors(self):
        self.assertEqual(helper.split_authors([u'Single, name']), [u'name Single'])
        self.assertEqual(helper.split_authors(['']), [u''])
        self.assertEqual(helper.split_authors(['Marilyn Allman Maye, Harold S. Buchanan, Jannette O. Domingo, Joyce Frisby Baynes, Marilyn Holifield, Myra E. Rose, Bridget Van Gronigen Warren & Aundrea White Kelley']),
                         ['Marilyn Allman Maye', 'Harold S. Buchanan', 'Jannette O. Domingo', 'Joyce Frisby Baynes',
                          'Marilyn Holifield', 'Myra E. Rose', 'Bridget Van Gronigen Warren', 'Aundrea White Kelley'])
        self.assertEqual(helper.split_authors([u'Single, Name, Pöo']), [u'Single', 'Name', 'Pöo'])
        self.assertEqual(helper.split_authors([u'Single, Name', 'Hügo Mertens', 'Hollo']),
                         [u'Name Single', 'Hügo Mertens', 'Hollo'])
        self.assertEqual(helper.split_authors([u'Single Name ;Name Nowhere & Thelma Mok']),
                         [u'Single Name', 'Name Nowhere', 'Thelma Mok'])
        self.assertEqual(helper.split_authors([u'Single Name ;Name Nowhere & Thelma Mok']),
                         [u'Single Name', 'Name Nowhere', 'Thelma Mok'])
        # You can't be right every time
        self.assertEqual(helper.split_authors([u'Martin, George R.R.; Garcia, Jr., Elio M.; Antonsson, Linda']),
                         ['George R.R. Martin','Garcia', 'Jr.', 'Elio M.', 'Linda Antonsson'])

    def test_random_password(self):
        for i in range(1,100):
            self.assertTrue(helper.generate_random_password())


    @classmethod
    def tearDownClass(cls):
        global helper
        # helper.global_WorkerThread.stop()
        del sys.modules["cps.helper"]
        del helper
        save_logfiles(cls.__name__)