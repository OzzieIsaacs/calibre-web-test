# -*- coding: utf-8 -*-

from HTMLTestRunner import runner as HTMLTestRunner
import os
import re
from subproc_wrapper import process_open
from config_test import CALIBRE_WEB_PATH, VENV_PYTHON, TEST_OS, base_path
import unittest
import sys
import venv
from CalibreResult import CalibreResult
from helper_environment import environment
from helper_func import kill_dead_cps, finishing_notifier, poweroff, result_move
from helper_certificate import generate_ssl_testing_files
from subprocess import CalledProcessError


if __name__ == '__main__':
    generate_ssl_testing_files()
    sub_dependencies = ["Werkzeug", "Jinja2", "singledispatch"]
    result = False
    retry = 0

    power = input('Power off after finishing tests? [y/N]').lower() == 'y'
    if power:
        print('!!!! PC will shutdown after tests finished !!!!')

    # check pip ist installed
    found = False
    python_exe = ""
    pversion = ["python3.10", "python3", "c:\\python39\\python.exe", "c:\\python310\\python.exe"]
    for python in pversion:
        try:
            p = process_open([python, "-m", "pip", "-V"])
        except (FileNotFoundError, Exception):
            print("{} not found".format(python))
            continue
        p.wait()
        res = (p.stdout.readlines())
        try:
            pip = re.match(("pip\s(.*)\sfrom\s(.*)\s\((.*)\).*"),res[0])
        except IndexError as e:
            continue
        except TypeError as e:
            pip = re.match(("pip\s(.*)\sfrom\s(.*)\s\((.*)\).*"), res[0].decode('utf-8'))
        if pip:
            print("Found Pip for {} in {}".format(pip[3],pip[2]))
            found = True
            python_exe = python
            break
        else:
            print("Pip not found, can't setup test environment")

    if not found:
        print("Pip not found, can't setup test environment")
        exit()

    # generate virtual environment
    venv_path = os.path.join(CALIBRE_WEB_PATH, "venv")
    try:
        venv.create(venv_path, clear=True, with_pip=True)
    except CalledProcessError:
        print("Error Creating virtual environment")
        venv.create(venv_path, system_site_packages=True, with_pip=False)
    print("Creating virtual environment for testing")


    requirements_file = os.path.join(CALIBRE_WEB_PATH, 'requirements.txt')
    python_executable = os.path.join(CALIBRE_WEB_PATH, "venv", VENV_PYTHON)
    p = process_open([python_executable, "-m", "pip", "install", "-r", requirements_file], (0, 5))
    if os.name == 'nt':
        while p.poll() == None:
            p.stdout.readline()
    else:
        p.wait()
    environment.init_environment(python_executable, sub_dependencies)

    all_tests = unittest.TestLoader().discover(base_path)
    # configure HTMLTestRunner options
    outfile = os.path.join(CALIBRE_WEB_PATH, 'test')
    template = os.path.join(os.path.dirname(__file__), 'htmltemplate', 'report_template.html')
    template2 = os.path.join(os.path.dirname(__file__), 'htmltemplate', 'report_template2.html')
    runner = HTMLTestRunner.HTMLTestRunner(output=outfile,
                                           report_name="Calibre-Web TestSummary_" + TEST_OS,
                                           report_title='Calibre-Web Tests',
                                           description='Systemtests for Calibre-web',
                                           combine_reports=True,
                                           template=[template, template2],
                                           stream=sys.stdout,
                                           resultclass=CalibreResult,
                                           open_in_browser=not power,
                                           verbosity=2)
    # run the suite using HTMLTestRunner
    runner.run(all_tests)
    print("\nAll tests finished, please check test results")
    kill_dead_cps()
    # E-Mail tests finished
    result_file = os.path.join(outfile, "Calibre-Web TestSummary_" + TEST_OS + ".html")
    finishing_notifier(result_file)
    result_file2 = os.path.join(outfile, "Calibre-Web TestSummary_" + TEST_OS + "_1.html")
    result_move(result_file2)
    poweroff(power)
    sys.exit(0)
