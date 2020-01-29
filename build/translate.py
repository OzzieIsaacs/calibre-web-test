# #!/usr/bin/env python
# # -*- coding: utf-8 -*-

import subprocess
import sys
import glob, os
import shutil
import json
from config import FILEPATH
import msgpack
import babel.messages.pofile as pofile

decoders = (
    None,
    lambda x, fj: set(x),
)

def msgpack_decoder(code, data):
    return decoders[code](msgpack_loads(data), False)

def msgpack_loads(dump):
    return msgpack.unpackb(dump, ext_hook=msgpack_decoder, raw=False)

need_iso = msgpack_loads(open('iso639.calibre_msgpack', 'rb').read())

workdir = os.getcwd()
os.chdir(FILEPATH)

# Extract all messages from the source code and create a template file
p = subprocess.Popen("pybabel extract --no-wrap -F babel.cfg -o messages.pot cps"
                     ,shell=True,stdout=subprocess.PIPE, stdin=subprocess.PIPE)
p.wait()

# update all translation files with the new content of the template file
# adding --ignore-obsolete will delete all obsolete translations
pot_path = os.path.join(FILEPATH,"messages.pot")
translation_path = os.path.join(FILEPATH,'cps','translations')
if sys.version_info < (3, 0):
    translation_path = translation_path.encode(sys.getfilesystemencoding())
p = subprocess.Popen("pybabel update --no-wrap -i "+ pot_path + " -d " + translation_path,
                     shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
p.wait()

# Include calibre iso639 translations of language names
out_iso = dict()
os.chdir(workdir)
invers_lang_table = [x for x in need_iso['3bto3t'].values()]
for file in glob.glob1("./translations", "*.po"):
    langcode=file[23:-3]
    message_path = os.path.join(FILEPATH,'cps','translations',langcode, 'LC_MESSAGES','messages.po')
    translateFile=open(message_path)
    mergedTranslation=pofile.read_po(translateFile,locale=langcode)
    translateFile.close()
    count = 0
    for msg in mergedTranslation:
        if msg.string != '' and msg.id != "":
            count += 1
    allMsg = len(mergedTranslation._messages)
    for x in mergedTranslation.check():
        print(x)
    languageFile=open("./translations/"+file)
    LanguageTranslation=pofile.read_po(languageFile)
    languageFile.close()
    print("Merging: {} {} of strings {} translated".format(langcode, count, allMsg))
    iso_translations = dict()
    for msg in LanguageTranslation:
        if msg.id:
            # msg=LanguageTranslation.__getitem__(msg)
            lCode = msg.auto_comments[0][9:]
            if lCode in need_iso['codes3t']:
                mergedTranslation.add(msg.id, msg.string, auto_comments=msg.auto_comments)
                if msg.string:
                    iso_translations[lCode] = msg.string
                else:
                    iso_translations[lCode] = msg.id
    message_path = os.path.join(FILEPATH, 'cps', 'translations', langcode, 'LC_MESSAGES', 'messages.po')
    allmessage_path = os.path.join(FILEPATH, "cps","translations" , langcode, "LC_MESSAGES","messages_all.po")
    shutil.move(message_path, allmessage_path)
    target_path = os.path.join(FILEPATH , "cps","translations" , langcode , "LC_MESSAGES","messages.po")
    targetFile = open(target_path,'wb')
    pofile.write_po(targetFile,mergedTranslation,ignore_obsolete=True)
    targetFile.close()
    out_iso[langcode]=iso_translations

# Add English to the translation table
for msg in LanguageTranslation:
    if msg.id:
        lCode = msg.auto_comments[0][9:]
        if lCode in need_iso['codes3t']:
            iso_translations[lCode] = msg.id
out_iso['en'] = iso_translations

header = '''# -*- coding: utf-8 -*-

# This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#   Copyright (C) 2019 OzzieIsaacs, pwr
# Licensed under GLPv3. See the project's LICENSE file for details.

# pylint: disable=too-many-lines,bad-continuation

from __future__ import unicode_literals


# map iso639 language codes to language names, translated

'''

with open(os.path.join(FILEPATH,'cps', 'iso_language_names.py'), 'w', encoding='utf8') as f:
    f.write(header)
    f.write('LANGUAGE_NAMES = ')
    json.dump(out_iso, f, indent=4, ensure_ascii=False)

# Generate .mo files
trans_path = "cps/translations"
if sys.version_info < (3, 0):
    trans_path = trans_path.encode(sys.getfilesystemencoding())
p = subprocess.Popen("pybabel compile -d " + FILEPATH + trans_path,
                     shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
p.wait()

# Rename messages_all.mo in messages.mo und delete messages_all.po
for file in glob.glob1("./translations", "*.po"):
    langcode=file[23:-3]
    file_path = os.path.join(FILEPATH,"cps","translations",langcode,"LC_MESSAGES")
    shutil.move(os.path.join(file_path, "messages_all.po"), os.path.join(file_path, "messages.po"))


