#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import re
from config_test import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME, VENV_PYTHON
from selenium.webdriver.support.ui import WebDriverWait
from subproc_wrapper import process_open
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import socket
import errno
import psutil
from helper_environment import environment
from psutil import process_iter
import os
import sys
import socket

if os.name != 'nt':
    from signal import SIGKILL
else:
    from signal import SIGTERM as SIGKILL

try:
    import pycurl
    from io import BytesIO
    curl_available = True
except ImportError:
    pycurl = None
    BytesIO = None
    curl_available = False


def is_port_in_use(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    except socket.error as e:
        if e.errno == errno.EADDRINUSE:
            return True
        else:
            return False
    s.close()
    return False


# Function to return IP address
def get_Host_IP():
    if os.name!='nt':
        addrs = psutil.net_if_addrs()
        for ele, key in enumerate(addrs):
            if key != 'lo':
                if addrs[key][0][2]:
                    return addrs[key][0][1]
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP


def debug_startup(inst, __, ___, login=True, host="http://127.0.0.1:8083", env=None):

    # create a new Firefox session
    inst.driver = webdriver.Firefox()

    inst.driver.implicitly_wait(BOOT_TIME)

    inst.driver.maximize_window()

    # navigate to the application home page
    inst.driver.get(host)

    inst.login("admin", "admin123")
    # login
    if not login:
        inst.logout()


def startup(inst, pyVersion, config, login=True, host="http://127.0.0.1:8083", env=None, only_startup=False):
    print("\n%s - %s: " % (inst.py_version, inst.__name__))
    try:
        os.remove(os.path.join(CALIBRE_WEB_PATH, 'app.db'))
    except Exception:
        pass
    try:
        os.chmod(TEST_DB, 0o764)
    except Exception:
        pass
    shutil.rmtree(TEST_DB, ignore_errors=True)
    shutil.copytree('./Calibre_db', TEST_DB)
    inst.p = process_open([pyVersion, os.path.join(CALIBRE_WEB_PATH, u'cps.py')], [1], sout=None, env=env)

    # create a new Firefox session
    inst.driver = webdriver.Firefox()
    # inst.driver = webdriver.Chrome()
    inst.driver.implicitly_wait(BOOT_TIME)
    time.sleep(1)
    if inst.p.poll():
        kill_old_cps()
        inst.p = process_open([pyVersion, os.path.join(CALIBRE_WEB_PATH, u'cps.py')], [1], sout=None, env=env)
        print('Calibre-Web restarted...')
        time.sleep(BOOT_TIME)

    inst.driver.maximize_window()

    # navigate to the application home page
    inst.driver.get(host)

    if not only_startup:
        # Wait for config screen to show up
        inst.fill_initial_config(dict(config_calibre_dir=config['config_calibre_dir']))
        del config['config_calibre_dir']

        # wait for cw to reboot
        time.sleep(BOOT_TIME)

        # Wait for config screen with login button to show up
        WebDriverWait(inst.driver, 5).until(EC.presence_of_element_located((By.NAME, "login")))
        login_button = inst.driver.find_element_by_name("login")
        login_button.click()
        inst.login("admin", "admin123")
        if config:
            inst.fill_basic_config(config)
        time.sleep(BOOT_TIME)
        # login
        if not login:
            inst.logout()


def wait_Email_received(func):
    i = 0
    while i < 10:
        if func():
            return True
        time.sleep(2)
        i += 1
    return False


def check_response_language_header(url, header, expected_response, search_text):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(pycurl.HTTPHEADER, header)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    if c.getinfo(c.RESPONSE_CODE) != expected_response:
        return False
    c.close()

    body = buffer.getvalue().decode('utf-8')
    return bool(re.search(search_text, body))


def digest_login(url, expected_response):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(pycurl.HTTPHEADER,
             ["Authorization: Digest username=\"admin\", "
              "realm=\"calibre\", "
              "nonce=\"40f00b48437860f60066:9bcc076210c0bbc2ebc9278fbba05716bcc55e09daa59f53b9ebe864635cf254\", "
              "uri=\"/config\", algorithm=MD5, response=\"c3d1e34c67fd8b408a167ca61b108a30\", "
              "qop=auth, nc=000000c9, cnonce=\"2a216b9b9c1b1108\""])
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    if c.getinfo(c.RESPONSE_CODE) != expected_response:
        c.close()
        return False
    c.close()
    return True


def add_dependency(name, testclass_name):
    element_version = list()
    with open(os.path.join(CALIBRE_WEB_PATH, 'optional-requirements.txt'), 'r') as f:
        requirements = f.readlines()
    for element in name:
        for line in requirements:
            if element.lower().startswith('git|') \
                    and not line.startswith('#') \
                    and not line == '\n' \
                    and line.lower().startswith('git') \
                    and line.lower().endswith('#egg=' + element.lower().lstrip('git|')+'\n'):
                element_version.append(line.strip('\n'))
            elif not line.startswith('#') \
                    and not line == '\n' \
                    and not line.startswith('git') \
                    and line.upper().startswith(element.upper()):
                element_version.append(line.split('=', 1)[0].strip('>'))
                break

    for indx, element in enumerate(element_version):
        with process_open([VENV_PYTHON, "-m", "pip", "install", element], (0, 5)) as r:
            if os.name == 'nt':
                while r.poll() == None:
                    print(r.stdout.readline())
            else:
                r.wait()
        if element.lower().startswith('git'):
            element_version[indx] = element[element.rfind('#egg=')+5:]

    environment.add_Environment(testclass_name, element_version)


def remove_dependency(names):
    for name in names:
        if name.startswith('git|'):
            name = name[4:]
        with process_open([VENV_PYTHON, "-m", "pip", "uninstall", "-y", name], (0, 5)) as q:
            if os.name == 'nt':
                while q.poll() == None:
                    print(q.stdout.readline())
            else:
                q.wait()


def kill_old_cps(port=8083):
    for proc in process_iter():
        try:
            for conns in proc.connections(kind='inet'):
                if conns.laddr.port == port:
                    proc.send_signal(SIGKILL)  # or SIGKILL
                    print('Killed old Calibre-Web instance')
                    break
        except (PermissionError, psutil.AccessDenied):
            pass


def unrar_path():
    if sys.platform == "win32":
        unrar_pth = ["C:\\program files\\WinRar\\unrar.exe", "C:\\program files(x86)\\WinRar\\unrar.exe"]
    else:
        unrar_pth = ["/usr/bin/unrar"]
    for element in unrar_pth:
        if os.path.isfile(element):
            return element
    return None


def is_unrar_not_present():
    return unrar_path() is None
