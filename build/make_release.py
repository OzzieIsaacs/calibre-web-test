# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
import os
import glob
from release.github_release import get_releases
from config import FILEPATH
import shutil
import subprocess
import codecs
import re

# test = get_releases('ozzieisaacs/calibre-web')
# print(test)

def change_homeconfig(targetfile, value):
    with codecs.open(targetfile, 'r') as fp:
        file = fp.read()
    replaced = re.sub("(HOME_CONFIG\s+=\s+)(.*)", r"\1" + value, file)
    f = codecs.open(targetfile, "w")
    f.write(replaced)
    f.close()


workdir = os.getcwd()
os.chdir(FILEPATH)
targetfile = os.path.join(FILEPATH, "src/calibreweb/cps/constants.py")

# create sourcedir
try:
    os.makedirs('src')
    print('Creating "src" directory')
except FileExistsError:
    pass
try:
    os.makedirs('src/calibreweb')
    print('Creating "calibreweb" directory')
except FileExistsError:
    pass

# delete build and dist dir
shutil.rmtree('build', ignore_errors=True)
shutil.rmtree('dist', ignore_errors=True)

# move cps and cps.py file to sourcefolder
try:
    os.remove('cps.pyc')
except:
    pass
try:
    os.remove('./cps/*.pyc')
except:
    pass
try:
    os.remove('./cps/services/*.pyc')
except:
    pass

shutil.move('cps.py','src/calibreweb/__init__.py')

shutil.move('cps','src/calibreweb')
print('Moving files to src directory')

change_homeconfig(targetfile, "True")
print('Change homeconfig settings to true')

# Generate package
print('Generating package')
p = subprocess.Popen("python3 setup.py sdist bdist_wheel"
                     ,shell=True,stdout=subprocess.PIPE, stdin=subprocess.PIPE)
p.communicate()[0]
p.wait()

# check succesfull
if p.returncode == 0:
    pass
# move files back
print('Change homeconfig settings to true')
change_homeconfig(targetfile, "False")

print('Moving files back to origin')
shutil.move('./src/calibreweb/__init__.py','./cps.py')
shutil.move('./src/calibreweb/cps','.')
print('Deleting "src" directory')
shutil.rmtree('src', ignore_errors=True)
print('Deleting "build" directory')
shutil.rmtree('build', ignore_errors=True)
os.chdir(workdir)

# twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# pip install --user --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple calibre-web
