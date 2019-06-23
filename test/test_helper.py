#!/usr/bin/env python
# -*- coding: utf-8 -*-

# import testconfig
import os
import sys
import unittest
from testconfig import CALIBRE_WEB_PATH

# Insert local directories into path
# sys.path.insert(0, os.path.join(CALIBRE_WEB_PATH, 'cps'))
sys.path.append(CALIBRE_WEB_PATH)
# sys.path.insert(0, os.path.join(CALIBRE_WEB_PATH, 'vendor'))


class calibre_helper(unittest.TestCase):

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

    def test_check_finish_Dot(self):
        self.assertEqual(helper.get_valid_filename(u'Nameless.'), u'Nameless_')

    def test_check_Limit_Length(self):
        self.assertEqual(helper.get_valid_filename(u'1234567890123456789012345678901234567890123456789012345678'
                u'901234567890123456789012345678901234567890123456789012345678901234567890'), u'123456789012345678901'
                u'23456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789'
                                                                                             u'012345678')
    def test_check_char_replacement(self):
        self.assertEqual(helper.get_valid_filename(u'A*B+C:D"E/F<G>H?'), u'A_B_C_D_E_F_G_H_')

    def test_check_degEUR_replacement(self):
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

    def test_author_sort_oneword(self):
        self.assertEqual(helper.get_sorted_author(u'Single'), u'Single')

    def test_author_sort_comma(self):
        self.assertEqual(helper.get_sorted_author(u'Single, name'), u'Single, name')

    @classmethod
    def tearDownClass(cls):
        global helper
        helper.global_WorkerThread.stop()
        del sys.modules["cps.helper"]
        del helper

