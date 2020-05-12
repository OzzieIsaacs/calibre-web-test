# #!/usr/bin/env python
# # -*- coding: utf-8 -*-

import os
if os.name == 'nt':
    FILEPATH="D:\\Desktop\\calibre-web\\"
    WIKIPATH=''
else:
    FILEPATH = os.path.abspath("./../../calibre-web/") + '/'
    WIKIPATH = os.path.abspath("./../../calibre-web.wiki")