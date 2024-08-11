#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shutil
from unittest import TestCase
import os
import time

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB, base_path
from helper_func import save_logfiles, startup
from helper_func import startup, add_dependency, remove_dependency
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from diffimg import diff
from io import BytesIO
import mutagen
from mutagen import mp3, wave, aiff
import os

RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


class TestUploadAudio(TestCase, ui_class):
    p = None
    driver = None
    dependencys = ["mutagen"]

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependencys, cls.__name__)
        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_uploading': 1},
                    port=PORTS[0], index=INDEX,
                    env={"APP_MODE": "test"})
            time.sleep(3)
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        except Exception:
            cls.driver.quit()
            cls.p.kill()

    @classmethod
    def tearDownClass(cls):
        remove_dependency(cls.dependencys)
        cls.driver.get("http://127.0.0.1:" + PORTS[0])
        cls.stop_calibre_web()
        # close the browser window and stop calibre-web
        cls.driver.quit()
        cls.p.terminate()
        save_logfiles(cls, cls.__name__)

    def test_upload_mp3(self):
        dest = os.path.join(base_path, "files", 'base.mp3')
        shutil.copyfile(os.path.join(base_path, "files", 'music.mp3'), dest)
        mp3_file = mp3.MP3(dest)
        mp3_file['TIT2'] = mutagen.id3.TIT2(encoding=1, text=['MP3 Title'])
        mp3_file['TPE1'] = mutagen.id3.TPE1(encoding=1, text=['MP3 Artist'])
        mp3_file['COMM'] = mutagen.id3.COMM(encoding=1, text=['No Comment'])
        mp3_file['TDRL'] = mutagen.id3.TDRL(encoding=1, text=['2022-312-12'])
        mp3_file['TCON'] = mutagen.id3.TCON(encoding=1, text=['Genr#ä'])
        mp3_file['TALB'] = mutagen.id3.TALB(encoding=1, text=['Album'])
        mp3_file['TRCK'] = mutagen.id3.TRCK(encoding=1, text=['2/7'])
        mp3_file['TPUB'] = mutagen.id3.TPUB(encoding=1, text=['Älsids sdk'])

        with open(os.path.join("files", 'cover.png'), "rb") as f:
            ref_picture = f.read()
        with open(os.path.join("files", 'cover.jpg'), "rb") as f:
            jpg_picture = f.read()

        mp3_file.tags.add(
            mutagen.id3.APIC(
                encoding=3,         # 3 is for utf-8
                mime='image/jpg',   # image/jpeg or image/png
                type=2,             # 3 is for the cover image
                desc=u'BackCover',
                data=jpg_picture
            )
        )
        mp3_file.tags.add(
            mutagen.id3.APIC(
                encoding=3,         # 3 is for utf-8
                mime='image/png',   # image/jpeg or image/png
                type=3,             # 3 is for the cover image
                desc=u'Cover',
                data=ref_picture
            )
        )
        mp3_file.save()

        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('MP3 Title', details['title'])
        self.assertEqual('MP3 Artist', details['author'][0])
        self.assertEqual('Genr#ä', details['tag'][0])
        self.assertEqual('Älsids sdk', details['publisher'][0])
        self.assertEqual('No Comment', details['comment'])
        self.assertEqual('2', details['series_index'])
        self.assertEqual('Album', details['series'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(ref_picture), BytesIO(cover_image), delete_diff_file=True), 0.007, delta=0.003)
        self.delete_book(details['id'])
        mp3_file = mp3.MP3(dest)
        mp3_file['TDRL'] = mutagen.id3.TDRL(encoding=1, text=['2022-12-12'])
        mp3_file.save()
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Dec 12, 2022', details['pubdate'])
        self.delete_book(details['id'])
        os.remove(dest)

    def test_upload_wav(self):
        dest = os.path.join(base_path, "files", 'base.wav')
        shutil.copyfile(os.path.join(base_path, "files", 'music.wav'), dest)
        wave_file = wave.WAVE(dest)
        wave_file['TIT2'] = mutagen.id3.TIT2(encoding=1, text=['Wav Title'])
        wave_file['TPE1'] = mutagen.id3.TPE1(encoding=1, text=['Wav Artist'])
        wave_file['COMM'] = mutagen.id3.COMM(encoding=1, text=['No Commento'])
        wave_file['TDRL'] = mutagen.id3.TDRL(encoding=1, text=['2022-312-12'])
        wave_file['TCON'] = mutagen.id3.TCON(encoding=1, text=['Genr#Ä'])
        wave_file['TALB'] = mutagen.id3.TALB(encoding=1, text=['Album'])
        wave_file['TRCK'] = mutagen.id3.TRCK(encoding=1, text=['2/12'])
        wave_file['TPUB'] = mutagen.id3.TPUB(encoding=1, text=['Älsids sdksdsd '])

        with open(os.path.join("files", 'cover.png'), "rb") as f:
            ref_picture = f.read()
        with open(os.path.join("files", 'cover.jpg'), "rb") as f:
            jpg_picture = f.read()


        wave_file.tags.add(
            mutagen.id3.APIC(
                encoding=3,         # 3 is for utf-8
                mime='image/jpg',   # image/jpeg or image/png
                type=3,             # 3 is for the cover image
                desc=u'BackCover',
                data=jpg_picture
            )
        )
        wave_file.tags.add(
            mutagen.id3.APIC(
                encoding=3,         # 3 is for utf-8
                mime='image/png',   # image/jpeg or image/png
                type=1,             # 3 is for the cover image
                desc=u'Cover',
                data=ref_picture
            )
        )
        wave_file.save()

        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Wav Title', details['title'])
        self.assertEqual('Wav Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        self.assertEqual('Älsids sdksdsd', details['publisher'][0])
        self.assertEqual('No Commento', details['comment'])
        self.assertEqual('2', details['series_index'])
        self.assertEqual('Album', details['series'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        # self.assertAlmostEqual(diff(BytesIO(jpg_picture), BytesIO(cover_image), delete_diff_file=True), 0.007, delta=0.003)
        self.delete_book(details['id'])
        wave_file = wave.WAVE(dest)
        wave_file['TDRL'] = mutagen.id3.TDRL(encoding=1, text=['2022-12-12'])
        wave_file.save()
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Dec 12, 2022', details['pubdate'])
        self.delete_book(details['id'])
        os.remove(dest)

    def test_upload_aiff(self):
        dest = os.path.join(base_path, "files", 'base.aiff')
        shutil.copyfile(os.path.join(base_path, "files", 'music.aiff'), dest)
        aiff_file = aiff.AIFF(dest)
        aiff_file['TIT2'] = mutagen.id3.TIT2(encoding=1, text=['Wav Title'])
        aiff_file['TPE1'] = mutagen.id3.TPE1(encoding=1, text=['Wav Artist'])
        aiff_file['COMM'] = mutagen.id3.COMM(encoding=1, text=['No Commento'])
        aiff_file['TDRL'] = mutagen.id3.TDRL(encoding=1, text=['2022-312-12'])
        aiff_file['TCON'] = mutagen.id3.TCON(encoding=1, text=['Genr#Ä'])
        aiff_file['TALB'] = mutagen.id3.TALB(encoding=1, text=['Album'])
        aiff_file['TRCK'] = mutagen.id3.TRCK(encoding=1, text=['2/12'])
        aiff_file['TPUB'] = mutagen.id3.TPUB(encoding=1, text=['Älsids sdksdsd '])

        with open(os.path.join("files", 'cover.png'), "rb") as f:
            ref_picture = f.read()

        aiff_file.tags.add(
            mutagen.id3.APIC(
                encoding=3,         # 3 is for utf-8
                mime='image/png',   # image/jpeg or image/png
                type=7,             # 3 is for the cover image
                desc=u'BackCover',
                data=ref_picture
            )
        )
        aiff_file.save()
        self.fill_basic_config({'config_upload_formats': 'djv,mobi,cbr,ogg,cbt,rtf,mp4,mp3,epub,fb2,m4b,pdf,cb7,opus,azw3,odt,flac,txt,lit,doc,prc,wav,kepub,djvu,docx,m4a,cbz,html,azw,aiff'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Wav Title', details['title'])
        self.assertEqual('Wav Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        self.assertEqual('Älsids sdksdsd', details['publisher'][0])
        self.assertEqual('No Commento', details['comment'])
        self.assertEqual('2', details['series_index'])
        self.assertEqual('Album', details['series'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(ref_picture), BytesIO(cover_image), delete_diff_file=True), 0.007, delta=0.003)
        self.delete_book(details['id'])
        aiff_file = aiff.AIFF(dest)
        aiff_file['TDRL'] = mutagen.id3.TDRL(encoding=1, text=['2022-12-12'])
        aiff_file.save()
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Dec 12, 2022', details['pubdate'])
        self.delete_book(details['id'])
        self.fill_basic_config({
                                   'config_upload_formats': 'djv,mobi,cbr,ogg,cbt,rtf,mp4,mp3,epub,fb2,m4b,pdf,cb7,opus,azw3,odt,flac,txt,lit,doc,prc,wav,kepub,djvu,docx,m4a,cbz,html,azw'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        os.remove(dest)

    '''def test_upload_ogg(self):
        dest = os.path.join(base_path, "files", 'base.aiff')
        shutil.copyfile(os.path.join(base_path, "files", 'music.aiff'), dest)
        aiff_file = aiff.AIFF(dest)
        aiff_file['TIT2'] = mutagen.id3.TIT2(encoding=1, text=['Wav Title'])
        aiff_file['TPE1'] = mutagen.id3.TPE1(encoding=1, text=['Wav Artist'])
        aiff_file['COMM'] = mutagen.id3.COMM(encoding=1, text=['No Commento'])
        aiff_file['TDRL'] = mutagen.id3.TDRL(encoding=1, text=['2022-312-12'])
        aiff_file['TCON'] = mutagen.id3.TCON(encoding=1, text=['Genr#Ä'])
        aiff_file['TALB'] = mutagen.id3.TALB(encoding=1, text=['Album'])
        aiff_file['TRCK'] = mutagen.id3.TRCK(encoding=1, text=['2/12'])
        aiff_file['TPUB'] = mutagen.id3.TPUB(encoding=1, text=['Älsids sdksdsd '])

        with open(os.path.join("files", 'cover.png'), "rb") as f:
            ref_picture = f.read()

        aiff_file.tags.add(
            mutagen.id3.APIC(
                encoding=3,         # 3 is for utf-8
                mime='image/png',   # image/jpeg or image/png
                type=7,             # 3 is for the cover image
                desc=u'BackCover',
                data=ref_picture
            )
        )
        aiff_file.save()
        self.fill_basic_config({'config_upload_formats': 'djv,mobi,cbr,ogg,cbt,rtf,mp4,mp3,epub,fb2,m4b,pdf,cb7,opus,azw3,odt,flac,txt,lit,doc,prc,wav,kepub,djvu,docx,m4a,cbz,html,azw,aiff'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Wav Title', details['title'])
        self.assertEqual('Wav Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        self.assertEqual('Älsids sdksdsd', details['publisher'][0])
        self.assertEqual('No Commento', details['comment'])
        self.assertEqual('2', details['series_index'])
        self.assertEqual('Album', details['series'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(ref_picture), BytesIO(cover_image), delete_diff_file=True), 0.007, delta=0.003)
        self.delete_book(details['id'])
        aiff_file = aiff.AIFF(dest)
        aiff_file['TDRL'] = mutagen.id3.TDRL(encoding=1, text=['2022-12-12'])
        aiff_file.save()
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Dec 12, 2022', details['pubdate'])
        self.delete_book(details['id'])
        self.fill_basic_config({
                                   'config_upload_formats': 'djv,mobi,cbr,ogg,cbt,rtf,mp4,mp3,epub,fb2,m4b,pdf,cb7,opus,azw3,odt,flac,txt,lit,doc,prc,wav,kepub,djvu,docx,m4a,cbz,html,azw'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        os.remove(dest)
        
    def test_upload_flac(self):
        dest = os.path.join(base_path, "files", 'base.aiff')
        shutil.copyfile(os.path.join(base_path, "files", 'music.aiff'), dest)
        aiff_file = aiff.AIFF(dest)
        aiff_file['TIT2'] = mutagen.id3.TIT2(encoding=1, text=['Wav Title'])
        aiff_file['TPE1'] = mutagen.id3.TPE1(encoding=1, text=['Wav Artist'])
        aiff_file['COMM'] = mutagen.id3.COMM(encoding=1, text=['No Commento'])
        aiff_file['TDRL'] = mutagen.id3.TDRL(encoding=1, text=['2022-312-12'])
        aiff_file['TCON'] = mutagen.id3.TCON(encoding=1, text=['Genr#Ä'])
        aiff_file['TALB'] = mutagen.id3.TALB(encoding=1, text=['Album'])
        aiff_file['TRCK'] = mutagen.id3.TRCK(encoding=1, text=['2/12'])
        aiff_file['TPUB'] = mutagen.id3.TPUB(encoding=1, text=['Älsids sdksdsd '])

        with open(os.path.join("files", 'cover.png'), "rb") as f:
            ref_picture = f.read()

        aiff_file.tags.add(
            mutagen.id3.APIC(
                encoding=3,         # 3 is for utf-8
                mime='image/png',   # image/jpeg or image/png
                type=7,             # 3 is for the cover image
                desc=u'BackCover',
                data=ref_picture
            )
        )
        aiff_file.save()
        self.fill_basic_config({'config_upload_formats': 'djv,mobi,cbr,ogg,cbt,rtf,mp4,mp3,epub,fb2,m4b,pdf,cb7,opus,azw3,odt,flac,txt,lit,doc,prc,wav,kepub,djvu,docx,m4a,cbz,html,azw,aiff'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Wav Title', details['title'])
        self.assertEqual('Wav Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        self.assertEqual('Älsids sdksdsd', details['publisher'][0])
        self.assertEqual('No Commento', details['comment'])
        self.assertEqual('2', details['series_index'])
        self.assertEqual('Album', details['series'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(ref_picture), BytesIO(cover_image), delete_diff_file=True), 0.007, delta=0.003)
        self.delete_book(details['id'])
        aiff_file = aiff.AIFF(dest)
        aiff_file['TDRL'] = mutagen.id3.TDRL(encoding=1, text=['2022-12-12'])
        aiff_file.save()
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Dec 12, 2022', details['pubdate'])
        self.delete_book(details['id'])
        self.fill_basic_config({
                                   'config_upload_formats': 'djv,mobi,cbr,ogg,cbt,rtf,mp4,mp3,epub,fb2,m4b,pdf,cb7,opus,azw3,odt,flac,txt,lit,doc,prc,wav,kepub,djvu,docx,m4a,cbz,html,azw'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        os.remove(dest)'''