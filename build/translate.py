# #!/usr/bin/env python
# # -*- coding: utf-8 -*-

import subprocess
import sys
import glob, os
import json
from config import FILEPATH, WIKIPATH
import msgpack
import babel.messages.pofile as pofile
import babel.messages.mofile as mofile
from babel import Locale as LC
import re

decoders = (
    None,
    lambda x, fj: set(x),
)

def default(obj):
    if isinstance(obj, set):
        return tuple(obj)  # msgpack module can't deal with sets so we make a tuple out of it
    else:
        return str(obj)


def msg_writer(data):
    with open('iso639_new.calibre_msgpack', "wb") as outfile:
        packed = msgpack.packb(data, use_bin_type=True, default=default) # ext_hook=msgpack_decoder)
        outfile.write(packed)

def msgpack_decoder(code, data):
    return decoders[code](msgpack_loads(data), False)

def msgpack_loads(dump):
    return msgpack.unpackb(dump, ext_hook=msgpack_decoder, raw=False)

need_iso = msgpack_loads(open('iso639.calibre_msgpack', 'rb').read())

#need_iso['name_map']['ge'] = 'hmj'
#need_iso['codes3t'].append('hmj')
#msg_writer(need_iso)
workdir = os.getcwd()
os.chdir(FILEPATH)

# Extract all messages from the source code and create a template file
p = subprocess.Popen("pybabel extract -k _extract --no-wrap -F babel.cfg -o messages.pot cps"
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
translation_list = list()
langcode_list = list()

lang_keys = need_iso['name_map'].keys()
eng_translations = dict()

for file in sorted(glob.glob1("./translations", "*.po")):
    langcode=file[23:-3]
    langcode_list.append(langcode)
    # Remove old content from po file
    message_path = os.path.join(FILEPATH,'cps', 'translations', langcode, 'LC_MESSAGES', 'messages.po')
    translateFile=open(message_path)
    mergedTranslation=pofile.read_po(translateFile,locale=langcode)
    translateFile.close()

    # transfer calibre language translation to
    count = 0
    for msg in mergedTranslation:
        if msg.string != '' and msg.id != "":
            count += 1
    allMsg = len(mergedTranslation._messages)
    for x in mergedTranslation.check():
        print(x)
    for element in mergedTranslation:
        idstring=re.findall("\((.*?)\)%s",element.id)
        if idstring and element.string:
            transid = set(re.findall("\((.*?)\)%s", element.string))
            origid = set(idstring)
            if transid != origid:
                print("Format string error {}: '{}'".format(langcode,element.id))
    # write mo and po files
    mo_path = os.path.join(FILEPATH , "cps","translations" , langcode , "LC_MESSAGES","messages.mo")
    target_path = os.path.join(FILEPATH, "cps", "translations", langcode, "LC_MESSAGES", "messages.po")
    targetFile = open(target_path,'wb')
    pofile.write_po(targetFile, mergedTranslation, ignore_obsolete=True, width=0)
    targetFile.close()
    mo_File = open(mo_path,'wb')
    mofile.write_mo(mo_File, mergedTranslation)
    mo_File.close()
    languageFile=open("./translations/" + file)
    LanguageTranslation=pofile.read_po(languageFile)
    languageFile.close()
    lang_name = LC.parse(langcode).english_name
    translation_list.append("| {} | {} of strings {} translated |".format(lang_name, count, allMsg))
    print("{} language: {} of strings {} translated".format(lang_name, count, allMsg))
    iso_translations = dict()
    # Add missing translated language names to translation
    for msg in LanguageTranslation:
        if msg.id:
            if msg.id.lower() == 'pushto':
                msg.id = 'Pashto'
            if msg.id.lower() in lang_keys:
                lCode = need_iso['name_map'][msg.id.lower()]
                if msg.string:
                    iso_translations[lCode] = msg.string
                else:
                    iso_translations[lCode] = msg.id
            # spanish translation is complete
            if langcode == "es":
                lCode = msg.auto_comments[0][9:]
                if lCode in need_iso['codes3t']:
                    eng_translations[lCode] = msg.id
    out_iso[langcode] = iso_translations

# Add English to the translation table
out_iso['en'] = eng_translations

header = '''# -*- coding: utf-8 -*-

# This file is part of the Calibre-Web (https://github.com/janeczku/calibre-web)
#   Copyright (C) 2019 OzzieIsaacs, pwr
# Licensed under GLPv3. See the project's LICENSE file for details.

# pylint: disable=too-many-lines,bad-continuation

# This file is autogenerated, do NOT add, change, or delete ANY string
# If you need help or assistance for adding a new language, please contact the project team  

# map iso639 language codes to language names, translated

'''

headline = '''## Translation status

The following user languages are available:

| Language  | Translations  |
| ---------- |:---------:|
'''

with open(os.path.join(FILEPATH,'cps', 'iso_language_names.py'), 'w', encoding='utf8') as f:
    f.write(header)
    f.write('LANGUAGE_NAMES = ')
    json.dump(out_iso, f, indent=4, ensure_ascii=False)

with open(os.path.join(WIKIPATH, 'Translation-Status.md'), 'w', encoding='utf8') as f:
    f.write(headline)
    f.write("\r\n".join(translation_list))

# check if all datepicker localefiles are present
for code in langcode_list:
    if not os.path.isfile(os.path.join(FILEPATH, 'cps', 'static', 'js', 'libs', 'bootstrap-datepicker', 'locales',
                                  'bootstrap-datepicker.'+ code +'.min.js')):
        print('                             !!!  Error Bootstrap Datepicker locale missing for: ' + code)
    if not os.path.isfile(os.path.join(FILEPATH, 'cps', 'static', 'js', 'libs', 'tinymce', 'langs',
                                  code +'.js')):
        print('                             !!!  Error TinyMCE locale missing for: ' + code)
    #path = os.path.join(FILEPATH, 'cps', 'static', 'js', 'libs', 'bootstrap-table', 'locale',
    #                    'bootstrap-table-' + code[:2] + '*.min.js')
    #if not glob.glob(path):
    #    print('                             !!!  Error Bootstrap-Table locale missing for: ' + code)


# Generate .mo files
#trans_path = "cps/translations"
#if sys.version_info < (3, 0):
#    trans_path = trans_path.encode(sys.getfilesystemencoding())
#p = subprocess.Popen("pybabel compile -d " + FILEPATH + trans_path,
#                     shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
#p.wait()


