# -*- coding: utf-8 -*-

from HTMLTestRunner import runner as HTMLTestRunner
import os
import re
import time
import requests
from subproc_wrapper import process_open
from config_test import SELENIUM_SERVER, CALIBRE_WEB_PATH, VENV_PATH, VENV_PYTHON
import unittest
import sys
import venv
from CalibreResult import CalibreResult
from helper_environment import environment
from subprocess import check_output, CalledProcessError

if __name__ == '__main__':
    sub_dependencys = ["Werkzeug", "Jinja2", "singledispatch"]
    result=False
    retry=0
    while True:
        try:
            r = requests.get('http://localhost:4444/wd/hub/status').json()
            result=True
        except:
            my_env = os.environ.copy()
            my_env["PATH"] = SELENIUM_SERVER + ":" + my_env["PATH"]
            print ('Selenium server not running, trying to start')
            p = process_open(["java", "-jar", SELENIUM_SERVER], [2], my_env)
            time.sleep(5)
            result= False
            retry +=1
            if retry >3:
                print ("Couldn't start Selenium server")
                exit()
        if result:
            print("Selenium server successfully started")
            break

    # check pip ist installed
    if True: # os.name != 'nt':
        found = False
        python_exe = ""
        pversion = ["python3.7", "python3.8", "python3", "c:\\python38\\python.exe", "c:\\python37\\python.exe"]
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
                # exit()
    else:
        print("Test are not guaranteed to run on windows")
        found = True
    if not found:
        print("Pip not found, can't setup test environment")
        exit()

    # generate virtual environment
    if os.name != 'nt':

        try:
            venv.create(VENV_PATH, clear=True, with_pip=True)
        except CalledProcessError:
            venv.create(VENV_PATH, system_site_packages =True, with_pip=False)
    else:
        p = process_open([python, "-m", "venv", "--upgrade", VENV_PATH])
        p.wait()
    print("Creating virtual environment for testing")


    requirements_file = os.path.join(CALIBRE_WEB_PATH, 'requirements.txt')
    p = process_open([VENV_PYTHON, "-m", "pip", "install", "-r", requirements_file],(0,5))
    if os.name == 'nt':
        while p.poll() == None:
            print(p.stdout.readline())
    else:
        p.wait()
    environment.init_Environment(VENV_PYTHON, sub_dependencys)

    all_tests = unittest.TestLoader().discover('.')
    # configure HTMLTestRunner options
    outfile = os.path.join(CALIBRE_WEB_PATH, 'test')
    template = os.path.join(os.path.dirname(__file__), 'htmltemplate', 'report_template.html')
    runner = HTMLTestRunner.HTMLTestRunner(output=outfile,report_name="Calibre-Web TestSummary",
                                           report_title='Calibre-Web Tests',
                                           description ='Systemtests for Calibre-web',
                                           combine_reports=True,
                                           template=template,
                                           stream=sys.stdout,
                                           resultclass=CalibreResult,
                                           open_in_browser=True,
                                           verbosity=2)
    # run the suite using HTMLTestRunner
    runner.run(all_tests)
    print("\nAll tests finished, please check testresults")
    sys.exit(0)
