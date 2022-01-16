# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
import os
import glob
from config import FILEPATH, VENV_PATH, VENV_PYTHON
import shutil
import sys
import subprocess
import codecs
import re
import tarfile
import venv
from subprocess import CalledProcessError
from subproc_wrapper import process_open
from helper_environment import environment, add_dependency
import configparser


def change_config(targetfile, config, value):
    if config == "HOME_CONFIG":
        home_file = os.path.join(os.path.dirname(targetfile), ".HOMEDIR")
        if value == 'False':
            if os.path.isfile(home_file):
                os.remove(home_file)
        else:
            open(home_file, 'w').close()
        return
    with codecs.open(targetfile, 'r') as fp:
        file = fp.read()
    replaced = re.sub("(" + config + "\s+=\s+)(.*)", r"\1" + value, file)
    f = codecs.open(targetfile, "w")
    f.write(replaced)
    f.close()

# Update requirements in config.cfg file
config = configparser.ConfigParser()
config.read(os.path.join(FILEPATH,"setup.cfg"))

print("Updating config.cfg from requirments.txt")
with open(os.path.join(FILEPATH, "requirements.txt"), "r") as stream:
    requirements = stream.readlines()

config['options']['install_requires'] = "\n" + "".join(requirements)

with open(os.path.join(FILEPATH, "optional-requirements.txt"), "r") as stream:
    opt_requirements = stream.readlines()

print("Updating config.cfg from optional-requirments.txt")
optional_reqs = dict()
option = ""
for line in opt_requirements:
    if line.startswith("#"):
        option = line[1:].split()[0].strip()
        optional_reqs[option] = "\n"
    else:
        if line != "\n":
            optional_reqs[option] += line

for key, value in optional_reqs.items():
    try:
        if config["options.extras_require"][key.lower()]:
            config["options.extras_require"][key.lower()] = value.rstrip("\n")
        print("'{}' block updated".format(key))
    except KeyError:
        print("Optional Requirement block '{}' not found in config.cfg".format(key.lower()))

with open(os.path.join(FILEPATH,"setup.cfg"), 'w') as configfile:
    config.write(configfile)

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
print('Moving files to "src" directory')

change_config(targetfile,"HOME_CONFIG", "True")
print('Change "homeconfig" settings to true')

# Generate package
print('Generating package')
error = False
p = subprocess.Popen(sys.executable + " setup.py sdist bdist_wheel"
                     ,shell=True,stdout=subprocess.PIPE, stdin=subprocess.PIPE)
p.communicate()[0]
p.wait()

# check succesfull
if p.returncode != 0:
    print('Error: package generation returned an error, aborting')
    error = True
# move files back
print('Change "homeconfig" settings back to false')
change_config(targetfile,"HOME_CONFIG", "False")

print('Moving files back to origin')
shutil.move('./src/calibreweb/__init__.py','./cps.py')
shutil.move('./src/calibreweb/cps','.')
print('Deleting "src" directory')
shutil.rmtree('src', ignore_errors=True)
print('Deleting "build" directory')
shutil.rmtree('build', ignore_errors=True)

if error:
    # if package generation had an error stop
    sys.exit(1)

print('Start building executable')
files = glob.glob(os.path.join('dist','*.tar.gz'))
if len(files) > 1:
    print('More than one package file found, aborting')
    sys.exit(1)

print('Deleting old "exe_temp" and "executable" directory')
shutil.rmtree('exe_temp', ignore_errors=True)
shutil.rmtree('executable', ignore_errors=True)
print('Creating "exe_temp" directory')
os.mkdir('exe_temp')
print('Extracting package file to "exe_temp" directory')
tar = tarfile.open(files[0], "r:gz")
tar.extractall('exe_temp')
tar.close()
os.chdir('exe_temp')
setup_file = glob.glob('**/setup.py', recursive=True)
if len(setup_file) > 1:
    print('More than one setup file found exiting')
    sys.exit(1)
os.chdir(os.path.dirname(setup_file[0]))
print('Changing directory to package root folder "src/calibreweb"')
os.chdir("src")
os.chdir("calibreweb")

print('Make Updater unavailable in excecutable')

targetfile = os.path.join("cps/constants.py")
change_config(targetfile,"UPDATER_AVAILABLE", "False")
if os.name == "nt":
    print('Store config for excecutable in program folder on Windows')
    change_config(targetfile,"HOME_CONFIG", "False")
    pyinst = "pyinstaller.exe"
else:
    pyinst = "pyinstaller"

# install requirements and optional requirements in venv of calibre-web
print("Creating virtual environment for executable")
try:
    venv.create(VENV_PATH, clear=True, with_pip=True)
except CalledProcessError:
    print("Error Creating virtual environment")
    venv.create(VENV_PATH, system_site_packages=True, with_pip=False)


print("Adding dependencies for executable from requirements file")
requirements_file = os.path.join(FILEPATH, 'requirements.txt')
p = process_open([VENV_PYTHON, "-m", "pip", "install", "-r", requirements_file], (0, 5))
while p.poll() == None:
    print(p.stdout.readline().strip("\n"))

# Adding precompiled dependencies for Windows
if os.name == "nt":
    print("Adding precompiled dependencies for executable for Windows")
    environment.init_Environment(VENV_PYTHON)
    add_dependency(["local|LDAP_WHL|python-ldap", "local|LEVENSHTEIN_WHL|python-Levenshtein"], "")

print("Adding dependencies for executable from optional_requirements file")
optional_requirements_file = os.path.join(FILEPATH, 'optional-requirements.txt')
p = process_open([VENV_PYTHON, "-m", "pip", "install", "-r", optional_requirements_file], (0, 5))
while p.poll() == None:
    print(p.stdout.readline().strip("\n"))

print("Adding pyinstaller to virtual environment")
p = process_open([VENV_PYTHON, "-m", "pip", "install", "pyinstaller"], (0,))
while p.poll() == None:
    print(p.stdout.readline().strip("\n"))


print("Starting build of executable via PyInstaller")
if os.name == "nt":
    sep = ";"
else:
    sep = ":"

pyinst_path = os.path.join(os.path.dirname(VENV_PYTHON), pyinst)
if os.name == "nt":
    google_api_path = glob.glob(os.path.join(FILEPATH, "venv","lib/site-packages/google_api_python*"))
else:
    google_api_path = glob.glob(os.path.join(FILEPATH, "venv","lib/**/site-packages/google_api_python*"))

if len(google_api_path) != 1:
    print('More than one google_api_python directory found exiting')
    sys.exit(1)
os.rename('__init__.py', 'root.py')
p = subprocess.Popen(pyinst_path + " root.py "
                                   "-i cps/static/favicon.ico "
                                   "-n calibreweb "
                                   "--add-data cps/static" + sep + "cps/static "
                                   "--add-data cps/metadata_provider" + sep + "cps/metadata_provider "                                                                   
                                   "--add-data cps/templates" + sep + "cps/templates "
                                   "--add-data cps/translations" + sep + "cps/translations "
                                   "--add-data " + google_api_path[0] + sep + os.path.basename(google_api_path[0]) + " "
                                   "--hidden-import sqlalchemy.sql.default_comparator ",
                                   # "--hidden-import flask_wtf "
                                   # "--debug all",
                     shell=True,
                     stdout=subprocess.PIPE,
                     stdin=subprocess.PIPE)
p.communicate()[0]
p.wait()

# check succesfull
if p.returncode != 0:
    print('Error: pyinstaller returned an error, aborting')
    sys.exit(1)

print('Moving folder to root folder')
shutil.move('./dist/calibreweb/',os.path.join(FILEPATH))
os.chdir(FILEPATH)
os.rename("calibreweb", "executable")
shutil.rmtree('exe_temp', ignore_errors=True)
os.chdir(workdir)

print('finished')
