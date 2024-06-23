# -*- coding: utf8 -*-
#
# Copyright (C) 2011 Sebastian Rahlf <basti at redtoad dot de>
#
# This program is release under the MIT license. You can find the full text of
# the license in the LICENSE file.
# original code from pytest-mockredis 0.1.6 (https://pypi.org/project/pytest-mockredis/)
# modified with timeout to enable stopping of server without receiving next packet

import threading
import collections
import socket

import hiredis

class Redis(threading.Thread):
    def __init__(self, address='localhost', port=6379, *args, **kwargs):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.settimeout(1)
        self.server.bind((address, port))
        self.channels = collections.defaultdict(list)
        self.is_alive = True

        self.__curconn = None
        self.__reader = hiredis.Reader()

        super().__init__()

    def _process_commands(self, addr, *args, conn=None):
        command = args[0].decode('utf-8').lower()

        if command == 'ping':
            try:
                self.__curconn.sendall(b'PONG')
            except (AttributeError, socket.timeout):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sck:
                    sck.connect(addr)
                    sck.sendall(b'PONG')
        elif command == 'subscribe':
            for elem in args[1:]:
                elem = elem.decode('utf-8')
                self.channels[elem] = addr
        elif command == 'published':
            if args[1].decode('utf-8') in self.channels:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sck:
                    sck.connect(addr)
                    sck.sendall(args[2])

    def start(self):
        self.is_alive = True
        self.server.listen()
        super().start()

    def run(self):
        while self.is_alive:
            try:
                conn, addr = self.server.accept()
            except socket.timeout:
                continue
            self.__curconn = conn
            with conn:
                data = conn.recv(65536)
                if not data:
                    continue

                self.__reader.feed(data)
                data = self.__reader.gets()
                self._process_commands(addr, *data)

    def stop(self):
        self.is_alive = False
        self.clear_all()
        self.join()

    def clear_all(self):
        self.channels.clear()
