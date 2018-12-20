from secure_smtpd import SMTPServer
import threading
import asyncore
import sys
import os
import time

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


class threaded_SMPTPServer(SMTPServer, threading.Thread):

    def __init__(self, *args, **kwargs):
        SMTPServer.__init__(self, *args, **kwargs)
        self._stopevent = threading.Event()
        threading.Thread.__init__(self)
        self.status = 1
        self.mailfrom = None
        self.recipents = None
        self.payload = None
        self.error_c = None
        self.size = 0

    def process_message(self, peer, mailfrom, rcpttos, message_data, emails, config):
        print('Receiving message from:', peer)
        print('Message addressed from:', mailfrom)
        print('Message addressed to  :', rcpttos)
        print('Message length        :', len(message_data))
        emails.append({'mailfrom':mailfrom,'recipents':rcpttos, 'size': len(message_data)})
        # print('Shared Memory: %i' % config['error_code'])
        if config['error_code'] == 552:
            return '552 Requested mail action aborted: exceeded storage allocation'
        else:
            return

    def run(self):
        asyncore.loop()
        while self.status:
            time.sleep(1)
        print('email server stopps')

    def stop(self):
        self.status = 0
        self.close()

'''class SSLSMTPServer(SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, message_data):
        print(message_data)'''
