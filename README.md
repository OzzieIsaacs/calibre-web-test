# Testing for calibre-web

## Prerequisites

- Installed python3 accessible with the command "python3" (tests currently done using python3.8.x Windows10 and LinuxMint20)
- installed calibre desktop program (optional)
- installed kepubify program (optional)
- for installing ldap requirements libsasl2-dev and libldap2-dev have to be installed (debian distro lib-names)
- Calibre-web-test has to be located on the same folder level as calibre-web
e.g.
```
.
..
calibre-web
  .
  ..
  cps
Calibre-web-test
  .
  ..
  test
```

- I'm doing my tests with Firefox, so geckodriver has to be installed and in path [https://github.com/mozilla/geckodriver/releases](https://github.com/mozilla/geckodriver/releases) and also Firefox itself

- All dependencies listed in requirements.txt have to be installed

- Ldaptor causes a problem in conjunction with the tests, so the patch suggested in https://github.com/twisted/ldaptor/issues/170 has to be applied

- tests are only running with tornado as wsgi server

- install Calibre as conversion tool (if running from within pycharm debugger no 4.xx version, 3.xx and 5.xx are fine to use, as Calibre 4.x crash during conversion in this configuration)

- Copy files from ./test/config_files to /test, configure folder names in file ./test/config_test.py

- optional: For testing of goodreads you need a goodreads account with the corresponding api-key, the credentials have to be added in config_goodreads.py

- optional: Testing GDrive requires a fully setup gdrive setup, please place the corresponding client_secrets.json and gdrive_credentials in calibre-web/test/files folder

- After finishing all tests an email can be send out, the password for the e-mail account and the location of the result file (accessible via ssh on a server) can be stored using keyring (https://pypi.org/project/keyring/), configuration options are stored in config_email

- Installing on Windows requires pycurl which can be installed using wheel in a virtual environment (download from here: https://www.lfd.uci.edu/~gohlke/pythonlibs/)

- Testing LDAP on windows requires the installation of python-ldap in the tested environment, therefore you need the corresponding wheel and you have to point to the file in config_test.py (variable LDAP_WHL)   

- SSL Files for testing will be automatically generated. A Tutorial for generating ssl files can be found here [https://www.golinuxcloud.com/create-certificate-authority-root-ca-linux](https://www.golinuxcloud.com/create-certificate-authority-root-ca-linux) and here [https://www.golinuxcloud.com/openssl-create-client-server-certificate](https://www.golinuxcloud.com/openssl-create-client-server-certificate)

## Start Testing

Tests are running with python 3.6+ (better 3.7 as with 3.6 testing the e-mail startssl/ssl functionality will be skipped) by starting ./test/main.py (tests run for ca. 45min), tested on Linux Mint 19.3. \
Calibre-web's app.db and logfiles will be overwritten.\
The testresult is written to the file "calibre-web/test/Calibre-Web TestSummary_xxx.html" (xxx for windows or Linux, MacOS is untested)

Hints for using pyCharm: 
It's recommended to have gevent compatible debugging set to **no** and also **do not attach to subprocess** (created trouble in combination with email sending). Due to a bug in pycharm the patch from here https://youtrack.jetbrains.com/issue/PY-43411?IssueComments has to be applied for testing on windows (and maybe also for MacOS)

# Compiling Language files

The script translate.py in the build folder is used for generating the binary translation files (.mo) and also to generate the language name translation table file 'iso_language_names.py' in the calibre-web cps folder. The script runs under python 3 (3.6 and 3.7 tested).\
The used languages were taken from the file iso639.calibre_msgpack. This is a magically (can't remember how I did it) shrinked file from the Calibre resoucres directory. The original file has over 7000 languages in it. Somewhere in the Calibre code there is a routine which is extracting several language names from this file (the 400 remaining), all other languages are not supported by calibre (at least at the time I created the file). By increasing the number of supported languages to the 7000, the speed of the language typeahead drops to nearly zero.
The language translations are taken from Calibre's iso639 folder in the transifex translation project. By adding up a new language the corresponding file has to be grabbed from this project. Before it can be used the timezonemarker in the header has to be changed from +MDT to +000.

# Build package files and executables

Edit the file config.py in the build folder and change the pathnames to the correct ones for you installation

For builing the exe installer on Windows, use Inno Setup, which can be downloaded from here https://jrsoftware.org/isinfo.php

Execute the build script make_release.py in the build folder, there will be a dist subfolder in calibre-web folder containing the sourcefile and the wheel file for publishing it on pypi
Furthermore there will be a new folder executable containing the executable files for the current platform. On Windows you need to have the precompilied binaries for python Levenshtein and python-ldap on your harddrive and point to them in the config file
On Windows you can start the installer packaging afterwards  using innosetup, by using the installer_script_windows.iss script file

# Update JS libs
## Making new versions of pdf Reader work

- Reported in https://github.com/janeczku/calibre-web/issues/2004 the original sources of pdf reader don't work well in Safari (iOS and Mac), all buttons disapearing. Safari seems not to handle double declaration of the images in "cps/static/css/libs/viewer.css" , like
 ``` 
  ...
  content: url(images/toolbarButton-menuArrow.svg);
  content: var(--toolbarButton-menuArrow-icon);
  ...
 ```
 Comment out all url definitions in `:root` block:
```
 :root {
  ...  	
  /*--loading-icon: url(images/loading.svg);
  ...*/
  }
 ```
All comment out all content: `var(--...);` occurences after the `url(images/` definitions.

- In our viewer some buttons disappear (download button) depending on the settings. This has also to be handled in pdf.js file by putting a "if button is present do, else not" query arount it. The exact positon differs form version to version.

## Bootstrap-Table

### 1) Handling quotes
Reported in https://github.com/janeczku/calibre-web/issues/2097 the original sources of bootstrap-table (editable) having a bug displaying double quotes (the issue originally was about single quotes)
The problem is double quotes aren't escaped properly by bootstrap-table-editable, so the visible string is truncated at the double quote. To prevent this the double quote has to be replaced with "&quot;".
This has to be done in bootstrap-table-editable.min.js (located in /cps/static/js/libs/bootstrap-table). Bold text has to be added. 

**if(typeof f==='string'){f=f.replace('\"',"&quot;");}**
return d.hasOwnProperty("noEditFormatter")&&(s=d.noEditFormatter(e,a,c)),!1===s?'<a href="javascript:void(0)"\n            data-name="'.concat(r.field,'"\n            data-pk="').concat(a[t.options.idField],'"\n            data-value="').concat(f,'"\n            ').concat(i.join(""),"></a>"):s}}})))}}

### 2) Success callback (don't show invalid edits)
Reported by me here https://github.com/wenzhixin/bootstrap-table/issues/5715.
The fix has to be applied in bootstrap-table-editable.min.js (located in /cps/static/js/libs/bootstrap-table). Bold text has to be changed. 

i.off("save").on("save",(function(t,o){var i=t.currentTarget,a=o.**newValue**,u=n.default(i)

# Debug outputs and more
The following enviromentvariables can be set to control debugging output

SQLALCHEMY_WARN_20 = 1 -> Outputs compatibility warnings for sqlalchemy 2.0
FLASK_DEBUG = 1 -> routes debug output to stream console
PYTHONWARNINGS = DEFAULT -> outputs depreciation warnings on console