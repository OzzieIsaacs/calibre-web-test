# -*- coding: utf-8 -*-

import sys
import unittest
from config_test import CALIBRE_WEB_PATH

import threading


def _get_updater_thread():
    for t in threading.enumerate():
        if isinstance(t, updater.Updater):
            return t
    return None


class DummyCLI():
    gd_path = ""

class TestCalibreHelper(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        sys.path.append(CALIBRE_WEB_PATH)

        global helper
        global updater
        # cli_param = DummyCLI()
        # if imported at top of file, the import is excecuted at startup and creates ghost calibre-web instance
        from cps import cli_param
        cli_param.gd_path = "gdrive.db"
        from cps import helper, updater
        # from cps import helper
        # startup function is not called, therfore direct print
        print("\n%s - %s: " % ("", cls.__name__))

    def test_check_high23(self):
        helper.config.config_unicode_filename = True
        self.assertEqual(helper.get_valid_filename(u'²³'), u'23')

    def test_check_doubleS(self):
        helper.config.config_unicode_filename = True
        self.assertEqual(helper.get_valid_filename(u'§ß'), u'SSss')

    def test_check_umlauts(self):
        helper.config.config_unicode_filename = True
        self.assertEqual(helper.get_valid_filename(u'ÄÜÖäöü'), u'AUOaou')

    def test_check_chinese_Characters(self):
        helper.config.config_unicode_filename = True
        self.assertEqual(helper.get_valid_filename(u'执一'), u'Zhi Yi')
        helper.config.config_unicode_filename = False
        self.assertEqual(helper.get_valid_filename(u'执一'), u'执一')

    def test_whitespaces(self):
        helper.config.config_unicode_filename = False
        self.assertEqual(helper.get_valid_filename(u' Alfaman '), u'Alfaman')

    def test_check_finish_Dot(self):
        helper.config.config_unicode_filename = False
        self.assertEqual(helper.get_valid_filename(u'Nameless.'), u'Nameless_')

    def test_check_Limit_Length(self):
        helper.config.config_unicode_filename = False
        self.assertEqual(helper.get_valid_filename(u'1234567890123456789012345678901234567890123456789012345678'
                u'901234567890123456789012345678901234567890123456789012345678901234567890'), u'123456789012345678901'
                u'23456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789'
                u'012345678')

    def test_check_char_replacement(self):
        helper.config.config_unicode_filename = False
        self.assertEqual(helper.get_valid_filename(u'A*B+C:D"E/F<G>H?'), u'A_B_C_D_E_F_G_H_')
        self.assertEqual(helper.get_valid_filename(u'Alfaman| Name'), u'Alfaman, Name')
        self.assertEqual(helper.get_valid_filename(u'**++** Numi **++**'), u'_ Numi _')

    def test_check_deg_eur_replacement(self):
        helper.config.config_unicode_filename = True
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
        # Updater Thread is running in the background, preventing tests main routine from finishing
        # -> Finds updater and stops it
        global helper
        global updater

        del sys.modules["cps.helper"]
        del helper

        updater_thread = _get_updater_thread()
        if updater_thread:
            updater_thread.stop()
        del sys.modules["cps.constants"]
        del sys.modules["cps.cli"]
        del sys.modules["cps.logger"]
        del sys.modules["cps.ub"]
        del sys.modules["cps.config_sql"]
        del sys.modules["cps.cache_buster"]
        del sys.modules["cps.iso_language_names"]
        del sys.modules["cps.isoLanguages"]
        del sys.modules["cps.pagination"]
        del sys.modules["cps.db"]
        del sys.modules["cps.reverseproxy"]
        del sys.modules["cps.server"]
        del sys.modules["cps.services"]
        del sys.modules["cps.updater"]
        del sys.modules["cps"]
        del sys.modules["cps.tasks"]
        del sys.modules["cps.services.worker"]
        del sys.modules["cps.subproc_wrapper"]
        del sys.modules["cps.gdriveutils"]
        del sys.modules["cps.tasks.mail"]
        del sys.modules["cps.tasks.convert"]
        del updater
