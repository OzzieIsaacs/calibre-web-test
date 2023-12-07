# Testing for calibre-web

## Prerequisites

- Installed python3 accessible with the command "python3" (tests currently done using python3.10.x Windows10 and LinuxMint20)
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

- All dependencies listed in requirements.txt in testing folder have to be installed to run all tests

- Ldaptor causes a problem in conjunction with the tests, so the patch suggested in https://github.com/twisted/ldaptor/issues/170 has to be applied

- tests are only running with tornado as wsgi server

- install Calibre as conversion tool (if running from within pycharm debugger don't use Calibre 4.xx version. 3.xx and 5.xx onwards are fine to use, as Calibre 4.x crash during conversion in this configuration)

- Copy files from ./test/config_files to /test, configure folder names in file ./test/config_test.py. The config_email.py file shows a small piece of code to store your email account passwort in the linux keyring system, this is optional. 

- optional: For testing of goodreads you need a goodreads account with the corresponding api-key, the credentials have to be added in config_goodreads.py

- optional: Testing GDrive requires a full setup gdrive setup, please place the corresponding client_secrets.json and gdrive_credentials in calibre-web/test/files folder

- optional: After finishing all tests an email can send out, the password for the e-mail account and the location of the result file (accessible via ssh on a server) can be stored using keyring (https://pypi.org/project/keyring/), configuration options are stored in config_email

- Installing on Windows requires pycurl which can be installed using wheel in a virtual environment (download from here: https://www.lfd.uci.edu/~gohlke/pythonlibs/)

- Testing LDAP on Windows requires the installation of python-ldap in the tested environment, therefore you need the corresponding wheel, and you have to point to the file in config_test.py (variable LDAP_WHL)   

- SSL Files for testing will be automatically generated. A Tutorial for generating ssl files can be found here [https://www.golinuxcloud.com/create-certificate-authority-root-ca-linux](https://www.golinuxcloud.com/create-certificate-authority-root-ca-linux) and here [https://www.golinuxcloud.com/openssl-create-client-server-certificate](https://www.golinuxcloud.com/openssl-create-client-server-certificate)

- Mitmporoxy for Windows is problematic, as several modules are no longer available for newer python versions, so download the mitmproxy source for version 6.02 and patch the setup file to accept cryptography 36.0 and zstandard>0.15. Afterwards install via pip from this source

## Start Testing

Tests are running with python 3.6+ (better to use 3.7+ as with 3.6 testing the e-mail startssl/ssl functionality will be skipped) by starting ./test/main.py (tests run for approx. 5h+), tested on Linux Mint 21 \
Calibre-web's app.db and logfiles will be overwritten. I'm currently using python 3.10. \
The test result is written to the file "calibre-web/test/Calibre-Web TestSummary_xxx.html" (xxx for windows or Linux, MacOS is untested)

Hints for using pyCharm: 
It's recommended to have gevent compatible debugging set to **no** and also **do not attach to subprocess** (created trouble in combination with email sending). Due to a bug in pycharm the patch from here https://youtrack.jetbrains.com/issue/PY-43411?IssueComments has to be applied for testing on Windows (and maybe also for MacOS)

# Compiling Language files

The script translate.py in the build folder is used for generating the binary translation files (.mo) and also to generate the language name translation table file 'iso_language_names.py' in the calibre-web cps folder. The script runs under python 3 (3.6 and 3.7 tested).\
The used languages were taken from the file iso639.calibre_msgpack. This is a magically (can't remember how I did it) shrank file from the Calibre resources directory. The original file has over 7000 languages in it. Somewhere in the Calibre code there is a routine which is extracting several language names from this file (the 400 remaining), all other languages are not supported by calibre (at least at the time I created the file). By increasing the number of supported languages to the 7000, the speed of the language typeahead drops to nearly zero.
The language translations are taken from Calibre's iso639 folder (https://github.com/kovidgoyal/calibre-translations/tree/master/iso_639) By adding up a new language the corresponding file has to be grabbed from this project. Before it can be used the timezone marker in the header has to be changed from +MDT to +000.

# Build package files and executables

Edit the file config.py in the build folder and change the path names to the correct ones for you installation

For building the exe installer on Windows, use Inno Setup, which can be downloaded from here https://jrsoftware.org/isinfo.php

Execute the build script make_release.py in the build folder, there will be a dist sub folder in calibre-web folder containing the sourcefile and the wheel file for publishing it on pypi
Furthermore there will be a new folder executable containing the executable files for the current platform. Uploading to pypi is done with the command "twine upload dist/*" afterwards, run from the calibre-web folder. 
On Windows you need to have the precompilied binaries for python Levenshtein and python-ldap on your hard drive and point to them in the config file
On Windows you can start the installer packaging afterwards  using innosetup, by using the installer_script_windows.iss script file

# Update JS libs
## Making new versions of pdf Reader work

- In our viewer some buttons disappear (download/print button) depending on the settings. This has also to be handled in viewer.js file by putting an "if button is present" query around it. The exact position differs form version to version.
```
if ( element !== null ) {       // Newline in line 14417 and 14428 of viewer.js
    element.addEventListener("click", evt => {
```
- furthermore it's needed to disable the file upload button. This is done in pdfviewer.html by deleting the corresponding "fileInput" entries. Furthermore, search for all reference in viewer.js like:
```
  const fileInput = appConfig.openFileInput;
  fileInput.value = null;
```
and 
```
eventBus._on("fileinputchange", webViewerFileInputChange);
eventBus._on("openfile", webViewerOpenFile);
```

## Bootstrap-Table

### 1) Handling special html chars
Reported in https://github.com/janeczku/calibre-web/issues/2097 the original sources of bootstrap-table (editable) having a bug displaying html special characters (',",\,<,>)
The problem is the escaped characters are displayed after editing. To prevent this the order of some commands has to be replaced
This has to be done in bootstrap-table-editable.min.js (located in /cps/static/js/libs/bootstrap-table). Bold text is the final order. 

**l[r.field]=a,a=wn.escapeHTML(a)**,u.data("value",a),e.trigger("editable-save"


### 2) Success callback (don't show invalid edits)
Reported by me here https://github.com/wenzhixin/bootstrap-table/issues/5715.
The fix has to be applied in bootstrap-table-editable.min.js (located in /cps/static/js/libs/bootstrap-table). Bold text has to be changed. 

i.off("save").on("save",(function(t,o){var i=t.currentTarget,a=o.**newValue**,u=n.default(i)

# Debug outputs and more
The following environment variables can be set to control debugging output

SQLALCHEMY_WARN_20 = 1 -> Outputs compatibility warnings for sqlalchemy 2.0
FLASK_DEBUG = 1 -> routes debug output to stream console
PYTHONWARNINGS = DEFAULT -> outputs depreciation warnings on console
