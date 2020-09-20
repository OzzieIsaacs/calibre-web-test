# Testing for calibre-web

## Prerequisites

- Installed python3 accessible with the command "python3"
- installed calibre desktop program v3.48
- for installing ldap requirements libsasl2-dev and libldap2-dev have to be installed (debian distro lib-names)
- Calibre-web-test has to be located on the same folder level as calibre-web
e.g.
```
.
..
calibre-web
  .
  ..
  cps
Calibre-web-test
  .
  ..
  test
```

- selenium (https://selenium-release.storage.googleapis.com/3.141/selenium-server-standalone-3.141.59.jar) has to be located in subfolder selenium (configurable)
- java has to be installed and in path

- I'm doing my tests with Firefox, so geckodriver has to be installed and in path (https://github.com/mozilla/geckodriver/releases) and also Firefox itself

- All dependencies listed in requirements.txt have to be installed

- Ldaptor causes a problem in conjunction with the tests, so the patch suggested in https://github.com/twisted/ldaptor/issues/170 has to be applied

- tests are only running with tornado as wsgi server

- install Calibre as conversion tool (if running from within pycharm debugger version 3.48 at most, as Calibre 4.x crash during conversion in this configuration)

- configure folder names in file ./test/config_test.py

## Start Testing

Tests are running with python 3.6+ (better 3.7 as with 3.6 testing the e-mail startssl/ssl functionality will be skipped) by starting ./test/main.py (tests run for ca. 45min), tested on Linux Mint 19.3. \
Calibre-web's app.db and logfiles will be overwritten.\
The testresult is written to the file "calibre-web/test/Calibre-Web TestSummary.html"

Hints for using pyCharm: 
It's recommended to have gevent compatible debugging set to **no** and also **do not attach to subprocess** (created trouble in combination with email sending)

### Compiling Language files

The script translate.py in the build folder is used for generating the binary translation files (.mo) and also to generate the language name translation table file 'iso_language_names.py' in the calibre-web cps folder. The script runs under python 3 (3.6 and 3.7 tested).\
The used languages were taken from the file iso639.calibre_msgpack. This is a magically (can't remember how I did it) shrinked file from the Calibre resoucres directory. The original file has over 7000 languages in it. Somewhere in the Calibre code there is a routine which is extracting several language names from this file (the 400 remaining), all other languages are not supported by calibre (at least at the time I created the file). By increasing the number of supported languages to the 7000, the speed of the language typeahead drops to nearly zero.
The language translations are taken from Calibre's iso639 folder in the transifex translation project. By adding up a new language the corresponding file has to be grabbed from this project. Before it can be used the timezonemarker in the header has to be changed from +MDT to +000.

