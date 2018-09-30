#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

base_path = os.path.dirname(os.path.abspath(__file__))

SELENIUM_SERVER = os.path.join(base_path, '..', 'selenium', 'selenium-server-standalone-3.14.0.jar')
CALIBRE_WEB_PATH = os.path.abspath(os.path.join(base_path, '..', '..', 'calibre-web'))
TEST_DB = os.path.abspath(os.path.join(base_path, '..', '..', 'Dokumente', 'tüst db')).decode('UTF-8')
