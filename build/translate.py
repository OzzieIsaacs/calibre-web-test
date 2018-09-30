# #!/usr/bin/env python
# # -*- coding: utf-8 -*-

import subprocess
import sys
import glob, os
import shutil
import cPickle
import babel.messages.pofile as pofile

# Path to calibre-web location with -> location of mo files
FILEPATH="D:\\Desktop\\calibre-web\\"

with open('iso639.pickle', 'rb') as f:
    need_iso = cPickle.load(f)

workdir = os.getcwd()
os.chdir(FILEPATH) # .encode(sys.getfilesystemencoding()

# Extract all messages from the source code and create a template file
p = subprocess.Popen("pybabel extract --no-wrap -F babel.cfg -o messages.pot cps"
                     ,shell=True,stdout=subprocess.PIPE, stdin=subprocess.PIPE)
p.wait()

# update all translation files with the new content of the template file
# adding --ignore-obsolete will delete all obsolete translations
p = subprocess.Popen("pybabel update --no-wrap -i "+FILEPATH+"messages.pot -d "+FILEPATH+"cps/translations".encode(sys.getfilesystemencoding()),
                     shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
p.wait()

# Include calibre iso639 translations of language names
out_iso = dict()
os.chdir(workdir)
invers_lang_table = [x for x in need_iso['3bto3t'].values()]
for file in glob.glob1("./translations", "*.po"):
    langcode=file[23:-3]
    translateFile=open(FILEPATH+"cps\\translations\\"+langcode+"\\LC_MESSAGES\\messages.po")
    mergedTranslation=pofile.read_po(translateFile,locale=langcode)
    translateFile.close()
    languageFile=open("./translations/"+file)
    LanguageTranslation=pofile.read_po(languageFile)
    languageFile.close()
    print("Merging: " + langcode)
    # for msg in LanguageTranslation._messages._keys:
    iso_translations = dict()
    # code3t = need_iso['3bto3t'].values().index(need_iso['2to3'][langcode])
    # iso_translations[invers_lang_table.index(code3t)] =
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
    # mergedTranslation.header_comment=mergedTranslation.header_comment+LanguageTranslation.header_comment
    shutil.move(os.path.join(FILEPATH,"cps\\translations\\"+langcode+"\\LC_MESSAGES\\messages.po"), os.path.join(FILEPATH,"cps\\translations\\"+langcode+"\\LC_MESSAGES\\messages_all.po"))
    targetFile = open(FILEPATH + "cps\\translations\\" + langcode + "\\LC_MESSAGES\\messages.po",'w')
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

# write language name table
with open(os.path.join(FILEPATH,'cps','translations','iso639.pickle'), 'wb') as f:
    cPickle.dump(out_iso,f)

# Generate .mo files
p = subprocess.Popen("pybabel compile -d " + FILEPATH + "cps/translations".encode(sys.getfilesystemencoding()),
                     shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
p.wait()

# Rename messages_all.mo in messages.mo und delete messages_all.po
for file in glob.glob1("./translations", "*.po"):
    langcode=file[23:-3]
    file_path = FILEPATH+"cps\\translations\\"+langcode+"\\LC_MESSAGES\\"
    shutil.move(os.path.join(file_path, "messages_all.po"), os.path.join(file_path, "messages.po"))

# start all tests

    # Server.startServer()

