#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shutil
from unittest import TestCase
import os
import time

from selenium.webdriver.common.by import By
from helper_ui import ui_class
from config_test import TEST_DB, base_path
from helper_func import save_logfiles
from helper_func import startup, add_dependency, remove_dependency
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from diffimg import diff
from io import BytesIO
import base64
import mutagen
from mutagen import mp3, wave, aiff, flac, oggvorbis, asf, mp4, apev2, oggopus, oggtheora
from mutagen.flac import Picture

RESOURCES = {'ports': 1}

PORTS = ['8083']
INDEX = ""


class TestUploadAudio(TestCase, ui_class):
    p = None
    driver = None
    dependencys = ["mutagen"]
    png_original = None
    jpg_original = None

    @classmethod
    def setUpClass(cls):
        add_dependency(cls.dependencys, cls.__name__)

        try:
            startup(cls, cls.py_version, {'config_calibre_dir': TEST_DB, 'config_uploading': 1},
                    port=PORTS[0], index=INDEX,
                    env={"APP_MODE": "test"})
            time.sleep(3)
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
            png_cover_path = os.path.join(base_path, 'files', 'cover.png')
            cls.edit_book(5, {"local_cover": png_cover_path}, detail_v=False)
            cls.png_original = cls.check_element_on_page((By.ID, "detailcover")).screenshot_as_png
            jpg_cover_path = os.path.join(base_path, 'files', 'cover.jpg')
            cls.edit_book(5, {"local_cover": jpg_cover_path}, detail_v=False)
            cls.get_book_details(5)
            cls.jpg_original = cls.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        except Exception as e:
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

        with open(os.path.join(base_path, "files", 'cover.jpg'), "rb") as f:
            ref_picture = f.read()
        with open(os.path.join(base_path, "files", 'cover.jpg'), "rb") as f:
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

        self.assertAlmostEqual(diff(BytesIO(self.png_original), BytesIO(cover_image), delete_diff_file=True), 0.0, delta=0.006)
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

        with open(os.path.join(base_path, "files", 'cover.jpg'), "rb") as f:
            ref_picture = f.read()
        with open(os.path.join(base_path, "files", 'cover.jpg'), "rb") as f:
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

        self.assertAlmostEqual(diff(BytesIO(self.png_original), BytesIO(cover_image), delete_diff_file=True), 0.0, delta=0.009)
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

    def test_upload_oggvorbis(self):
        dest = os.path.join(base_path, "files", 'base.ogg')
        shutil.copyfile(os.path.join(base_path, "files", 'music.ogg'), dest)
        ogg_file = oggvorbis.OggVorbis(dest)
        ogg_file['TITLE'] = "Ogg Title"
        ogg_file['ARTIST'] = "Ogg Artist"
        ogg_file['ALBUM'] = "Ogg Album"
        ogg_file['DATE'] = "2022-312-12"
        ogg_file['TRACKNUMBER'] = "9"
        ogg_file['COMMENTS'] = "OGG Comments"
        ogg_file['LABEL'] = " Älsids sdksdsd "
        ogg_file['GENRE'] = "Genr#Ä"

        with open(os.path.join("files", 'cover.png'), "rb") as f:
            ref_picture = f.read()
        picture = Picture()
        picture.data = ref_picture
        picture.type = 17
        picture.desc = u"Desription"
        picture.mime = u"image/png"
        picture.width = 654
        picture.height = 100
        picture.depth = 24

        encoded_data = base64.b64encode(picture.write())
        vcomment_value = encoded_data.decode("ascii")

        ogg_file["metadata_block_picture"] = [vcomment_value]
        ogg_file.save()

        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Ogg Title', details['title'])
        self.assertEqual('Ogg Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        self.assertEqual('Älsids sdksdsd', details['publisher'][0])
        self.assertEqual('OGG Comments', details['comment'])
        self.assertEqual('9', details['series_index'])
        self.assertEqual('Ogg Album', details['series'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(self.png_original), BytesIO(cover_image), delete_diff_file=True), 0.0, delta=0.009)
        self.delete_book(details['id'])
        ogg_file = oggvorbis.OggVorbis(dest)
        ogg_file['DATE'] = '2022-12-12'
        ogg_file['TRACKNUMBER'] = "Q"
        ogg_file.save()
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Dec 12, 2022', details['pubdate'])
        self.assertEqual('1', details['series_index'])  # due to wrong format, reset to default
        self.delete_book(details['id'])
        os.remove(dest)
        
    def test_upload_flac(self):
        dest = os.path.join(base_path, "files", 'base.flac')
        shutil.copyfile(os.path.join(base_path, "files", 'music.flac'), dest)
        flac_file = flac.FLAC(dest)
        flac_file['TITLE'] = "Flac Title"
        flac_file['ARTIST'] = "Flac Artist"
        flac_file['ALBUM'] = "Flac Album"
        flac_file['DATE'] = "2022-312-12"
        flac_file['TRACKNUMBER'] = "11"
        flac_file['COMMENTS'] = "Flac Commento"
        flac_file['LABEL'] = " Älsids sdksdsd "
        flac_file['GENRE'] = "Genr#Ä"

        with open(os.path.join("files", 'cover.png'), "rb") as f:
            ref_picture = f.read()
        picture = Picture()
        picture.data = ref_picture
        picture.type = 17
        picture.desc = u"Desription"
        picture.mime = u"image/png"
        picture.width = 654
        picture.height = 100
        picture.depth = 24

        flac_file.add_picture(picture)
        flac_file.add_picture(picture)

        flac_file.save()
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Flac Title', details['title'])
        self.assertEqual('Flac Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        self.assertEqual('Älsids sdksdsd', details['publisher'][0])
        self.assertEqual('Flac Commento', details['comment'])
        self.assertEqual('11', details['series_index'])
        self.assertEqual('Flac Album', details['series'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(self.png_original), BytesIO(cover_image), delete_diff_file=True), 0.0, delta=0.009)
        self.delete_book(details['id'])
        flac_file = flac.FLAC(dest)
        flac_file['DATE'] = "2022-12-11"
        flac_file['TRACKNUMBER'] = "Q"
        flac_file.save()
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.assertTrue(self.check_element_on_page((By.ID, "flash_warning")))
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Dec 11, 2022', details['pubdate'])
        self.assertEqual('1', details['series_index'])  # due to wrong format, reset to default
        self.delete_book(details['id'])
        os.remove(dest)

    def test_upload_aac(self):
        dest = os.path.join(base_path, "files", 'base.aac')
        shutil.copyfile(os.path.join(base_path, "files", 'music.aac'), dest)
        aac_file = apev2.APEv2File(dest)
        aac_file.add_tags()
        # aac_file = aac.AAC(dest)
        aac_file['Title'] = mutagen.apev2.APETextValue("Aac Title") #  mutagen.apev2.APETextValue(encoding=1, text=['Wav Title'])
        aac_file['Artist'] = mutagen.apev2.APETextValue("Aac Artist")
        aac_file['Album'] = mutagen.apev2.APETextValue("Aac Album")
        aac_file['Year'] = mutagen.apev2.APETextValue("2022-12-12")
        aac_file['Track'] = mutagen.apev2.APETextValue("22")
        aac_file['Comment'] = mutagen.apev2.APETextValue("aac Comments")
        aac_file['Label'] = mutagen.apev2.APETextValue(" Ölsids sdksdsd ")
        aac_file['Genre'] = mutagen.apev2.APETextValue("Gönr#Ä")

        with open(os.path.join(base_path, "files", 'cover.jpg'), "rb") as f:
            ref_picture = f.read()
        aac_file["Cover Art (Front)"] = mutagen.apev2.APEBinaryValue(b"Cover Art (Front)\00" + ref_picture)
        aac_file.save()

        self.fill_basic_config({'config_upload_formats': 'djv,mobi,cbr,ogg,cbt,rtf,mp4,mp3,epub,fb2,m4b,pdf,cb7,opus,azw3,odt,flac,txt,lit,doc,prc,wav,kepub,djvu,docx,m4a,cbz,html,azw,aac'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Aac Title', details['title'])
        self.assertEqual('Aac Artist', details['author'][0])
        self.assertEqual('Gönr#Ä', details['tag'][0])
        self.assertEqual('Ölsids sdksdsd', details['publisher'][0])
        self.assertEqual('aac Comments', details['comment'])
        self.assertEqual('22', details['series_index'])
        self.assertEqual('Aac Album', details['series'])
        self.assertEqual('Dec 12, 2022', details['pubdate'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(self.jpg_original), BytesIO(cover_image), delete_diff_file=True), 0.0, delta=0.009)
        self.delete_book(details['id'])
        self.fill_basic_config({'config_upload_formats': 'mobi,pdf,m4b,html,cbr,doc,lit,azw,mp4,odt,wav,prc,kepub,docx,cbt,mp3,rtf,epub,cb7,ogg,azw3,flac,opus,txt,djvu,cbz,fb2,djv,m4a'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

        os.remove(dest)

    def test_upload_asf(self):
        dest = os.path.join(base_path, "files", 'base.asf')
        shutil.copyfile(os.path.join(base_path, "files", 'music.asf'), dest)
        asf_file = asf.ASF(dest)
        asf_file['Title'] = "ASF Title"
        asf_file['Artist'] = "ASF Artist"
        asf_file['Album'] = "Asf Album"
        asf_file['Year'] = "2022-12-12"
        asf_file['Track'] = "19"
        asf_file['Comments'] = "Asf Comments"
        asf_file['Label'] = " Älsids sdksdsd "
        asf_file['Genre'] = "Genr#Ä"

        with open(os.path.join(base_path, "files", 'cover.jpg'), "rb") as f:
            ref_picture = f.read()

        asf_file["WM/Picture"] = ref_picture
        asf_file.save()

        self.fill_basic_config({'config_upload_formats': 'mobi,pdf,m4b,html,cbr,doc,lit,azw,mp4,odt,wav,prc,kepub,docx,cbt,mp3,rtf,epub,cb7,ogg,azw3,flac,opus,txt,djvu,cbz,fb2,djv,m4a,asf'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('ASF Title', details['title'])
        self.assertEqual('ASF Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        self.assertEqual('Älsids sdksdsd', details['publisher'][0])
        self.assertEqual('Asf Comments', details['comment'])
        self.assertEqual('19', details['series_index'])
        self.assertEqual('Asf Album', details['series'])
        self.assertEqual('Dec 12, 2022', details['pubdate'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(self.jpg_original), BytesIO(cover_image), delete_diff_file=True), 0.0, delta=0.009)
        self.delete_book(details['id'])
        self.fill_basic_config({'config_upload_formats': 'mobi,pdf,m4b,html,cbr,doc,lit,azw,mp4,odt,wav,prc,kepub,docx,cbt,mp3,rtf,epub,cb7,ogg,azw3,flac,opus,txt,djvu,cbz,fb2,djv,m4a'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        os.remove(dest)

    def test_upload_mp4(self):
        dest = os.path.join(base_path, "files", 'base.mp4')
        shutil.copyfile(os.path.join(base_path, "files", 'music.mp4'), dest)
        mp4_file = mp4.MP4(dest)
        mp4_file['©nam'] = "Mp4 Title"
        mp4_file['©ART'] = "MP4 Artist"
        mp4_file['©alb'] = "Mp4 Album"
        mp4_file['©day'] = "2022-12-12"
        mp4_file['trkn'] = [[3, 12]]
        mp4_file['©cmt'] = "MP4 Comments"
        mp4_file['©gen'] = "Genr#Ä"

        with open(os.path.join("files", 'cover.png'), "rb") as f:
            ref_picture = f.read()

        pic = mutagen.mp4.MP4Cover(ref_picture, imageformat=mutagen.mp4.MP4Cover.FORMAT_PNG)
        mp4_file["covr"] = [pic]
        mp4_file.save()

        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Mp4 Title', details['title'])
        self.assertEqual('MP4 Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        # self.assertEqual('Älsids sdksdsd', details['publisher'][0])
        self.assertEqual('MP4 Comments', details['comment'])
        self.assertEqual('3', details['series_index'])
        self.assertEqual('Mp4 Album', details['series'])
        self.assertEqual('Dec 12, 2022', details['pubdate'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(self.png_original), BytesIO(cover_image), delete_diff_file=True), 0.0, delta=0.009)
        self.delete_book(details['id'])
        os.remove(dest)

    def test_upload_m4a(self):
        dest = os.path.join(base_path, "files", 'base.m4a')
        shutil.copyfile(os.path.join(base_path, "files", 'music.m4a'), dest)
        m4a_file = mp4.MP4(dest)
        m4a_file['©nam'] = "Mp4 Title"
        m4a_file['©ART'] = "MP4 Artist"
        m4a_file['©alb'] = "Mp4 Album"
        m4a_file['©day'] = "2022-12-12"
        m4a_file['trkn'] = [[3, 12]]
        m4a_file['©cmt'] = "MP4 Comments"
        m4a_file['©gen'] = "Genr#Ä"

        with open(os.path.join(base_path, "files", 'cover.jpg'), "rb") as f:
            ref_picture = f.read()

        pic = mutagen.mp4.MP4Cover(ref_picture, imageformat=mutagen.mp4.MP4Cover.FORMAT_JPEG)
        m4a_file["covr"] = [pic]
        m4a_file.save()

        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Mp4 Title', details['title'])
        self.assertEqual('MP4 Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        self.assertEqual('MP4 Comments', details['comment'])
        self.assertEqual('3', details['series_index'])
        self.assertEqual('Mp4 Album', details['series'])
        self.assertEqual('Dec 12, 2022', details['pubdate'])

        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(self.jpg_original), BytesIO(cover_image), delete_diff_file=True), 0.0, delta=0.009)
        self.delete_book(details['id'])
        os.remove(dest)

    def test_upload_m4b(self):
        dest = os.path.join(base_path, "files", 'base.m4b')
        shutil.copyfile(os.path.join(base_path, "files", 'music.m4b'), dest)
        m4a_file = mp4.MP4(dest)
        m4a_file['©nam'] = "Mp4 Title"
        m4a_file['©ART'] = "MP4 Artist"
        m4a_file['©alb'] = "Mp4 Album"
        m4a_file['©day'] = "2022-12-12"
        m4a_file['trkn'] = [[4, 14]]
        m4a_file['©cmt'] = "MP4 Comments"
        m4a_file['©gen'] = "Genr#Ä"

        with open(os.path.join(base_path, "files", 'cover.jpg'), "rb") as f:
            ref_picture = f.read()

        pic = mutagen.mp4.MP4Cover(ref_picture, imageformat=mutagen.mp4.MP4Cover.FORMAT_JPEG)
        m4a_file["covr"] = [pic]
        m4a_file.save()

        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Mp4 Title', details['title'])
        self.assertEqual('MP4 Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        self.assertEqual('MP4 Comments', details['comment'])
        self.assertEqual('4', details['series_index'])
        self.assertEqual('Mp4 Album', details['series'])
        self.assertEqual('Dec 12, 2022', details['pubdate'])

        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(self.jpg_original), BytesIO(cover_image), delete_diff_file=True), 0.0, delta=0.009)
        self.delete_book(details['id'])
        os.remove(dest)

    def test_upload_opus(self):
        dest = os.path.join(base_path, "files", 'base.opus')
        shutil.copyfile(os.path.join(base_path, "files", 'music.opus'), dest)
        opus_file = oggopus.OggOpus(dest)
        opus_file['TITLE'] = "Ogg Title"
        opus_file['ARTIST'] = "Ogg Artist"
        opus_file['ALBUM'] = "Ogg Album"
        opus_file['DATE'] = "2022-312-12"
        opus_file['TRACKNUMBER'] = "9"
        opus_file['COMMENTS'] = "OGG Comments"
        opus_file['LABEL'] = " Älsids sdksdsd "
        opus_file['GENRE'] = "Genr#Ä"

        with open(os.path.join("files", 'cover.png'), "rb") as f:
            ref_picture = f.read()
        picture = Picture()
        picture.data = ref_picture
        picture.type = 17
        picture.desc = u"Desription"
        picture.mime = u"image/png"
        picture.width = 654
        picture.height = 100
        picture.depth = 24

        encoded_data = base64.b64encode(picture.write())
        vcomment_value = encoded_data.decode("ascii")

        opus_file["metadata_block_picture"] = [vcomment_value]
        opus_file.save()

        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Ogg Title', details['title'])
        self.assertEqual('Ogg Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        self.assertEqual('Älsids sdksdsd', details['publisher'][0])
        self.assertEqual('OGG Comments', details['comment'])
        self.assertEqual('9', details['series_index'])
        self.assertEqual('Ogg Album', details['series'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(self.png_original), BytesIO(cover_image), delete_diff_file=True), 0.0, delta=0.009)
        self.delete_book(details['id'])
        os.remove(dest)

    def test_upload_ogv(self):
        dest = os.path.join(base_path, "files", 'base.ogv')
        shutil.copyfile(os.path.join(base_path, "files", 'music.ogv'), dest)
        theora_file = oggvorbis.OggVorbis(dest)
        theora_file['TITLE'] = "Ogg Title"
        theora_file['ARTIST'] = "Ogg Artist"
        theora_file['ALBUM'] = "Ogg Album"
        theora_file['DATE'] = "2022-12-12"
        theora_file['TRACKNUMBER'] = "9"
        theora_file['COMMENTS'] = "OGG Comments"
        theora_file['LABEL'] = " Älsids sdksdsd "
        theora_file['GENRE'] = "Genr#Ä"

        with open(os.path.join("files", 'cover.png'), "rb") as f:
            ref_picture = f.read()

        picture = Picture()
        picture.data = ref_picture
        picture.type = 17
        picture.desc = u"Desription"
        picture.mime = u"image/png"
        picture.width = 654
        picture.height = 100
        picture.depth = 24

        encoded_data = base64.b64encode(picture.write())
        vcomment_value = encoded_data.decode("ascii")

        theora_file["metadata_block_picture"] = [vcomment_value]
        theora_file.save()

        self.fill_basic_config({'config_upload_formats': 'mobi,pdf,m4b,html,cbr,doc,lit,azw,mp4,odt,wav,prc,kepub,docx,cbt,mp3,rtf,epub,cb7,ogg,azw3,flac,opus,txt,djvu,cbz,fb2,djv,m4a,ogv'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))

        self.goto_page('nav_new')
        upload = self.check_element_on_page((By.ID, 'btn-upload'))
        upload.send_keys(dest)
        time.sleep(3)
        self.check_element_on_page((By.ID, 'edit_cancel')).click()
        time.sleep(2)
        details = self.get_book_details()
        self.assertEqual('Ogg Title', details['title'])
        self.assertEqual('Ogg Artist', details['author'][0])
        self.assertEqual('Genr#Ä', details['tag'][0])
        self.assertEqual('Älsids sdksdsd', details['publisher'][0])
        self.assertEqual('OGG Comments', details['comment'])
        self.assertEqual('9', details['series_index'])
        self.assertEqual('Ogg Album', details['series'])
        self.assertEqual('Dec 12, 2022', details['pubdate'])
        cover_image = self.check_element_on_page((By.ID, "detailcover")).screenshot_as_png

        self.assertAlmostEqual(diff(BytesIO(self.png_original), BytesIO(cover_image), delete_diff_file=True), 0.0, delta=0.009)
        self.delete_book(details['id'])
        self.fill_basic_config({'config_upload_formats': 'mobi,pdf,m4b,html,cbr,doc,lit,azw,mp4,odt,wav,prc,kepub,docx,cbt,mp3,rtf,epub,cb7,ogg,azw3,flac,opus,txt,djvu,cbz,fb2,djv,m4a'})
        self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))
        os.remove(dest)
