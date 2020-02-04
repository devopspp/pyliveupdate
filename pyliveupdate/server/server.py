from pyliveupdate import IPC
import os, sys, stat, socket, struct, readline
import tempfile, traceback, subprocess, platform
from os.path import dirname, abspath, join


class UpdateServer():
    def __init__(self, host='localhost', port=9001, timeout=5):
        super(UpdateServer, self).__init__()
        self.sock = None
        self.server_sock = None
        self.hostname = host
        self.port = port
        self.timeout = float(timeout)

    def __exit__(self, *args, **kwargs):
        try:
            if self.sock:
                self.sock.close()
            if self.server_sock:
                self.server_sock.close()
        except:
            traceback.print_exc()

    def _listen(self):
        """Listen on a random port"""
        for res in socket.getaddrinfo('localhost', 9001, socket.AF_UNSPEC,
                                      socket.SOCK_STREAM, 0, 0):
            af, socktype, proto, canonname, sa = res
            try:
                self.server_sock = socket.socket(af, socktype, proto)
                try:
                    self.server_sock.bind(sa)
                    self.server_sock.listen(1)
                except socket.error:
                    self.server_sock.close()
                    self.server_sock = None
                    continue
            except socket.error:
                print("error 117")
                self.server_sock = None
                continue
            break

        if not self.server_sock:
            raise Exception('Unable to setup a local server socket')
        else:
            self.hostname, self.port = self.server_sock.getsockname()[0:2]
            print("Start update server starts: process {} listening on {}:{}".format(
                os.getpid(), self.hostname, self.port))

    def _wait(self):
        """Wait for the injected payload to connect back to us"""
        (clientsocket, address) = self.server_sock.accept()
        self.sock = clientsocket
        #print("ipc.wait. self.sock: ", self.sock)
        self.sock.settimeout(self.timeout)
        self.address = address
        
    def start(self):
#         print('Starting update server')
        self._listen()
        self._wait()
        ipc = IPC(self.sock)
        prompt, payload = ipc.recv().split('\n', 1)
        
        ### py3k compat ###
        try:
            input_ = raw_input
        except NameError:
            input_ = input
        
        while True:
            try:
                try:
                    input_line = input_(prompt)
                except Exception as e:
                    print("Error: ", e, prompt)
                    input_line = '101 exit()'
                    ipc.send(input_line)
                    break
                ipc.send(input_line)
                payload = ipc.recv()
                if payload is not None:
                    prompt, payload = payload.split('\n', 1)
                    print(payload)
            except:
                raise Exception('Server error')