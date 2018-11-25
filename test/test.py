#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import HTMLTestRunner
import os
import time
import requests
from subproc_wrapper import process_open
from testconfig import SELENIUM_SERVER, CALIBRE_WEB_PATH
from test_helper import calibre_helper
from test_logging import test_logging
from test_cli import test_cli
from test_shelf import test_shelf
from test_user_template import test_user_template
from test_visiblilitys import calibre_web_visibilitys
from test_anonymous import test_anonymous
from test_ebook_convert import test_ebook_convert
from test_edit_books import test_edit_books
from test_edit_books_gdrive import test_edit_books_gdrive
from test_login import test_login
from test_opds_feed import test_opds_feed
from test_updater import test_updater
from test_register import test_register


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

    calibre_web_Test = unittest.TestLoader().loadTestsFromTestCase(calibre_web_visibilitys)
    helper_test = unittest.TestLoader().loadTestsFromTestCase(calibre_helper)
    logging_test = unittest.TestLoader().loadTestsFromTestCase(test_logging)
    cli_test = unittest.TestLoader().loadTestsFromTestCase(test_cli)
    anonymous_test = unittest.TestLoader().loadTestsFromTestCase(test_anonymous)
    ebook_convert_test = unittest.TestLoader().loadTestsFromTestCase(test_ebook_convert)
    edit_books_test = unittest.TestLoader().loadTestsFromTestCase(test_edit_books)
    edit_books_gdrive_test = unittest.TestLoader().loadTestsFromTestCase(test_edit_books_gdrive)
    login_test = unittest.TestLoader().loadTestsFromTestCase(test_login)
    opds_feed_test = unittest.TestLoader().loadTestsFromTestCase(test_opds_feed)
    updater_test = unittest.TestLoader().loadTestsFromTestCase(test_updater)
    register_test = unittest.TestLoader().loadTestsFromTestCase(test_register)
    shelf_test = unittest.TestLoader().loadTestsFromTestCase(test_shelf)
    user_template_test = unittest.TestLoader().loadTestsFromTestCase(test_user_template)
    # cli test has to be last, helper test has to be used after smtp server started/stopped
    all_tests = unittest.TestSuite([shelf_test, logging_test, calibre_web_Test, user_template_test,
                                    anonymous_test, edit_books_test, edit_books_gdrive_test, ebook_convert_test,
                                    login_test, opds_feed_test, updater_test, helper_test, register_test, cli_test])
    # all_tests = unittest.TestSuite([ebook_convert_test, helper_test])
    # open the report file
    outfile = open(os.path.join(CALIBRE_WEB_PATH,'test',"Calibre-Web TestSummary.html"), "w")
    # configure HTMLTestRunner options
    runner = HTMLTestRunner.HTMLTestRunner(stream=outfile, title='Test Report', description='All Calibre-Web tests')
    # run the suite using HTMLTestRunner
    runner.run(all_tests)
    print("\nAll tests finished, please check testresults")
