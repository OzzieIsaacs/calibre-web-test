# from secure_smtpd import SMTPServer
import sys
import os

from gevent import monkey
from gsmtpd.server import SMTPServer
# import logging

monkey.patch_all()

def is_calibre_not_present():
    if calibre_path():
        return False
    else:
        return True

def calibre_path():
    if sys.platform == "win32":
        calibre_path = ["C:\\program files\calibre\calibre-convert.exe", "C:\\program files(x86)\calibre\calibre-convert.exe"]
    else:
        calibre_path = ["/opt/calibre/ebook-convert"]
    for element in calibre_path:
        if os.path.isfile(element):
            return element
    return None


class CredentialValidator(object):

    def validate(self, username, password):
        print('User: %s, Password: %s' % (username,password))
        if username == 'name@host.com' and password == '10234':
            return True
        return False


class Gevent_SMPTPServer(SMTPServer):

    def __init__(self, *args, **kwargs):
        SMTPServer.__init__(self, *args, **kwargs)
        self.status = 1
        self.mailfrom = None
        self.recipents = None
        self.payload = None
        self.error_c = None
        self.size = 0
        self.ret_value = 0

    def process_message(self, peer, mailfrom, rcpttos, message_data):
        print('Receiving message from:', peer)
        print('Message addressed from:', mailfrom)
        print('Message addressed to  :', rcpttos)
        print('Message length        :', len(message_data))
        self.size = len(message_data)
        if self.ret_value == 552:
            return '552 Requested mail action aborted: exceeded storage allocation'
        else:
            return

    @property
    def message_size(self):
        return self.size

    def set_return_value(self, value):
        self.ret_value = value
