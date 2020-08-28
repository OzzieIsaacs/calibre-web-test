#-*- coding: utf-8 -*-
"""
------------------------------------------------------------------------
Copyright (c) 2004-2007, Wai Yip Tung
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.
* Neither the name Wai Yip Tung nor the names of its contributors may be
  used to endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# URL: http://tungwaiyip.info/software/HTMLTestRunner.html
from __future__ import print_function

import os
import sys
import time
import copy
import traceback
from unittest import TestResult, TextTestResult
from unittest.result import failfast
import pkg_resources
from config_test import CALIBRE_WEB_PATH
import platform
from helper_environment import environment
from jinja2 import Template

PY3K = (sys.version_info[0] > 2)
if PY3K:
    import io as StringIO
else:
    import StringIO

DEFAULT_TEMPLATE = os.path.join(os.path.dirname(__file__), "template", "report_template.html")


def to_unicode(s):
    try:
        if not PY3K:
            return unicode(s)
        return s
    except UnicodeDecodeError:
        # s is non ascii byte string
        return s.decode('unicode_escape')

class OutputRedirector(object):
    """ Wrapper to redirect stdout or stderr """

    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(to_unicode(s))

    def writelines(self, lines):
        lines = map(to_unicode, lines)
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()

#stdout_redirector = OutputRedirector(sys.stdout)
#stderr_redirector = OutputRedirector(sys.stderr)

def load_template(template):
    """ Try to read a file from a given path, if file
        does not exist, load default one. """
    file = None
    try:
        if template:
            with open(template, "r") as f:
                file = f.read()
    except Exception as err:
        print("Error: Your Template wasn't loaded", err,
              "Loading Default Template", sep="\n")
    finally:
        if not file:
            with open(DEFAULT_TEMPLATE, "r") as f:
                file = f.read()
        return file


def render_html(template, **kwargs):
    template_file = load_template(template)
    if template_file:
        template = Template(template_file)
        return template.render(**kwargs)


def testcase_name(test_method):
    testcase = type(test_method)

    module = testcase.__module__ + "."
    if module == "__main__.":
        module = ""
    result = module + testcase.__name__
    return result


def strip_module_names(testcase_names):
    """Examine all given test case names and strip them the minimal
    names needed to distinguish each. This prevents cases where test
    cases housed in different files but with the same names cause clashes."""
    result = copy.copy(testcase_names)
    for i, testcase in enumerate(testcase_names):
        classname = testcase.split(".")[-1]
        duplicate_found = False
        testcase_names_ = copy.copy(testcase_names)
        del testcase_names_[i]
        for testcase_ in testcase_names_:
            classname_ = testcase_.split(".")[-1]
            if classname_ == classname:
                duplicate_found = True
        if not duplicate_found:
            result[i] = classname
    return result


class _TestInfo(object):
    """" Keeps information about the execution of a test method. """

    (SUCCESS, FAILURE, ERROR, SKIP) = range(4)

    def __init__(self, test_result, test_method, outcome=SUCCESS,
                 err=None, subTest=None):
        self.test_result = test_result
        self.outcome = outcome
        self.elapsed_time = 0
        self.err = err
        self.stdout = test_result._stdout_data
        self.stderr = test_result._stderr_data

        self.is_subtest = subTest is not None

        self.test_description = self.test_result.getDescription(test_method)
        self.test_exception_info = (
            '' if outcome in (self.SUCCESS, self.SKIP)
            else self.test_result._exc_info_to_string(
                self.err, test_method))

        self.test_name = testcase_name(test_method)
        if not self.is_subtest:
            self.test_id = test_method.id()
        else:
            self.test_id = subTest.id()

    def id(self):
        return self.test_id

    def test_finished(self):
        self.elapsed_time = self.test_result.stop_time - self.test_result.start_time

    def get_description(self):
        return self.test_description

    def get_error_info(self):
        return self.test_exception_info


class _SubTestInfos(object):
    # TODO: make better: inherit _TestInfo?
    (SUCCESS, FAILURE, ERROR, SKIP) = range(4)

    def __init__(self, test_id, subtests):
        self.subtests = subtests
        self.test_id = test_id
        self.outcome = self.check_outcome()

    def check_outcome(self):
        outcome = _TestInfo.SUCCESS
        for subtest in self.subtests:
            if subtest.outcome != _TestInfo.SUCCESS:
                outcome = _TestInfo.FAILURE
                break
        return outcome


class CalibreResult(TextTestResult):
    """ A test result class that express test results in Html. """

    start_time = None
    stop_time = None
    default_prefix = "TestResults_"

    STATUS = {
        0: 'PASS',
        1: 'FAIL',
        2: 'ERROR',
        3: 'SKIP',
    }

    def __init__(self, stream, descriptions, verbosity):
        TextTestResult.__init__(self, stream, descriptions, verbosity)
        self.buffer = False
        self._stdout_data = None
        self._stderr_data = None
        self.successes = []
        self.subtests = {}
        self.callback = None
        self.infoclass = _TestInfo
        self.report_files = []

        self.outputBuffer = StringIO.StringIO()
        self.stdout0 = None
        self.stderr0 = None
        self.verbosity = verbosity

        # result is a list of result in 5 tuple
        # (
        #   result code (0: success; 1: fail; 2: error; 3: skip),
        #   TestCase object,
        #   Test output (byte string),
        #   stack trace,
        # )
        self.result = []

    def _prepare_callback(self, test_info, target_list, verbose_str,
                          short_str, reason=None):
        """ Appends a 'info class' to the given target list and sets a
            callback method to be called by stopTest method."""
        target_list.append(test_info)

        def callback():
            """ Print test method outcome to the stream and elapsed time too."""
            test_info.test_finished()

            if self.showAll:
                self.stream.writeln(
                    "{} ({:1f})s".format(verbose_str, test_info.elapsed_time))
                if reason:
                    self.stream.writeln(' - ' + str(reason))
            elif self.dots:
                self.stream.write(short_str)

        self.callback = callback

    def getDescription(self, test):
        """ Return the test description if not have test name. """
        return str(test)

    def startTest(self, test):
        """ Called before execute each method. """
        self.start_time = time.time()
        TestResult.startTest(self, test)

        if self.showAll:
            self.stream.write(" " + self.getDescription(test))
            self.stream.write(" ... ")

        # just one buffer for both stdout and stderr
        '''self.outputBuffer = StringIO.StringIO()
        stdout_redirector.fp = self.outputBuffer
        stderr_redirector.fp = self.outputBuffer'''
        '''self.stdout0 = sys.stdout
        self.stderr0 = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector'''

    #def complete_output(self):
        """
        Disconnect output redirection and return buffer.
        Safe to call multiple times.
        """
        '''if self.stdout0:
            sys.stdout = self.stdout0
            sys.stderr = self.stderr0
            self.stdout0 = None
            self.stderr0 = None
        return self.outputBuffer.getvalue()'''
        #return self._stdout_data

    def _save_output_data(self):
        try:
            self._stdout_data = sys.stdout.getvalue()
            self._stderr_data = sys.stderr.getvalue()
        except AttributeError:
            pass


    def stopTest(self, test):
        """ Called after execute each test method. """
        self._save_output_data()
        TestResult.stopTest(self, test)
        self.stop_time = time.time()

        if self.callback and callable(self.callback):
            self.callback()
            self.callback = None
        # Usually one of addSuccess, addError or addFailure
        # would have been called.
        # But there are some path in unittest that would bypass this.
        # We must disconnect stdout in stopTest(),
        # which is guaranteed to be called.
        # self.complete_output()


    def addSuccess(self, test):
        """ Called when a test executes successfully. """
        self._save_output_data()
        self._prepare_callback(self.infoclass(self, test), self.successes, "OK", ".")
        # output = self.complete_output()
        self.result.append((0, test, self._stdout_data, ''))

    @failfast
    def addFailure(self, test, err):
        """ Called when a test method fails. """
        self._save_output_data()
        testinfo = self.infoclass(self, test, self.infoclass.FAILURE, err)
        self._prepare_callback(testinfo, self.failures, "FAIL", "F")
        # output = self.complete_output()
        self.result.append((1, test, self._stdout_data, testinfo.test_exception_info))

    @failfast
    def addError(self, test, err):
        """" Called when a test method raises an error. """
        self._save_output_data()
        testinfo = self.infoclass(self, test, self.infoclass.ERROR, err)
        self._prepare_callback(testinfo, self.errors, 'ERROR', 'E')
        # output = self.complete_output()
        self.result.append((2, test, self._stdout_data, testinfo.test_exception_info))

    def addSubTest(self, testcase, test, err):
        """ Called when a subTest completes. """
        self._save_output_data()
        # TODO: should ERROR cases be considered here too?
        if err is None:
            testinfo = self.infoclass(self, testcase, self.infoclass.SUCCESS, err, subTest=test)
            self._prepare_callback(testinfo, self.successes, "OK", ".")
        else:
            testinfo = self.infoclass(self, testcase, self.infoclass.FAILURE, err, subTest=test)
            self._prepare_callback(testinfo, self.failures, "FAIL", "F")

        test_id_components = str(testcase).rstrip(')').split(' (')
        test_id = test_id_components[1] + '.' + test_id_components[0]
        if test_id not in self.subtests:
            self.subtests[test_id] = []
        self.subtests[test_id].append(testinfo)

    def addSkip(self, test, reason):
        """" Called when a test method was skipped. """
        self._save_output_data()
        testinfo = self.infoclass(self, test, self.infoclass.SKIP, reason)
        self._prepare_callback(testinfo, self.skipped, "SKIP", "S")
        # output = self.complete_output()
        self.result.append((3, test, self._stdout_data, reason))

    def printErrorList(self, flavour, errors):
        """
        Writes information about the FAIL or ERROR to the stream.
        """
        for test_info in errors:
            self.stream.writeln(self.separator1)
            self.stream.writeln(
                '{} [{:3f}s]: {}'.format(flavour, test_info.elapsed_time,
                                         test_info.test_id)
            )
            self.stream.writeln(self.separator2)
            self.stream.writeln('%s' % test_info.get_error_info())

    def _get_info_by_testcase(self):
        """ Organize test results by TestCase module. """

        tests_by_testcase = {}

        subtest_names = set(self.subtests.keys())
        for test_name, subtests in self.subtests.items():
            subtest_info = _SubTestInfos(test_name, subtests)
            testcase_name = ".".join(test_name.split(".")[:-1])
            if testcase_name not in tests_by_testcase:
                tests_by_testcase[testcase_name] = []
            tests_by_testcase[testcase_name].append(subtest_info)

        for tests in (self.successes, self.failures, self.errors, self.skipped):
            for test_info in tests:
                # subtests will be contained by _SubTestInfos objects but there is also the
                # case where all subtests pass and the method is added as a success as well
                # which must be filtered out
                if test_info.is_subtest or test_info.test_id in subtest_names:
                    continue
                if isinstance(test_info, tuple):  # TODO: does this ever occur?
                    test_info = test_info[0]
                testcase_name = ".".join(test_info.test_id.split(".")[:-1])
                if testcase_name not in tests_by_testcase:
                    tests_by_testcase[testcase_name] = []
                tests_by_testcase[testcase_name].append(test_info)

        # unittest tests in alphabetical order based on test name so re-assert this
        for testcase in tests_by_testcase.values():
            testcase.sort(key=lambda x: x.test_id)

        return tests_by_testcase

    @staticmethod
    def _format_duration(elapsed_time):
        """Format the elapsed time in seconds, or milliseconds if the duration is less than 1 second."""
        if elapsed_time > 3600:
            duration = '{}h {} min'.format(int(elapsed_time / 3600), int((elapsed_time % 3600)/60))
        elif elapsed_time > 60:
            duration = '{}:{} min'.format(int(elapsed_time/60), int(elapsed_time%60))
        elif elapsed_time > 1:
            duration = '{:2.2f} s'.format(elapsed_time)
        else:
            duration = '{:d} ms'.format(int(elapsed_time * 1000))
        return duration

    def get_results_summary(self, tests):
        """Create a summary of the outcomes of all given tests."""

        failures = errors = skips = successes = 0
        for test in tests:
            outcome = test.outcome
            if outcome == test.ERROR:
                errors += 1
            elif outcome == test.FAILURE:
                failures += 1
            elif outcome == test.SKIP:
                skips += 1
            elif outcome == test.SUCCESS:
                successes += 1

        elapsed_time = 0
        for testinfo in tests:
            if not isinstance(testinfo, _SubTestInfos):
                elapsed_time += testinfo.elapsed_time
            else:
                for subtest in testinfo.subtests:
                    elapsed_time += subtest.elapsed_time

        results_summary = {
            "total": len(tests),
            "error": errors,
            "failure": failures,
            "skip": skips,
            "success": successes,
            "duration": self._format_duration(elapsed_time)
        }

        return results_summary

    def _get_header_info(self, tests, start_time, stop_time):
        results_summary = self.get_results_summary(tests)

        header_info = {
            "start_time": start_time,
            "status": results_summary,
            "stop_time": stop_time
        }
        return header_info

    def _get_report_summaries(self, all_results, testRunner):
        """ Generate headers and summaries for all given test cases."""
        summaries = {}
        for test_case_class_name, test_case_tests in all_results.items():
            summaries[test_case_class_name] = self.get_results_summary(test_case_tests)

        return summaries


    def generate_reports(self, testRunner):
        """ Generate report(s) for all given test cases that have been run. """
        status_tags = ('success', 'danger', 'warning', 'info')
        all_results = self._get_info_by_testcase()
        summaries = self._get_report_summaries(all_results, testRunner)
        report =self._generate_report(self.result)

        if not testRunner.combine_reports:
            # # ToDo Implementent
            for test_case_class_name, test_case_tests in all_results.items():
                header_info = self._get_header_info(test_case_tests, testRunner.start_time,
                                                    testRunner.start_time+ testRunner.time_taken)
                html_file = render_html(
                    testRunner.template,
                    title=testRunner.report_title,
                    header_info=header_info,
                    all_results={test_case_class_name: test_case_tests},
                    status_tags=status_tags,
                    summaries=summaries,
                    environ=environment.get_Environment(),
                    **testRunner.template_args
                )
                # append test case name if multiple reports to be generated
                if testRunner.report_name is None:
                    report_name_body = self.default_prefix + test_case_class_name
                else:
                    report_name_body = "{}_{}".format(testRunner.report_name, test_case_class_name)
                self.generate_file(testRunner, report_name_body, html_file)

        else:
            header_info = self._get_header_info(
                [item for sublist in all_results.values() for item in sublist],
                testRunner.start_time,
                testRunner.start_time + testRunner.time_taken
            )
            html_file = render_html(
                testRunner.template,
                title=testRunner.report_title,
                header_info=header_info,
                all_results=all_results,
                results = report,
                status_tags=status_tags,
                summaries=summaries,
                environ=environment.get_Environment(),
                **testRunner.template_args
            )
            # if available, use user report name
            if testRunner.report_name is not None:
                report_name_body = testRunner.report_name
            else:
                report_name_body = self.default_prefix + "_".join(strip_module_names(list(all_results.keys())))
            self.generate_file(testRunner, report_name_body, html_file)

    def generate_file(self, testRunner, report_name, report):
        """ Generate the report file in the given path. """
        dir_to = testRunner.output
        if not os.path.exists(dir_to):
            os.makedirs(dir_to)

        report_name += ".html"

        path_file = os.path.abspath(os.path.join(dir_to, report_name))
        self.stream.writeln(os.path.relpath(path_file))
        self.report_files.append(path_file)
        try:
            with open(path_file, 'w') as report_file:
                report_file.write(report)
        except UnicodeEncodeError:
            with open(path_file, 'wb') as report_file:
                report_file.write(report.encode('utf-8'))


    def _exc_info_to_string(self, err, test):
        """ Converts a sys.exc_info()-style tuple of values into a string."""
        # This comes directly from python2 unittest
        exctype, value, tb = err
        # Skip test runner traceback levels
        while tb and self._is_relevant_tb_level(tb):
            tb = tb.tb_next

        if exctype is test.failureException:
            # Skip assert*() traceback levels
            length = self._count_relevant_tb_levels(tb)
            msg_lines = traceback.format_exception(exctype, value, tb, length)
        else:
            msg_lines = traceback.format_exception(exctype, value, tb)

        if self.buffer:
            # Only try to get sys.stderr as it might not be
            # StringIO yet, e.g. when test fails during __call__
            try:
                error = sys.stderr.getvalue()
            except AttributeError:
                error = None
            if error:
                if not error.endswith('\n'):
                    error += '\n'
                msg_lines.append(error)
        # This is the extra magic to make sure all lines are str
        encoding = getattr(sys.stdout, 'encoding', 'utf-8')
        lines = []
        for line in msg_lines:
            if not isinstance(line, str):
                # utf8 shouldn't be hard-coded, but not sure f
                line = line.encode(encoding)
            lines.append(line)

        return ''.join(lines)

    def _generate_report(self, result):
        report = []
        sorted_result = sort_result(result)
        for cid, (cls, cls_results) in enumerate(sorted_result):
            rows = []
            # subtotal for a class
            np = nf = ne = ns = 0
            for n, t, o, e in cls_results:
                if n == 0:
                    np += 1
                elif n == 1:
                    nf += 1
                elif n == 2:
                    ne += 1
                elif n == 3:
                    ns += 1

            # format class description
            #if cls.__module__ == "__main__":
            name = cls.__name__
            #else:
            # name = "%s.%s" % (cls.__module__, cls.__name__)
            doc = cls.__doc__ and cls.__doc__.split("\n")[0] or ""
            desc = doc and '%s: %s' % (name, doc) or name
            if not PY3K:
                if isinstance(desc, str):
                    desc = desc.decode("utf-8")

            s = ne > 0 and 'errorClass' \
                or nf > 0 and 'failClass' \
                or ns > 0 and 'skipClass' \
                or 'passClass'

            rowheader = dict(
                style=s,
                desc=desc,
                count=np + nf + ne + ns,
                Pass=np,
                fail=nf,
                error=ne,
                skip=ns,
                cid='c%s' % (cid + 1),
            )

            for tid, (n, t, o, e) in enumerate(cls_results):
                self._generate_report_test(rows, cid, tid, n, t, o, e)
            report.append({'header':rowheader,'tests':rows})

        return report

    def _prep_desc(self,desc, classname=True):
        namelist = desc.split('.')
        if len(namelist) >= 3:
            if classname:
                name = namelist[-2] + ' - ' + namelist[-1]
            else:
                name = namelist[-1]
        else:
            name = ''.join(namelist[:-1])+')'
        return name

    def _generate_report_test(self, rows, class_id, test_id, n, t, output, e):
        # e.g. 'pt1.1', 'ft1.1', etc
        has_output = bool(output or e)

        # skipped
        if n == 3:
            name = self._prep_desc(t.id())
            test_id = 's' + 't%s.%s' \
                      % (class_id + 1, test_id + 1)
        # error
        elif n == 2:
            name = self._prep_desc(t.id())
            test_id = 'e' + 't%s.%s' \
                      % (class_id + 1, test_id + 1)
        # pass or fail
        else:
            name = self._prep_desc(t.id())
            test_id = (n == 0 and 'p' or 'f') + 't%s.%s' \
                                            % (class_id + 1, test_id + 1)
        doc = t.shortDescription() or ""
        desc = doc and ('%s: %s' % (name, doc)) or name

        if not PY3K:
            if isinstance(desc, str):
                desc = desc.decode("utf-8")
        # o and e should be byte string because
        # they are collected from stdout and stderr?
        if output is None:
            output = ""
        if isinstance(output, str):
            # TODO: some problem with 'string_escape':
            # it escape \n and mess up formatting
            if not PY3K:
                uo = output.decode('latin-1')
            else:
                uo = output
        else:
            uo = output
        if isinstance(e, str):
            # TODO: some problem with 'string_escape':
            # it escape \n and mess up formatting
            # ue = unicode(e.encode('string_escape'))
            if not PY3K:
                ue = e.decode('latin-1')
            else:
                ue = e
        else:
            ue = e

        script = dict(
            id=test_id,
            output=(uo.strip() + ue.strip()),
        )
        row = dict(
            tid=test_id,
            Class=(n == 0 and 'hiddenRow' or 'none'),
            style=n == 2 and 'bg-info' or (
                n == 1 and 'bg-danger' or n == 3 and 'bg-warning' or 'bg-success'),
            desc=desc,
            script=script,
            status=self.STATUS[n],
        )
        rows.append(row)
        return rows

    def _generate_ending(self):
        return self.ENDING_TEMPLATE


def sort_result(result_list):
    # unittest does not seems to run in any particular order.
    # Here at least we want to group them together by class.
    rmap = {}
    classes = []
    for n, t, o, e in result_list:
        cls = t.__class__
        if cls not in rmap:
            rmap[cls] = []
            classes.append(cls)
        rmap[cls].append((n, t, o, e))
    r = [(clazz, rmap[clazz]) for clazz in classes]
    return r