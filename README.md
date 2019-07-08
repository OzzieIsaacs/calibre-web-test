# Testing for calibre-web

## Prerequisites

- Installed python2 accessable with the command "python"
- Installed python3 accessable with the command "python3"

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

- python package "selenium" has to be installed

- tests are only running with gevent as wsgi server, tornado in newer versions has the problem that it can't be stopped (bug?)

- configure folder names in file ./test/testconfig.py

## Start Testing

Tests currently are only run with python 2.7 by starting ./test/main.py (tests run for ca. 45min), tested on Linux Mint 19.1. \
Calibre-web's app.db and logfiles will be overwritten.\
The testresult is written to the file "calibre-web/test/Calibre-Web TestSummary.html"


