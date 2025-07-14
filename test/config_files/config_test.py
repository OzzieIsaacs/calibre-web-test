# -*- coding: utf-8 -*-

import os


base_path = os.path.dirname(os.path.abspath(__file__))

CALIBRE_WEB_PATH = os.path.abspath(os.path.join(base_path, '..', '..', 'calibre-web'))
VENV_PATH = os.path.join(CALIBRE_WEB_PATH, 'venv')

if os.name == 'nt':
    VENV_PYTHON = os.path.join(VENV_PATH, 'Scripts', 'python.exe')
    LDAP_WHL = os.path.abspath(os.path.join(base_path, '..', 'selenium', 'python_ldap-3.3.1-cp38-cp38-win32.whl'))
    TEST_OS = 'Windows'
    WAIT_GDRIVE = 20
else:
    VENV_PYTHON = os.path.join(VENV_PATH, 'bin', 'python3')
    LDAP_WHL = None
    TEST_OS = 'Linux'
    WAIT_GDRIVE = 20

TEST_DB = os.path.abspath(os.path.join(base_path, '..', '..', 'Dokumente', 'tüst db'))

# Boottime in seconds
BOOT_TIME = 10

# Python binary
PY_BIN = VENV_PYTHON # before: u'/usr/bin/python3'
