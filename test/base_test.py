import sys
import os
import time
import tempfile
import unittest
import shutil
import fcntl
import json
import logging
import inspect
import subprocess
import traceback
from datetime import datetime
from helper_func import save_logfiles, add_dependency, remove_dependency
from helper_ui import ui_class
from helper_gdrive import prepare_gdrive
from config_test import TEST_BASE, VENV_PYTHON, base_path, LOG_FILE_ENV, RESOURCE_DIR, REPORT_DIR
from selenium.common.exceptions import WebDriverException


os.makedirs(RESOURCE_DIR,exist_ok=True)
STATE_FILE = os.path.join(RESOURCE_DIR, "resources.json")
LOCK_FILE = os.path.join(RESOURCE_DIR, "resources.lock")

log_now = datetime.now().strftime("%H%M%S")
LOG_FILE = os.path.join(TEST_BASE, f"test_runner_{log_now}.log")


logger = logging.getLogger("calibre_web_test.test_runner")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    log_target = os.getenv(LOG_FILE_ENV, "").strip()
    if log_target:
        target_file = LOG_FILE if log_target.lower() in ("1", "true", "yes") else log_target
        handler = logging.FileHandler(target_file, encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False

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


def _build_initial_state():
    state = {}
    for pool_name, resources in RESOURCE_POOLS.items():
        state[pool_name] = {}
        for resource in resources:
            state[pool_name][str(resource)] = False
    return state


def _write_state(state):
    temp_file = f"{STATE_FILE}.{os.getpid()}.tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp_file, STATE_FILE)


def _read_state():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_log_context(owner=None, worker_id=None, class_name=None):
    resolved_worker_id = worker_id
    resolved_class_name = class_name

    if owner is not None:
        if resolved_class_name is None:
            resolved_class_name = owner.__name__ if isinstance(owner, type) else owner.__class__.__name__
        if resolved_worker_id is None:
            resolved_worker_id = getattr(owner, "worker_id", None)

    if resolved_class_name is None or resolved_worker_id is None:
        frame = inspect.currentframe()
        try:
            caller = frame.f_back if frame else None
            while caller:
                cls_obj = caller.f_locals.get("cls")
                if isinstance(cls_obj, type):
                    if resolved_class_name is None:
                        resolved_class_name = cls_obj.__name__
                    if resolved_worker_id is None:
                        resolved_worker_id = getattr(cls_obj, "worker_id", None)
                    break

                self_obj = caller.f_locals.get("self")
                if self_obj is not None:
                    if resolved_class_name is None:
                        resolved_class_name = self_obj.__class__.__name__
                    if resolved_worker_id is None:
                        resolved_worker_id = getattr(self_obj, "worker_id", None)
                    break
                caller = caller.f_back
        finally:
            del frame

    if resolved_worker_id is None:
        resolved_worker_id = os.getenv("TEST_WORKER_ID", "?")
    if resolved_class_name is None:
        resolved_class_name = "ResourceManager"

    return resolved_worker_id, resolved_class_name


def _log(message, owner=None, worker_id=None, class_name=None):
    resolved_worker_id, resolved_class_name = _resolve_log_context(owner, worker_id, class_name)
    now = datetime.now().strftime("%H:%M:%S")
    logger.info(f"[Worker {resolved_worker_id}] {now} - {resolved_class_name} {message}")


def log_message(message, owner=None, worker_id=None, class_name=None):
    _log(message, owner=owner, worker_id=worker_id, class_name=class_name)


# =========================================================
# INIT STATE
# =========================================================
def _init_state():
    lock = _lock_file(LOCK_FILE)
    try:
        if os.path.exists(STATE_FILE):
            try:
                _read_state()
                return
            except (json.JSONDecodeError, OSError):
                pass
        _write_state(_build_initial_state())
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


# =========================================================
# ACQUIRE RESOURCE
# =========================================================
def acquire_resource(pool_name, wait=True, retry_interval=1, owner=None, worker_id=None, class_name=None):
    _init_state()

    while True:
        lock = _lock_file(LOCK_FILE)
        try:
            try:
                state = _read_state()
            except (json.JSONDecodeError, OSError):
                _log(
                    "resource state empty/corrupt, rebuilding",
                    owner=owner,
                    worker_id=worker_id,
                    class_name=class_name,
                )
                state = _build_initial_state()
                _write_state(state)

            if pool_name not in state:
                raise RuntimeError(f"Unknown resource pool: {pool_name}")

            for resource, used in state[pool_name].items():
                if not used:
                    state[pool_name][resource] = True
                    _write_state(state)
                    # preserve int type for ports
                    try:
                        _log(
                            f"{pool_name}: {resource} acquired",
                            owner=owner,
                            worker_id=worker_id,
                            class_name=class_name,
                        )
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
def release_resource(pool_name, resource, owner=None, worker_id=None, class_name=None):
    _init_state()
    lock = _lock_file(LOCK_FILE)
    try:
        try:
            state = _read_state()
        except (json.JSONDecodeError, OSError):
            state = _build_initial_state()

        state[pool_name][str(resource)] = False
        _write_state(state)
        _write_state(state)
        _log(
            f"{pool_name}: {resource} released",
            owner=owner,
            worker_id=worker_id,
            class_name=class_name,
        )

    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()

class ParallelTestCase(unittest.TestCase, ui_class):

    _results = []
    _counter = 0
    _start = None
    _end = None
    _setup_failure_handled = False
    driver = None
    p = None
    tearDown_exceptions = []

    @classmethod
    def log_class(cls, message):
        _log(message, owner=cls)

    def log(self, message):
        _log(message, owner=self.__class__)

    @classmethod
    def _cleanup_driver_and_process(cls):
        driver = getattr(cls, "driver", None)
        if driver is not None:
            try:
                driver.quit()
            except Exception as cleanup_error:
                _log(f"Cleanup failed while closing WebDriver: {cleanup_error}", owner=cls)

        process = getattr(cls, "p", None)
        if process is not None:
            try:
                running = process.poll() is None
            except Exception as cleanup_error:
                running = True
                _log(f"Cleanup failed while checking application process: {cleanup_error}", owner=cls)

            if running:
                try:
                    process.terminate()
                except Exception as cleanup_error:
                    _log(f"Cleanup failed while stopping application process: {cleanup_error}", owner=cls)

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                    process.wait(timeout=5)
                except Exception as cleanup_error:
                    _log(f"Cleanup failed while killing application process: {cleanup_error}", owner=cls)
            except Exception as cleanup_error:
                _log(f"Cleanup failed while waiting for application process: {cleanup_error}", owner=cls)

    @classmethod
    def _handle_setup_failure(cls, error):
        if cls._setup_failure_handled:
            return
        cls._setup_failure_handled = True

        duration = time.time() - cls._start if cls._start is not None else 0
        details = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        cls._counter += 1
        _log(f"{cls.__name__}.setUpClass: ERROR ({duration:.2f}s)", owner=cls)
        _log(f"Setup failure:\n{details}", owner=cls)
        cls._results.append({
            "tid": cls._counter,
            "result": "ERROR",
            "desc": f"{cls.__name__} - setUpClass",
            "duration_seconds": f"{duration:.3f}",
            "output": details,
        })

        for attribute, methods in (
                ("email_server", ("stop",)),
                ("server", ("stop_LdapServer",)),
                ("proxy", ("stop", "stop_proxy"))):
            resource = getattr(cls, attribute, None)
            if resource is None:
                continue
            cleanup = next((getattr(resource, method, None) for method in methods
                            if callable(getattr(resource, method, None))), None)
            if cleanup is not None:
                try:
                    cleanup()
                except Exception as cleanup_error:
                    _log(f"Cleanup failed while stopping {attribute}: {cleanup_error}", owner=cls)

        extra_port = getattr(cls, "port", None)
        worker_port = getattr(cls, "worker_port", None)
        if extra_port is not None and str(extra_port) != str(worker_port):
            try:
                release_resource("port", extra_port, owner=cls)
            except Exception as cleanup_error:
                _log(f"Cleanup failed while releasing port {extra_port}: {cleanup_error}", owner=cls)

        cls._cleanup_driver_and_process()

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
        cls._results = []
        cls._counter = 0
        cls._start = time.time()
        cls._end = None
        cls._setup_failure_handled = False
        cls.driver = None
        cls.p = None
        cls.worker_id = None
        cls.py_resource = None
        cls.py_version = None
        cls.worker_port = None
        cls.port = None
        cls.temp_dir = None
        cls.app_dir = None
        cls.gdrive_file = None

        try:
            super().setUpClass()

            cls.worker_id = int(os.getenv("TEST_WORKER_ID", "0"))
            cls.py_resource = acquire_resource("venv", owner=cls)
            cls.py_version = os.path.join(cls.py_resource, VENV_PYTHON)
            cls.worker_port = str(acquire_resource("port", owner=cls))

            _log("start Testing", owner=cls)
            _log(f"running on {cls.py_resource}", owner=cls)
            _log(f"using port {cls.worker_port}", owner=cls)

            cls.temp_dir = tempfile.mkdtemp(prefix=f"cw_test_worker_{cls.worker_id}_", dir=os.path.join(TEST_BASE, "target"))
            cls.app_dir = tempfile.mkdtemp(prefix=f"cw_app_{cls.worker_id}_", dir=os.path.join(TEST_BASE, "target"))

            # CLASS LEVEL LOCK
            if getattr(cls, "resource_lock", None):
                _log(f"LOCK WAIT {cls.resource_lock}", owner=cls)
                cls.gdrive_file = acquire_resource("gdrive", cls.resource_lock, owner=cls)
                _log(f"LOCK ACQUIRED {cls.resource_lock}", owner=cls)
                _log("preparing GDrive", owner=cls)
                prepare_gdrive()
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

            if hasattr(cls, "dependency"):
                add_dependency(cls.py_version, cls.dependency, cls.__name__, cls.worker_id)
        except Exception as error:
            cls._handle_setup_failure(error)
            raise

    def run(self, result=None):

        name = self._testMethodName
        start = time.time()

        try:

            super().run(result)

            duration = time.time() - start

            matching_failures = [tb for t, tb in result.failures if t == self]
            if matching_failures:
                self._add("FAIL", name, duration, matching_failures[0])
                return

            matching_errors = [tb for t, tb in result.errors if t == self]
            if matching_errors:
                self._add("ERROR", name, duration, matching_errors[0])
                return

            matching_skipped = [reason for t, reason in result.skipped if t == self]
            if matching_skipped:
                self._add("SKIP", name, duration, matching_skipped[0])
                return

            self._add("SUCCESS", name, duration)

        except Exception as e:
            self._add("ERROR", name, time.time() - start, str(e))
            _log("unexpected exception in run()", owner=self.__class__)
            raise

    def _add(self, status, name, duration, extra=""):
        self.__class__._counter += 1
        _log(f"{self.__class__.__name__}.{name}: {status} ({duration:.2f}s)", owner=self.__class__)
        if extra != "":
            _log(f"{extra}", owner=self.__class__)
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
            driver = getattr(cls, "driver", None)
            if driver is not None:
                try:
                    driver.get("http://127.0.0.1:" + cls.worker_port)
                except Exception as e:
                    _log(f"Class teardown failed while loading the application: {e}", owner=cls)
                try:
                    cls.stop_calibre_web()
                except Exception as e:
                    _log(f"Class teardown failed while stopping the application: {e}", owner=cls)
            cls._cleanup_driver_and_process()
        super().tearDownClass()

    @classmethod
    def doClassCleanups(cls):
        if cls._start is None:
            super().doClassCleanups()
            return

        def run_cleanup(description, cleanup):
            try:
                cleanup()
            except Exception as error:
                _log(f"{description}: {error}", owner=cls)

        try:
            if cls.app_dir is not None:
                _log("saving logbooks", owner=cls)
                run_cleanup("Failed to save logbooks", lambda: save_logfiles(cls, cls.__name__))

            if cls.worker_port is not None:
                run_cleanup(
                    f"Failed to release port {cls.worker_port}",
                    lambda: release_resource("port", cls.worker_port, owner=cls),
                )
            if cls.gdrive_file is not None:
                run_cleanup(
                    f"Failed to release GDrive lock {cls.resource_lock}",
                    lambda: release_resource("gdrive", cls.gdrive_file, owner=cls),
                )

            if cls.py_version is not None and hasattr(cls, "dependency"):
                _log("remove dependecies", owner=cls)
                run_cleanup(
                    "Failed to remove dependencies",
                    lambda: remove_dependency(cls.py_version, cls.dependency),
                )

            if cls.py_version is not None and hasattr(cls, "hidden_dependency"):
                _log("remove hidden dependecies", owner=cls)
                run_cleanup(
                    "Failed to remove hidden dependencies",
                    lambda: remove_dependency(cls.py_version, cls.hidden_dependency),
                )

            if cls.temp_dir is not None:
                run_cleanup("Failed to remove temporary test directory",
                            lambda: shutil.rmtree(cls.temp_dir, ignore_errors=True))

            if cls.app_dir is not None:
                run_cleanup("Failed to remove temporary application directory",
                            lambda: shutil.rmtree(cls.app_dir, ignore_errors=True))
            if cls.py_resource is not None:
                run_cleanup(
                    f"Failed to release venv {cls.py_resource}",
                    lambda: release_resource("venv", cls.py_resource, owner=cls),
                )

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
            _log(
                f"FINISHED Tests: {total} (Pass:{success} Fail:{fail} Error:{error} Skip:{skip})",
                owner=cls,
            )
            name_class = f"{cls.__module__}.{cls.__name__}"
            _log(
                f"Testresult: Start: {data[name_class]['start_time']} Duration {data[name_class]['duration']}s",
                owner=cls,
            )
            target_path = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
            filename = os.path.join(target_path, REPORT_DIR, f"{cls.__name__}.json")

            def write_report():
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            run_cleanup(f"Failed to write test report {filename}", write_report)
        except Exception as e:
            _log(f"Failed while finalizing test class: {e}", owner=cls)
        finally:
            super().doClassCleanups()