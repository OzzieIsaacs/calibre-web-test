import keyring
# E-Mail Adress for sending results
E_MAIL_ADDRESS = ''
E_MAIL_SERVER_ADDRESS = ''
STARTSSL = True
EMAIL_SERVER_PORT = 587
E_MAIL_LOGIN = ''
E_MAIL_PASSWORD = keyring.get_password('system', E_MAIL_ADDRESS)
SERVER_NAME = ''
SERVER_PORT = ''
SERVER_USER = ''
SERVER_PASSWORD =  keyring.get_password('system', SERVER_USER)
SERVER_FILE_DESTINATION = ''
