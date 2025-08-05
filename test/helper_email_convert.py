# -*- coding: utf-8 -*-

import asyncio
import base64

import sys
import os
import re
import ssl

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import AuthResult, LoginPassword
# from aiosmtpd.controller import get_server_context

from email import message_from_bytes, message_from_string

COMMASPACE = ', '


def is_calibre_not_present():
    return calibre_path() is None


def calibre_path():
    if sys.platform == "win32":
        calibre_path = ["C:\\program files\\calibre2",
                        "C:\\program files(x86)\\calibre2",
                        "C:\\program files\\calibre",
                        "C:\\program files(x86)\\calibre"]
    else:
        calibre_path = ["/opt/calibre"]
    for element in calibre_path:
        if os.path.isdir(element):
            return element
    return None

def is_kepubify_not_present():
    return kepubify_path() is None


def kepubify_path():
    if sys.platform == "win32":
        kepubify_path = ["C:\\program files\\kepubify\\kepubify-windows-64Bit.exe",
                        "C:\\program files(x86)\\kepubify\\kepubify-windows-64Bit.exe"]
    else:
        kepubify_path = ["/opt/kepubify/kepubify-linux-64bit", "/opt/kepubify/kepubify-linux-32bit"]
    for element in kepubify_path:
        if os.path.isfile(element):
            return element
    return None

class MyMessage:
    def __init__(self):
        self.ret_value = 0
        self.size = 0
        self.message = None

    async def handle_DATA(self, __, session, envelope):
        envelope = self.prepare_message(session, envelope)
        return self.handle_message(envelope)

    def prepare_message(self, session, envelope):
        # If the server was created with decode_data True, then data will be a
        # str, otherwise it will be bytes.
        data = envelope.content
        if isinstance(data, bytes):
            message = message_from_bytes(data)
        else:
            assert isinstance(data, str), (
              'Expected str or bytes, got {}'.format(type(data)))
            message = message_from_string(data)
        message['X-Peer'] = str(session.peer)
        message['X-MailFrom'] = envelope.mail_from
        message['X-RcptTo'] = COMMASPACE.join(envelope.rcpt_tos)
        return message

    def handle_message(self, message):
        message_data = message.get_payload()
        if isinstance(message_data, list):
            if len(message_data) == 1:
                message_data = message_data[0].get_payload(decode=True)
                self.attachment = None
            else:
                self.attachment = message_data[1].get_payload(decode=True)
                message_data = message_data[0].get_payload(decode=True) + self.attachment
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
            message = base64.b64decode(self.message)
            username = re.findall(r'Username:\s(.*)\r', message.decode('utf-8'))
            password = re.findall(r'Password:\s(.*)\r', message.decode('utf-8'))
            if len(username) and len(password):
                return [username[0], password[0]]
        return [False, False]

    def check_email_received(self):
        if 0 < self.size < 1000:
            return bool(self.message)
        return bool(self.size)

    def reset_email_received(self):
        self.size = 0

    def get_email_attachment(self):
        return self.attachment

class Authenticator:
    def __init__(self):
        pass

    def __call__(self, server, session, envelope, mechanism, auth_data):
        fail_nothandled = AuthResult(success=False, handled=False)
        if mechanism not in ("LOGIN", "PLAIN"):
            return fail_nothandled
        if not isinstance(auth_data, LoginPassword):
            return fail_nothandled
        username = auth_data.login.decode('utf-8')
        password = auth_data.password.decode('utf-8')
        if username == 'name@host.com' and password == '10234':
            return AuthResult(success=True)
        else:
            return fail_nothandled


def get_server_context(certfile='files/server.crt', keyfile='files/server.key'):
    tls_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    tls_context.load_cert_chain(certfile, keyfile)
    return tls_context


def AIOSMTPServer(hostname='', port=1025, startSSL=False, only_ssl=False,
                  authenticate=True, certfile=None, keyfile=None, timeout=300):
    print("Starting E-Mail Server")
    # SSL
    ssl_context = None
    if only_ssl or startSSL:
        tls_context = get_server_context(certfile, keyfile)
        auth_require_tls = True
        if only_ssl:
            ssl_context = tls_context
            auth_require_tls = False
    else:
        tls_context = None
        auth_require_tls = False
    auth = Authenticator()
    controller = Controller(MyMessage(),
                            hostname=hostname,
                            authenticator=auth,
                            require_starttls=startSSL,
                            tls_context=tls_context,
                            ssl_context=ssl_context,
                            auth_require_tls=auth_require_tls,
                            auth_required=authenticate,
                            timeout=timeout,
                            port=port)
    return controller

"""
Little testcode for startssl and ssl clients.
For ssl connectiosn always make sure the server certificates are !! valid !!
from smtplib import SMTP, SMTP_SSL
import smtplib, ssl

port = 1027  # For starttls
smtp_server = socket.gethostname()
sender_email = "name@host.com"
receiver_email = "your@gmail.com"
password = "10234"
message = '''\
Subject: Hi there

This message is sent from Python.'''

context = ssl.create_default_context()
with smtplib.SMTP(smtp_server, port, timeout=5) as server:
    server.starttls(context=context)
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)


# SSL
'''context = ssl.create_default_context()
with smtplib.SMTP_SSL(smtp_server, port, context=context, timeout=5) as server:
    # server.starttls(context=context)
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, message)'''
"""
