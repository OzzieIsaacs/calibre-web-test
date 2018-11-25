#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import lxml.etree
from StringIO import StringIO

# Dict for pages and the way to reach them
page = dict()
page['nav_serie']={'check':(By.TAG_NAME, "h1"),'click':[(By.ID, "nav_serie")]}
page['nav_publisher']={'check':(By.TAG_NAME, "h1"),'click':[(By.ID, "nav_publisher")]}
page['nav_new']={'check':None,'click':[(By.ID, "nav_new")]}
page['nav_cat']={'check':(By.TAG_NAME, "h1"),'click':[(By.ID, "nav_cat")]}
page['nav_author']={'check':(By.TAG_NAME, "h1"),'click':[(By.ID, "nav_author")]}
page['nav_lang']={'check':(By.TAG_NAME, "h1"),'click':[(By.ID, "nav_lang")]}
page['nav_hot']={'check':None,'click':[(By.ID, "nav_hot")]}
page['nav_about']={'check':(By.ID, "stats"),'click':[(By.ID, "nav_about")]}
page['nav_rated']={'check':None,'click':[(By.ID, "nav_rated")]}
page['nav_read']={'check':None,'click':[(By.ID, "nav_read")]}
page['nav_unread']={'check':None,'click':[(By.ID, "nav_unread")]}
page['nav_sort_old']={'check':None,'click':[(By.ID, "nav_sort"),(By.ID, "nav_sort_old")]}
page['nav_sort_new']={'check':None,'click':[(By.ID, "nav_sort"),(By.ID, "nav_sort_new")]}
page['nav_sort_asc']={'check':None,'click':[(By.ID, "nav_sort"),(By.ID, "nav_sort_asc")]}
page['nav_sort_desc']={'check':None,'click':[(By.ID, "nav_sort"),(By.ID, "nav_sort_desc")]}
page['basic_config']={'check':(By.ID, "config_calibre_dir"),'click':[(By.ID, "top_admin"),(By.ID, "basic_config")]}
page['view_config']={'check':None,'click':[(By.ID, "top_admin"),(By.ID, "view_config")]}
page['mail_server']={'check':(By.ID, "mail_server"),'click':[(By.ID, "top_admin"),(By.ID, "admin_edit_email")]}
page['admin_setup']={'check':(By.ID, "admin_edit_email"),'click':[(By.ID, "top_admin")]}
page['user_setup']={'check':(By.ID, "kindle_mail"),'click':[(By.ID, "top_user")]}
page['create_shelf']={'check':(By.ID, "title"),'click':[(By.ID, "nav_createshelf")]}
page['create_user']={'check':(By.ID, "nickname"),'click':[(By.ID, "top_admin"),(By.ID, "admin_new_user")]}
page['register']={'check':(By.ID, "nickname"),'click':[(By.ID, "register")]}

class ui_class():

    @classmethod
    def login(cls,user, passwd):
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.NAME, "username")))
        username = cls.driver.find_element_by_name("username")
        password = cls.driver.find_element_by_name("password")
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
    def check_user_logged_in(cls,user, noCompare=False):
        user_element = cls.check_element_on_page((By.ID, "top_user"))
        if user_element:
            if noCompare:
                return True
            if user_element.text.lower() == user.lower():
                return True
        return False

    @classmethod
    def list_shelfs(cls, search_name=None):
        public_shelfs = cls.driver.find_elements_by_xpath( "//a/span[@class='glyphicon glyphicon-list public_shelf']//ancestor::a")
        private_shelfs = cls.driver.find_elements_by_xpath("//a/span[@class='glyphicon glyphicon-list private_shelf']//ancestor::a")
        ret_shelfs = list()
        ret_ele = None
        for shelf in private_shelfs:
            sh = dict()
            sh['id'] = shelf.get_attribute('href')[shelf.get_attribute('href').rfind('/')+1:]
            sh['name'] = shelf.text
            sh['ele'] = shelf
            sh['public'] = False
            if search_name == shelf.text:
                ret_ele = sh
            else:
                ret_shelfs.append(sh)
        for shelf in public_shelfs:
            no = next((index for (index, d) in enumerate(ret_shelfs) if d["name"] == shelf.text), None)
            if no:
                ret_shelfs[no]['public'] = True
                ret_shelfs[no]['ele'] = shelf
            else:
                sh = dict()
                sh['id'] = shelf.get_attribute('href')[shelf.get_attribute('href').rfind('/')+1:]
                sh['name'] = shelf.text
                sh['public'] = True
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
    def page_has_loaded(cls):
        # self.log.info("Checking if {} page is loaded.".format(self.driver.current_url))
        page_state = cls.driver.execute_script('return document.readyState;')
        return page_state == 'complete'

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

                # check if got to page
                if page[page_target]['check'][0] == By.TAG_NAME:
                    WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located(page[page_target]['check']))
                    list_type=cls.driver.find_element_by_tag_name('h1')
                if page[page_target]['check'][0] == By.ID:
                    WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located(page[page_target]['check']))
                    return True
                if page[page_target]['check'][0] == None:
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
        cls.driver.find_element_by_id("submit").click()
        return cls.check_element_on_page((By.ID, "flash_success"))

    @classmethod
    def fill_initial_config(cls,elements=None):
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.ID, "config_calibre_dir")))
        accordions=cls.driver.find_elements_by_class_name("accordion-toggle")
        opener = list()
        process_checkboxes = dict()
        process_elements = dict()
        process_options =dict()
        process_select = dict()
        # special handling for checkboxes
        checkboxes = ['config_uploading', 'config_anonbrowse', 'config_public_reg', 'config_remote_login']
        options = ['config_log_level', 'config_google_drive_folder']
        selects = ['config_ebookconverter']
        # depending on elements open accordions or not
        if any(key in elements for key in ['config_port', 'config_certfile','config_keyfile']):
            opener.append(1)
        if any(key in elements for key in ['config_log_level','config_logfile']):
            opener.append(2)
        if any(key in elements for key in ['config_uploading', 'config_anonbrowse', 'config_public_reg',
                                           'config_remote_login', 'config_use_goodreads', 'config_goodreads_api_key',
                                           'config_goodreads_api_secret']):
            opener.append(3)
        if any(key in elements for key in ['config_ebookconverter', 'config_calibre',
                                           'config_converterpath','config_rarfile_location']):
            opener.append(4)

        # open all necessary accordions
        for o in opener:
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
            if (elements[checkbox] == 1 and not ele.is_selected() )or elements[checkbox] == 0 and ele.is_selected():
                ele.click()

        for select in process_select:
            ele = cls.driver.find_elements_by_name(select)
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

    def fill_basic_config(self,elements=None):
        self.goto_page('basic_config')
        self.fill_initial_config(elements)

    @classmethod
    def fill_view_config(cls,elements=None):
        cls.goto_page('view_config')
        WebDriverWait(cls.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "discover")))
        accordions=cls.driver.find_elements_by_class_name("accordion-toggle")
        opener = list()
        process_checkboxes = dict()
        process_elements = dict()
        process_options = dict()
        # special handling for checkboxes
        checkboxes = ['admin_role', 'download_role', 'upload_role', 'edit_role', 'delete_role', 'passwd_role',
                        'edit_shelf_role', 'show_random', 'show_recent', 'show_sorted', 'show_hot', 'show_best_rated',
                        'show_language', 'show_series', 'show_category', 'show_author', 'show_read_and_unread',
                        'show_detail_random', 'show_mature_content', 'show_publisher']
        options = ['config_read_column']
        # depending on elements open accordions or not
        if any(key in elements for key in ['config_calibre_web_title', 'config_books_per_page',
                                           'config_random_books', 'config_columns_to_ignore',
                                           'config_read_column', 'config_title_regex', 'config_mature_content_tags']):
            opener.append(0)
        if any(key in elements for key in ['admin_role', 'download_role', 'upload_role', 'edit_role',
                                           'delete_role', 'passwd_role', 'edit_shelf_role']):
            opener.append(1)
        if any(key in elements for key in ['show_random', 'show_recent', 'show_sorted', 'show_hot', 'show_best_rated',
                                           'show_language', 'show_series', 'show_category', 'show_author',
                                           'show_read_and_unread', 'show_detail_random', 'show_mature_content',
                                            'show_publisher']):
            opener.append(2)

        # open all necessary accordions
        for o in opener:
            accordions[o].click()
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
            if (elements[checkbox] == 1 and not ele.is_selected() )or elements[checkbox] == 0 and ele.is_selected():
                ele.click()

        # process all text fields
        for element, key in enumerate(process_elements):
            ele = cls.driver.find_element_by_id(key)
            ele.clear()
            ele.send_keys(process_elements[key])

        # finally submit settings
        cls.driver.find_element_by_name("submit").click()


    def restart_calibre_web(self):
        self.goto_page('admin_setup')
        self.driver.find_element_by_id('admin_restart').click()
        element = self.check_element_on_page((By.ID, "restart"))
        element.click()
        time.sleep (10)

    def stop_calibre_web(self):
        self.goto_page('admin_setup')
        self.driver.find_element_by_id('admin_stop').click()
        element = self.check_element_on_page((By.ID, "shutdown"))
        element.click()

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
    def check_element_on_page(cls, element, timeout=5):
        try:
            el = WebDriverWait(cls.driver, timeout).until(EC.presence_of_element_located(element))
            return el
        except TimeoutException:
            return False

    @classmethod
    def edit_user(cls, name, element):
        cls.goto_page('admin_setup')
        user = cls.driver.find_elements_by_xpath("//table[@id='table_user']/tbody/tr/td/a")
        for ele in user:
            if name == ele.text:
                ele.click()
                if not cls.check_element_on_page((By.ID, "email")):
                    print('Could user: %s not edit' % name)
                    return False
                return cls.change_user(element)
        print('User: %s not found' % name)
        return False


    @classmethod
    def change_visibility_me(cls, nav_element):
        ''' All Checkboses are:
            'show_random','show_recent', 'show_hot', 'show_best_rated', 'show_language', 'show_series',
            'show_category', 'show_author', 'show_read_and_unread', 'show_detail_random' '''
        selects = ['locale', 'theme', 'default_language']
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
                process_checkboxes[key] = nav_element[key]
            else:
                process_selects[key] = nav_element[key]

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
        cls.driver.find_element_by_id("submit").click()


    def create_shelf(self, name, public=False):
        self.goto_page('create_shelf')
        ele = self.check_element_on_page((By.ID,'title'))
        if ele:
            ele.clear()
            ele.send_keys(name.decode('utf-8'))
            if public:
                public_shelf = self.check_element_on_page((By.NAME,'is_public'))
                if public_shelf:
                    public_shelf.click()
                else:
                    return False
            submit = self.check_element_on_page((By.ID, 'submit'))
            if submit:
                submit.click()
                return True
        return False

    @classmethod
    def create_user(cls, name, config):
        if name:
            config['nickname'] = name
        cls.goto_page('create_user')
        return cls.change_user(config)

    @classmethod
    def change_user(cls, config):
        ''' All Checkboses are:
            'show_random','show_recent', 'show_hot', 'show_best_rated', 'show_language', 'show_series',
            'show_category', 'show_author', 'show_read_and_unread', 'show_detail_random' '''
        selects = ['locale', 'theme', 'default_language']
        text_inputs = ['kindle_mail','email', 'password', 'nickname']
        process_selects = dict()
        process_checkboxes = dict()
        process_text = dict()
        # check if checkboxes are in list and seperate lists
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
        cls.driver.find_element_by_id("submit").click()


    @classmethod
    def get_user_list(cls):
        cls.goto_page('admin_setup')
        return cls.driver.find_elements_by_xpath("//table[@id='table_user']/tbody/tr")

    @classmethod
    def get_books_displayed(cls):
        parser = lxml.etree.HTMLParser()
        html = cls.driver.page_source

        tree = lxml.etree.parse(StringIO(html), parser)
        books_rand = list()
        br = tree.xpath("//*[@class='discover']/div/div")
        for book_rand in br:
            ele = book_rand.getchildren()
            meta=ele[1].getchildren()
            book_r = dict()
            book_r['link'] = ele[0].getchildren()[0].attrib['href']
            book_r['ele'] = cls.check_element_on_page((By.XPATH,"//a[@href='"+book_r['link']+"']/img"))
            book_r['id'] = book_r['link'][6:]
            book_r['title']= meta[0].text
            authors = meta[1].getchildren()
            book_r['author'] = [a.text for a in authors]
            if len(meta) == 3:
                ratings = meta[2].getchildren()
                counter = 0
                for rating in ratings:
                    if rating.attrib['class'] == 'glyphicon glyphicon-star good':
                        counter += 1
                book_r['rating'] = counter
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
            bk['ele'] = cls.check_element_on_page((By.XPATH,"//a[@href='"+bk['link']+"']/img"))
            bk['title']= meta[0].text
            authors = meta[1].getchildren()
            bk['author'] = [a.text for a in authors]
            if len(meta) == 3:
                ratings = meta[2].getchildren()
                counter = 0
                for rating in ratings:
                    if rating.attrib['class'] == 'glyphicon glyphicon-star good':
                        counter += 1
                bk['rating'] = counter
            books.append(bk)

        pages = tree.xpath("//*[@class='pagination']/a")
        pagination = None
        if len(pages):
            pagination = [p.text for p in pages]
        return [books_rand, books, pagination]
        # elements = cls.driver.find_elements_by_xpath("//*[starts-with(@id,'books')]")
        # print elements
        # pass

    @classmethod
    def get_book_details(cls,id=-1,root_url="http://127.0.0.1:8083"):
        if id>0:
            cls.driver.get(root_url + "/book/"+str(id))
        cls.check_element_on_page((By.TAG_NAME,"h2"))
        ret = dict()
        try:
            # WebDriverWait(cls.driver, 0)
            parser = lxml.etree.HTMLParser()
            html = cls.driver.page_source

            tree = lxml.etree.parse(StringIO(html), parser)
            # reader = cls.driver.find_elements_by_xpath("//*[@aria-labelledby='read-in-browser']//li")
            reader = tree.findall("//*[@aria-labelledby='read-in-browser']/li/a")
            ret['reader'] = [r.text for r in reader]

            # ret['title'] = cls.check_element_on_page((By.TAG_NAME,"h2")).text
            title = tree.find("//h2")
            if title is not None:
                ret['title'] = title.text
            # author = cls.driver.find_elements_by_xpath("//*[@class='author']/a")
            author = tree.findall("//*[@class='author']/a")
            ret['author'] = [aut.text for aut in author]

            # ret['rating'] = cls.driver.find_elements_by_xpath("//*[@class='glyphicon glyphicon-star good']/span")
            ret['rating']= tree.findall("//*[@class='glyphicon glyphicon-star good']/span")

            # languages = cls.driver.find_elements_by_xpath("//*[@class='languages']//span")
            languages = tree.findall("//*[@class='languages']//span")
            ret['languages'] = [lang.text for lang in languages]

            # ids = cls.driver.find_elements_by_xpath("//*[@class='identifiers']//a")
            ids = tree.findall("//*[@class='identifiers']//a")
            ret['Identifier'] = [id.text for id in ids]

            # tags = cls.driver.find_elements_by_xpath("//*[@class='tags']//a")
            tags = tree.findall("//*[@class='tags']//a")
            ret['tag'] = [tag.text for tag in tags]

            # publishers = cls.driver.find_elements_by_xpath("//*[@class='publishers']//span")
            publishers = tree.findall("//*[@class='publishers']//a")
            ret['publisher'] = [pub.text for pub in publishers]

            # Pubdate
            # pubdate = cls.driver.find_elements_by_xpath("//p[starts-with(.,'Publishing date:')]")
            pubdate = tree.xpath("//p[starts-with(text(),'Publishing date:')]")
            if len(pubdate):
                ret['pubdate']= pubdate[0].text

            # ret['comment'] = cls.check_element_on_page((By.TAG_NAME, "h3"))
            comment = tree.find("//*[@class='comments']")
            if comment is not None:
                ret['comment'] = ''
                for ele in comment.getchildren()[1].getchildren():
                    ret['comment'] += ele.text
            # add_shelf = cls.driver.find_elements_by_xpath("//*[@id='add-to-shelves']//a")
            add_shelf = tree.findall("//*[@id='add-to-shelves']//a")
            ret['add_shelf'] = [sh.text.strip().lstrip() for sh in add_shelf]

            # del_shelf = cls.driver.find_elements_by_xpath("//*[@id='remove-from-shelves']//a")
            del_shelf = tree.findall("//*[@id='remove-from-shelves']//a")
            ret['del_shelf'] = [sh.text.strip().lstrip() for sh in del_shelf]

            # ret['edit_enable'] = cls.check_element_on_page((By.XPATH,"//*[@class='glyphicon glyphicon-edit']"))
            ret['edit_enable'] = bool(tree.find("//*[@class='glyphicon glyphicon-edit']"))

            # ret['kindle'] = cls.check_element_on_page((By.ID, "sendbtn"))
            ret['kindle'] = bool(tree.find("//*[@id='sendbtn']"))
            if not ret['kindle']:
                ret['kindle'] = tree.findall("//*[@aria-labelledby='send-to-kindle']/li/a")

            # download1 = cls.driver.find_elements_by_xpath("//*[@aria-labelledby='btnGroupDrop1']//a")
            download1 = tree.findall("//*[@aria-labelledby='btnGroupDrop1']//a")
            if not download1:
                download1 = tree.xpath("//*[starts-with(@id,'btnGroupDrop')]")
                if download1:
                    ret['download'] = list()
                    for ele in download1:
                        ret['download'].append(ele.getchildren()[0].tail.strip())
            else:
                # download1 = cls.driver.find_elements_by_xpath("//*[@class='glyphicon glyphicon-download']//ancestor::a")
                ret['download'] = [d.text for d in download1]

            # ret['read'] = cls.check_element_on_page((By.ID,"have_read_cb"))
            ret['read']= bool(tree.find("//*[@id='have_read_cb']"))

            # series = tree.xpath("//*[contains(@href,'series')]//ancestor::p")[0].text + \
            #         tree.xpath("//*[contains(@href,'series')]")[1].text
            series = tree.xpath("//*[contains(@href,'series')]/ancestor::p")
            if series:
                ret['series_all'] = ""
                ret['series_index'] = series[0].text[5:-3]
                for ele in series[0].iter():
                    ret['series_all'] += ele.text
                    ret['series'] = ele.text
                    # series = cls.driver.find_elements_by_xpath("//*[contains(@href,'series')]//ancestor::p")
                    # if series:
                    #    ret['series']=series[0].text

            # custom cloumns ??
            # cover type

        except Exception as e:
            print(e)
            pass
        return ret

    @classmethod
    def register_user(cls,user, email):
        cls.logout()
        if cls.goto_page('register'):
            name = cls.check_element_on_page((By.ID, "nickname"))
            em = cls.check_element_on_page((By.ID, "email"))
            submit = cls.check_element_on_page((By.ID, "submit"))
            name.send_keys(user)
            em.send_keys(email)
            submit.click()
            return cls.check_element_on_page(((By.ID, "flash_success")))
        else:
            return False


    @classmethod
    def edit_book(cls, id=-1, content=dict(), detail_v=False, root_url='http://127.0.0.1:8083'):
        if id>0:
            cls.driver.get(root_url + "/admin/book/"+str(id))
        cls.check_element_on_page((By.ID,"book_edit_frm"))

        if 'rating' in content:
            cls.driver.execute_script("arguments[0].setAttribute('value', arguments[1])",
                                  cls.driver.find_element_by_xpath("//input[@id='rating']"), content['rating'])
            content.pop('rating')
        for element, key in enumerate(content):
            ele = cls.check_element_on_page((By.ID, key))
            ele.send_keys(Keys.CONTROL, "a")
            ele.send_keys(Keys.DELETE)
            if ele.get_attribute('value') != '':
                print("clear didn't work")
            ele.send_keys(content[key])

        # don't stay on page after edit
        if detail_v:
            cls.check_element_on_page((By.NAME, "detail_view")).click()

        submit = cls.check_element_on_page((By.ID, "submit"))
        submit.click()
        return
        # return cls.check_element_on_page(((By.ID, "flash_success")))


        '''number
        'rating'
        'upload-cover'
        'pubdate'
        'upload-format'
        custom coloums
        'detail_view'
        'get_meta' '''