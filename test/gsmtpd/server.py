#!/usr/bin/env python
# encoding: utf-8

"""
An RFC 2821 smtp proxy server port from Python Standrad Library for Gevent usage
"""

# Overview:
#
# This file implements the minimal SMTP protocol as defined in RFC 821.  It
# has a hierarchy of classes which implement the backend functionality for the
# smtpd.  A number of classes are provided:
#
#   SMTPServer - the base class for the backend.  Raises NotImplementedError
#   if you try to use it.
#
#   DebuggingServer - simply prints each message it receives on stdout.
#
#   PureProxy - Proxies all messages to a real smtpd which does final
#   delivery.  One known problem with this class is that it doesn't handle
#   SMTP errors from the backend server at all.  This should be fixed
#   (contributions are welcome!).
#
# Please note that this script requires Python 2.7
#
# Author: Barry Warsaw <barry@python.org>
#         Meng Zhuo <mengzhuo1203@gmail.com>
# TODO:
#
# - support mailbox delivery
# - alias files
# - ESMTP
# - handle error codes from the backend smtpd

import logging
from . import log
import ssl
from ssl import CERT_NONE
from .channel import SMTPChannel
try:
    from UserDict import UserDict
except ImportError:
    from collections import UserDict
from gevent import socket, monkey, Timeout

monkey.patch_all()

from gevent.server import StreamServer


logger = logging.getLogger(log.LOG_NAME)

__all__ = ["SMTPServer", 'SSLSettings']

class ConnectionTimeout(Exception):
    pass

NEWLINE = '\n'
EMPTYSTRING = ''
COMMASPACE = ', '

class SSLSettings(UserDict):
    """SSL settings object"""
    def __init__(self, keyfile=None, certfile=None,
                 ssl_version='PROTOCOL_SSLv23', ca_certs=None,
                 do_handshake_on_connect=True, cert_reqs=CERT_NONE,
                 suppress_ragged_eofs=True, ciphers=None, **kwargs):
        """settings of SSL

        :param keyfile: SSL key file path usally end with ".key"
        :param certfile: SSL cert file path usally end with ".crt"
        """
        UserDict.__init__(self)
        self.data.update( dict(keyfile = keyfile,
                                certfile = certfile,
                                server_side = True,
                                ssl_version = getattr(ssl, ssl_version, ssl.PROTOCOL_SSLv23),
                                ca_certs = ca_certs,
                                do_handshake_on_connect = do_handshake_on_connect,
                                cert_reqs=cert_reqs,
                                suppress_ragged_eofs = suppress_ragged_eofs,
                                ciphers = ciphers))


class SMTPServer(StreamServer):
    """Abstrcted SMTP server
    """

    def __init__(self, localaddr=None, remoteaddr=None,
                 timeout=60, data_size_limit=10240000, only_ssl = False, credential_validator=None, **kwargs):
        """Initialize SMTP Server

        :param localaddr: tuple pair that start server, like `('127.0.0.1', 25)`
        :param remoteaddr: ip address (string or list) that can relay on this server
        :param timeout: int that connection Timeout
        :param data_size_limit: max byte per mail data
        :param kwargs: other key-arguments will pass to :class:`.SSLSettings`
        """
        self.relay = bool(remoteaddr)
        self.remoteaddr = remoteaddr

        self.localaddr = localaddr
        if not self.localaddr:
            self.localaddr = ('127.0.0.1', 25)

        self.credential_validator = credential_validator

        self.timeout = int(timeout)
        self.data_size_limit = int(data_size_limit)

        # valid combinations:
        # no starttls no certs, no ssl -> pure plain connection
        # starttls, valid certs, no ssl -> start unencrpyted, after starttls encrypted
        # no starttls, valid certs, ssl -> start unencrpyted, after starttls encrypted
        self.ssl = None
        self.only_ssl = only_ssl
        if 'keyfile' in kwargs:
            self.ssl = SSLSettings(**kwargs)

        super(SMTPServer, self).__init__(self.localaddr, self.handle)

    def handle(self, sock, addr):

        logger.debug('Incomming connection %s:%s', *addr[:2])
        print('Incomming connection %s:%s' % (addr[0], addr[1]))

        if self.relay and not addr[0] in self.remoteaddr:
            logger.debug('Not in remoteaddr', *addr[:2])
            return
        try:
            with Timeout(self.timeout, ConnectionTimeout):
                sc = SMTPChannel(self, sock, addr, self.data_size_limit, self.credential_validator, self.only_ssl)
                while not sc.closed:
                    sc.handle_read()

        except ConnectionTimeout:
            logger.warn('%s:%s Timeouted', *addr[:2])
            print('%s:%s Timeouted' % (addr[0],addr[1]))
            try:
                sc.smtp_TIMEOUT()
            except Exception as err:
                logger.debug(err)
        except Exception as err:
            logger.error(err)

    # API for "doing something useful with the message"
    def process_message(self, peer, mailfrom, rcpttos, data):
        """Override this abstract method to handle messages from the client.

        :param peer: is a tuple containing (ipaddr, port) of the client that made\n
                     the socket connection to our smtp port.
        :param mailfrom: is the raw address the client claims the message is coming from.
        :param rcpttos: is a list of raw addresses the client wishes to deliver the message to.
        :param data: is a string containing the entire full text of the message,\n
                     headers (if supplied) and all.  It has been `de-transparencied'\n
                     according to RFC 821, Section 4.5.2.\n
                     In other words, a line containing a `.' followed by other text has had the leading dot
        removed.

        This function should return None, for a normal `250 Ok' response;
        otherwise it returns the desired response string in RFC 821 format.

        """
        raise NotImplementedError

    # API that handle rcpt
    def process_rcpt(self, address):
        """Override this abstract method to handle rcpt from the client

        :param address: is raw address the client wishes to deliver the message to

        This function should return None, for a normal `250 Ok' response;
        otherwise it returns the desired response string in RFC 821 format.
        """
        pass