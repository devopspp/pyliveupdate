import sys
import socket
import traceback
import threading
from code import InteractiveConsole
from io import StringIO
from pyliveupdate import *

class DistantInteractiveConsole(InteractiveConsole):
    def __init__(self, ipc):
        InteractiveConsole.__init__(self, globals())
        self.ipc = ipc
        self.set_buffer()

    def set_buffer(self):
        self.out_buffer = StringIO()
        sys.stdout = sys.stderr = self.out_buffer

    def unset_buffer(self):
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        value = self.out_buffer.getvalue()
        self.out_buffer.close()

        return value

    def raw_input(self, prompt=""):
        output = self.unset_buffer()        
        self.ipc.send('\n'.join((prompt, output)))

        try:
            cmd = self.ipc.recv()
        except Exception as e:
            print("reverse Error: ",e)
        
        self.set_buffer()

        return cmd


class UpdateClient(threading.Thread):
    """
    A reverse Python shell that behaves like Python interactive interpreter.
    """
    def __init__(self, host='localhost', port=9001):
        super(UpdateClient, self).__init__()
        self.daemon = True
        self.host = host
        self.port = port
        self.sock = None
    def run(self):
        try:
            for res in socket.getaddrinfo(self.host, self.port,
                    socket.AF_UNSPEC, socket.SOCK_STREAM):
                af, socktype, proto, canonname, sa = res
                try:
                    self.sock = socket.socket(af, socktype, proto)
                    try:
                        self.sock.connect(sa)
                    except socket.error:
                        self.sock.close()
                        self.sock = None
                        continue
                except socket.error:
                    self.sock = None
                    continue
                break

            if not self.sock:
                raise Exception('pyrasite cannot establish reverse ' +
                        'connection to %s:%d' % (self.host, self.port))
            try:
                print('========Update client started=========')
                ipc = IPC(self.sock)
                DistantInteractiveConsole(ipc).interact()
            except Exception as e:
                print(e)
            finally:
                self.sock.close()
        except SystemExit:
            pass
        except:
            traceback.print_exc(file=sys.__stderr__)
        finally:
            sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__