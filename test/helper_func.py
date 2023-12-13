#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shutil
import re
import mimetypes
from config_test import CALIBRE_WEB_PATH, TEST_DB, BOOT_TIME, VENV_PYTHON, base_path, TEST_OS
from selenium.webdriver.support.ui import WebDriverWait
from subproc_wrapper import process_open
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import errno
import psutil
from helper_environment import environment
from psutil import process_iter
import os
import sys
import socket
import importlib
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import zipfile
from bs4 import BeautifulSoup
import codecs
from io import StringIO

try:
    import pdfkit
    convert_config = True
except ImportError:
    convert_config = False
try:
    from config_email import E_MAIL_ADDRESS, E_MAIL_SERVER_ADDRESS, STARTSSL, EMAIL_SERVER_PORT
    from config_email import E_MAIL_LOGIN, E_MAIL_PASSWORD
    if E_MAIL_ADDRESS != '' and E_MAIL_SERVER_ADDRESS != '' and E_MAIL_LOGIN != '' and E_MAIL_PASSWORD != '':
        email_config = True
    else:
        email_config = False
        print('config_email.py E-Mail not configured')
except ImportError:
    email_config = False

try:
    from config_email import SERVER_PASSWORD, SERVER_NAME, SERVER_FILE_DESTINATION, SERVER_USER, SERVER_PORT
    if SERVER_PASSWORD != '' and SERVER_NAME != '' and SERVER_FILE_DESTINATION != '' and SERVER_USER != '':
        server_config = True
    else:
        print('config_email.py Server not configured')
        server_config = False
except ImportError:
    server_config = False

try:
    from config_email import SERVER_MOVE
    move_config = True
except ImportError:
    move_config = False

try:
    import paramiko
except ImportError:
    print('Create config_email.py file to email finishing message')
    server_config = False

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
    if os.name != 'nt':
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


def debug_startup(inst, __, ___, login=True, host="http://127.0.0.1", port="8083", env=None):

    # create a new Firefox session
    inst.driver = webdriver.Firefox()
    inst.driver.implicitly_wait(BOOT_TIME)
    inst.driver.maximize_window()

    # navigate to the application home page
    inst.driver.get(host)
    WebDriverWait(inst.driver, 5).until(EC.title_contains("Calibre-Web"))
    inst.login("admin", "admin123")
    # login
    if not login:
        inst.logout()


def startup(inst, pyVersion, config, login=True, host="http://127.0.0.1", port="8083", index = "",
            env=None, parameter=None, work_path=None, only_startup=False, only_metadata=False):
    print("\n%s - %s: " % (inst.py_version, inst.__name__))
    try:
        os.remove(os.path.join(CALIBRE_WEB_PATH + index, 'app.db'))
    except PermissionError:
        kill_dead_cps()
        time.sleep(5)
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH + index, 'app.db'))
        except Exception as e:
            print(e)
    except Exception as ex:
        print(ex)
    try:
        os.remove(os.path.join(CALIBRE_WEB_PATH + index, 'gdrive.db'))
    except PermissionError:
        time.sleep(5)
        try:
            os.remove(os.path.join(CALIBRE_WEB_PATH + index, 'gdrive.db'))
        except Exception as e:
            print(e)
    except Exception as ex:
        print(ex)
    try:
        os.chmod(TEST_DB + index, 0o764)
    except Exception:
        pass
    shutil.rmtree(TEST_DB + index, ignore_errors=True)

    thumbail_cache_path = os.path.join(CALIBRE_WEB_PATH + index, 'cps', 'cache')
    try:
        os.chmod(thumbail_cache_path, 0o764)
    except Exception:
        pass
    shutil.rmtree(thumbail_cache_path, ignore_errors=True)

    if not only_metadata:
        try:
            shutil.copytree(os.path.join(base_path, 'Calibre_db'), TEST_DB + index)
        except FileExistsError:
            print('Test DB already present, might not be a clean version')
    else:
        try:
            os.makedirs(TEST_DB)
            shutil.copy(os.path.join(base_path, 'Calibre_db', 'metadata.db'), os.path.join(TEST_DB + index, 'metadata.db'))
        except FileExistsError:
            print('Metadata.db already present, might not be a clean version')
    command = [pyVersion, os.path.join(CALIBRE_WEB_PATH + index, u'cps.py')]
    if parameter:
        command.extend(parameter)
    inst.p = process_open(command, [1], sout=None, env=env, cwd=work_path)
    # create a new Firefox session
    inst.driver = webdriver.Firefox()
    # inst.driver = webdriver.Chrome()
    time.sleep(BOOT_TIME)
    if inst.p.poll():
        kill_old_cps()
        inst.p = process_open(command, [1], sout=None, env=env, cwd=work_path)
        print('Calibre-Web restarted...')
        time.sleep(BOOT_TIME)

    inst.driver.maximize_window()

    # navigate to the application home page
    inst.driver.get(host + ":" + port)
    WebDriverWait(inst.driver, 5).until(EC.title_contains("Calibre-Web"))
    if not only_startup:
        # Wait for config screen to show up
        inst.fill_db_config(dict(config_calibre_dir=config['config_calibre_dir']))
        del config['config_calibre_dir']

        # wait for cw to reboot
        time.sleep(5)
        try:
            WebDriverWait(inst.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        except Exception:
            pass

        if config:
            inst.fill_basic_config(config)
        time.sleep(BOOT_TIME)
        try:
            WebDriverWait(inst.driver, 5).until(EC.presence_of_element_located((By.ID, "flash_success")))
        except Exception:
            pass
        # login
        if not login:
            inst.logout()


def wait_Email_received(func):
    i = 0
    while i < 10:
        time.sleep(2)
        if func():
            return True
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


def add_dependency(name, testclass_name, index=""):
    print("Adding dependencies")
    element_version = list()
    with open(os.path.join(CALIBRE_WEB_PATH + index, 'optional-requirements.txt'), 'r') as f:
        requirements = f.readlines()
    for element in name:
        if element.lower().startswith('local|'):
            # full_module_name = ".config_test." + element.split('|')[1]
            # The file gets executed upon import, as expected.
            # tmp = __import__('pkg', fromlist=['mod', 'mod2'])
            whl = importlib.__import__("config_test", fromlist=[element.split('|')[1]])
            element_version.append(whl.__dict__[element.split('|')[1]])
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
                    and not line.startswith('local') \
                    and line.upper().startswith(element.upper()):
                element_version.append(line.split('=', 1)[0].strip('>'))
                break

    for indx, element in enumerate(element_version):
        python_exe = os.path.join(CALIBRE_WEB_PATH + index, 'venv', VENV_PYTHON)
        with process_open([python_exe, "-m", "pip", "install", element], (0, 4)) as r:
            while r.poll() == None:
                r.stdout.readline().strip("\n")
            # if os.name == 'nt':
            #    while r.poll() == None:
            #        r.stdout.readline()
            # else:
            #    r.wait()
        if element.lower().startswith('git'):
            element_version[indx] = element[element.rfind('#egg=')+5:]

    environment.add_environment(testclass_name, element_version)


def remove_dependency(names, index=""):
    python_exe = os.path.join(CALIBRE_WEB_PATH + index, 'venv', VENV_PYTHON)
    for name in names:
        if name.startswith('git|'):
            name = name[4:]
        if name.startswith('local|'):
            name = name.split('|')[2]
        with process_open([python_exe, "-m", "pip", "uninstall", "-y", name], (0, 5)) as q:
            if os.name == 'nt':
                while q.poll() == None:
                    q.stdout.readline()
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
    # Give Calibre-Web time to die
    time.sleep(3)


def kill_dead_cps():
    for proc in process_iter():
        try:
            if 'python' in proc.name():
                res = [i for i in proc.cmdline() if 'cps.py' in i]
                if res:
                    proc.send_signal(SIGKILL)
                    print('Killed dead Calibre-Web instance')
                    time.sleep(2)
        except (PermissionError, psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    # Give Calibre-Web time to die
    time.sleep(3)


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


def save_logfiles(inst, module_name, index=""):
    result = ""
    if not os.path.isdir(os.path.join(base_path, 'outcome')):
        os.makedirs(os.path.join(base_path, 'outcome'))
    datestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    outdir = os.path.join(base_path, 'outcome', module_name + '-' + datestamp)
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    for file in ['calibre-web.log', 'calibre-web.log', 'calibre-web.log.1', 'calibre-web.log.2',
                 'access.log', 'access.log.1', 'access.log.2']:
        src = os.path.join(CALIBRE_WEB_PATH + index, file)
        dest = os.path.join(outdir, file)
        if os.path.exists(src):
            with open(src) as fc:
                if "Traceback" in fc.read():
                    result = file
            shutil.move(src, dest)
    inst.assertTrue(result == "", "Exception in File {}".format(result))


def get_attachment(filename):
    file_ = open(filename, 'rb')
    data = file_.read()
    file_.close()
    content_type, encoding = mimetypes.guess_type(filename)
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    attachment = MIMEBase(main_type, sub_type)
    attachment.set_payload(data)
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
    return attachment


def finishing_notifier(result_file):
    try:
        if server_config:
            result_upload(TEST_OS)
    except Exception as e:
        print(e)
    if convert_config:
        # needed for newer versions of wkhtmltopdf
        options = {
            "enable-local-file-access": None
        }
    try:
        pdfkit.from_file(result_file, 'out.pdf', options=options)
        if email_config:
            msg = MIMEMultipart()
            message = MIMEText('Calibre-Web Tests finished')
            msg['Subject'] = 'Calibre-Web Tests on ' + TEST_OS + ' finished'
            msg['From'] = E_MAIL_ADDRESS
            msg['To'] = E_MAIL_ADDRESS
            msg.attach(message)
            if convert_config:
                msg.attach(get_attachment('out.pdf'))
            s = smtplib.SMTP(E_MAIL_SERVER_ADDRESS, EMAIL_SERVER_PORT)
            if STARTSSL:
                s.starttls()
            if E_MAIL_LOGIN and E_MAIL_PASSWORD:
                s.login(E_MAIL_LOGIN, E_MAIL_PASSWORD)
            s.send_message(msg)
            s.quit()
        if convert_config:
            os.remove('out.pdf')
    except Exception as e:
        print(e)



def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, int(port), user, password, look_for_keys=False, allow_agent=False)
    return client


def result_upload(test_os):
    ssh = createSSHClient(SERVER_NAME, SERVER_PORT, SERVER_USER, SERVER_PASSWORD)
    ftp_client = ssh.open_sftp()
    file_destination = os.path.normpath(os.path.join(SERVER_FILE_DESTINATION,
                                                     'Calibre-Web TestSummary_' + test_os + '.html')).replace('\\', '/')
    ftp_client.put('./../../calibre-web/test/Calibre-Web TestSummary_' + test_os + '.html', file_destination)
    ftp_client.close()

def result_move(file):
    if move_config:
        shutil.move(file, SERVER_MOVE)


def poweroff(power):
    if power:
        if os.name == 'nt':
            os.system('shutdown /s')
        else:
            os.system('shutdown -P')
        time.sleep(1)


def createcbz(zipname, filenames, finalnames):
    with zipfile.ZipFile(zipname, 'w') as zp:
        for indx, item in enumerate(filenames):
            with open(item, "rb") as f:
                zp.writestr(finalnames[indx], f.read())


def updateZip(zipname_new, zipname_org, filename, data):
    # create a temp copy of the archive without filename
    with zipfile.ZipFile(zipname_org, 'r') as zin:
        with zipfile.ZipFile(zipname_new, 'w') as zout:
            zout.comment = zin.comment  # preserve the comment
            for item in zin.infolist():
                if item.filename != filename:
                    zout.writestr(item, zin.read(item.filename))

    # now add filename with its new data
    with zipfile.ZipFile(zipname_new, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, data)


def change_epub_meta(zipname_new=None, zipname_org='./files/book.epub', meta={}, item={}, guide={}, meta_change={}):
    with codecs.open(os.path.join(base_path, 'files', 'test.opf'), "r", "utf-8") as f:
        soup = BeautifulSoup(f.read(), "xml")
    for el in soup.findAll("meta"):
        el.prefix = ""
        el.namespace = ""
    soup.find("metadata").prefix = ""
    for k, v in meta.items():
        if k == "author":
            pass
        el = soup.find(k)
        if el is not None:
            el.string = v
        else:
            new_element = soup.new_tag("dc:" + k)
            new_element[k] = v
            soup.find("metadata").append(new_element)

    # handle meta_handle block
    for task, to_do in meta_change.items():
        if task == 'create':
            new_element = soup.new_tag("meta")
            for key, value in to_do.items():
                new_element[key] = value
                soup.find("metadata").append(new_element)
        elif task == 'delete':
            for key, value in to_do.items():
                soup.find(key).extract()
        if task == 'change':
            element = soup.find(to_do.pop('find_title', None))
            # to_do.pop('find_title', None)
            for key, value in to_do.items():
                if key == "string":
                    element.string = value
                else:
                    element[key] = value

    # handle item block
    for task, to_do in item.items():
        if task == 'change':
            element = soup.find("item", {'id': to_do['find_id']})
            to_do.pop('find_id', None)
            for key, value in to_do.items():
                element[key] = value
        elif task == 'create':
            new_element = soup.new_tag("item")
            for key, value in to_do.items():
                new_element[key] = value
            soup.find("manifest").append(new_element)
        elif task == 'delete':
            for key, value in to_do.items():
                soup.find("item", {key: value}).extract()

    # handle guide block
    for task, to_do in guide.items():
        if task == 'change':
            element = soup.find("reference", {'title': to_do['find_title']})
            to_do.pop('find_title', None)
            for key, value in to_do.items():
                element[key] = value
        elif task == 'create':
            new_element = soup.new_tag("reference")
            for key, value in to_do.items():
                new_element[key] = value
            soup.find("guide").append(new_element)
        elif task == 'delete':
            for key, value in to_do.items():
                soup.find("reference", {key: value}).extract()

    updateZip(zipname_new, zipname_org, 'content.opf', str(soup))


def change_comic_meta(zipname_new=None, zipname_org='./files/book1.cbz', element={}):
    with codecs.open(os.path.join(base_path, 'files', 'ComicInfo.xml'), "r", "utf-8") as f:
        soup = BeautifulSoup(f.read(), "xml")
    for k, v in element.items():
        el = soup.find(k)
        el.string = v
    updateZip(zipname_new, zipname_org, 'ComicInfo.xml', str(soup))


def create_2nd_database(new_path):
    try:
        shutil.rmtree(new_path, ignore_errors=True)
        shutil.copytree(os.path.join(base_path, 'Calibre_db'), new_path)
    except FileExistsError:
        print('Test DB already present, might not be a clean version')


def count_files(folder):
    total_files = 0
    for base, dirs, files in os.walk(folder):
        for _ in files:
            total_files += 1
    return total_files


def read_metadata_epub(content):
    with zipfile.ZipFile(BytesIO(content)) as thezip:
        contentopf = thezip.read("content.opf").decode('utf-8')
    return read_opf_metadata(contentopf)


def read_opf_metadata(file):
    result = {}
    if os.path.isfile(file):
        with codecs.open(file, "r", "utf-8") as f:
            soup = BeautifulSoup(f.read(), "xml")
    elif isinstance(file, str):
        soup = BeautifulSoup(file, "xml")
    result['identifier'] = soup.findAll("identifier")
    cover = soup.find("reference")
    result['cover'] = cover.attrs if cover else ""
    title = soup.find("dc:title")
    result['title'] = title.contents[0] if title else ""
    author = soup.findAll("dc:creator")
    result['author'] = [a.contents[0] for a in author]
    result['author_attr'] = [a.attrs for a in author]
    contributor = soup.find("dc:contributor")
    if contributor:
        result['contributor'] = contributor.contents
        result['contributor_attr'] = contributor.attrs
    else:
        result['contributor'] = ""
        result['contributor_attr'] = ""
    try:
        format_string = "%Y-%m-%dT%H:%M:%S"
        time_string = soup.find("dc:date").contents[0]
        if "." in time_string:
            format_string +=".%f"
        result['pub_date'] = datetime.datetime.strptime(time_string, format_string)
    except ValueError:
        result['pub_date'] = datetime.datetime.strptime(time_string, format_string + "%z")
    language = soup.findAll("dc:language")
    result['language'] = [lang.contents[0] for lang in language] if language else []
    publisher = soup.find("dc:publisher")
    result['publisher'] = publisher.contents[0] if publisher else ""
    tags = soup.findAll("dc:subject")
    result['tags'] = [t.contents[0] for t in tags] if tags else []
    comment = soup.find("dc:description")
    result['description'] = comment.contents[0] if comment else ""
    series_index = soup.find("meta", {"name": "calibre:series_index"})
    result['series_index'] = series_index.attrs if series_index else ""
    author_link_map = soup.find("meta", {"name": "calibre:author_link_map"})
    result['author_link_map'] = author_link_map.attrs if author_link_map else ""
    series = soup.find("meta", {"name": "calibre:series"})
    result['series'] = series.attrs if series else ""
    rating = soup.find("meta", {"name": "calibre:rating"})
    result['rating'] = rating.attrs if rating else ""
    try:
        format_string = "%Y-%m-%dT%H:%M:%S"
        time_string = soup.find("meta", {"name": "calibre:timestamp"}).attrs['content']
        if "." in time_string:
            format_string +=".%f"
        result['timestamp'] = datetime.datetime.strptime(time_string, format_string)
    except ValueError:
        result['timestamp'] = datetime.datetime.strptime(time_string, format_string + "%z")

    title_sort = soup.find("meta", {"name": "calibre:title_sort"})
    result['title_sort'] = title_sort.attrs if title_sort else ""
    custom_1 = soup.find("meta", {"name": "calibre:user_metadata:#cust1"})
    result['custom_1'] = custom_1.attrs if custom_1 else ""
    custom_2 = soup.find("meta", {"name": "calibre:user_metadata:#cust2"})
    result['custom_2'] = custom_2.attrs if custom_2 else ""
    custom_3 = soup.find("meta", {"name": "calibre:user_metadata:#cust3"})
    result['custom_3'] = custom_3.attrs if custom_3 else ""
    custom_4 = soup.find("meta", {"name": "calibre:user_metadata:#cust4"})
    result['custom_4'] = custom_4.attrs if custom_4 else ""
    custom_5 = soup.find("meta", {"name": "calibre:user_metadata:#cust5"})
    result['custom_5'] = custom_5.attrs if custom_5 else ""
    custom_6 = soup.find("meta", {"name": "calibre:user_metadata:#cust6"})
    result['custom_6'] = custom_6.attrs if custom_6 else ""
    custom_7 = soup.find("meta", {"name": "calibre:user_metadata:#cust7"})
    result['custom_7'] = custom_7.attrs if custom_7 else ""
    custom_8 = soup.find("meta", {"name": "calibre:user_metadata:#cust8"})
    result['custom_8'] = custom_8.attrs if custom_8 else ""
    custom_9 = soup.find("meta", {"name": "calibre:user_metadata:#cust9"})
    result['custom_9'] = custom_9.attrs if custom_9 else ""
    custom_10 = soup.find("meta", {"name": "calibre:user_metadata:#cust10"})
    result['custom_10'] = custom_10.attrs if custom_10 else ""

    return result