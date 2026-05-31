import sys
import os
import time
import re
import tempfile
import unittest
import shutil
import fcntl
import json
from datetime import datetime
from helper_func import save_logfiles, add_dependency, remove_dependency
from helper_ui import ui_class
from helper_gdrive import prepare_gdrive
from config_test import TEST_BASE, VENV_PYTHON, base_path
from selenium.common.exceptions import WebDriverException

RESOURCE_DIR = "/tmp/calibre_web_test_resources"
os.makedirs(RESOURCE_DIR,exist_ok=True)

STATE_FILE = os.path.join(RESOURCE_DIR, "resources.json")
LOCK_FILE = os.path.join(RESOURCE_DIR, "resources.lock")

REPORT_DIR = "test_reports"

# =========================================================
# CONFIGURE RESOURCES HERE
# =========================================================

RESOURCE_POOLS = {
    "venv": [                           # virtual environments
        TEST_BASE + "venv_1",
        TEST_BASE + "venv_2",
        TEST_BASE + "venv_3",
        TEST_BASE + "venv_4",
    ],
    "gdrive": [                         # gdrive accounts
        "gdrive_account_1",
    ],
    "port": list(range(8000, 8150)),     # ports
}


# LOCK FILE
def _lock_file(path):
    f = open(path, "a+")
    fcntl.flock(f, fcntl.LOCK_EX)
    return f


# =========================================================
# INIT STATE
# =========================================================
def _init_state():
    if os.path.exists(STATE_FILE):
        return
    state = {}

    for pool_name, resources in RESOURCE_POOLS.items():
        state[pool_name] = {}
        for resource in resources:
            state[pool_name][str(resource)] = False

        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)


# =========================================================
# ACQUIRE RESOURCE
# =========================================================
def acquire_resource(pool_name, wait=True, retry_interval=1):
    _init_state()

    while True:
        lock = _lock_file(LOCK_FILE)
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)

            if pool_name not in state:
                raise RuntimeError(f"Unknown resource pool: {pool_name}")

            for resource, used in state[pool_name].items():
                if not used:
                    state[pool_name][resource] = True

                    with open(STATE_FILE, "w") as f:
                        json.dump(state, f, indent=4)

                    # preserve int type for ports
                    try:
                        return int(resource)
                    except ValueError:
                        return resource
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
            lock.close()
        # -------------------------------------
        # no free resource
        # -------------------------------------
        if not wait:
            raise RuntimeError(f"No free resource in pool {pool_name}")

        time.sleep(retry_interval)


# =========================================================
# RELEASE RESOURCE
# =========================================================
def release_resource(pool_name, resource):
    _init_state()
    lock = _lock_file(LOCK_FILE)
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)

        state[pool_name][str(resource)] = False

        with open(STATE_FILE, "w") as f:

            json.dump(state, f, indent=4)

        # print(f"[RESOURCE RELEASED] {pool_name}: {resource}")

    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()

class ParallelTestCase(unittest.TestCase, ui_class):

    _results = []
    _counter = 0
    _start = None
    _end = None
    driver = None
    p = None
    tearDown_exceptions = []

    def __init__(self, tests):
        main_module = sys.modules["__main__"]
        if "_jb_unittest_runner.py" in main_module.__file__:
            if os.path.exists(STATE_FILE):
                os.unlink(STATE_FILE)
            if os.path.exists(LOCK_FILE):
                os.unlink(LOCK_FILE)

        super().__init__(tests)

    @classmethod
    def setUpClass(cls):

        super().setUpClass()


        cls._results = []
        cls._counter = 0
        cls._start = time.time()

        cls.py_resource = acquire_resource("venv")
        cls.py_version = os.path.join(cls.py_resource, VENV_PYTHON)

        cls.worker_id = int(os.getenv("TEST_WORKER_ID", "0"))
        cls.worker_port = str(acquire_resource("port"))

        now = datetime.now().strftime("%H:%M:%S")
        print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} start Testing")
        print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} running on {cls.py_resource}")
        print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} using port {cls.worker_port}")

        cls.temp_dir = tempfile.mkdtemp(prefix=f"cw_test_worker_{cls.worker_id}_", dir=os.path.join(TEST_BASE, "target"))
        cls.app_dir = tempfile.mkdtemp(prefix=f"cw_app_{cls.worker_id}_", dir=os.path.join(TEST_BASE, "target"))

        # CLASS LEVEL LOCK
        cls.gdrive_file = None
        if getattr(cls, "resource_lock", None):
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} LOCK WAIT {cls.resource_lock}")
            cls.gdrive_file = acquire_resource("gdrive", cls.resource_lock)
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} LOCK ACQUIRED {cls.resource_lock}")
            print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} preparing GDrive")
            prepare_gdrive()
            try:
                src = os.path.join(base_path, "files", "client_secrets.json")
                dst = os.path.join(cls.app_dir, "client_secrets.json")
                os.chmod(src, 0o764)
                if os.path.exists(dst):
                    os.unlink(dst)
                shutil.copy(src, dst)

                # delete settings_yaml file
                set_yaml = os.path.join(cls.app_dir, "settings.yaml")
                if os.path.exists(set_yaml):
                    os.unlink(set_yaml)

                # delete gdrive file
                gdrive_db = os.path.join(cls.app_dir, "gdrive.db")
                if os.path.exists(gdrive_db):
                    os.unlink(gdrive_db)

                # delete gdrive authenticated file
                src = os.path.join(base_path, 'files', "gdrive_credentials")
                dst = os.path.join(cls.app_dir, "gdrive_credentials")
                os.chmod(src, 0o764)
                if os.path.exists(dst):
                    os.unlink(dst)
                shutil.copy(src, dst)
            except Exception as e:
                pass

        if hasattr(cls, "dependency"):
            add_dependency(cls.py_version, cls.dependency, cls.__name__, cls.worker_id)

    def run(self, result=None):

        name = self._testMethodName
        start = time.time()

        try:

            super().run(result)

            duration = time.time() - start

            if any(t == self for t, _ in result.failures):
                self._add("FAIL", name, duration, result.failures)
                return

            if any(t == self for t, _ in result.errors):
                self._add("ERROR", name, duration, result.errors)
                return

            if any(t == self for t, _ in result.skipped):
                self._add("SKIP", name, duration)
                return

            self._add("SUCCESS", name, duration)

        except Exception as e:
            self._add("ERROR", name, time.time() - start, str(e))
            print("huhu")
            raise

    def _add(self, status, name, duration, extra=""):
        if isinstance(extra, list):
            extra = str(extra[0][1])
        self.__class__._counter += 1
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[Worker {self.worker_id}] {now} - {self.__class__.__name__}.{name}: {status} ({duration:.2f}s)")
        if extra != "":
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[Worker {self.worker_id}] {now} - {extra}")
        self.__class__._results.append({
            "tid": self.__class__._counter,
            "result": status,
            "desc": f"{self.__class__.__name__} - {name}",
            "duration_seconds": f"{duration:.3f}",
            "output": extra,
        })

    def tearDown(self):
        if hasattr(self, "driver"):
            if self.driver:
                if "problem loading" in self.driver.title.lower():
                    try:
                        self.driver.refresh()  # reload page
                    except WebDriverException:
                        pass

    @classmethod
    def tearDownClass(cls, no=False):
        if not no:
            try:
                # close the browser window and stop calibre-web
                cls.driver.get("http://127.0.0.1:" + cls.worker_port)
                cls.stop_calibre_web()
                cls.driver.quit()
                cls.p.terminate()
            except Exception as e:
                print(e)
        super().tearDownClass()

    @classmethod
    def doClassCleanups(cls):
        try:
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} saving logbooks")
            save_logfiles(cls, cls.__name__)

            print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} RESOURCE released port:{cls.worker_port}")
            release_resource("port", cls.worker_port)

            # release class level lock
            if hasattr(cls, "resource_lock"):
                now = datetime.now().strftime("%H:%M:%S")
                print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} LOCK RELEASED {cls.resource_lock}")
                release_resource("gdrive", cls.gdrive_file)

            if hasattr(cls, "dependency"):
                now = datetime.now().strftime("%H:%M:%S")
                print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} remove dependecies")
                remove_dependency(cls.py_version, cls.dependency)

            if hasattr(cls, "temp_dir"):
                shutil.rmtree(cls.temp_dir, ignore_errors=True)

            if hasattr(cls, "app_dir"):
                shutil.rmtree(cls.app_dir, ignore_errors=True)
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} RESOURCE released venv:{cls.py_resource}")
            release_resource("venv", cls.py_resource)

            cls._end = time.time()
            total = len(cls._results)

            fail = sum(1 for x in cls._results if x["result"] == "FAIL")
            error = sum(1 for x in cls._results if x["result"] == "ERROR")
            skip = sum(1 for x in cls._results if x["result"] == "SKIP")
            success = sum(1 for x in cls._results if x["result"] == "SUCCESS")

            data = {
                f"{cls.__module__}.{cls.__name__}": {
                    "start_time": datetime.fromtimestamp(cls._start).strftime("%H:%M:%S"),
                    "end_time": datetime.fromtimestamp(cls._end).strftime("%H:%M:%S"),
                    "duration": f"{(cls._end - cls._start):.2f}",
                    "tests": cls._results,
                    "stats": {
                        "total": total,
                        "pass": success,
                        "fail": fail,
                        "error": error,
                        "skip": skip,
                    }
                }
            }
            now = datetime.now().strftime("%H:%M:%S")
            print(
                f"[Worker {cls.worker_id}] {now} - {cls.__name__} FINISHED "
                f"Tests: {total} (Pass:{success} Fail:{fail} Error:{error} Skip:{skip})"
            )
            name_class = f"{cls.__module__}.{cls.__name__}"
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[Worker {cls.worker_id}] {now} - {cls.__name__} Testresult: Start: {data[name_class]['start_time']} Duration {data[name_class]['duration']}s")
            target_path = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
            filename = os.path.join(target_path, REPORT_DIR, f"{cls.__name__}.json")

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

        except Exception as e:
            print(e)