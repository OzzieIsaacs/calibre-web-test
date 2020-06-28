# -*- coding: utf-8 -*-

import os
import sys

base_path = os.path.dirname(os.path.abspath(__file__))

SELENIUM_SERVER = os.path.join(base_path, '..', 'selenium', 'selenium-server-standalone-3.141.59.jar')
CALIBRE_WEB_PATH = os.path.abspath(os.path.join(base_path, '..', '..', 'calibre-web'))
VENV_PATH = os.path.join(CALIBRE_WEB_PATH, 'venv')
VENV_PYTHON = os.path.join(VENV_PATH, 'bin', 'python3')
if sys.version_info < (3, 0):
    TEST_DB = os.path.abspath(os.path.join(base_path, '..', '..', 'Dokumente', 'tüst db')).decode('UTF-8')
else:
    TEST_DB = os.path.abspath(os.path.join(base_path, '..', '..', 'Dokumente', 'tüst db'))

# Boottime in seconds
BOOT_TIME = 5

# Python binary
PY_BIN = VENV_PYTHON # before: u'/usr/bin/python3'
