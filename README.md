# Testing for calibre-web

## Prerequisites

- Installed python3 accessible with the command "python3"
- installed calibre desktop program 3.48
- for instlling ldap requirements libsasl2-dev and libldap2-dev have to be installed (debian distro lib-names)
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

- I'm doing my tests with firefox, so geckodriver has to be installed and in path (https://github.com/mozilla/geckodriver/releases)

- All dependencies listed in requirements.txt have to be installed

- tests are only running with tornado as wsgi server

- install Calibre as conversion tool (if running from within pycharm debugger version 3.48 at most, as Calibre 4.x crash during conversion in this configuration)

- configure folder names in file ./test/testconfig.py

## Start Testing

Tests are running with python 3.6+ (better 3.7 as with 3.6 testing the e-mail startssl/ssl functionality will be skipped) by starting ./test/main.py (tests run for ca. 45min), tested on Linux Mint 19.3. \
Calibre-web's app.db and logfiles will be overwritten.\
The testresult is written to the file "calibre-web/test/Calibre-Web TestSummary.html"

Hints for using pyCharm: 
It's recommended to have gevent compatible debugging set to **no** and also **do not attach to subprocess** (created trouble in combination with email sending)

