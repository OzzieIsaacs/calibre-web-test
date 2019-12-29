from gevent import monkey
monkey.patch_all()

from gsmtpd.server import SMTPServer
import re
import email
import time


class CredentialValidator(object):

    def validate(self, username, password):
        print('User: %s, Password: %s' % (username,password))
        if username == 'user' and password == 'password':
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
        self.message = None

    def process_message(self, peer, mailfrom, rcpttos, message_data):
        print('Receiving message from:', peer)
        print('Message addressed from:', mailfrom)
        print('Message addressed to  :', rcpttos)
        print('Message length        :', len(message_data))
        self.size = len(message_data)
        if self.size < 1000:
            self.message = message_data
        if self.ret_value == 552:
            return '552 Requested mail action aborted: exceeded storage allocation'
        else:
            return

    @property
    def message_size(self):
        return self.size

    def set_return_value(self, value):
        self.ret_value = value

    def extract_register_info(self):
        if self.message:
            self.message = email.message_from_string(self.message).get_payload(0).get_payload(decode=True).decode('utf-8')
            username = re.findall('User name:\s(.*)\r',self.message)
            password = re.findall('Password:\s(.*)\r',self.message)
            if len(username) and len(password):
                return (username[0], password[0])
        return (False, False)

    def check_email_received(self):
        return bool(self.size)

    def reset_email_received(self):
        self.size = 0

if __name__ == '__main__':
    email_server = Gevent_SMPTPServer(
        ('127.0.0.1', 1027),
        only_ssl=True,
        certfile='SSL/ssl.crt',
        keyfile='SSL/ssl.key',
        credential_validator=CredentialValidator(),
        timeout=10
    )
    email_server.start()
    try:
        while True:
            time.sleep()
    except KeyboardInterrupt:
        pass

