# -*- coding: utf-8 -*-

import selenium.webdriver as webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from config_test import PY_BIN, BOOT_TIME
import requests
import time
import lxml.etree
from PIL import Image
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

RESTRICT_TAG_ME         = 0
RESTRICT_COL_ME         = 1
RESTRICT_TAG_USER       = 2
RESTRICT_COL_USER       = 3
RESTRICT_TAG_TEMPLATE   = 4
RESTRICT_COL_TEMPLATE   = 5

# Dict for pages and the way to reach them
page = dict()
page['nav_serie'] = {'check': (By.TAG_NAME, "h1"), 'click': [(By.ID, "nav_serie")]}
page['nav_publisher'] = {'check': (By.TAG_NAME, "h1"), 'click': [(By.ID, "nav_publisher")]}
page['nav_rand'] = {'check': (By.TAG_NAME, "h2"), 'click': [(By.ID, "nav_rand")]}
page['nav_format'] = {'check': (By.TAG_NAME, "h1"), 'click': [(By.ID, "nav_format")]}
page['nav_rate'] = {'check': (By.TAG_NAME, "h1"), 'click': [(By.ID, "nav_rate")]}
page['nav_archived'] = {'check': (By.TAG_NAME, "h1"), 'click': [(By.ID, "nav_archived")]}
page['nav_new'] = {'check': None, 'click': [(By.ID, "nav_new")]}
page['nav_cat'] = {'check': (By.TAG_NAME, "h1"), 'click': [(By.ID, "nav_cat")]}
page['nav_author'] = {'check': (By.TAG_NAME, "h1"), 'click': [(By.ID, "nav_author")]}
page['nav_lang'] = {'check': (By.TAG_NAME, "h1"), 'click': [(By.ID, "nav_lang")]}
page['nav_hot'] = {'check': None, 'click': [(By.ID, "nav_hot")]}
page['nav_download'] = {'check': (By.TAG_NAME, "h1"), 'click': [(By.ID, "nav_download")]}
page['nav_list'] = {'check': (By.ID, "merge_books"), 'click': [(By.ID, "nav_list")]}
page['nav_about'] = {'check': (By.ID, "stats"), 'click': [(By.ID, "nav_about")]}
page['nav_rated'] = {'check': None, 'click': [(By.ID, "nav_rated")]}
page['nav_read'] = {'check': (By.CLASS_NAME, "read"), 'click': [(By.ID, "nav_read")]}
page['nav_unread'] = {'check': (By.CLASS_NAME, "unread"), 'click': [(By.ID, "nav_unread")]}
page['nav_archived'] = {'check': (By.CLASS_NAME, "archived"), 'click': [(By.ID, "nav_archived")]}
page['db_config'] = {'check': (By.ID, "config_calibre_dir"),
                        'click': [(By.ID, "top_admin"), (By.ID, "db_config")]}
page['basic_config'] = {'check': (By.ID, "config_port"),
                        'click': [(By.ID, "top_admin"), (By.ID, "basic_config")]}
page['view_config'] = {'check': (By.NAME, "submit"), 'click': [(By.ID, "top_admin"), (By.ID, "view_config")]}
page['mail_server'] = {'check': (By.ID, "mail_server"), 'click': [(By.ID, "top_admin"), (By.ID, "admin_edit_email")]}
page['user_list'] = {'check': (By.ID, "user_delete_selection"), 'click': [(By.ID, "top_admin"), (By.ID, "admin_user_table")]}
page['admin_setup'] = {'check': (By.ID, "admin_edit_email"), 'click': [(By.ID, "top_admin")]}
page['user_setup'] = {'check': (By.ID, "kindle_mail"), 'click': [(By.ID, "top_user")]}
page['create_shelf'] = {'check': (By.ID, "title"), 'click': [(By.ID, "nav_createshelf")]}
page['create_user'] = {'check': (By.ID, "name"), 'click': [(By.ID, "top_admin"), (By.ID, "admin_new_user")]}
page['register'] = {'check': (By.ID, "email"), 'click': [(By.ID, "register")]}
page['tasks'] = {'check': (By.TAG_NAME, "h2"), 'click': [(By.ID, "top_tasks")]}
page['login'] = {'check': (By.NAME, "username"), 'click': [(By.ID, "logout")]}
page['unlogged_login'] = {'check': (By.NAME, "username"), 'click': [(By.CLASS_NAME, "glyphicon-log-in")]}
page['logviewer'] = {'check': (By.ID, "log_group"), 'click': [(By.ID, "top_admin"), (By.ID, "logfile")]}
page['adv_search'] = {'check': (By.ID, "adv_submit"), 'click': [(By.ID, "advanced_search")]}


class ui_class():
    py_version = PY_BIN

    @classmethod
    def login(cls, user, passwd):
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "username")))
        username = cls.driver.find_element_by_id("username")
        password = cls.driver.find_element_by_id("password")
        submit = cls.driver.find_element_by_name("submit")
        username.send_keys(user)
        password.send_keys(passwd)
        submit.click()
        try:
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.NAME, "query")))
            return True
        except:
            return False

    @classmethod
    def logout(cls):
        logout = cls.check_element_on_page((By.ID, "logout"))
        if logout:
            logout.click()
            return cls.check_element_on_page((By.ID, "username"))
        return False

    @classmethod
    def check_user_logged_in(cls, user, noCompare=False):
        user_element = cls.check_element_on_page((By.ID, "top_user"))
        if user_element:
            if noCompare:
                return True
            if user_element.text.lower() == user.lower():
                return True
        return False

    @classmethod
    def register(cls, user, email):
        cls.goto_page('register')
        if user != '':
            username = cls.driver.find_element_by_name("name")
            username.send_keys(user)
        emailfield = cls.driver.find_element_by_name("email")
        submit = cls.driver.find_element_by_id("submit")
        emailfield.send_keys(email)
        submit.click()
        flash = cls.check_element_on_page((By.CLASS_NAME, "alert"))
        if flash:
            id = flash.get_attribute('id')
            return id
        else:
            return False

    @classmethod
    def forgot_password(cls, user):
        cls.goto_page('login')
        username = cls.driver.find_element_by_name("username")
        submit = cls.driver.find_element_by_name("forgot")
        username.send_keys(user)
        submit.click()
        return bool(cls.check_element_on_page((By.ID, "flash_info")))


    @classmethod
    def list_shelfs(cls, search_name=None):
        all_shelfs = cls.driver.find_elements_by_xpath( "//a/span[@class='glyphicon glyphicon-list shelf']//ancestor::a")
        ret_shelfs = list()
        ret_ele = None

        for shelf in all_shelfs:
            sh = dict()
            sh['id'] = shelf.get_attribute('href')[shelf.get_attribute('href').rfind('/')+1:]
            sh['name'] = shelf.text
            if shelf.text.endswith('(Public)'):
                sh['public'] = True
            else:
                sh['public'] = False
            sh['ele'] = shelf
            if search_name == shelf.text:
                if ret_ele:
                    ret_ele = [sh, ret_ele]
                else:
                    ret_ele = sh
            else:
                ret_shelfs.append(sh)
        if search_name:
            return ret_ele
        else:
            return ret_shelfs

    @classmethod
    def goto_page(cls, page_target):
        if page_target in page:
            try:
                for element in page[page_target]['click']:
                    WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located(element))
                    # goto Page
                    if element[0] == By.ID:
                        cls.driver.find_element_by_id(element[1]).click()
                    if element[0] == By.NAME:
                        cls.driver.find_element_by_name(element[1]).click()
                    if element[0] == By.CLASS_NAME:
                        cls.driver.find_element_by_class_name(element[1]).click()

                # check if got to page
                if page[page_target]['check'][0] == By.TAG_NAME:
                    WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located(page[page_target]['check']))
                    if page[page_target]['check'][1] == 'h1':
                        list_type=cls.driver.find_element_by_tag_name(page[page_target]['check'][1])
                    else:
                        return True
                if page[page_target]['check'][0] == By.ID:
                    WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located(page[page_target]['check']))
                    return True
                elif page[page_target]['check'][0] == By.NAME:
                    WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located(page[page_target]['check']))
                    return True
                elif page[page_target]['check'][0] == None:
                    return True

                if list_type:
                    return cls.driver.find_elements_by_xpath("//*[contains(@id, 'list_')]")
                else:
                    return False
            except:
                # page not found on current webpage
                return False
        else:
            # Page_target element not found
            return False

    @classmethod
    def change_current_user_password(cls, new_passwd):
        cls.driver.find_element_by_id("top_user").click()
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "password")))
        cls.driver.find_element_by_id("password").send_keys(new_passwd)
        cls.driver.find_element_by_id("user_submit").click()
        return cls.check_element_on_page((By.ID, "flash_success"))

    @classmethod
    def fill_db_config(cls,elements=None):
        if not cls.check_user_logged_in('admin'):
            cls.login('admin', 'admin123')
            time.sleep(1)
        if not cls.check_element_on_page((By.ID, "config_calibre_dir")):
            cls.goto_page('db_config')
        try:
            WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "config_calibre_dir")))
        except Exception:
            print("no config_calibre_dir visible")
        process_checkboxes = dict()
        process_elements = dict()
        process_options =dict()
        # special handling for checkboxes
        checkboxes = ['config_use_google_drive']
        options = ['config_google_drive_folder']

        # check if checkboxes are in list and seperate lists
        for element,key in enumerate(elements):
            if key in checkboxes:
                process_checkboxes[key] = elements[key]
            elif key in options:
                process_options[key] = elements[key]
            else:
                process_elements[key] = elements[key]
        # process all checkboxes Todo: If status was wrong before is not included in response
        for checkbox in process_checkboxes:
            ele = cls.driver.find_element_by_id(checkbox)
            if (elements[checkbox] == 1 and not ele.is_selected() ) or elements[checkbox] == 0 and ele.is_selected():
                ele.click()

        # process all selects
        for option, key in enumerate(process_options):
            select = Select(cls.driver.find_element_by_id(key))
            select.select_by_visible_text(process_options[key])

        # process all text fields
        for element, key in enumerate(process_elements):
            ele = cls.driver.find_element_by_id(key)
            ele.clear()
            ele.send_keys(process_elements[key])

        # finally submit settings
        cls.driver.find_element_by_name("submit").click()

    @classmethod
    def _fill_basic_config(cls,elements=None):
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "config_port")))
        opener = list()
        process_checkboxes = dict()
        process_elements = dict()
        process_options =dict()
        process_select = dict()
        # special handling for checkboxes
        checkboxes = ['config_uploading', 'config_anonbrowse', 'config_public_reg', 'config_remote_login',
                      'config_access_log', 'config_kobo_sync', 'config_kobo_proxy', 'config_ldap_openldap',
                      'config_use_goodreads', 'config_register_email', 'config_use_google_drive',
                      'config_allow_reverse_proxy_header_login']
        options = ['config_log_level', 'config_google_drive_folder', 'config_updatechannel', 'config_login_type',
                   'config_ldap_encryption', 'config_ldap_authentication', 'ldap_import_user_filter']
        selects = ['config_ebookconverter']
        # depending on elements open accordions or not
        if any(key in elements for key in ['config_port', 'config_certfile','config_keyfile', 'config_updatechannel']):
            opener.append(0)
        if any(key in elements for key in ['config_log_level','config_logfile', 'config_access_logfile',
                                           'config_access_log']):
            opener.append(1)
        if any(key in elements for key in ['config_uploading', 'config_anonbrowse', 'config_public_reg',
                                           'config_register_email', 'config_upload_formats',
                                           'config_remote_login', 'config_use_goodreads', 'config_goodreads_api_key',
                                           'config_goodreads_api_secret', 'config_kobo_sync', 'config_kobo_proxy',
                                           'config_login_type', 'config_ldap_provider_url', 'config_ldap_port',
                                           'config_ldap_encryption', 'config_ldap_cacert_path',
                                           'config_ldap_cert_path', 'config_ldap_key_path',
                                           'config_ldap_serv_username', 'ldap_import_user_filter'
                                           'config_ldap_serv_password', 'config_ldap_dn', 'config_ldap_user_object',
                                           'config_ldap_group_object_filter', 'config_ldap_group_name',
                                           'config_ldap_group_members_field', 'config_ldap_openldap',
                                           'config_ldap_authentication', 'config_ldap_member_user_object',
                                           'config_1_oauth_client_id', 'config_1_oauth_client_secret',
                                           'config_2_oauth_client_id', 'config_2_oauth_client_secret',
                                           'config_allow_reverse_proxy_header_login',
                                           'config_reverse_proxy_login_header_name'
                                           ]):
            opener.append(2)
        if any(key in elements for key in ['config_ebookconverter', 'config_calibre', 'config_kepubifypath',
                                           'config_converterpath', 'config_rarfile_location']):
            opener.append(3)

        # open all necessary accordions
        accordions = cls.driver.find_elements_by_class_name("accordion-toggle")
        for o in opener:
            time.sleep(1)
            accordions[o].click()
        # check if checkboxes are in list and seperate lists
        for element,key in enumerate(elements):
            if key in checkboxes:
                process_checkboxes[key] = elements[key]
            elif key in options:
                process_options[key] = elements[key]
            elif key in selects:
                process_select[key] = elements[key]
            else:
                process_elements[key] = elements[key]
        # process all checkboxes Todo: If status was wrong before is not included in response
        for checkbox in process_checkboxes:
            ele = cls.driver.find_element_by_id(checkbox)
            if (elements[checkbox] == 1 and not ele.is_selected() ) or elements[checkbox] == 0 and ele.is_selected():
                ele.click()

        for select in process_select:
            ele = cls.driver.find_elements_by_name(select)
            time.sleep(1)
            for el in ele:
                if el.get_attribute('id') == elements[select]:
                    el.click()
                    break

        # process all selects
        for option, key in enumerate(process_options):
            select = Select(cls.driver.find_element_by_id(key))
            select.select_by_visible_text(process_options[key])

        # process all text fields
        for element, key in enumerate(process_elements):
            ele = cls.driver.find_element_by_id(key)
            ele.clear()
            ele.send_keys(process_elements[key])

        # finally submit settings
        cls.driver.find_element_by_name("submit").click()


    @classmethod
    def fill_basic_config(cls, elements=None):
        if not cls.goto_page('basic_config'):
            print("page not reached")
        cls._fill_basic_config(elements)

    @classmethod
    def fill_view_config(cls,elements=None):
        cls.goto_page('view_config')
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "discover")))
        accordions=cls.driver.find_elements_by_class_name("accordion-toggle")
        opener = list()
        process_checkboxes = dict()
        process_elements = dict()
        # process_options = dict()
        process_selects = dict()
        # special handling for checkboxes
        checkboxes = ['admin_role', 'download_role', 'upload_role', 'edit_role', 'delete_role', 'passwd_role',
                      'viewer_role', 'edit_shelf_role', 'show_32', 'show_16', 'show_128', 'show_32768',
                        'show_2', 'show_4', 'show_8', 'show_64', 'show_256', 'show_8192', 'show_16384',
                        'Show_detail_random', 'show_4096', 'show_65536', 'show_131072']
        selects = ['config_theme', 'config_restricted_column', 'config_read_column']
        # depending on elements open accordions or not
        if any(key in elements for key in ['config_calibre_web_title', 'config_books_per_page', 'config_theme',
                                           'config_random_books', 'config_columns_to_ignore', 'config_authors_max',
                                           'config_restricted_column', 'config_read_column', 'config_title_regex']):
            opener.append(0)
        if any(key in elements for key in ['admin_role', 'download_role', 'upload_role', 'edit_role', 'viewer_role',
                                           'delete_role', 'passwd_role', 'edit_shelf_role']):
            opener.append(1)
        if any(key in elements for key in ['show_32', 'show_16', 'show_128', 'show_32768', 'show_65536',
                                           'show_2', 'show_4', 'show_8', 'show_64', 'show_8192', 'show_16384',
                                           'show_256', 'Show_detail_random', 'show_4096', 'show_131072']):
            opener.append(2)

        # open all necessary accordions
        for o in opener:
            accordions[o].click()
        # check if checkboxes are in list and seperate lists
        for element,key in enumerate(elements):
            if key in checkboxes:
                process_checkboxes[key] = elements[key]
            #elif key in options:
            #    process_options[key] = elements[key]
            elif key in selects:
                process_selects[key] = elements[key]
            else:
                process_elements[key] = elements[key]

        # process all checkboxes Todo: If status was wrong before is not included in response
        for checkbox in process_checkboxes:
            ele = cls.driver.find_element_by_id(checkbox)
            if (elements[checkbox] == 1 and not ele.is_selected() )or elements[checkbox] == 0 and ele.is_selected():
                ele.click()

        # process all text fields
        for element, key in enumerate(process_elements):
            ele = cls.driver.find_element_by_id(key)
            ele.clear()
            ele.send_keys(process_elements[key])

        for option, key in enumerate(process_selects):
            select = Select(cls.driver.find_element_by_id(key))
            select.select_by_visible_text(process_selects[key])

        # finally submit settings
        cls.driver.find_element_by_name("submit").click()


    def restart_calibre_web(self):
        self.goto_page('admin_setup')
        self.driver.find_element_by_id('admin_restart').click()
        element = self.check_element_on_page((By.ID, "restart"))
        element.click()
        time.sleep (10)

    def reconnect_database(self):
        self.goto_page('admin_setup')
        self.driver.find_element_by_id('restart_database').click()
        element = self.check_element_on_page((By.ID, "DialogFinished"))
        element.click()
        time.sleep (3)

    @classmethod
    def stop_calibre_web(cls, proc=None):
        try:
            cls.goto_page('admin_setup')
        except:
            cls.driver.get("http://127.0.0.1:8083")
            if not cls.check_user_logged_in("admin",True):
                cls.login('admin','admin123')
            cls.goto_page('admin_setup')
        cls.driver.find_element_by_id('admin_stop').click()
        element = cls.check_element_on_page((By.ID, "shutdown"))
        element.click()
        try:
            if cls.p:
                time.sleep(3)
                cls.p.poll()
        except Exception as e:
            pass
        if proc:
            time.sleep(3)
            proc.poll()

    def list_domains(self, allow=True):
        if not self.check_element_on_page((By.ID, "mail_server")):
            if not self.goto_page('mail_server'):
                print('got page failed')
                return False
        if allow:
            table_id = 'domain-allow-table'
        else:
            table_id = 'domain-deny-table'
        if not self.check_element_on_page((By.ID, table_id)):
            print('table not found')
            return False
        time.sleep(1)
        parser = lxml.etree.HTMLParser()
        html = self.driver.page_source

        tree = lxml.etree.parse(StringIO(html), parser)
        vals = tree.xpath("//table[@id='" + table_id + "']/tbody/tr")
        val = list()
        for va in vals:
            try:
                go = va.getchildren()[0].getchildren()[0]
                id = go.attrib['data-pk']
                delButton = self.driver.find_element_by_css_selector("a[data-pk='"+id+"']")
                editButton = self.driver.find_element_by_css_selector("a[data-value='"+id+"']")
                val.append({'domain':go.text, 'delete': delButton, 'edit':editButton, 'id': id})
            except IndexError:
                pass
        return val

    def edit_domains(self, id,  new_value, accept, allow=True):
        if allow:
            table_id = 'domain-allow-table'
        else:
            table_id = 'domain-deny-table'
        if not self.check_element_on_page((By.ID, table_id)):
            return False
        editButton = self.check_element_on_page((By.CSS_SELECTOR, "a[data-pk='" + id + "']"))
        if not editButton:
            return False
        editButton.click()
        editor=self.check_element_on_page((By.CLASS_NAME, "input-sm"))
        if not editor:
            return False
        editor.clear()
        editor.send_keys(new_value)
        if accept:
            submit = self.check_element_on_page((By.CLASS_NAME, "editable-submit"))
        else:
            submit = self.check_element_on_page((By.CLASS_NAME, "editable-cancel"))
        submit.click()

    def delete_domains(self, id, accept, allow=True):
        if allow:
            table_id = 'domain-allow-table'
        else:
            table_id = 'domain-deny-table'
        if not self.check_element_on_page((By.ID, table_id)):
            return False
        deleteButton = self.check_element_on_page((By.CSS_SELECTOR, "a[data-value='" + id + "']"))
        if not deleteButton:
            return False
        deleteButton.click()
        if accept:
            submit = self.check_element_on_page((By.ID, "btnConfirmYes-GeneralDeleteModal"))
        else:
            submit = self.check_element_on_page((By.ID, "btnConfirmNo-GeneralDeleteModal"))
        submit.click()
        time.sleep(2)

    def add_domains(self, new_value, allow=True):
        if allow:
            edit = self.check_element_on_page((By.ID, "domainname_allow"))
            add = self.check_element_on_page((By.ID, "domain_allow_submit"))
        else:
            edit = self.check_element_on_page((By.ID, "domainname_deny"))
            add = self.check_element_on_page((By.ID, "domain_deny_submit"))
        if not edit:
            return False
        edit.clear()
        edit.send_keys(new_value)
        if not add:
            return False
        add.click()

    def list_restrictions(self, type, username=""):
        if type == RESTRICT_TAG_ME:
            if not self.goto_page('user_setup'):
                return False
            restrict = self.check_element_on_page((By.ID, 'get_user_tags'))
            if not restrict:
                return False
            restrict.click()
        elif type == RESTRICT_COL_ME:
            if not self.goto_page('user_setup'):
                return False
            restrict = self.check_element_on_page((By.ID, 'get_user_column_values'))
            if not restrict:
                return False
            restrict.click()
        elif type == RESTRICT_TAG_USER:
            if username:
                self.goto_page('admin_setup')
                user = self.driver.find_elements_by_xpath("//table[@id='table_user']/tbody/tr/td/a")
                for ele in user:
                    if username == ele.text:
                        ele.click()
                        if not self.check_element_on_page((By.ID, "email")):
                            print('Could not edit user: %s' % username)
                            return False
                        break
            restrict = self.check_element_on_page((By.ID, 'get_user_tags'))
            if not restrict:
                return False
            restrict.click()
        elif type == RESTRICT_COL_USER:
            if username:
                self.goto_page('admin_setup')
                user = self.driver.find_elements_by_xpath("//table[@id='table_user']/tbody/tr/td/a")
                for ele in user:
                    if username == ele.text:
                        ele.click()
                        if not self.check_element_on_page((By.ID, "email")):
                            print('Could not edit user: %s' % username)
                            return False
                        break
            restrict = self.check_element_on_page((By.ID, 'get_user_column_values'))
            if not restrict:
                return False
            restrict.click()
        elif type == RESTRICT_TAG_TEMPLATE:
            self.goto_page('view_config')
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "discover")))
            accordions = self.driver.find_elements_by_class_name("accordion-toggle")
            accordions[2].click()
            restrict = self.check_element_on_page((By.ID, 'get_tags'))
            if not restrict:
                return False
            restrict.click()
        elif type == RESTRICT_COL_TEMPLATE:
            self.goto_page('view_config')
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "discover")))
            accordions = self.driver.find_elements_by_class_name("accordion-toggle")
            accordions[2].click()
            restrict = self.check_element_on_page((By.ID, 'get_column_values'))
            if not restrict:
                return False
            restrict.click()
        else:
            print('unknown restriction type')
            return False
        table_id='restrict-elements-table'
        if not self.check_element_on_page((By.ID, table_id)):
            return False
        parser = lxml.etree.HTMLParser()
        html = self.driver.page_source

        tree = lxml.etree.parse(StringIO(html), parser)
        vals = tree.xpath("//table[@id='"+table_id+"']/tbody/tr")
        val = list()
        for va in vals:
            try:
                go = va.getchildren()[0].getchildren()
                id = go[0].attrib['data-pk']
                editButton = self.driver.find_element_by_css_selector("a[data-pk='"+id+"']")
                delButton = self.driver.find_element_by_css_selector("div[data-restriction-id='"+id+"']")
                val.append({'restriction':go[0].text,
                            'delete': delButton,
                            'edit':editButton,
                            'id':id,
                            'type': va[1].text})
            except IndexError:
                pass
        return val

    def edit_restrictions(self, id,  new_value, accept):
        table_id = 'restrict-elements-table'
        if not self.check_element_on_page((By.ID, table_id)):
            return False
        editButton = self.check_element_on_page((By.CSS_SELECTOR, "a[data-pk='" + id + "']"))
        if not editButton:
            return False
        editButton.click()
        editor=self.check_element_on_page((By.CLASS_NAME, "input-sm"))
        if not editor:
            return False
        editor.clear()
        editor.send_keys(new_value)
        if accept:
            submit = self.check_element_on_page((By.CLASS_NAME, "editable-submit"))
        else:
            submit = self.check_element_on_page((By.CLASS_NAME, "editable-cancel"))
        submit.click()

    def delete_restrictions(self, id):
        table_id = 'restrict-elements-table'
        if not self.check_element_on_page((By.ID, table_id)):
            return False
        deleteButton = self.check_element_on_page((By.CSS_SELECTOR, "div[data-restriction-id='" + id + "']"))
        if not deleteButton:
            return False
        deleteButton.click()

    def add_restrictions(self, new_value, allow=True):
        edit = self.check_element_on_page((By.ID, "add_element"))
        if allow:
            add = self.check_element_on_page((By.ID, "submit_allow"))
        else:
            add = self.check_element_on_page((By.ID, "submit_restrict"))
        if not edit:
            return False
        edit.clear()
        edit.send_keys(new_value)
        if not add:
            return False
        add.click()

    @classmethod
    def setup_server(cls, test_on_return, elements):
        cls.goto_page('mail_server')
        process_options = dict()
        process_elements = dict()
        options = ['mail_use_ssl']
        for element,key in enumerate(elements):
            if key in options:
                process_options[key] = elements[key]
            else:
                process_elements[key] = elements[key]

        # process all selects
        for option, key in enumerate(process_options):
            select = Select(cls.driver.find_element_by_id(key))
            select.select_by_visible_text(process_options[key])

        # process all text fields
        for element, key in enumerate(process_elements):
            ele = cls.driver.find_element_by_id(key)
            ele.clear()
            ele.send_keys(process_elements[key])
        if test_on_return:
            clicker = 'test'
        else:
            clicker = 'submit'
        cls.driver.find_element_by_name(clicker).click()

    @classmethod
    def check_element_on_page(cls, element, timeout=BOOT_TIME):
        try:
            el = WebDriverWait(cls.driver, timeout).until(EC.presence_of_element_located(element))
            return el
        except TimeoutException:
            return False

    @classmethod
    def edit_user(cls, name, element, abort=False):
        if cls.navigate_to_user(name):
            return cls.change_user(element, abort)
        return False

    @classmethod
    def navigate_to_user(cls, name):
        cls.goto_page('admin_setup')
        user = cls.driver.find_elements_by_xpath("//table[@id='table_user']/tbody/tr/td/a")
        # table
        if not user:
            user_table = cls.check_element_on_page((By.ID, "admin_user_table"))
            if not user_table:
                return False
            else:
                user_table.click()
                # wait for page loaded
                cls.check_element_on_page((By.ID, "user_delete_selection"))
                time.sleep(1)
                search = cls.check_element_on_page((By.CLASS_NAME, "search-input"))
                if search:
                    search.send_keys(name)
                    cls.check_element_on_page((By.NAME, "search")).click()
                    time.sleep(1)
                users = cls.driver.find_elements_by_xpath("//table[@id='user-table']/tbody/tr")
                for usr in users:
                    if len(usr.find_elements_by_xpath("//td/a[@data-name='name'][text()='" + name + "']")):
                        usr.find_element_by_xpath("//td/a").click()
                        if not cls.check_element_on_page((By.ID, "email")):
                            print('Could not edit user: %s' % name)
                            return False
                        return True
        else:
            for ele in user:
                if name == ele.text:
                    ele.click()
                    if not cls.check_element_on_page((By.ID, "email")):
                        print('Could not edit user: %s' % name)
                        return False
                    return True
        print('User: %s not found' % name)
        return False

    def get_user_settings(self, name):
        if self.navigate_to_user(name):
            user_settings=dict()
            element = self.check_element_on_page((By.ID, "name"))
            if element:
                user_settings['name'] = element.get_attribute('value')
            else:
                user_settings['name'] = None
            user_settings['email'] = self.check_element_on_page((By.ID, "email")).get_attribute('value')
            user_settings['kindle_mail'] = self.check_element_on_page((By.ID, "kindle_mail")).get_attribute('value')
            element = self.check_element_on_page((By.ID, "locale"))
            if element:
                user_settings['locale'] = element.get_attribute('value')
            else:
                user_settings['locale'] = None
            # user_settings['locale'] = Select(self.check_element_on_page((By.ID, "locale"))).first_selected_option.text
            user_settings['default_language'] = Select(self.check_element_on_page((By.ID, "default_language"))).first_selected_option.text
            user_settings['show_2'] = int(self.check_element_on_page((By.ID, "show_2")).is_selected())
            user_settings['show_4'] = int(self.check_element_on_page((By.ID, "show_4")).is_selected())
            user_settings['show_8'] = int(self.check_element_on_page((By.ID, "show_8")).is_selected())
            user_settings['show_16'] = int(self.check_element_on_page((By.ID, "show_16")).is_selected())
            user_settings['show_32'] = int(self.check_element_on_page((By.ID, "show_32")).is_selected())
            user_settings['show_64'] = int(self.check_element_on_page((By.ID, "show_64")).is_selected())
            user_settings['show_128'] = int(self.check_element_on_page((By.ID, "show_128")).is_selected())
            element = self.check_element_on_page((By.ID, "show_256"))
            if element:
                user_settings['show_256'] = element.is_selected()
            else:
                user_settings['show_256'] = None
            user_settings['show_512'] = None
            user_settings['show_1024'] = None  # was sorted
            user_settings['show_2048'] = None  # was mature content
            user_settings['show_4096'] = int(self.check_element_on_page((By.ID, "show_4096")).is_selected())
            user_settings['show_8192'] = int(self.check_element_on_page((By.ID, "show_8192")).is_selected())
            user_settings['show_16384'] = int(self.check_element_on_page((By.ID, "show_16384")).is_selected())
            element = self.check_element_on_page((By.ID, "show_32768"))
            if element:
                user_settings['show_32768'] = element.is_selected()
            else:
                user_settings['show_32768'] = None
            element = self.check_element_on_page((By.ID, "show_65536"))
            if element:
                user_settings['show_65536'] = element.is_selected()
            else:
                user_settings['show_65536'] = None
            element = self.check_element_on_page((By.ID, "show_131072"))
            if element:
                user_settings['show_131072'] = element.is_selected()
            else:
                user_settings['show_131072'] = None
            user_settings['Show_detail_random'] = int(self.check_element_on_page((By.ID, "Show_detail_random")).is_selected())
            element = self.check_element_on_page((By.ID, "admin_role"))
            if element:
                user_settings['admin_role'] = element.is_selected()
            else:
                user_settings['admin_role'] = None

            user_settings['download_role'] = int(self.check_element_on_page((By.ID, "download_role")).is_selected())
            user_settings['upload_role'] = int(self.check_element_on_page((By.ID, "upload_role")).is_selected())
            user_settings['edit_role'] = int(self.check_element_on_page((By.ID, "edit_role")).is_selected())
            user_settings['delete_role'] = int(self.check_element_on_page((By.ID, "delete_role")).is_selected())
            element = self.check_element_on_page((By.ID, "kobo_only_shelves_sync"))
            if element:
                user_settings['kobo_only_shelves_sync'] = element.is_selected()
            else:
                user_settings['kobo_only_shelves_sync'] = None
            element = self.check_element_on_page((By.ID, "passwd_role"))
            if element:
                user_settings['passwd_role'] = element.is_selected()
            else:
                user_settings['passwd_role'] = None
            element = self.check_element_on_page((By.ID, "edit_shelf_role"))
            if element:
                user_settings['edit_shelf_role'] = element.is_selected()
            else:
                user_settings['edit_shelf_role'] = None
            user_settings['viewer_role'] = int(self.check_element_on_page((By.ID, "viewer_role")).is_selected())
            return user_settings
        return False

    @classmethod
    def change_visibility_me(cls, nav_element):
        ''' All Checkboses are:
            'show_32','show_512', 'show_16', 'show_128', 'show_2', 'show_4',
            'show_8', 'show_64', 'show_256', 'Show_detail_random' '''
        selects = ['locale', 'default_language']
        cls.goto_page('user_setup')
        process_selects = dict()
        process_checkboxes = dict()
        if 'kindle_mail' in nav_element:
            ele = cls.driver.find_element_by_id('kindle_mail')
            ele.clear()
            ele.send_keys(nav_element['kindle_mail'])
            nav_element.pop('kindle_mail')
        if 'password' in nav_element:
            ele = cls.driver.find_element_by_id('password')
            ele.clear()
            ele.send_keys(nav_element['password'])
            nav_element.pop('password')
        if 'email' in nav_element:
            ele = cls.driver.find_element_by_id('email')
            ele.clear()
            ele.send_keys(nav_element['email'])
            nav_element.pop('email')


        # check if checkboxes are in list and seperate lists
        for element,key in enumerate(nav_element):
            if key in selects:
                process_selects[key] = nav_element[key]
            else:
                process_checkboxes[key] = nav_element[key]

        # process all checkboxes Todo: If status was wrong before is not included in response
        for checkbox in process_checkboxes:
            ele = cls.driver.find_element_by_id(checkbox)
            if (nav_element[checkbox] == 1 and not ele.is_selected()) or nav_element[checkbox] == 0 and ele.is_selected():
                ele.click()

        # process all selects
        for option, key in enumerate(process_selects):
            select = Select(cls.driver.find_element_by_id(key))
            select.select_by_visible_text(process_selects[key])

        # finally submit settings
        cls.driver.find_element_by_id("user_submit").click()

    def create_shelf(self, name, public=False, sync=None):
        self.goto_page('create_shelf')
        ele = self.check_element_on_page((By.ID,'title'))
        if ele:
            ele.clear()
            ele.send_keys(name)
            if public:
                public_shelf = self.check_element_on_page((By.NAME,'is_public'))
                if public_shelf:
                    public_shelf.click()
                else:
                    return False
            if sync:
                sync_shelf = self.check_element_on_page((By.NAME, 'kobo_sync'))
                if sync_shelf:
                    sync_shelf.click()
            submit = self.check_element_on_page((By.ID, 'submit'))
            if submit:
                submit.click()
                return True
        return False

    def change_shelf(self, name, new_name=None, public=None, sync=None):
        shelf = self.list_shelfs(name)
        if shelf:
            shelf['ele'].click()
            edit = self.check_element_on_page((By.ID, "edit_shelf"))
            self.assertTrue(edit)
            edit.click()
            if new_name:
                title = self.check_element_on_page((By.ID, "title"))
                self.assertTrue(title)
                title.clear()
                title.send_keys(new_name)
            if public != None:
                access = self.check_element_on_page((By.NAME, "is_public"))
                self.assertTrue(access)
                if (public == 1 and not access.is_selected()) or public == 0 and access.is_selected():
                    access.click()
            if sync != None:
                sync_box = self.check_element_on_page((By.NAME, "kobo_sync"))
                self.assertTrue(sync_box)
                if (sync == 1 and not sync_box.is_selected()) or sync == 0 and sync_box.is_selected():
                    access.click()

            if new_name or public:
                submit = self.check_element_on_page((By.ID, "submit"))
                submit.click()
                self.assertTrue(self.check_element_on_page((By.ID, "flash_success")))


        else:
            return False
        ele = self.check_element_on_page((By.ID,'title'))
        if ele:
            ele.clear()
            ele.send_keys(name)
            if public:
                public_shelf = self.check_element_on_page((By.NAME,'is_public'))
                if public_shelf:
                    public_shelf.click()
                else:
                    return False
            submit = self.check_element_on_page((By.ID, 'user_submit'))
            if submit:
                submit.click()
                return True
        return False

    def delete_shelf(self, name=None):
        if name:
            self.list_shelfs(name)['ele'].click()
        self.check_element_on_page((By.ID, "delete_shelf")).click()
        self.check_element_on_page((By.ID, "btnConfirmYes-GeneralDeleteModal")).click()
        time.sleep(1)
        return


    @classmethod
    def create_user(cls, name, config):
        if name:
            config['name'] = name
        cls.goto_page('create_user')
        return cls.change_user(config)

    @classmethod
    def get_user_list(cls):
        cls.goto_page('admin_setup')
        userlist = cls.driver.find_elements_by_xpath("//table[@id='table_user']/tbody/tr/td[1]")
        users = list()
        for element in userlist:
            users.append(element.text)
        return users

    @classmethod
    def change_user(cls, config, abort=False):
        ''' All Checkboses are:
            'show_32','show_512', 'show_16', 'show_128', 'show_2', 'show_4',
            'show_8', 'show_64', 'show_256', 'Show_detail_random' '''
        selects = ['locale', 'default_language']
        text_inputs = ['kindle_mail', 'email', 'password', 'name']
        process_selects = dict()
        process_checkboxes = dict()
        process_text = dict()
        if 'delete' in config:
            if config['delete'] == 1:
                time.sleep(2)
                cls.driver.find_element_by_id('btndeluser').click()
                time.sleep(2)
                if not abort:
                    cls.driver.find_element_by_id('btnConfirmYes-GeneralDeleteModal').click()
                else:
                    cls.driver.find_element_by_id('btnConfirmNo-GeneralDeleteModal').click()
                time.sleep(2)
                if abort:
                    cls.check_element_on_page((By.ID, "back")).click()
                    time.sleep(1)
                return

        # check if checkboxes are in list and seperate lists
        if 'resend_password' in config:
            ele = cls.driver.find_element_by_id('resend_password')
            if ele:
                ele.click()
                return cls.driver.find_element_by_id('flash_success')
            return ele

        for element,key in enumerate(config):
            if key in selects:
                process_selects[key] = config[key]
            elif key in text_inputs:
                process_text[key] = config[key]
            else:
                process_checkboxes[key] = config[key]

        # process all checkboxes Todo: If status was wrong before is not included in response
        for checkbox in process_checkboxes:
            ele = cls.driver.find_element_by_id(checkbox)
            if (config[checkbox] == 1 and not ele.is_selected()) or config[checkbox] == 0 and ele.is_selected():
                ele.click()
                eleclick = cls.driver.find_element_by_id(checkbox)
                if (config[checkbox] == 1 and not eleclick.is_selected()) or config[checkbox] == 0 and eleclick.is_selected():
                    print('click did not work')
                    time.sleep(2)
                    ele.click()

        # process all selects
        for option, key in enumerate(process_selects):
            select = Select(cls.driver.find_element_by_id(key))
            select.select_by_visible_text(process_selects[key])

        # process all text fields
        for element, key in enumerate(process_text):
            ele = cls.driver.find_element_by_id(key)
            ele.clear()
            ele.send_keys(config[key])

        # finally submit settings
        cls.driver.find_element_by_id("user_submit").click()


    @classmethod
    def get_opds_index(cls,text):
        ret = dict()
        parser = lxml.etree.HTMLParser()
        try:
            tree = lxml.etree.fromstring(text.encode('utf-8'), parser)
            ret['updated'] = tree.xpath("/html/body/feed/updated")[0].text
            links= tree.xpath("/html/body/feed/link")
            ret['links'] = links
            for link in links:
                if link.attrib['rel'] == "self":
                    ret['self_link'] = link.attrib['href']
                if link.attrib['rel'] == "start":
                    ret['start_link'] = link.attrib['href']
                if link.attrib['rel'] == "search" and link.attrib['type'] == "application/opensearchdescription+xml":
                    ret['osd_link'] = link.attrib['href']
                if link.attrib['rel'] == "search" and link.attrib['type'] == "application/atom+xml":
                    ret['search_link'] = link.attrib['href']
            ret['title'] = tree.xpath("/html/body/feed/title")[0].text
            ret['id'] = tree.xpath("/html/body/feed/id")[0].text
            ret['update'] = tree.xpath("/html/body/feed/updated")[0].text
            ret['author'] = tree.xpath("/html/body/feed/author/name")[0].text
            ret['uri'] = tree.xpath("/html/body/feed/author/uri")[0].text
            for element in tree.xpath("/html/body/feed/entry"):
                el = dict()
                el['link'] = element.find('link').attrib['href']
                el['id'] = element.find('id').text
                el['updated'] = element.find('updated').text
                el['content'] = element.find('content').text
                ret[element.find('title').text] = el
        except:
            pass
        return ret


    @classmethod
    def get_opds_feed(cls, text):
        ret = dict()
        parser = lxml.etree.HTMLParser()
        try:
            tree = lxml.etree.fromstring(text.encode('utf-8'), parser)
            # tree = lxml.etree.parse(StringIO(text.encode('utf-8')), parser)
            ret['title'] = tree.xpath("/html/body/feed/title")[0].text
            ret['id'] = tree.xpath("/html/body/feed/id")[0].text
            links= tree.xpath("/html/body/feed/link")
            ret['links'] = links
            for link in links:
                if link.attrib['rel'] == "self":
                    ret['self_link'] = link.attrib['href']
                if link.attrib['rel'] == "start":
                    ret['start_link'] = link.attrib['href']
                if link.attrib['rel'] == "up":
                    ret['up_link'] = link.attrib['href']
                if link.attrib['rel'] == "first":
                    ret['first_link'] = link.attrib['href']
                if link.attrib['rel'] == "next":
                    ret['next_link'] = link.attrib['href']
                if link.attrib['rel'] == "previous":
                    ret['previous_link'] = link.attrib['href']
                if link.attrib['rel'] == "search" and link.attrib['type'] == "application/opensearchdescription+xml":
                    ret['osd_link'] = link.attrib['href']
                if link.attrib['rel'] == "search" and link.attrib['type'] == "application/atom+xml":
                    ret['search_link'] = link.attrib['href']
            ret['update'] = tree.xpath("/html/body/feed/updated")[0].text
            ret['author'] = tree.xpath("/html/body/feed/author/name")[0].text
            ret['uri'] = tree.xpath("/html/body/feed/author/uri")[0].text
            ret['elements'] = list()
            key = 0
            for element in tree.xpath("/html/body/feed/entry"):
                el = dict()
                el['link'] = element.find('link').attrib['href']
                el['id'] = element.find('id').text
                el['title'] = element.find('title').text
                ele =  element.find('language')
                if ele is not None and ele.text:
                    el['language'] = ele
                ele = element.findall('link')
                if ele is not None:
                    el['cover'] = ele[0].attrib['href']
                    if len(ele) >=2:
                        el['download'] = ele[2].attrib['href']
                        el['filesize'] = ele[2].attrib['length']
                        el['filetype'] = ele[2].attrib['type']
                        el['time'] = ele[2].attrib['mtime']
                ele = element.find('author')
                if ele is not None:
                    author_list = list()
                    for aut in ele.getchildren():
                        author_list.append(aut.text)
                    el['author']=author_list
                    el['author_len'] = len(el['author'])
                ele = element.find('summary')
                if ele is not None:
                    el['comment'] = ele
                ele = element.find('category')
                if ele is not None:
                    tag_list = list()
                    for tag in ele:
                        tag_list.append(tag.attrib['term'])
                    el['tags'] = tag_list
                    el['tag_len'] = len(el['tags'])
                ret['elements'].append(el)
                key += 1
        except:
            pass
        ret['len'] = key
        return ret


    @classmethod
    def get_opds_search(cls, text):
        ret = dict()
        parser = lxml.etree.HTMLParser()
        try:
            tree = lxml.etree.fromstring(text.encode('utf-8'), parser)
            ret['longname'] = tree.xpath("/html/body/opensearchdescription/longname")[0].text
            ret['shortname'] = tree.xpath("/html/body/opensearchdescription/shortname")[0].text
            ret['description'] = tree.xpath("/html/body/opensearchdescription/description")[0].text
            ret['author'] = tree.xpath("/html/body/opensearchdescription/developer")[0].text
            ret['uri'] = tree.xpath("/html/body/opensearchdescription/contact")[0].text
            ret['search'] = tree.xpath("/html/body/opensearchdescription/url")
            ret['language'] = tree.xpath("/html/body/opensearchdescription/language")[0].text
            ret['out_encoding'] = tree.xpath("/html/body/opensearchdescription/outputencoding")[0].text
            ret['in_encoding'] = tree.xpath("/html/body/opensearchdescription/inputencoding")[0].text
        except Exception as e:
            pass
        return ret

    @classmethod
    def get_books_displayed(cls):
        parser = lxml.etree.HTMLParser()
        html = cls.driver.page_source

        tree = lxml.etree.parse(StringIO(html), parser)
        books_rand = list()
        br = tree.xpath("//*[@class='discover random-books']/div/div")
        for book_rand in br:
            ele = book_rand.getchildren()
            meta=ele[1].getchildren()
            book_r = dict()
            book_r['link'] = ele[0].getchildren()[0].attrib['href']
            book_r['ele'] = cls.check_element_on_page((By.XPATH,"//a[@href='"+book_r['link']+"']//img"))
            book_r['id'] = book_r['link'][6:]
            book_r['title']= meta[0].getchildren()[0].text
            authors = meta[1].getchildren()
            book_r['author'] = [a.text for a in authors if a.text != '&' and a.attrib.get('class') != 'author-name author-hidden']
            if len(meta) >= 3:
                for met in meta[2:]:
                    element = met.getchildren()
                    if len(element):
                        if 'class' in element[0].attrib:
                            counter = 0
                            for rating in element:
                                if rating.attrib['class'] == 'glyphicon glyphicon-star good':
                                    counter += 1
                            book_r['rating'] = counter
                        elif 'href' in element[0].attrib:
                            book_r['series'] = element[0].text.rstrip().lstrip()
                            book_r['series_index'] = element[0].tail.rstrip().lstrip().strip(')').lstrip('(')
            books_rand.append(book_r)
        books = list()
        b = tree.xpath("//*[@class='discover load-more']/div/div")
        for book in b:
            ele = book.getchildren()
            # ele[0] -> cover
            meta=ele[1].getchildren()
            bk = dict()
            bk['link'] = ele[0].getchildren()[0].attrib['href']
            bk['id'] = bk['link'][6:]
            bk['ele'] = cls.check_element_on_page((By.XPATH,"//a[@href='"+bk['link']+"']//img"))
            bk['title']= meta[0].getchildren()[0].text
            authors = meta[1].getchildren()
            bk['author'] = [a.text for a in authors if a.text != '&' and a.attrib.get('class') != 'author-name author-hidden']
            if len(meta) >= 3:
                for met in meta[2:]:
                    element = met.getchildren()
                    if len(element):
                        if 'class' in element[0].attrib:
                            counter = 0
                            for rating in element:
                                if rating.attrib['class'] == 'glyphicon glyphicon-star good':
                                    counter += 1
                            bk['rating'] = counter
                        elif 'href' in element[0].attrib:
                            bk['series'] = element[0].text.rstrip().lstrip()
                            bk['series_index'] = element[0].tail.rstrip().lstrip().strip(')').lstrip('(')
            books.append(bk)

        pages = tree.xpath("//*[@class='pagination']/a")
        pagination = None
        if len(pages):
            pagination = [p.text for p in pages]
        return [books_rand, books, pagination]

    @classmethod
    def get_series_books_displayed(cls):
        # expects grid view
        #grid = cls.check_element_on_page((By.ID, "list-button"))
        #if grid:
        #    grid.click()
        #    cls.check_element_on_page((By.ID, "grid-button"))
        parser = lxml.etree.HTMLParser()
        html = cls.driver.page_source

        tree = lxml.etree.parse(StringIO(html), parser)
        books = list()
        b = tree.xpath("//*[@id='list']/div")
        for book in b:
            ele = book.getchildren()
            # ele[0] -> cover
            meta=ele[1].getchildren()
            bk = dict()
            bk['link'] = ele[1].getchildren()[0].attrib['href']
            bk['id'] = bk['link'].split('/')[-1]
            bk['ele'] = cls.check_element_on_page((By.XPATH,"//a[@href='"+bk['link']+"']//img"))
            bk['title']= meta[0].getchildren()[0].text
            books.append(bk)

        return books

    def verify_order(self, page, index=-1, order=None):
        if order is None:
            order = {}
        if page =="search":
            list_elements = self.get_shelf_books_displayed()
        else:
            list_elements = self.goto_page(page)
        time.sleep(2)
        if index >= 0:
            if not len(list_elements):
                list_elements = self.get_series_books_displayed()
                list_elements[index]['ele'].click()
            else:
                if page == "nav_rate":
                    list_elements[index].find_element_by_xpath('..').click()
                else:
                    list_elements[index].click()
        for key, element in order.items():
            self.check_element_on_page((By.ID, key)).click()
            if page == "search":
                books = self.get_shelf_books_displayed()
            else:
                books = self.get_books_displayed()
            for index, expected_result in enumerate(element):
                if page == "search":
                    book_id = int(books[index]['id'])
                else:
                    book_id = int(books[1][index]['id'])
                self.assertEqual(book_id, expected_result, "Key sorting order wrong: " + key)

    def get_shelf_books_displayed(self):
        parser = lxml.etree.HTMLParser()
        html = self.driver.page_source
        tree = lxml.etree.parse(StringIO(html), parser)

        books = list()
        b = tree.xpath("//*[@class='row display-flex']/div")
        for book in b:
            ele = book.getchildren()
            # ele[0] -> cover
            meta=ele[1].getchildren()
            bk = dict()
            bk['link'] = ele[0].getchildren()[0].attrib['href']
            bk['id'] = bk['link'][6:]
            bk['ele'] = self.check_element_on_page((By.XPATH,"//a[@href='"+bk['link']+"']//img"))
            bk['title']= meta[0].getchildren()[0].text
            authors = meta[1].getchildren()
            bk['author'] = [a.text for a in authors if a.text != '&' and a.attrib.get('class') != 'author-name author-hidden']
            if len(meta) >= 3:
                for met in meta[2:]:
                    element = met.getchildren()
                    if len(element):
                        if 'class' in element[0].attrib:
                            counter = 0
                            for rating in element:
                                if rating.attrib['class'] == 'glyphicon glyphicon-star good':
                                    counter += 1
                            bk['rating'] = counter
                        elif 'href' in element[0].attrib:
                            bk['series'] = element[0].text.rstrip().lstrip()
                            bk['series_index'] = element[0].tail.rstrip().lstrip().strip(')').lstrip('(')
            books.append(bk)
        return books

    def get_order_shelf_list(self):
        parser = lxml.etree.HTMLParser()
        html = self.driver.page_source
        tree = lxml.etree.parse(StringIO(html), parser)

        books = list()
        b = tree.xpath("//*[@id='sortTrue']/div")
        for book in b:
            #ele = book.getchildren()
            # ele[0] -> cover
            meta=book.getchildren()[0].getchildren()[1]
            bk = dict()
            bk['id'] = book.attrib['id']
            #bk['link'] = ele[0].getchildren()[0].attrib['href']
            #bk['id'] = bk['link'][6:]
            bk['ele'] = self.check_element_on_page((By.ID,bk['id']))
            bk['title']= meta.text.strip()
            next = meta.getchildren()
            if len(next) == 2:
                bk['author'] = meta.getchildren()[1].tail.strip()
                bk['series'] = meta.getchildren()[0].tail.strip()
            else:
                bk['author'] = meta.getchildren()[0].tail.strip()
            books.append(bk)
        return books

    @classmethod
    def get_book_details(cls,id=-1,root_url="http://127.0.0.1:8083"):
        ret = dict()
        if id > 0:
            cls.driver.get(root_url + "/book/" + str(id))
            ret['id'] = id
        else:
            ret['id'] = int(cls.driver.current_url.split("/")[-1])
        cls.check_element_on_page((By.TAG_NAME,"h2"))
        try:
            parser = lxml.etree.HTMLParser()
            html = cls.driver.page_source

            tree = lxml.etree.parse(StringIO(html), parser)
            reader = tree.findall("//*[@aria-labelledby='read-in-browser']/li/a")
            ret['reader'] = [r.text for r in reader]

            title = tree.find("//h2")
            if title is not None:
                ret['title'] = title.text
            author = tree.findall("//*[@class='author']/a")
            ret['author'] = [aut.text for aut in author]

            ret['rating']= len(tree.findall("//*[@class='glyphicon glyphicon-star good']"))

            languages = tree.findall("//*[@class='languages']//span")
            if languages:
                only_lang = languages[0].text.split(': ')[1].lstrip()
                ret['languages'] = only_lang.split(', ')

            ids = tree.findall("//*[@class='identifiers']//a")
            ret['identifier'] = [{id.text:id.attrib['href']} for id in ids]

            # find cover
            ret['cover'] = tree.find("//*[@class='cover']//img").attrib['src']

            tags = tree.findall("//*[@class='tags']//a")
            ret['tag'] = [tag.text for tag in tags]

            publishers = tree.findall("//*[@class='publishers']//a")
            ret['publisher'] = [pub.text for pub in publishers]

            # Pubdate
            pubdate = tree.xpath("//p[starts-with(text(),'Published:')]")
            if len(pubdate):
                ret['pubdate']= pubdate[0].text.lstrip('Published: ').strip()

            comment = tree.find("//*[@class='comments']")
            ret['comment'] = ''
            if comment is not None:
                if len(comment.getchildren()) == 1:
                    ret['comment'] = comment.getchildren()[0].tail.strip()
                else:
                    comm = tree.xpath("//*[@class='comments']/h3/following-sibling::*")
                    if comm[0].getchildren():
                        for ele in comm[0].getchildren():
                            if isinstance(ele.text,str):
                                ret['comment'] += ele.text.strip()
                    else:
                        for ele in comm:
                            if isinstance(ele.text, str):
                                ret['comment'] += ele.text.strip()

            add_shelf = tree.findall("//*[@id='add-to-shelves']//a")
            ret['add_shelf'] = [sh.text.strip().lstrip() for sh in add_shelf]

            del_shelf = tree.findall("//*[@id='remove-from-shelves']//a")
            ret['del_shelf'] = [sh.text.strip().lstrip() for sh in del_shelf]

            ret['edit_enable'] = tree.find("//*[@class='glyphicon glyphicon-edit']") is not None

            ele = tree.xpath("//*[starts-with(@id,'sendbtn')]")
            # bk['ele'] = cls.check_element_on_page((By.XPATH, "//a[@href='" + bk['link'] + "']/img"))
            if len(ele):
                all = tree.findall("//*[@aria-labelledby='send-to-kindle']/li/a")
                if all:
                    ret['kindlebtn'] = cls.driver.find_element_by_id("sendbtn2")
                    ret['kindle'] = all
                else:
                    ret['kindlebtn'] = cls.driver.find_element_by_id("sendbtn")
                    ret['kindle'] = list(ele)
            else:
                ret['kindle'] = None
                ret['kindlebtn'] = None

            download1 = tree.findall("//*[@aria-labelledby='btnGroupDrop1']//a")
            if not download1:
                download1 = tree.xpath("//*[starts-with(@id,'btnGroupDrop')]")
                if download1:
                    ret['download'] = list()
                    for ele in download1:
                        ret['download'].append(ele.getchildren()[0].tail.strip())
            else:
                ret['download'] = [d.text for d in download1]

            element = cls.check_element_on_page((By.XPATH, "//*[@id='have_read_cb']"))
            if element:
                ret['read']= element.is_selected()
            else:
                ret['read'] = None
            archive = cls.check_element_on_page((By.XPATH, "//*[@id='archived_cb']"))
            if archive:
                ret['archived'] = archive.is_selected()
            else:
                ret['archived'] = None


            series = tree.xpath("//*[contains(@href,'series')]/ancestor::p")
            if series:
                ret['series_all'] = ""
                ret['series_index'] = series[0].text[5:-3].strip()
                for ele in series[0].iter():
                    ret['series_all'] += ele.text
                    ret['series'] = ele.text

            cust_columns = tree.xpath("//div[@class='real_custom_columns']")
            if len(cust_columns) :      # we have custom columns
                ret['cust_columns'] = list()
                for col in cust_columns: # .getchildren()[0].getchildren()[1:]:
                    element = dict()
                    if len(col.text.strip()):
                        if len(col.getchildren()):
                            element['Text'] = col.text.lstrip().split(':')[0]
                            try:
                                element['value'] = col.getchildren()[0].attrib['class'][20:]
                            except KeyError:
                                element['value'] = col.getchildren()[0].text
                            ret['cust_columns'].append(element)
                        elif ':' in col.text:
                            element['Text'] = col.text.lstrip().split(':')[0]
                            element['value'] = col.text.split(':')[1].strip()
                            ret['cust_columns'].append(element)
                        else:
                            pass
        except Exception as e:
            print(e)
            pass
        return ret

    def download_book(self, id, user, password):
        self.get_book_details(id)
        element = self.check_element_on_page((By.XPATH, "//*[starts-with(@id,'btnGroupDrop')]"))
        download_link = element.get_attribute("href")
        r = requests.session()
        payload = {'username': user, 'password': password, 'submit':"", 'next':"/", "remember_me":"on"}
        r.post('http://127.0.0.1:8083/login', data=payload)
        resp = r.get(download_link)
        r.close()
        return resp.status_code, resp.content

    @classmethod
    def check_tasks(cls, ref=None):
        if cls.goto_page('tasks'):
            time.sleep(1)
            parser = lxml.etree.HTMLParser()
            html = cls.driver.page_source

            tree = lxml.etree.parse(StringIO(html), parser)
            vals = tree.xpath("//table[@id='tasktable']/tbody/tr")
            val = list()
            for va in vals:
                try:
                    go = va.getchildren()
                    if len(go) == 6:
                        val.append({'user':' '.join(go[0].itertext()),
                                    'task': ''.join(go[1].itertext()),
                                    'result': ''.join(go[2].itertext()),
                                    'progress': ''.join(go[3].itertext()),
                                    'duration': ''.join(go[4].itertext()),
                                    'start':''.join(go[5].itertext())})
                    else:
                        val.append({'user': None,
                                    'task': ''.join(go[0].itertext()),
                                    'result': ''.join(go[1].itertext()),
                                    'progress': ''.join(go[2].itertext()),
                                    'duration': ''.join(go[3].itertext()),
                                    'start': ''.join(go[4].itertext())})
                except IndexError:
                    pass
            if isinstance(ref, list):
                res = len([i for i in val if i in ref])
                return (len(val) - res), val
            return val
        else:
            return False

    @classmethod
    def select_date_with_editor(cls, element, delete_element, target_date):
        if target_date == "":
            cls.check_element_on_page((By.ID, delete_element)).click()
        else:
            dates = target_date.split('/')
            month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                           'October', 'November', 'December']
            cls.check_element_on_page((By.ID, element)).click()
            month_year = cls.check_element_on_page((By.CLASS_NAME, 'datepicker-switch')).text.split(' ')
            if month_year[1] != dates[2] or month_year[0] != month_names[int(dates[1]) - 1]:
                cls.check_element_on_page((By.CLASS_NAME, 'datepicker-switch')).click()
                if month_year[1] != dates[2]:
                    cls.driver.find_element_by_xpath(
                        "//div[@class='datepicker-months']//th[@class='datepicker-switch']").click()
                    year_range = cls.driver.find_element_by_xpath(
                        "//div[@class='datepicker-years']//th[@class='datepicker-switch']").text.split('-')
                    if dates[2] < year_range[0] or dates[2] > year_range[1]:
                        if dates[2] < year_range[0]:
                            while dates[2] < year_range[0]:
                                cls.driver.find_element_by_xpath(
                                    "//div[@class='datepicker-years']//th[@class='prev']").click()
                                year_range = cls.driver.find_element_by_xpath(
                                    "//div[@class='datepicker-years']//th[@class='datepicker-switch']").text.split('-')
                        else:
                            while dates[2] > year_range[1]:
                                cls.driver.find_element_by_xpath(
                                    "//div[@class='datepicker-years']//th[@class='next']").click()
                                year_range = cls.driver.find_element_by_xpath(
                                    "//div[@class='datepicker-years']//th[@class='datepicker-switch']").text.split('-')
                    years = cls.driver.find_elements_by_xpath("//span[starts-with(@class,'year')]")
                    for y in years:
                        if y.text == dates[2]:
                            y.click()
                            break
                months = cls.driver.find_elements_by_class_name("month")
                months[int(dates[1]) - 1].click()
            days = cls.driver.find_elements_by_xpath("//td[starts-with(@class,'day')]")
            days[int(dates[0]) - 1].click()
            webdriver.ActionChains(cls.driver).send_keys(Keys.ESCAPE).perform()

    @classmethod
    def edit_book(cls, id=-1, content=dict(), custom_content=dict(), detail_v=False, root_url='http://127.0.0.1:8083'):
        if id>0:
            cls.driver.get(root_url + "/admin/book/"+str(id))
            time.sleep(2)
        cls.check_element_on_page((By.ID,"book_edit_frm"))

        if custom_content:
            # Handle custom columns:
            parser = lxml.etree.HTMLParser()
            html = cls.driver.page_source

            tree = lxml.etree.parse(StringIO(html), parser)

            cust_columns = tree.xpath("//*[starts-with(@for,'custom_column')]")
            if cust_columns:
                for col in cust_columns:
                    element = dict()
                    element['label'] = col.text
                    element['index'] = col.attrib['for']
                    if element['label'] in custom_content:
                        if element['label'] == 'Custom Date Column 人物':
                            cls.select_date_with_editor('custom_column_2', 'custom_column_2_delete',
                                                        custom_content['Custom Date Column 人物'])
                        elif col.getnext().tag == 'select':
                            select = Select(cls.driver.find_element_by_id(element['index']))
                            select.select_by_visible_text(custom_content[element['label']])
                        elif col.getnext().tag == 'input':
                            edit = cls.check_element_on_page((By.ID, element['index']))
                            edit.send_keys(Keys.CONTROL, "a")
                            edit.send_keys(Keys.DELETE)
                            edit.send_keys(custom_content[element['label']])
                        elif col.getnext().tag == 'textarea':
                            cls.driver.switch_to.frame(element['index'] + "_ifr")
                            ele = cls.check_element_on_page((By.ID, 'tinymce'))
                            ele.clear()
                            ele.send_keys(custom_content[element['label']])
                            cls.driver.switch_to.default_content()

        if 'local_cover' in content:
            local_cover = cls.check_element_on_page((By.ID, 'btn-upload-cover'))
            local_cover.send_keys(content['local_cover'])
            content.pop('local_cover')

        if 'rating' in content:
            cls.driver.execute_script("arguments[0].setAttribute('value', arguments[1])",
                                  cls.driver.find_element_by_xpath("//input[@id='rating']"), content['rating'])
            content.pop('rating')

        if 'description' in content:
            cls.driver.switch_to.frame("description_ifr")
            ele = cls.check_element_on_page((By.ID, 'tinymce'))
            ele.clear()
            ele.send_keys(content['description'])
            cls.driver.switch_to.default_content()
            content.pop('description')


        for element, key in enumerate(content):
            if key == 'pubdate':
                continue
            ele = cls.check_element_on_page((By.ID, key))
            ele.send_keys(Keys.CONTROL, "a")
            ele.send_keys(Keys.DELETE)
            if ele.get_attribute('value') != '':
                print("clear didn't work")
            ele.send_keys(content[key])

        if 'pubdate' in content:
            cls.select_date_with_editor('pubdate', 'pubdate_delete', content['pubdate'])

        # don't stay on page after edit
        if detail_v:
            cls.check_element_on_page((By.NAME, "detail_view")).click()

        submit = cls.check_element_on_page((By.ID, "submit"))
        submit.click()
        return

    def save_cover_screenshot(self, filename):
        element = self.driver.find_element_by_tag_name('img')
        location = element.location
        size = element.size
        self.driver.save_screenshot("page.png")
        x = location['x']
        y = location['y']
        width = location['x'] + size['width']
        height = location['y'] + size['height']
        im = Image.open('page.png')
        im = im.crop((int(x), int(y), int(width), int(height)))
        im.save(filename)

    def add_identifier(self, key, value):
        add_button = self.check_element_on_page((By.ID, "add-identifier-line"))
        if not add_button:
            return False
        add_button.click()
        try:
            key_input = self.driver.find_elements_by_xpath("//input[starts-with(@name, 'identifier-type-')]")[-1]
        except Exception:
            return False
        try:
            value_input = self.driver.find_elements_by_xpath("//input[starts-with(@name, 'identifier-val-')]")[-1]
        except Exception:
            return False
        key_input.send_keys(key)
        value_input.send_keys(value)
        return key_input.get_attribute("name").split('-')[-1]

    def edit_identifier_value(self, key, value):
        value_input = self.check_element_on_page((By.XPATH, "//input[starts-with(@name, 'identifier-val-" + key + "')]"))
        if not value_input:
            return False
        value_input.send_keys(Keys.CONTROL, "a")
        value_input.send_keys(Keys.DELETE)
        value_input.send_keys(value)
        return True

    def edit_identifier_key(self, key_old, key_new):
        key_input = self.check_element_on_page((By.XPATH, "//input[starts-with(@name, 'identifier-type-" + key_old + "')]"))
        if not key_input:
            return False
        key_input.send_keys(Keys.CONTROL, "a")
        key_input.send_keys(Keys.DELETE)
        key_input.send_keys(key_new)
        return True

    def get_identifier_value(self, key):
        value = self.check_element_on_page((By.XPATH, "//input[starts-with(@name, 'identifier-val-" + key + "')]"))
        if not value:
            return False
        return value.get_attribute('value')


    def delete_identifier(self, key):
        delete_button = self.check_element_on_page((By.XPATH, "//tr[td/input[@name='identifier-type-" + key + "']]/td/a"))
        if not delete_button:
            return False
        delete_button.click()
        return True

    def delete_book(self, id):
        self.get_book_details(id)
        self.check_element_on_page((By.ID, "edit_book")).click()
        self.check_element_on_page((By.ID, "delete")).click()
        self.check_element_on_page((By.ID, "delete_confirm")).click()
        time.sleep(2)

    def delete_book_format(self, id, format):
        self.get_book_details(id)
        self.check_element_on_page((By.ID, "edit_book")).click()
        b = self.check_element_on_page((By.XPATH, "//*[@data-delete-format='" + format.upper() + "']"))
        if not b:
            return False
        b.click()
        c = self.check_element_on_page((By.ID, "delete_confirm"))
        if not c:
            return False
        c.click()
        time.sleep(2)
        return True

    def goto_list_page(self, page):
        if page == 1:
            return True
        pages = self.driver.find_elements_by_class_name("page-item")
        for p in pages:
            if p.text == str(page):
                if 'active' not in p.get_attribute('class'):
                    ele = p.find_element_by_xpath('./a')
                    ele.click()
                return True
        return False

    def get_books_list(self, page=1):
        # get current page
        if not page == -1:
            self.goto_page('nav_list')
            time.sleep(2)
            if not self.goto_list_page(page):
                return False
        else:
            time.sleep(1)
        header = self.driver.find_elements_by_xpath("//thead/tr/th/div[starts-with(@class, 'th-inner')]")
        rows = self.driver.find_elements_by_xpath("//tbody/tr")
        table = list()
        ret = dict()
        for element in rows:
            ele = dict()
            row_elements = element.find_elements_by_xpath("./td")
            for cnt, el in enumerate(row_elements):
                click_element = el.find_elements_by_xpath("./a | ./label/input | ./div")
                if click_element and len(click_element):
                    click_element = click_element[0]
                else:
                    click_element = el
                if header[cnt].text == "":
                    index = "selector"
                else:
                    index = header[cnt].text
                if click_element.text == "" and click_element.tag_name == "a":
                    element_text = "+" if "glyphicon-plus" in click_element.find_elements_by_xpath("./span")[0].get_attribute('class') else ""
                else:
                    element_text = el.text
                ele[index] = {'element': click_element, 'sort': header[cnt], 'text': element_text}
            table.append(ele)

        ret['pagination'] = dict()
        if self.check_element_on_page((By.CLASS_NAME, "pagination")):
            pages = self.driver.find_elements_by_class_name("page-item")
            for page in pages:
                active = 'active' in page.get_attribute('class')
                disabled = "disabled" in page.get_attribute('class')
                ret['pagination'][page.text] = {'link': page.find_element_by_xpath('./a'), 'active': active, 'disabled': disabled}
        ret['table'] = table
        ret['column'] = self.check_element_on_page((By.XPATH, "//*[@aria-label='Columns']"))
        ret['column_elements'] = self.driver.find_elements_by_xpath("//*[@role='menuitem']/label/input")
        ret['column_texts'] = self.driver.find_elements_by_xpath("//*[@role='menuitem']/label/span")
        ret['search'] = self.check_element_on_page((By.CLASS_NAME, "search-input"))
        ret['remove-btn'] = self.check_element_on_page((By.ID, "delete_selection"))
        ret['merge-btn'] = self.check_element_on_page((By.ID, "merge_books"))
        ret['title_sort'] = self.check_element_on_page((By.ID, "autoupdate_titlesort"))
        ret['author_sort'] = self.check_element_on_page((By.ID, "autoupdate_authorsort"))
        return ret

    def edit_table_select(self, table_select, new_value, cancel=False):
        table_select.click()
        select = Select(table_select.find_element_by_xpath("..//select"))
        select.select_by_visible_text(new_value)

        if not cancel:
            table_select.find_element_by_xpath("..//button[contains(@class,'btn-primary')]").click()
        else:
            table_select.find_element_by_xpath("..//button[contains(@class,'btn-default')]").click()

    def edit_table_element(self, table_element, new_value, cancel=False):
        # get text of element
        table_element.click()
        element = table_element.find_element_by_xpath("..//input") # .get_attribute('value')
        element.clear()
        element.send_keys(new_value)
        if not cancel:
            table_element.find_element_by_xpath("..//button[contains(@class,'btn-primary')]").click()
        else:
            table_element.find_element_by_xpath("..//button[contains(@class,'btn-default')]").click()

    def get_user_table(self, page=1):
        # get current page
        if not page == -1:
            self.goto_page('user_list')
            time.sleep(2)
            if not self.goto_list_page(page):
                return False
        else:
            time.sleep(1)
        # header = self.driver.find_elements_by_xpath("//thead/tr/th/div[starts-with(@class, 'th-inner')]")
        header_edit = list()
        header = self.driver.find_elements_by_xpath("//table[@id='user-table']/thead/tr/th")
        for cnt, head in enumerate(header):
            header_edit.insert(cnt, dict())
            header_edit[cnt]['sort'] = head.find_element_by_xpath("./div[starts-with(@class, 'th-inner')]")
            if head.get_attribute("data-field") == "locale":
                header_edit[cnt]['text'] = head.text.split("\n")[-1]
                header_edit[cnt]['element'] = head.find_element_by_xpath(".//div/select")
            elif head.get_attribute("data-field") == "default_language":
                header_edit[cnt]['text'] = head.text.split("\n")[-1]
                header_edit[cnt]['element'] = head.find_element_by_xpath(".//div/select")
            elif head.get_attribute("data-field") in ["role", "sidebar_view"]:
                if head.get_attribute("data-field") == "role":
                    header_edit[cnt]['text'] = head.get_attribute("data-field") + "_" + head.find_element_by_xpath("./div").text.split("\n")[2]
                else:
                    header_edit[cnt]['text'] = head.find_element_by_xpath("./div").text.split("\n")[2]
                header_edit[cnt]['element'] = head.find_elements_by_xpath(".//div[contains(@class,'form-check')]//input")
            elif head.get_attribute("data-field") in ["denied_tags", "allowed_tags"]:
                try:
                    header_edit[cnt]['element'] = head.find_element_by_xpath(
                        ".//div[contains(@class,'multi_select')]")
                    header_edit[cnt]['text'] = head.find_elements_by_xpath("./div")[1].text
                except NoSuchElementException:
                    header_edit[cnt]['text'] = ""
            else:
                if header_edit[cnt]['sort'].text == "":
                    header_edit[cnt]['text'] = "selector"
                else:
                    header_edit[cnt]['text'] = header_edit[cnt]['sort'].text.split('\n')[-1]

        rows = self.driver.find_elements_by_xpath("//tbody/tr")

        table = list()
        ret = dict()
        for element in rows:
            ele = dict()
            row_elements = element.find_elements_by_xpath("./td")
            for cnt, el in enumerate(row_elements):
                click_element = el.find_elements_by_xpath("./a | ./label/input | ./div | ./button | ./input")
                if click_element and len(click_element):
                    click_element = click_element[0]
                else:
                    click_element = el
                index = header_edit[cnt]['text']
                if click_element.text == "" and click_element.tag_name == "a":
                    try:
                        element_text = "+" if "glyphicon-plus" in click_element.find_elements_by_xpath("./span")[0].get_attribute('class') else ""
                    except:
                        element_text = ""
                else:
                    element_text = el.text
                ele[index] = {'element': click_element, 'sort': header_edit[cnt]['sort'], 'text': element_text}
            table.append(ele)

        ret['pagination'] = dict()
        if self.check_element_on_page((By.CLASS_NAME, "pagination")):
            pages = self.driver.find_elements_by_class_name("page-item")
            for page in pages:
                active = 'active' in page.get_attribute('class')
                disabled = "disabled" in page.get_attribute('class')
                ret['pagination'][page.text] = {'link': page.find_element_by_xpath('./a'), 'active': active, 'disabled': disabled}
        ret['table'] = table
        ret['header'] = header_edit
        ret['column'] = self.check_element_on_page((By.XPATH, "//*[@aria-label='Columns']"))
        ret['column_elements'] = self.driver.find_elements_by_xpath("//*[@role='menuitem']/label/input")
        ret['column_texts'] = self.driver.find_elements_by_xpath("//*[@role='menuitem']/label/span")
        ret['search'] = self.check_element_on_page((By.CLASS_NAME, "search-input"))
        ret['remove-btn'] = self.check_element_on_page((By.ID, "user_delete_selection"))
        return ret


    @classmethod
    def get_convert_book(cls, id=-1, root_url='http://127.0.0.1:8083'):
        if id>0:
            cls.driver.get(root_url + "/admin/book/"+str(id))
        cls.check_element_on_page((By.ID,"book_edit_frm"))
        parser = lxml.etree.HTMLParser()
        html = cls.driver.page_source

        tree = lxml.etree.parse(StringIO(html), parser)
        ret = dict()
        ret['from_book'] = tree.findall("//select[@id='book_format_from']/option")
        ret['to_book'] = tree.findall("//select[@id='book_format_to']/option")
        if not ret['from_book'] and not ret['to_book']:
            ret['btn_from'] = False
            ret['btn_to'] = False
        else:
            ret['btn_from'] = cls.check_element_on_page((By.XPATH, "//select[@id='book_format_from']"))
            ret['btn_to'] = cls.check_element_on_page((By.XPATH, "//select[@id='book_format_to']"))
        return ret

    def search(self, term):
        field = self.check_element_on_page((By.ID, "query"))
        if field:
            field.clear()
            field.send_keys(term)
            send = self.check_element_on_page((By.ID, "query_submit"))
            if send:
                send.click()
                return self.get_shelf_books_displayed()
        return False

    # currently only title, author, comment
    def adv_search(self, term_dict, get=False):
        if self.goto_page('adv_search'):
            if get:
                inc_tags = self.driver.find_elements_by_xpath("//select[@id='include_tag']/option")
                exc_tags = self.driver.find_elements_by_xpath("//select[@id='exclude_tag']/option")
                inc_series = self.driver.find_elements_by_xpath("//select[@id='include_serie']/option")
                exc_series = self.driver.find_elements_by_xpath("//select[@id='exclude_serie']/option")
                inc_languages = self.driver.find_elements_by_xpath("//select[@id='include_language']/option")
                exc_languages = self.driver.find_elements_by_xpath("//select[@id='exclude_language']/option")
                inc_extensions = self.driver.find_elements_by_xpath("//select[@id='include_extension']/option")
                exc_extensions = self.driver.find_elements_by_xpath("//select[@id='exclude_extension']/option")
                inc_shelf = self.driver.find_elements_by_xpath("//select[@id='include_shelf']/option")
                exc_shelf = self.driver.find_elements_by_xpath("//select[@id='exclude_shelf']/option")

                cust_columns = self.driver.find_elements_by_xpath("//label[starts-with(@for, 'custom_')]")
                ret = dict()
                if len(cust_columns):  # we have custom columns
                    for col in cust_columns:
                        ret[col.text]= cust_columns[0].find_element_by_xpath(".//following-sibling::*")

                return {'include_tags':inc_tags,
                        'exclude_tags':exc_tags,
                        'include_serie': inc_series,
                        'exclude_serie': exc_series,
                        'include_language': inc_languages,
                        'exclude_language': exc_languages,
                        'include_extension': inc_extensions,
                        'exclude_extension': exc_extensions,
                        'include_shelf': inc_shelf,
                        'exclude_shelf': exc_shelf,
                        'cust_columns': ret
                        }
            else:
                text_inputs = ['book_title', 'bookAuthor', 'publisher', 'comment', 'custom_column_8',
                               'custom_column_10', 'custom_column_1', 'custom_column_6', 'custom_column_4',
                               'custom_column_5']
                date_inputs = ["publishstart", "publishend", 'custom_column_2_start', "custom_column_2_end"]
                selects = ['custom_column_9', 'custom_column_3', "read_status"]
                multi_selects = ['include_tag', 'exclude_tag', 'include_serie',
                                'exclude_serie', 'include_language', 'exclude_language', 'include_extension',
                                'exclude_extension', 'include_shelf', 'exclude_shelf']
                process_text = dict()
                process_checkboxes = dict()
                process_select = dict()
                process_mulitselect = dict()
                process_date = dict()

                # check if checkboxes are in list and separate lists
                for element, key in enumerate(term_dict):
                    if key in text_inputs:
                        process_text[key] = term_dict[key]
                    elif key in selects:
                        process_select[key] = term_dict[key]
                    elif key in date_inputs:
                        process_date[key] = term_dict[key]
                    elif key in multi_selects:
                        process_mulitselect[key] = term_dict[key]
                    else:
                        process_checkboxes[key] = term_dict[key]

                for element, key in enumerate(process_date):
                    self.select_date_with_editor(key, key + '_delete',
                                                process_date[key])

                for element, key in enumerate(process_text):
                    ele = self.driver.find_element_by_id(key)
                    ele.clear()
                    ele.send_keys(process_text[key])

                for element, key in enumerate(process_select):
                    select = Select(self.driver.find_element_by_id(key))
                    select.select_by_visible_text(process_select[key])

                for element, key in enumerate(process_mulitselect):
                    button = self.driver.find_element(By.XPATH, "//select[@id='"+key+"']/following-sibling::button")
                    button.click()
                    ele = self.driver.find_elements(By.XPATH,
                                              "//select[@id='" + key + "']/following-sibling::div//a[@role='option']")
                    for e in ele:
                        if e.text == process_mulitselect[key]:
                            e.click()
                            break
                    #select.select_by_visible_text(process_mulitselect[key])

                for element, key in enumerate(process_checkboxes):
                    ele = self.driver.find_element(By.XPATH,
                                                   "//input[@value = '" + process_checkboxes[key] +
                                                   "' and starts-with(@id, '" + key + "') ]/..")
                    ele.click()
                self.check_element_on_page((By.ID, "adv_submit")).click()
                return self.get_shelf_books_displayed()
        return False
