# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
from release.github_release import get_releases

test = get_releases('ozzieisaacs/calibre-web')
print(test)

# search for 'return {'version': '0.6.0'} # Current version