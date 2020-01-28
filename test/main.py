#!/usr/bin/env python
# -*- coding: utf-8 -*-
#from gevent import monkey
#monkey.patch_all()

# from parameterized import parameterized_class
from HTMLTestRunner import runner as HTMLTestRunner
import os
import time
import requests
from subproc_wrapper import process_open
from testconfig import SELENIUM_SERVER, CALIBRE_WEB_PATH
import unittest
import sys
from CalibreResult import CalibreResult


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
            print ('Selenium not running')
            p = process_open(["java", "-jar", SELENIUM_SERVER], (2), my_env)
            time.sleep(5)
            result= False
            retry +=1
            if retry >3:
                print ("Can't start selenium server")
                exit()
        if result:
            break


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
