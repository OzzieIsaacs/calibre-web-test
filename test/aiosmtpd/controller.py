import os
import asyncio
import threading
import ssl
import sys

from aiosmtpd.smtp import SMTP
from public import public


def get_server_context(certfile='files/server.crt', keyfile='files/server.key'):
    tls_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    tls_context.load_cert_chain(certfile, keyfile)
    return tls_context


@public
class Controller:
    def __init__(self, handler, loop=None, hostname=None, port=8025, *,
                 ready_timeout=1.0, enable_SMTPUTF8=True, ssl_context=None, authenticate=False,
                 startSSL=False, certfile=None, keyfile=None, timeout=300, global_timeout=2):
        """
        `Documentation can be found here
        <http://aiosmtpd.readthedocs.io/en/latest/aiosmtpd\
/docs/controller.html#controller-api>`_.
        """
        self.handler = handler
        self.hostname = '::1' if hostname is None else hostname
        self.port = port
        self.enable_SMTPUTF8 = enable_SMTPUTF8
        self.ssl_context = ssl_context
        self.loop = asyncio.new_event_loop() if loop is None else loop
        self.server = None
        self._thread = None
        self._thread_exception = None
        self.ready_timeout = os.getenv(
            'AIOSMTPD_CONTROLLER_TIMEOUT', ready_timeout)
        self.authenticate = authenticate
        self.startSSL = startSSL
        self.certfile = certfile
        self.keyfile = keyfile
        self.ssl = ssl
        self.timeout = timeout
        self._global_timeout_duration = global_timeout
        self._global_timeout_handle = None

    def factory(self):
        """Allow subclasses to customize the handler/server creation."""
        ssl = self.ssl_context
        if self.startSSL:
            ssl = get_server_context(self.certfile, self.keyfile)
        return SMTP(self.handler, enable_SMTPUTF8=self.enable_SMTPUTF8, require_starttls=self.startSSL,
                    authenticate=self.authenticate, tls_context=ssl, decode_data=True, timeout=self.timeout)

    def _run(self, ready_event):
        asyncio.set_event_loop(self.loop)
        try:
            if sys.version_info < (3, 7):
                self.server = self.loop.run_until_complete(
                    self.loop.create_server(
                        self.factory, host=self.hostname, port=self.port,
                        ssl=self.ssl_context))
            else:
                timeout = 10 if self.ssl_context else None
                self.server = self.loop.run_until_complete(
                    self.loop.create_server(
                        self.factory, host=self.hostname, port=self.port,
                        ssl=self.ssl_context, ssl_handshake_timeout=timeout))
        except Exception as error:
            self._thread_exception = error
            return
        self.loop.call_soon(ready_event.set)
        self.loop.run_forever()
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())
        self.loop.close()
        self.server = None

    def start(self):
        assert self._thread is None, 'SMTP daemon already running'
        ready_event = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(ready_event,))
        self._thread.daemon = True
        self._thread.start()
        # Wait a while until the server is responding.
        ready_event.wait(self.ready_timeout)
        if self._thread_exception is not None:
            raise self._thread_exception

    def _stop(self):
        self.loop.stop()
        if sys.version_info < (3, 7):
            for task in asyncio.Task.all_tasks(self.loop):
                task.cancel()
        else:
            for task in asyncio.all_tasks(self.loop):
                task.cancel()

    def stop(self):
        assert self._thread is not None, 'SMTP daemon not running'
        self.loop.call_soon_threadsafe(self._stop)
        self._thread.join()
        self._thread = None
