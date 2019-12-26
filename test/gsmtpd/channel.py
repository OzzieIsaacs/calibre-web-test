#!/usr/bin/env python
# encoding: utf-8

import logging
logger = logging.getLogger(__name__)
from gevent import monkey, socket, ssl

import errno
import base64
from asynchat import find_prefix_at_end

NEWLINE = '\n'.encode('utf-8')
EMPTYSTRING = ''.encode('utf-8')
COMMASPACE = ', '.encode('utf-8')

monkey.patch_all()

def decode_b64(data):
    '''Wrapper for b64decode, without having to struggle with bytestrings.'''
    byte_string = data.encode('utf-8')
    decoded = base64.b64decode(byte_string)
    return decoded.decode('utf-8')


def encode_b64(data):
    '''Wrapper for b64encode, without having to struggle with bytestrings.'''
    byte_string = data.encode('utf-8')
    encoded = base64.b64encode(byte_string)
    return encoded.decode('utf-8')


class SMTPChannel(object):
    """
    Port from stdlib smtpd used by Gevent
    """
    COMMAND = 0
    DATA = 1

    def __init__(self, server, conn, addr, data_size_limit=1024000,
                 credential_validator=None, only_ssl=False):
        self.server = server
        self.conn = conn
        self.addr = addr
        self.line = []
        self.state = self.COMMAND
        self.seen_greeting = 0
        self.mailfrom = None
        self.rcpttos = []
        self.data = ''
        self.fqdn = socket.getfqdn()
        self.ac_in_buffer_size = 4096

        self.ac_in_buffer = u''.encode('utf-8')
        self.closed = False
        self.data_size_limit = data_size_limit # in byte
        self.current_size = 0

        # Need authentication?
        if credential_validator:
            self.require_authentication = True
        else:
            self.require_authentication = False
        self.credential_validator = credential_validator
        self.authenticated = False
        self.authenticating = False
        self.auth_type = None
        self.username = None
        self.password = None

        try:
            self.peer = conn.getpeername()
        except socket.error as err:
            # a race condition  may occur if the other end is closing
            # before we can get the peername
            logger.error(err)
            self.conn.close()
            if err[0] != errno.ENOTCONN:
                raise
            return
        # Connection should be esablished using ssl
        if not only_ssl and self.server.ssl:
            self.starttls = True
        else:
            self.starttls = False

        if only_ssl and self.server.ssl:
            self.conn = ssl.wrap_socket(self.conn, **self.server.ssl)
            self.tls = True
        else:
            self.tls = False

        self.push(u'220 %s GSMTPD at your service' % self.fqdn)
        self.terminator = u'\r\n'
        logger.debug(u'SMTP channel initialized')

    # Overrides base class for convenience
    def push(self, msg):
        logger.debug(u'PUSH %s' % msg)
        self.conn.send((msg + u'\r\n').encode('utf-8')) # python2

    # Implementation of base class abstract method
    def collect_incoming_data(self, data):
        self.line.append(data)
        self.current_size += len(data)
        if self.current_size > self.data_size_limit:
            self.push('452 Command has been aborted because mail too big')
            self.close_when_done()

    # Implementation of base class abstract method
    def found_terminator(self):
        line = EMPTYSTRING.join(self.line)
        self.line = []
        if self.state == self.COMMAND:
            if not line:
                self.push('500 Error: bad syntax')
                return
            method = None
            i = line.find(' '.encode('utf-8'))
            if self.authenticating:
                # If we are in an authenticating state, call the
                # method smtp_AUTH.
                arg = line.strip()
                command = 'AUTH'
            elif i < 0:
                command = line.upper().strip().decode('UTF-8')
                arg = None
            else:
                command = line[:i].upper().decode('UTF-8')
                arg = line[i+1:].strip()

            print('Received: ' + command)
            # White list of operations that are allowed prior to AUTH.
            if not command in ['AUTH', 'EHLO', 'HELO', 'NOOP', 'RSET', 'QUIT', 'STARTTLS']:
                if self.require_authentication and not self.authenticated:
                    self.push('530 Authentication required')
                    return
            method = getattr(self, 'smtp_' + command, None)
            logger.debug('%s:%s', command, arg)
            if not method:
                self.push('502 Error: command "%s" not implemented' % command)
                return
            if arg:
                arg = arg.decode('utf-8')
            method(arg)
            return
        else:
            if self.state != self.DATA:
                self.push('451 Internal confusion')
                return
            # Remove extraneous carriage returns and de-transparency according
            # to RFC 821, Section 4.5.2.
            data = []
            for text in line.split('\r\n'.encode('utf-8')):
                if text and text[0] == '.':
                    data.append(text[1:])
                else:
                    data.append(text)
            self.data = NEWLINE.join(data)
            status = self.server.process_message(self.peer,
                                                   self.mailfrom,
                                                   self.rcpttos,
                                                   self.data)
            self.rcpttos = []
            self.mailfrom = None
            self.state = self.COMMAND
            self.terminator = '\r\n'
            if not status:
                self.push('250 Ok')
            else:
                self.push(status)

    # factored
    def getaddr(self, keyword, arg):
        address = None
        keylen = len(keyword)
        if arg[:keylen].upper() == keyword:
            address = arg[keylen:].strip()
            if not address:
                pass
            elif address[0] == '<' and address[-1] == '>' and address != '<>':
                # Addresses can be in the form <person@dom.com> but watch out
                # for null address, e.g. <>
                address = address[1:-1]
        return address

    # SMTP and ESMTP commands
    def smtp_HELO(self, arg):
        if not arg:
            self.push('501 Syntax: HELO hostname')
            return
        if self.seen_greeting:
            self.push('503 Duplicate HELO/EHLO')
        else:
            self.seen_greeting = arg
            self.push('250 %s' % self.fqdn)

    def smtp_EHLO(self, arg):
        if not arg:
            self.push('501 Syntax: EHLO hostname')
            return
        if self.seen_greeting:
            self.push('503 Duplicate HELO/EHLO')
        else:
            self.seen_greeting = arg
            self.extended_smtp = True
            if self.tls:
                self.push('250-%s on TLS' % self.fqdn)
            else:
                self.push('250-%s on plain' % self.fqdn)
            try:
                if self.require_authentication:
                    self.push('250-AUTH LOGIN PLAIN')
                if self.starttls and not self.tls:
                    self.push('250-STARTTLS')
            except AttributeError:
                pass
            if self.data_size_limit:
                self.push('250-SIZE %s' % self.data_size_limit)
            self.push('250 HELP')

    def smtp_AUTH(self, arg):
        if not arg:
            self.push('500 Syntax error, command unrecognized')
            return
        if self.seen_greeting == 0:
            self.push('503 Bad sequence of commands')
            return
        if not self.require_authentication:
            self.push('502 Error: command AUTH is not supported by server')
            return
        # if starttls is required and done, or not required give answer
        if self.starttls and not self.tls:
            self.push('530 Must issue a STARTTLS command first')
            return
        # arg = arg.decode('utf-8')
        if 'PLAIN' in arg or self.auth_type=='PLAIN':
            if arg == 'PLAIN':
                self.authenticating = True
                self.auth_type = 'PLAIN'
                self.push('334 ')
            else:
                split_args = arg.split(' ')
                if len(split_args) == 2:
                    auth_arg = split_args[1]
                else:
                    auth_arg = arg
                self.authenticating = False
                # second arg is Base64-encoded string of blah\0username\0password
                authbits = decode_b64(auth_arg).split('\0')
                self.username = authbits[1]
                self.password = authbits[2]
                if self.credential_validator and self.credential_validator.validate(self.username, self.password):
                    self.authenticated = True
                    self.push('235 Authentication successful.')
                else:
                    self.push('454 Temporary authentication failure.')
                    self.close_when_done()
        elif 'LOGIN' in arg or self.auth_type=='LOGIN':
            self.authenticating = True
            split_args = arg.split(' ')
            # Some implmentations of 'LOGIN' seem to provide the username
            # along with the 'LOGIN' stanza, hence both situations are
            # handled.
            if len(split_args) == 2:
                self.username = decode_b64(arg.split(' ')[1])
                self.push('334 ' + encode_b64('Username'))
            else:
                self.push('334 ' + encode_b64('Username'))
        elif not self.username:
            self.username = decode_b64(arg)
            self.push('334 ' + encode_b64('Password'))
        else:
            self.authenticating = False
            self.password = decode_b64(arg)
            if self.credential_validator and self.credential_validator.validate(self.username, self.password):
                self.authenticated = True
                self.push('235 Authentication successful.')
            else:
                self.push('454 Temporary authentication failure.')
                self.close_when_done()

    def smtp_NOOP(self, arg):
        if arg:
            self.push('501 Syntax: NOOP')
        else:
            self.push('250 Ok')

    def smtp_QUIT(self, arg=""):
        # args is ignored
        self.push('221 Bye')
        self.close_when_done()

    def smtp_TIMEOUT(self, arg=""):
        self.push('421 2.0.0 Bye')
        self.close_when_done()

    def smtp_MAIL(self, arg):
        address = self.getaddr('FROM:', arg) if arg else None
        if not address:
            self.push('501 Syntax: MAIL FROM:<address>')
            return
        if self.mailfrom:
            self.push('503 Error: nested MAIL command')
            return
        self.mailfrom = address
        self.push('250 Ok')

    def smtp_RCPT(self, arg):
        if not self.mailfrom:
            self.push('503 Error: need MAIL command')
            return
        address = self.getaddr('TO:', arg) if arg else None
        if not address:
            self.push('501 Syntax: RCPT TO: <address>')
            return

        result = self.server.process_rcpt(address)
        if not result:
            self.rcpttos.append(address)
            self.push('250 Ok')
        else:
            self.push(result)

    def smtp_RSET(self, arg):
        if arg:
            self.push('501 Syntax: RSET')
            return
        # Resets the sender, recipients, and data, but not the greeting
        self.mailfrom = None
        self.rcpttos = []
        self.data = ''
        self.state = self.COMMAND
        self.push('250 Ok')

    def smtp_DATA(self, arg):
        if not self.rcpttos:
            self.push('503 Error: need RCPT command')
            return
        if arg:
            self.push('501 Syntax: DATA')
            return
        self.state = self.DATA
        self.terminator = '\r\n.\r\n'
        self.push('354 End data with <CR><LF>.<CR><LF>')

    def smtp_STARTTLS(self, arg):
        if self.seen_greeting == 0:
            self.push('503 Bad sequence of commands')   # must send greetings first
            return
        if arg:
            self.push('501 Syntax: STARTTLS')
            return
        if not self.starttls:
            self.push('502 Error: command STARTTLS is not supported by server')
            return
        if self.data:
            self.push('500 Too late to changed')
            return
        self.push('220 Ready to start TLS')
        try:
            self.conn = ssl.wrap_socket(self.conn, **self.server.ssl)
            self.state = self.COMMAND
            self.seen_greeting = 0
            self.rcpttos = []
            self.mailfrom = None
            self.tls = True
        except Exception as err:
            logger.error(err, exc_info=True)
            self.push('503 certificate is FAILED')
            self.close_when_done()

    def smtp_HELP(self, arg):

        if arg:
            if arg == 'ME':
                self.push('504 Go to https://github.com/34nm/gsmtpd/issues for help')
            else:
                self.push('501 Syntax: HELP')
        else:
            self.push('214 SMTP server is running...go to website for further help')

    def handle_read(self):
        try:
            data = self.conn.recv(self.ac_in_buffer_size)
            if len(data) == 0:
                # issues 2 TCP connect closed will send a 0 size pack
                self.close_when_done()
        except socket.error:
            self.handle_error()
            return

        self.ac_in_buffer = self.ac_in_buffer + data # .decode('utf-8') # python2

        # Continue to search for self.terminator in self.ac_in_buffer,
        # while calling self.collect_incoming_data.  The while loop
        # is necessary because we might read several data+terminator
        # combos with a single recv(4096).

        while self.ac_in_buffer:
            lb = len(self.ac_in_buffer)
            logger.debug(self.ac_in_buffer)
            if not self.terminator:
                # no terminator, collect it all
                self.collect_incoming_data(self.ac_in_buffer)
                self.ac_in_buffer = ''
            elif isinstance(self.terminator, int): # or isinstance(self.terminator, long): python2
                # numeric terminator
                n = self.terminator
                if lb < n:
                    self.collect_incoming_data(self.ac_in_buffer)
                    self.ac_in_buffer = ''
                    self.terminator = self.terminator - lb
                else:
                    self.collect_incoming_data (self.ac_in_buffer[:n])
                    self.ac_in_buffer = self.ac_in_buffer[n:]
                    self.terminator = 0
                    self.found_terminator()
            else:
                # 3 cases:
                # 1) end of buffer matches terminator exactly:
                #    collect data, transition
                # 2) end of buffer matches some prefix:
                #    collect data to the prefix
                # 3) end of buffer does not match any prefix:
                #    collect data
                terminator_len = len(self.terminator)
                index = self.ac_in_buffer.find(self.terminator.encode('utf-8'))
                if index != -1:
                    # we found the terminator
                    if index > 0:
                        # don't bother reporting the empty string (source of subtle bugs)
                        self.collect_incoming_data (self.ac_in_buffer[:index])
                    self.ac_in_buffer = self.ac_in_buffer[index+terminator_len:]
                    # This does the Right Thing if the terminator is changed here.
                    self.found_terminator()
                else:
                    # check for a prefix of the terminator
                    index = find_prefix_at_end(self.ac_in_buffer, self.terminator.encode('utf-8'))
                    if index:
                        if index != lb:
                            # we found a prefix, collect up to the prefix
                            self.collect_incoming_data (self.ac_in_buffer[:-index])
                            self.ac_in_buffer = self.ac_in_buffer[-index:]
                        break
                    else:
                        # no prefix, collect it all
                        self.collect_incoming_data(self.ac_in_buffer)
                        self.ac_in_buffer = ''.encode('utf-8')

    def handle_error(self):
        self.close_when_done()

    def close_when_done(self):

        if not self.conn.closed:
            logger.debug('CLOSED %s' % self.conn)
            self.conn.close()
        self.closed = True
