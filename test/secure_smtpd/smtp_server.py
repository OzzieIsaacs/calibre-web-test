import secure_smtpd
import ssl, smtpd, asyncore, socket, logging, signal, time, sys
from .smtp_channel import SMTPChannel
from asyncore import ExitNow
from ssl import SSLError
from multiprocessing import Value, Process, Manager

error_code = Value('i', 0)

'''try:
    from Queue import Empty
except ImportError:
    # We're on python3
    from queue import Empty'''
manager = Manager()
emails = manager.list()
config = manager.dict()

smtpd.DEBUGSTREAM = sys.stdout

class SMTPServer(smtpd.SMTPServer):

    def __init__(self, localaddr, remoteaddr, starttls=True, use_ssl=False, certfile=None, keyfile=None, ssl_version=ssl.PROTOCOL_SSLv23, require_authentication=False, credential_validator=None, maximum_execution_time=30, process_count=5):
        smtpd.SMTPServer.__init__(self, localaddr, remoteaddr)
        self.logger = logging.getLogger( secure_smtpd.LOG_NAME )
        self.certfile = certfile
        self.keyfile = keyfile
        self.ssl_version = ssl_version
        self.subprocesses = []
        self.starttls = starttls
        self.require_authentication = require_authentication
        self.credential_validator = credential_validator
        self.ssl = use_ssl
        self.maximum_execution_time = maximum_execution_time
        self.process_count = process_count
        config['error_code'] = 0

    def handle_accept(self):
        for i in range(0, self.process_count):
            process = Process(target=self._accept_subprocess, args=[emails,config]) # (emails,config))
            process.daemon = True
            process.start()
        self.close()

    def _accept_subprocess(self, emails, config): # emails, config):
        while True:
            try:
                self.socket.setblocking(1)
                pair = self.accept()
                map = {}

                if pair is not None:

                    self.logger.info('_accept_subprocess(): smtp connection accepted within subprocess.')

                    newsocket, fromaddr = pair
                    newsocket.settimeout(self.maximum_execution_time)

                    if self.ssl:
                        newsocket = ssl.wrap_socket(
                            newsocket,
                            server_side=True,
                            certfile=self.certfile,
                            keyfile=self.keyfile,
                            ssl_version=self.ssl_version,
                        )
                    SMTPChannel(
                        self,
                        newsocket,
                        fromaddr,
                        require_authentication=self.require_authentication,
                        credential_validator=self.credential_validator,
                        map=map,
                        # er_code = error_code,
                        emails = emails,
                        config = config
                    )

                    self.logger.info('_accept_subprocess(): starting asyncore within subprocess.')

                    asyncore.loop(map=map)

                    self.logger.error('_accept_subprocess(): asyncore loop exited.')
            except (ExitNow, SSLError):
                self._shutdown_socket(newsocket)
                self.logger.info('_accept_subprocess(): smtp channel terminated asyncore.')
            except Exception as e:
                self._shutdown_socket(newsocket)
                self.logger.error('_accept_subprocess(): uncaught exception: %s' % str(e))

    def set_return_value(self, val):
        config['error_code'] = val
        # error_code.value = val

    def get_message_size(self):
        if 'size' in emails[-1]:
            return emails[-1]['size']
        else:
            return 0

    def get_recipents(self):
        if 'recipents' in emails[-1]:
            return emails[-1]['recipents']
        else:
            return None

    def get_sender(self):
        if 'mailfrom' in emails[-1]:
            return emails[-1]['mailfrom']
        else:
            return None

    '''@property
    def get_message_body(self):
        return self.payload'''

    def _shutdown_socket(self, s):
        try:
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        except Exception as e:
            self.logger.error('_shutdown_socket(): failed to cleanly shutdown socket: %s' % str(e))


    def run(self):
        asyncore.loop()
        if hasattr(signal, 'SIGTERM'):
            def sig_handler(signal,frame):
                self.logger.info("Got signal %s, shutting down." % signal)
                sys.exit(0)
            try:
                signal.signal(signal.SIGTERM, sig_handler)
            except Exception as e:
                self.logger.error('Failed to register signal: %s', str(e))
        while 1:
            time.sleep(1)
