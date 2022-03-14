#!/usr/bin/env python
# -*- coding: utf-8 -*-


from unittest import TestCase
import os
import time

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB, base_path, BOOT_TIME
from helper_func import save_logfiles, startup, change_epub_meta, updateZip
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from diffimg import diff

class TestUploadEPubs(TestCase, ui_class):
    p = None
    driver = None

    @classmethod
    def setUpClass(cls):
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_uploading': 1}, env = {"APP_MODE": "test"})
            time.sleep(3)
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        # remove_dependency(cls.dependencys)
        cls.driver.get("http://127.0.0.1:8083")
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_upload_epub_duplicate(self):
        epub_file = os.path.join(base_path, 'files', 'title.epub')
        change_epub_meta(epub_file, meta={'title': "Der titel", 'creator': "Kurt Hugo"})
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Der titel', details['title'])
        self.assertEqual('Kurt Hugo', details['author'][0])
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details2 = self.get_book_details()
        self.delete_book(details['id'])
        self.delete_book(details2['id'])
        os.remove(epub_file)

    def verify_upload(self, epub_file, check_warning=False):
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(epub_file)
        time.sleep(3)
        if check_warning:
            self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(1)
        return self.get_book_details()

    def test_upload_epub_lang(self):
        epub_file = os.path.join(base_path, 'files', 'lang.epub')
        self.change_visibility_me({'locale': "Italiano"})
        change_epub_meta(epub_file, meta={'title': "Langtest", 'creator': "Nobody Perfect", "language": "xx"})
        details = self.verify_upload(epub_file, check_warning=True)
        self.assertEqual('Langtest', details['title'])
        self.assertEqual('Nobody Perfect', details['author'][0])
        self.assertNotIn('languages', details)
        self.delete_book(details['id'])
        change_epub_meta(epub_file, meta={'title': "Langtest", 'creator': "Nobody Perfect", "language": "xyz"})
        details = self.verify_upload(epub_file, check_warning=True)
        self.assertNotIn('languages', details)
        self.delete_book(details['id'])
        change_epub_meta(epub_file, meta={'title': "Langtest", 'creator': "Nobody Perfect", "language": "deu"})
        details = self.verify_upload(epub_file)
        self.assertEqual('Tedesco', details['languages'][0])
        list_element = self.goto_page("nav_lang")
        self.assertEqual('Tedesco', list_element[2].text)
        list_element[2].click()
        self.assertEqual("Lingua: Tedesco", self.driver.find_elements(By.TAG_NAME, "h2")[1].text)
        self.assertEqual(len(self.adv_search({u'include_language': u'Tedesco'})), 1)
        self.delete_book(details['id'])
        change_epub_meta(epub_file, meta={'title': "Langtest", 'creator': "Nobody Perfect", "language": "lat"})
        details = self.verify_upload(epub_file)
        self.assertEqual('Latino', details['languages'][0])
        list_element = self.goto_page("nav_lang")
        self.assertEqual('Latino', list_element[1].text)
        list_element[1].click()
        self.assertEqual("Lingua: Latino", self.driver.find_elements(By.TAG_NAME, "h2")[1].text)
        self.assertEqual(len(self.adv_search({u'include_language': u'Latino'})), 1)
        self.delete_book(details['id'])
        change_epub_meta(epub_file, meta={'title': "Langtest", 'creator': "Nobody Perfect", "language": "und"})
        details = self.verify_upload(epub_file)
        self.assertEqual('Non determinato', details['languages'][0])
        self.delete_book(details['id'])

        change_epub_meta(epub_file, meta={'title': "Langtest", 'creator': "Nobody Perfect", "language": "de"})
        details = self.verify_upload(epub_file)
        self.assertEqual('Tedesco', details['languages'][0])
        self.delete_book(details['id'])
        self.change_visibility_me({'locale': "English", "default_language": "Inglese"})
        # Check uploaded book with applied visibility restriction is visible -> book language is changed
        details = self.verify_upload(epub_file)
        self.assertEqual('English', details['languages'][0])
        self.delete_book(details['id'])
        self.change_visibility_me({'default_language': "Show All"})
        os.remove(epub_file)

    def test_upload_epub_cover(self):
        orig = self.verify_upload(os.path.join(base_path, 'files', 'book.epub'))
        self.save_cover_screenshot('original.png')
        self.delete_book(orig['id'])

        # check cover-image is detected
        epub_file = os.path.join(base_path, 'files', 'cover.epub')
        change_epub_meta(epub_file, meta={'title': "Coverimage", 'creator': "Testo"},
                         item={'change': {"find_id": "cover", 'id':'cover-image'}})
        ci = self.verify_upload(epub_file)
        self.save_cover_screenshot('cover_image.png')
        self.delete_book(ci['id'])
        self.assertAlmostEqual(diff('original.png', 'cover_image.png', delete_diff_file=True), 0.0, delta=0.0001)

        # check if multiple cover-image ids are detected correct
        change_epub_meta(epub_file, meta={'title': "Multi Coverimage", 'creator': "Testo"},
                         meta_change={'create': {"name": "cover", 'content': "cover-image"}},
                         item={'change': {"find_id": "cover", 'id': 'cover-image', 'href': 'cover.html'},
                               'create': {"id": "cover-image", 'href': 'cover.jpeg', 'media-type': 'image/jpeg'}})
        ci = self.verify_upload(epub_file)
        self.save_cover_screenshot('cover_image.png')
        self.delete_book(ci['id'])
        self.assertAlmostEqual(diff('original.png', 'cover_image.png', delete_diff_file=True), 0.0, delta=0.0001)

        # check if properties as cover selector is detected with reference from meta
        change_epub_meta(epub_file, meta={'title': "Properties Cover", 'creator': "Testo"},
                         meta_change={'create': {"name": "cover", 'content': "cover-imag"}},
                         item={'delete': {"id": "cover"},
                               'create': {"id": "id_Images_jpg", "properties": "cover-imag", 'href': 'cover.jpeg',
                                          'media-type': 'image/jpeg'}})
        ci = self.verify_upload(epub_file)
        self.save_cover_screenshot('cover_image.png')
        self.delete_book(ci['id'])
        self.assertAlmostEqual(diff('original.png', 'cover_image.png', delete_diff_file=True), 0.0, delta=0.0001)

        # check if content cover selector is detected with reference from meta
        change_epub_meta(epub_file, meta={'title': "Cover", 'creator': "Testo"},
                         meta_change={'create': {"name": "cover", 'content': "cover-imge"}},
                         item={'delete': {"id": "cover"},
                               'create': {"id": "cover-imge", 'href': 'cover.jpeg', 'media-type': 'image/jpeg'}})
        ci = self.verify_upload(epub_file)
        self.save_cover_screenshot('cover_image.png')
        self.delete_book(ci['id'])
        self.assertAlmostEqual(diff('original.png', 'cover_image.png', delete_diff_file=True), 0.0, delta=0.0001)

        # check if guide reference can act as cover with reference from meta
        change_epub_meta(epub_file, meta={'title': "Cover", 'creator': "Testo"},
                         item={'delete': {"id": "cover"}},
                         guide={'change': {"find_title": "Cover", "href": 'cover.jpeg'}})
        ci = self.verify_upload(epub_file)
        self.save_cover_screenshot('cover_image.png')
        self.delete_book(ci['id'])
        self.assertAlmostEqual(diff('original.png', 'cover_image.png', delete_diff_file=True), 0.0, delta=0.0001)

        # check if multiple guide reference can act as cover with reference from meta
        change_epub_meta(epub_file, meta={'title': "Cover", 'creator': "Testo"},
                         item={'delete': {"id": "cover"}},
                         guide={'create': {"title": "Cover", "href": 'cover.jpeg'}})
        ci = self.verify_upload(epub_file)
        self.save_cover_screenshot('cover_image.png')
        self.delete_book(ci['id'])
        self.assertAlmostEqual(diff('original.png', 'cover_image.png', delete_diff_file=True), 0.0, delta=0.0001)

        os.remove(epub_file)
        os.remove('cover_image.png')
        os.remove('original.png')

    def test_upload_epub_cover_formats(self):
        orig = self.verify_upload(os.path.join(base_path, 'files', 'book.epub'))
        self.save_cover_screenshot('original.png')
        self.delete_book(orig['id'])

        # check cover-image is detected
        epub_file = os.path.join(base_path, 'files', 'cover.epub')
        change_epub_meta(epub_file, meta={'title': "png Cover", 'creator': "Testo"},
                         item={'change': {"find_id": "cover", 'id':'cover-image', 'href': 'cover.png'}})
        with open(os.path.join(base_path, 'files', 'cover.png'), "rb") as f:
            data = f.read()
        epub_png = os.path.join(base_path, 'files', 'png.epub')
        updateZip(epub_png, epub_file, 'cover.png', data)

        ci = self.verify_upload(epub_png)
        self.save_cover_screenshot('cover_image.png')
        self.delete_book(ci['id'])
        self.assertAlmostEqual(diff('original.png', 'cover_image.png', delete_diff_file=True), 0.0058, delta=0.0001)

        os.remove(epub_file)
        os.remove(epub_png)
        os.remove('cover_image.png')
        os.remove('original.png')
