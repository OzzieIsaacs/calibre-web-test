# -*- coding: utf-8 -*-

from HTMLTestRunner import runner as HTMLTestRunner
import os
import re
from subproc_wrapper import process_open
from config_test import CALIBRE_WEB_PATH, VENV_PATH, VENV_PYTHON, TEST_OS
import unittest
import sys
import venv
from CalibreResult import CalibreResult
from helper_environment import environment
from helper_func import kill_dead_cps, finishing_notifier, poweroff
from helper_certificate import generate_ssl_testing_files
from subprocess import CalledProcessError
from concurrencytest import ConcurrentTestSuite, iterate_tests, fork2_for_tests #  fork_for_tests, partition_tests
import testtools

class new_testresult(testtools.StreamResult):

    def __init__(self):
        super().__init__()

    def status(self, test_id=None, test_status=None, test_tags=None,
               runnable=True, file_name=None, file_bytes=None, eof=False,
               mime_type=None, route_code=None, timestamp=None):
        if test_status == "success":
            print(test_id + " ...........ok")
        if test_status == "fail":
            print(test_id + " ...........fail")

def partition_tests(suite):
    """Partition suite into count lists of tests."""
    # This just assigns tests in a round-robin fashion.  On one hand this
    # splits up blocks of related tests that might run faster if they shared
    # resources, but on the other it avoids assigning blocks of slow tests to
    # just one partition.  So the slowest partition shouldn't be much slower
    # than the fastest.
    # return ((case) for case in suite)
    partitions = list()
    tests = iterate_tests(suite)
    return tests
    '''elements = 0
    tests = list()
    for s in suite._tests[0]:
        if s._tests:
            elements += 1
            tests.append(s)
            if elements == 2:
                partitions.append(unittest.TestSuite(tests))
                elements = 0
                tests = list()
    return partitions'''


if __name__ == '__main__':
    generate_ssl_testing_files()
    sub_dependencies = ["Werkzeug", "Jinja2", "singledispatch"]
    result = False
    retry = 0
    power = 0
    '''power = input('Power off after finishing tests? [y/N]').lower() == 'y'
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
    try:
        venv.create(VENV_PATH, clear=True, with_pip=True)
    except CalledProcessError:
        print("Error Creating virtual environment")
        venv.create(VENV_PATH, system_site_packages=True, with_pip=False)
    print("Creating virtual environment for testing")


    requirements_file = os.path.join(CALIBRE_WEB_PATH, 'requirements.txt')
    p = process_open([VENV_PYTHON, "-m", "pip", "install", "-r", requirements_file], (0, 5))
    if os.name == 'nt':
        while p.poll() == None:
            p.stdout.readline()
    else:
        p.wait()
    environment.init_environment(VENV_PYTHON, sub_dependencies)'''

    all_tests = unittest.TestLoader().discover('.')
    # configure HTMLTestRunner options
    outfile = os.path.join(CALIBRE_WEB_PATH, 'test')
    template = os.path.join(os.path.dirname(__file__), 'htmltemplate', 'report_template.html')
    runner = HTMLTestRunner.HTMLTestRunner(output=outfile,
                                           report_name="Calibre-Web TestSummary_" + TEST_OS,
                                           report_title='Calibre-Web Tests',
                                           description='Systemtests for Calibre-web',
                                           combine_reports=True,
                                           template=template,
                                           stream=sys.stdout,
                                           resultclass=CalibreResult,
                                           open_in_browser=not power,
                                           verbosity=2)
    # run the suite using HTMLTestRunner
    # runner.run(all_tests)
    # ConcurrentTestSuite
    # concurrent_suite = testtools.ConcurrentStreamTestSuite(lambda: ((case, None) for case in all_tests))
    results = new_testresult() # (testtools.StreamResult()) # unittest.TestResult()
    results.startTestRun()
    concurrent_suite = testtools.ConcurrentStreamTestSuite(fork2_for_tests(all_tests, 2))
    concurrent_suite.run(results)
    results.stopTestRun()
    # suite = unittest.TestLoader().loadTestsFromTestCase(all_tests)
    # concurrent_suite = testtools.ConcurrentTestSuite(all_tests, partition_tests)
    #concurrent_suite = ConcurrentTestSuite(all_tests, fork_for_tests(2))
    #concurrent_suite = testtools.ConcurrentStreamTestSuite(lambda: ((case, None) for case in all_tests))
    #concurrent_suite.run(results)
    #results.stopTestRun()
    # runner.run(concurrent_suite)
    print("\nAll tests finished, please check test results")
    kill_dead_cps()
    # E-Mail tests finished
    #result_file = os.path.join(outfile, "Calibre-Web TestSummary_" + TEST_OS + ".html")
    #finishing_notifier(result_file)

    #poweroff(power)
    sys.exit(0)
