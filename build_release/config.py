# #!/usr/bin/env python
# # -*- coding: utf-8 -*-

import os
base_path = os.path.dirname(os.path.abspath(__file__))

if os.name == 'nt':
    FILEPATH = "C:\\Entwicklung\\calibre-web\\"
    WIKIPATH = "C:\\Entwicklung\\calibre-web-wiki\\"
    LDAP_WHL = os.path.abspath(os.path.join(base_path,'..', 'test', 'files', 'python_ldap-3.4.4-cp311-cp311-win_amd64.whl'))
    # LEVENSHTEIN_WHL = os.path.abspath(os.path.join(base_path, '../..', 'test', 'files', 'python_Levenshtein-0.12.2-cp39-cp39-win_amd64.whl'))
else:
    FILEPATH = os.path.abspath("../../calibre-web/") + '/'
    WIKIPATH = os.path.abspath("../../calibre-web-wiki/") + '/'
    LDAP_WHL = None
    # LEVENSHTEIN_WHL = None


VENV_PATH = os.path.join(FILEPATH, 'venv')
if os.name == 'nt':
    VENV_PYTHON = os.path.join(VENV_PATH, 'Scripts', 'python.exe')
else:
    VENV_PYTHON = os.path.join(VENV_PATH, 'bin', 'python3')