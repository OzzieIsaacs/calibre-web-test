# -*- coding: utf-8 -*-

import asyncio

import sys
import os
import re
import email

from aiosmtpd.controller import Controller
from aiosmtpd.controller import get_server_context

from email import message_from_bytes, message_from_string

COMMASPACE = ', '


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

class MyMessage():
    def __init__(self, message_class=None):
        self.message_class = message_class
        self.ret_value = 0
        self.size = 0
        self.message = None

    async def handle_AUTH(self, server, session, envelope, username, password):
        print('User: %s, Password: %s' % (username,password))
        if username == 'name@host.com' and password == '10234':
            return 235
        return 454

    async def handle_DATA(self, server, session, envelope):
        envelope = self.prepare_message(session, envelope)
        return self.handle_message(envelope)

    def prepare_message(self, session, envelope):
        # If the server was created with decode_data True, then data will be a
        # str, otherwise it will be bytes.
        data = envelope.content
        if isinstance(data, bytes):
            message = message_from_bytes(data, self.message_class)
        else:
            assert isinstance(data, str), (
              'Expected str or bytes, got {}'.format(type(data)))
            message = message_from_string(data, self.message_class)
        message['X-Peer'] = str(session.peer)
        message['X-MailFrom'] = envelope.mail_from
        message['X-RcptTo'] = COMMASPACE.join(envelope.rcpt_tos)
        return message

    def handle_message(self, message):
        message_data = message.get_payload()
        if isinstance(message_data, list):
            if len(message_data) == 1:
                message_data = message_data[0].get_payload(decode=True)
            else:
                message_data = message_data[0].get_payload(decode=True) + message_data[1].get_payload(decode=True)
        print('Receiving message from:', message.get('X-Peer'))
        print('Message addressed from:', message.get('From'))
        print('Message addressed to:', message.get('To'))
        print('Message length        :', len(message_data)) # len(message_data))
        self.size = len(message_data)
        if self.size < 1000:
            self.message = message_data
        if self.ret_value == 552:
            return '552 Requested mail action aborted: exceeded storage allocation'
        else:
            return '250 OK'

    @property
    def message_size(self):
        return self.size

    def set_return_value(self, value):
        self.ret_value = value

    def extract_register_info(self):
        if self.message:
            # self.message = email.message_from_string(self.message).get_payload(0).get_payload(decode=True).decode('utf-8')
            username = re.findall('User name:\s(.*)\r',self.message.decode('utf-8'))
            password = re.findall('Password:\s(.*)\r',self.message.decode('utf-8'))
            if len(username) and len(password):
                return (username[0], password[0])
        return (False, False)

    def check_email_received(self):
        return bool(self.size)

    def reset_email_received(self):
        self.size = 0

def AIOSMTPServer(hostname='', port=1025, authenticate=True, startSSL=False, only_ssl=None,
                       certfile=None, keyfile=None, timeout=300):
    # logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    # SSL
    # controller= amain(authenticate=True, startSSL=False, ssl_only=True)
    if only_ssl:
        only_ssl = get_server_context(certfile, keyfile)
    if only_ssl == False:
        only_ssl = None
    controller= Controller(MyMessage(), hostname=hostname, port=port, startSSL=startSSL, authenticate=authenticate,
               ssl_context=only_ssl, certfile=certfile, keyfile=keyfile, timeout=timeout)
    return controller

