#!/usr/bin/env python
# encoding: utf-8

"""
gsmtpd server
---------------------

gsmtpd is a SMTP server implement based on Gevent library,
better in conccurence and more API

Example

.. code:: python

    from gevent import monkey
    monkey.patch_all()

    from gsmtpd.server import SMTPServer

    class PrintSMTPServer(SMTPServer):

        def process_message(self, peer, mailfrom, rcpttos, data):
            print data

    print_server = PrintSMTPServer()
    print_server.serve_forever()

"""

__title__ = 'gsmtpd'
__version__ = '0.1.9.3'
__author__ = 'Meng Zhuo <mengzhuo1203@gmail.com>'

# Set default logging handler to avoid "No handler found" warnings.
import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
