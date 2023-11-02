# This is a simple port-forward / proxy, written using only the default python
# library. If you want to make a suggestion or fix something you can contact-me
# at voorloop_at_gmail.com
# Distributed over IDC(I Don't Care) license

import socket
import select
import threading


buffer_size = 4096


class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def start(self, socket_file):
        try:
            self.forward.connect(socket_file)
            return self.forward
        except Exception:
            return False

class SocketForwardServer(threading.Thread):
    input_list = []
    channel = {}

    def __init__(self, host=None, port=None, socket_file=None):
        threading.Thread.__init__(self)
        self.stop = False
        self.socket_file = socket_file
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen()

    def run(self):
        self.input_list.append(self.server)
        #print("Server started and listening")
        while not self.stop:
            # time.sleep(delay)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [], 1)
            for self.s in inputready:
                if self.s == self.server:
                    self.on_accept()
                    break

                self.data = self.s.recv(buffer_size)
                if len(self.data) == 0:
                    self.on_close()
                    break
                else:
                    self.on_recv()
        for sock in self.input_list:
            sock.close()
        #print("Server stopping")

    def on_accept(self):
        forward = Forward().start(self.socket_file)
        clientsock, clientaddr = self.server.accept()
        if forward:
            # print(clientaddr, "has connected")
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock
        else:
            #print("Can't establish connection with remote server.",)
            #print("Closing connection with client side", clientaddr)
            clientsock.close()

    def on_close(self):
        #remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]

    def on_recv(self):
        # here we can parse and/or modify the data before send forward
        self.channel[self.s].send(self.data)

    def stop_server(self):
        self.stop = True
