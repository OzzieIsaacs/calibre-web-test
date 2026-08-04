import argparse
import importlib
import multiprocessing
import os
import re
import datetime
import pkgutil
import sys
import glob
import unittest
import shutil
import json
import virtualenv
import io

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(ROOT_DIR, "test")
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, TEST_DIR)

from test.subproc_wrapper import process_open
from test.base_test import RESOURCE_DIR, RESOURCE_POOLS, REPORT_DIR
from test.config_test import CALIBRE_WEB_PATH, VENV_PYTHON, TEST_BASE
from test.helper_certificate import generate_ssl_testing_files
from test.helper_func import poweroff, finishing_notifier, result_move
from test.helper_environment import environment
from combine_results import combine_reports, OUTPUT_FILE, INPUT_DIR


TEST_PACKAGE = "test"
BASE_PORT = 8083


# =========================================================
# DISCOVERY
# =========================================================
def discover_test_modules():
    package = importlib.import_module(TEST_PACKAGE)
    modules = []
    for _, module_name, is_pkg in pkgutil.walk_packages(
        package.__path__,
        package.__name__ + "."
    ):
        if is_pkg:
            continue
        if not module_name.split(".")[-1].startswith("test"):
            continue
        modules.append(module_name)
    return modules


def discover_test_classes():
    discovered = []
    for module_name in discover_test_modules():
        module = importlib.import_module(module_name)
        for name in dir(module):
            obj = getattr(module, name)
            if not isinstance(obj, type):
                continue
            if not issubclass(obj, unittest.TestCase):
                continue
            if obj is unittest.TestCase:
                continue
            # skip your abstract/base test class
            if obj.__name__ == "ParallelTestCase":
                continue
            discovered.append((module_name, name))
    return discovered


# =========================================================
# WORKER
# =========================================================
def run_test_class(args):

    module_name, class_name, worker_id = args

    try:

        os.environ["TEST_WORKER_ID"] = str(worker_id)
        os.environ["TEST_PORT"] = str(BASE_PORT + worker_id)
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[Worker {worker_id}] {now} - {class_name} starting")

        # -------------------------------------------------
        # LOAD TEST CLASS
        # -------------------------------------------------
        module = importlib.import_module(module_name)

        test_class = getattr(module, class_name)

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(test_class)
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[Worker {worker_id}] {now} - {class_name} found {suite.countTestCases()} tests")
        silent_stream = io.StringIO()
        result = unittest.TextTestRunner(verbosity=0, stream=silent_stream).run(suite)
        success = result.wasSuccessful()
        error_holders = [(test, err) for test, err in result.errors if isinstance(test, unittest.suite._ErrorHolder)]

        if error_holders:
            target_path = os.path.abspath(os.path.join(os.path.dirname(__file__)))
            report_file = os.path.join(target_path, REPORT_DIR, f"{class_name}.json")
            with open(report_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            dict_key = next(iter(data))
            data[dict_key]['stats']['error'] += 1
            tid = 1
            for element in data[dict_key]['tests']:
                tid = max(element['tid'], tid)
            addtional_data = {
                            "tid": tid + 1,
                            "result": "ERROR",
                            "duration_seconds": "41.517",
                            "desc": f"{class_name} - {result.errors[0][0].__class__.__name__}",
                            "output": result.errors[0][1]
                        }
            data[dict_key]['tests'].append(addtional_data)

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        return {
            "module": module_name,
            "class": class_name,
            "success": success,
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
        }

    except Exception as e:
        return {
            "module": module_name,
            "class": class_name,
            "success": False,
            "error": str(e),
        }


# =========================================================
# MAIN
# =========================================================
def main():
    sub_dependencies = ["Werkzeug", "Jinja2", "singledispatch"]

    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    # parser.add_argument("--nopoweroff", type=int, default=1)
    args = parser.parse_args()

    power = 1 # input('Power off after finishing tests? [y/N]').lower() == 'y'
    if power:
        print('!!!! PC will shutdown after tests finished !!!!')
    # check pip ist installed
    found = False
    pversion = ["python3.12", "python3", "c:\\python312\\python.exe", "c:\\python310\\python.exe"]
    for python in pversion:
        try:
            p = process_open([python, "-m", "pip", "-V"])
        except (FileNotFoundError, Exception):
            print("{} not found".format(python))
            continue
        p.wait(timeout=2)
        res = p.communicate(timeout=10)
        try:
            pip = re.match(r"pip\s(.*)\sfrom\s(.*)\s\((.*)\).*", res[0])
        except IndexError:
            continue
        except TypeError:
            pip = re.match(r"pip\s(.*)\sfrom\s(.*)\s\((.*)\).*", res[0].decode('utf-8'))
        if pip:
            print("Found Pip for {} in {}".format(pip[3],pip[2]))
            found = True
            break
        else:
            print("Pip not found, can't setup test environment")

    if not found:
        print("Pip not found, can't setup test environment")
        exit()

    # delete cache folders
    for folder in glob.iglob(CALIBRE_WEB_PATH + "/cps/**/__pycache__/", recursive=True):
        shutil.rmtree(folder, ignore_errors=True)

    requirements_file = os.path.join(CALIBRE_WEB_PATH, 'requirements.txt')

    venv_pip = ""
    # generate virtual environments
    for venv_path in RESOURCE_POOLS['venv']:
        print(f"Creating virtual environment {venv_path} for testing")
        virtualenv.cli_run([venv_path, "--clear"])
        # venv.create(venv_path, system_site_packages=True, with_pip=False)
        venv_pip = os.path.join(venv_path, VENV_PYTHON)
        p = process_open([venv_pip, "-m", "pip", "install", "-r", requirements_file], (0, 5))
        if os.name == 'nt':
            while p.poll() is None:
                p.stdout.readline()
        else:
            p.wait()
    environment.init_environment(venv_pip, sub_dependencies)

    # discover tests
    discovered = discover_test_classes()

    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[System] {now} - Found {len(discovered)} test classes")
    tasks = []

    for index, (module_name, class_name) in enumerate(discovered):
        worker_id = index % args.workers
        tasks.append((module_name, class_name, worker_id,))

    with multiprocessing.Pool(processes=args.workers) as pool:
        results = pool.map(run_test_class,tasks,)

    print("\n====================")
    print("FINAL RESULTS")
    print("====================")
    print("\nAll tests finished, please check test results")

    failed = False

    for r in results:

        status = "OK" if r["success"] else "FAILED"

        print(f"{status} | {r['module']}.{r['class']}")

        if not r["success"]:
            failed = True

    html_file = combine_reports()
    # E-Mail tests finished
    result_json = os.path.join(os.path.join(os.path.dirname(__file__), OUTPUT_FILE))

    finishing_notifier(html_file)
    if os.path.isfile(result_json):
        result_move(result_json)
    poweroff(power)

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    generate_ssl_testing_files()
    shutil.rmtree(RESOURCE_DIR, ignore_errors=True)
    shutil.rmtree(os.path.join(TEST_BASE, "target"), ignore_errors=True)
    os.makedirs(os.path.join(TEST_BASE, "target"))
    multiprocessing.set_start_method("spawn", force=True)
    main()