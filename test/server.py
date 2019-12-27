import asyncio
import logging
import re
import email
import ssl
import os

from aiosmtpd.controller import Controller
from aiosmtpd.controller import Controller as BaseController
from aiosmtpd.handlers import Sink
from aiosmtpd.smtp import SMTP as SMTPProtocol
from email.mime.text import MIMEText
from smtplib import SMTP

from email import message_from_bytes, message_from_string
from public import public

COMMASPACE = ', '

def get_server_context():
    tls_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    tls_context.load_cert_chain('SSL/ssl.crt','SSL/ssl.key')
        #pkg_resources.resource_filename('aiosmtpd.tests.certs', 'server.crt'),
        #pkg_resources.resource_filename('aiosmtpd.tests.certs', 'server.key'))
    return tls_context

class ReceivingHandler:
    def __init__(self):
        self.box = []

    async def handle_DATA(self, server, session, envelope):
        self.box.append(envelope)
        return '250 OK'


class Controller(BaseController):
    def factory(self):
        return SMTPProtocol(self.handler)



class TLSRequiredController(Controller):
    def factory(self):
        return SMTPProtocol(
            self.handler,
            decode_data=True,
            require_starttls=True,
            tls_context=get_server_context())


class Message:
    def __init__(self, message_class=None):
        self.message_class = message_class
        self.ret_value = 0
        self.size = 0


    async def handle_AUTH(self, server, session, envelope, username, password):
        print('User: %s, Password: %s' % (username,password))
        if username == 'user' and password == 'password':
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



async def amain(loop, authenticate, startSSL= False, ssl_only=None):
    #if startSSL:
    #controller = TLSRequiredController(Sink)
    #controller.start()

    cont = Controller(Message(), hostname='', port=8025, startSSL=startSSL, authenticate=authenticate, ssl_context = ssl_only) # require_starttls=True)
    #else:
    #    cont = Controller(Message(), hostname='', port=8024, authenticate=authenticate, ssl_context = ssl_only)
    cont.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    # loop.create_task(amain(loop=loop, authenticate=True, startSSL= True))
    # loop.create_task(amain(loop=loop, authenticate=True))  # , ssl_only=get_server_context()))
    loop.create_task(amain(loop=loop, authenticate=True, startSSL=False, ssl_only=None))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass





