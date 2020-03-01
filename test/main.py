#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# from parameterized import parameterized_class
from HTMLTestRunner import runner as HTMLTestRunner
import os
import re
import time
import requests
from subproc_wrapper import process_open
from testconfig import SELENIUM_SERVER, CALIBRE_WEB_PATH, VENV_PATH, VENV_PYTHON
import unittest
import sys
import venv
from CalibreResult import CalibreResult
from helper_environment import environment

if __name__ == '__main__':
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
            p = process_open(["java", "-jar", SELENIUM_SERVER], (2), my_env)
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
    p = process_open(["python3", "-m", "pip", "-V"])
    p.wait()
    res = (p.stdout.readlines())
    pip = re.match(("pip\s(.*)\sfrom\s(.*)\s\((.*)\).*"),res[0])
    if pip:
        print("Found Pip for {} in {}".format(pip[3],pip[2]))
    else:
        print("Pip not found, can't setup test environment")
        exit()

    # generate virtual environment
    venv.create(VENV_PATH, clear=True, with_pip=True)
    print("Creating virtual environment for testing")


    requirements_file = os.path.join(CALIBRE_WEB_PATH,'requirements.txt')
    p = process_open([VENV_PYTHON, "-m", "pip", "install", "-r",requirements_file],(0,5))
    p.wait()
    '''for l in p.stdout.readlines():
        if isinstance(l, bytes):
            l = l.decode('utf-8')
        print(l)'''
    environment.init_Environment(VENV_PYTHON)
    # all_tests = unittest.TestLoader().loadTestsFromName('test_email_ssl')
    all_tests = unittest.TestLoader().discover('.')
    # open the report file
    outfile = open(os.path.join(CALIBRE_WEB_PATH,'test',"Calibre-Web TestSummary1.html"), "w")
    # configure HTMLTestRunner options
    #runner = HTMLTestRunner.HTMLTestRunner(stream=outfile, report_title='Test Report', report_name='All Calibre-Web tests', verbosity=2)
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
