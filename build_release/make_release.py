# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
__package__ = "build_release"
import os
import glob
import shutil
import sys
import subprocess
import codecs
import re
import tarfile
import venv
from subprocess import CalledProcessError
from subproc_wrapper import process_open
import configparser
import argparse
import platform

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import FILEPATH, VENV_PATH, VENV_PYTHON
from .helper_environment import environment, add_dependency

def find_version(file_paths):
    with codecs.open(file_paths, 'r') as fp:
        version_file = fp.read()
    version_match = re.search(r"^STABLE_VERSION\s+=\s+{['\"]version['\"]:\s*['\"](.*)['\"]}",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


def change_config(target_file, config, value):
    if config == "HOME_CONFIG":
        home_file = os.path.join(os.path.dirname(target_file), ".HOMEDIR")
        if value == 'False':
            if os.path.isfile(home_file):
                os.remove(home_file)
        else:
            open(home_file, 'w').close()
        return
    with codecs.open(target_file, 'r') as fp:
        file = fp.read()
    replaced = re.sub("(" + config + r"\s+=\s+)(.*)", r"\1" + value, file)
    f = codecs.open(target_file, "w")
    f.write(replaced)
    f.close()


def update_requirements():
    # Update requirements in config.cfg file
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(FILEPATH, "setup.cfg"))

    print("* Updating config.cfg from requirements.txt")
    with open(os.path.join(FILEPATH, "requirements.txt"), "r") as stream:
        requirements = stream.readlines()

    cfg['options']['install_requires'] = "\n" + "".join(requirements)

    with open(os.path.join(FILEPATH, "optional-requirements.txt"), "r") as stream:
        opt_requirements = stream.readlines()

    print("* Updating config.cfg from optional-requirements.txt")
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
            if cfg["options.extras_require"][key.lower()]:
                cfg["options.extras_require"][key.lower()] = value.rstrip("\n")
            print("'{}' block updated".format(key))
        except KeyError:
            print("* Optional Requirement block '{}' not found in config.cfg".format(key.lower()))

    with open(os.path.join(FILEPATH, "setup.cfg"), 'w') as configfile:
        cfg.write(configfile)


def parse_arguments(*args):
    parser = argparse.ArgumentParser(description='Build files installer files of Calibre-web\n', prog='make_release.py')
    parser.add_argument('-u', action='store_true', help='Update setup.cfg file')
    parser.add_argument('-p', action='store_true', help='Only generate pypi package file')
    return parser.parse_args(*args)


def prepare_folders():
    # create source folder
    try:
        os.makedirs('src')
        print('* Creating "src" directory')
    except FileExistsError:
        pass
    try:
        os.makedirs('src/calibreweb')
        print('* Creating "calibreweb" directory')
    except FileExistsError:
        pass

    # delete build and dist dir
    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('dist', ignore_errors=True)

    # move cps and cps.py file to source folder
    try:
        os.remove('cps.pyc')
    except OSError:
        pass
    try:
        os.remove('./cps/*.pyc')
    except OSError:
        pass
    try:
        os.remove('./cps/services/*.pyc')
    except OSError:
        pass
    shutil.copy('cps.py', 'src/calibreweb/__main__.py')
    shutil.move('cps.py', 'src/calibreweb/__init__.py')
    shutil.move('cps', 'src/calibreweb')
    shutil.move(os.path.join(FILEPATH, 'requirements.txt'), 'src/calibreweb/requirements.txt')
    shutil.move(os.path.join(FILEPATH, 'optional-requirements.txt'), 'src/calibreweb/optional-requirements.txt')
    print('* Moving files to "src" directory')


def generate_package():
    prepare_folders()
    # Change home-config setting
    target_file = os.path.join(FILEPATH, "src", "calibreweb", "cps", "constants.py")
    change_config(target_file, "HOME_CONFIG", "True")
    print('* Change "homeconfig" settings to true')

    # Generate package
    print('* Generating package')
    error = False
    p = process_open([sys.executable, "-m", "build"])
    while p.poll() is None:
        out = p.stdout.readline()
        out != "" and print(out.strip("\n"))

    err = p.stderr.readlines()
    print("".join(err), file=sys.stderr)

    # check successful
    if p.returncode != 0:
        print('## Error: package generation returned an error, aborting ##')
        error = True

    # Change home-config setting back
    print('* Change "homeconfig" settings back to false')
    change_config(target_file, "HOME_CONFIG", "False")

    # move files back in original place
    print('* Moving files back to origin')
    shutil.move(os.path.join(FILEPATH, 'src', 'calibreweb', '__init__.py'), os.path.join(FILEPATH, 'cps.py'))
    os.remove(os.path.join(FILEPATH, 'src/calibreweb/__main__.py'))
    shutil.move(os.path.join(FILEPATH, 'src/calibreweb/cps'), FILEPATH)
    shutil.move(os.path.join(FILEPATH, 'src/calibreweb/requirements.txt'), FILEPATH)
    shutil.move(os.path.join(FILEPATH, 'src/calibreweb/optional-requirements.txt'), FILEPATH)

    print('* Deleting "src" directory')
    shutil.rmtree(os.path.join(FILEPATH, 'src'), ignore_errors=True)
    print('* Deleting "build" directory')
    shutil.rmtree(os.path.join(FILEPATH, 'build'), ignore_errors=True)

    return error


def create_python_environment():
    # install requirements and optional requirements in venv of calibre-web
    print("* Creating virtual environment for executable")
    try:
        venv.create(VENV_PATH, clear=True, with_pip=True)
    except CalledProcessError:
        print("## Error Creating virtual environment ##")
        venv.create(VENV_PATH, system_site_packages=True, with_pip=False)

    print("* Adding dependencies for executable from requirements file")
    requirements_file = os.path.join(FILEPATH, 'requirements.txt')
    p = process_open([VENV_PYTHON, "-m", "pip", "install", "-r", requirements_file], (0, 5))
    while p.poll() is None:
        out = p.stdout.readline()
        out != "" and print(out.strip("\n"))

    # Adding precompiled dependencies for Windows
    if os.name == "nt":
        print("* Adding precompiled dependencies for executable for Windows")
        add_dependency(["local|LDAP_WHL|python-ldap"], "")

    print("* Adding dependencies for executable from optional_requirements file")
    optional_requirements_file = os.path.join(FILEPATH, 'optional-requirements.txt')
    p = process_open([VENV_PYTHON, "-m", "pip", "install", "-r", optional_requirements_file], (0, 5))
    while p.poll() is None:
        out = p.stdout.readline()
        out != "" and print(out.strip("\n"))

    print("* Saving installed requirement versions")
    environment.init_environment(VENV_PYTHON)
    environment.save_environment(os.path.join(FILEPATH, '.pip_installed'))

    print("Adding pyinstaller to virtual environment")
    p = process_open([VENV_PYTHON, "-m", "pip", "install", "pyinstaller"], (0,))
    while p.poll() is None:
        out = p.stdout.readline()
        out != "" and print(out.strip("\n"))


def create_executable():
    error = False
    print('* Make updater unavailable in executable')
    target_file = os.path.join("cps/constants.py")
    change_config(target_file, "UPDATER_AVAILABLE", "False")
    if os.name == "nt":
        print('* Store config for executable in program folder on Windows')
        change_config(target_file, "HOME_CONFIG", "False")
        py_inst = "pyinstaller.exe"
    else:
        py_inst = "pyinstaller"

    print("* Starting build of executable via PyInstaller")

    sep = ";" if os.name == "nt" else ":"

    py_inst_path = os.path.join(os.path.dirname(VENV_PYTHON), py_inst)
    if os.name == "nt":
        google_api_path = glob.glob(os.path.join(FILEPATH, "venv", "lib/site-packages/google_api_python*"))
        iso639_path = os.path.join(FILEPATH, "venv", "lib", "site-packages", "iso639")
    else:
        google_api_path = glob.glob(os.path.join(FILEPATH, "venv", "lib/**/site-packages/google_api_python*"))
        iso639_path = glob.glob(os.path.join(FILEPATH, "venv", "lib", "python*", "site-packages", "iso639"))[0]

    if len(google_api_path) != 1:
        print('* More than one google_api_python directory found exiting')
        sys.exit(1)
    os.rename('__init__.py', 'root.py')
    shutil.move(os.path.join(FILEPATH, 'requirements.txt'), 'requirements.txt')
    shutil.move(os.path.join(FILEPATH, 'optional-requirements.txt'), 'optional-requirements.txt')
    shutil.move(os.path.join(FILEPATH, '.pip_installed'), '.pip_installed')
    command = (py_inst_path + " root.py -i cps/static/favicon.ico "
                              "-n calibreweb "
                              "--add-data cps/static" + sep + "cps/static "
                              "--add-data cps/metadata_provider" + sep + "cps/metadata_provider "
                              "--add-data cps/templates" + sep + "cps/templates "
                              "--add-data cps/translations" + sep + "cps/translations "
                              "--add-data requirements.txt" + sep + ". "
                              "--add-data optional-requirements.txt" + sep + ". "
                              "--add-data .pip_installed" + sep + ". "
                              "--add-data " + iso639_path + sep + "iso639" + " "
                              "--add-data " + google_api_path[0] + sep + os.path.basename(google_api_path[0]) + " "
                              "--hidden-import sqlalchemy.sql.default_comparator ")
    p = subprocess.Popen(command,
                         # "--debug all",
                         shell=True,
                         stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE)
    p.communicate()[0]
    p.wait()

    # check successful
    if p.returncode != 0:
        print('## Error: pyinstaller returned an error, aborting ##')
        error = True
    return error


def prepare_files_pyinstaller():
    print('* Start building executable')
    files = glob.glob(os.path.join('dist', '*.tar.gz'))
    if len(files) > 1:
        print('## More than one package file found, aborting ##')
        sys.exit(1)

    print('* Deleting old "exe_temp" and "executable" directory')
    shutil.rmtree('exe_temp', ignore_errors=True)
    shutil.rmtree('executable', ignore_errors=True)
    print('* Creating "exe_temp" directory')
    os.mkdir('exe_temp')
    print('* Extracting package file to "exe_temp" directory')
    tar = tarfile.open(files[0], "r:gz")
    tar.extractall('exe_temp')
    tar.close()
    os.chdir('exe_temp')
    setup_file = glob.glob('**/setup.py', recursive=True)
    if len(setup_file) > 1:
        print('## More than one setup file found, aborting ##')
        sys.exit(1)
    os.chdir(os.path.dirname(setup_file[0]))
    print('* Changing directory to package root folder "src/calibreweb"')
    os.chdir("src")
    os.chdir("calibreweb")


def revert_files_pyinstaller(workdir):
    print('* Moving folder to root folder')
    shutil.move('./dist/calibreweb/', os.path.join(FILEPATH))
    shutil.move('requirements.txt', os.path.join(FILEPATH, 'requirements.txt'))
    shutil.move('optional-requirements.txt', os.path.join(FILEPATH, 'optional-requirements.txt'))
    # created .pip installed file is deleted
    # shutil.move(os.path.join(FILEPATH, '.pip_installed', '.pip_installed'))
    os.chdir(FILEPATH)
    os.rename("calibreweb", "executable")
    shutil.rmtree('exe_temp', ignore_errors=True)
    os.chdir(workdir)


def create_deb_package():
    shutil.rmtree(os.path.join(FILEPATH, "debian"), ignore_errors=True)
    arch = platform.uname().machine
    if arch == "x86_64":
        arch = "amd64"
    elif arch == "aarch64":
        arch = "arm64"
    version_file = os.path.join(FILEPATH, "cps", "constants.py")
    version_string = find_version(version_file).replace(" ", "-")
    os.makedirs(os.path.join(FILEPATH, "debian"))
    with open(os.path.join(FILEPATH, "debian", "control"), "w") as f:
        f.write("Source: Calibre-Web\n")
        f.write("\n")
        f.write("Package: Calibre-Web\n")
        f.write("Version: {}\n".format(version_string))
        f.write("Architecture: {}\n".format(arch))
        f.write("Maintainer: Ozzie Isaacs <Ozzie.Fernandez.Isaacs@googlemail.com>\n")
        f.write("Description: Calibre-Web is a web app providing a clean interface for browsing, "
                "reading and downloading eBooks using a valid Calibre database.\n")
    target_dir = "calibre-web_" + version_string + "_" + arch
    os.makedirs(os.path.join(FILEPATH, target_dir))
    os.makedirs(os.path.join(FILEPATH, target_dir, "DEBIAN"))
    os.makedirs(os.path.join(FILEPATH, target_dir, "opt"))
    shutil.copytree(os.path.join(FILEPATH, "executable"), os.path.join(FILEPATH, target_dir, "opt", "calibre-web"))
    exefile = os.path.join(target_dir, "opt", "calibre-web", "calibreweb")
    command = ("dpkg-shlibdeps -O " + "./" + exefile)
    p = subprocess.Popen(command,
                         cwd=FILEPATH,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE)
    p.wait()
    lines = p.stdout.readlines()
    dep_line = "".join([line.decode('utf-8') for line in lines])
    print("* Output dpkg-shlibdeps: {}".format(dep_line))
    dep_line = dep_line[15:].rstrip("\n")
    # check successful
    if p.returncode != 0:
        print('## Error: dpkg-shlibdeps returned an error, aborting ##')
        return True

    with open(os.path.join(FILEPATH, target_dir, "DEBIAN", "control"), "w") as f:
        f.write("Package: Calibre-Web\n")
        f.write("Version: {}\n".format(version_string))
        f.write("Architecture: {}\n".format(arch))
        f.write("Depends: {}\n".format(dep_line))
        f.write("Maintainer: Ozzie Isaacs <Ozzie.Fernandez.Isaacs@googlemail.com>\n")
        f.write("Description: Calibre-Web is a web app providing a clean interface for browsing, "
                "reading and downloading eBooks using a valid Calibre database.\n")

    command = ("dpkg-deb --build --root-owner-group " + target_dir)
    p = subprocess.Popen(command,
                         cwd=FILEPATH,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stdin=subprocess.PIPE)
    p.wait()
    lines = p.stdout.readlines()
    print("* Output dpkg-deb: ")
    for line in lines:
        print(line.decode('utf-8'))
    # check successful
    if p.returncode != 0:
        print('## Error: dpkg-deb returned an error, aborting ##')
        return True
    print('* Delete temporary files for .deb generation and move deb file to directory "debian"')
    os.remove(os.path.join(FILEPATH, "debian", "control"))
    shutil.move(os.path.join(FILEPATH, target_dir + ".deb"), os.path.join(FILEPATH, "debian"))
    shutil.rmtree(os.path.join(FILEPATH, target_dir), ignore_errors=True)
    return False

def clean_folders():
    cache_folders = glob.glob('cps/**/__pycache__', recursive=True)
    for folder in cache_folders:
        shutil.rmtree(os.path.join(FILEPATH, folder), ignore_errors=True)
    shutil.rmtree(os.path.join(FILEPATH, "debian"), ignore_errors=True)
    shutil.rmtree(os.path.join(FILEPATH, "executable"), ignore_errors=True)
    shutil.rmtree(os.path.join(FILEPATH, "dist"), ignore_errors=True)
    shutil.rmtree(os.path.join(FILEPATH, "src"), ignore_errors=True)

def main(args):
    update_requirements()
    if args.u:
        return 0

    # Change workdir to calibre folder
    workdir = os.getcwd()
    os.chdir(FILEPATH)

    # clean old build results
    clean_folders()

    # Generate pypi package
    # if package generation had an error stop
    if generate_package():
        return 1

    if args.p:
        return 0

    # move files for pyinstaller
    prepare_files_pyinstaller()
    # Prepare environment for pyinstaller
    create_python_environment()
    # create pyinstaller executable
    error = create_executable()
    revert_files_pyinstaller(workdir)

    if error:
        print('## Pyinstaller finished with error, aborting ##')
        return 1

    if sys.platform.lower() == "linux":
        print('* Generating Debian DEB package')
        if create_deb_package():
            print('## Generate DEB-package finished with error, aborting ##')
            return 1
    print('* Build Successfully Finished')
    return 0


if __name__ == '__main__':
    args = parse_arguments()
    ret = main(args)
    sys.exit(ret)
