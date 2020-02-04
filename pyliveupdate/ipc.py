import struct

class IPC(object):
    def __init__(self, sock):
        super(IPC, self).__init__()
        self.sock = sock

    def send(self, data):
        """
        Send arbitrary data to the process via self.sock
        """
        header = ''.encode('utf-8')
        data = data.encode('utf-8')
        header = struct.pack('<L', len(data))
        self.sock.sendall(header + data)

    def recv(self):
        """
        Receive a command from a given socket
        """
        header_data = self.recv_bytes(4)
        
        if len(header_data) == 4:
            msg_len = struct.unpack('<L', header_data)[0]
#             print("header_data: ", struct.unpack('<L', header_data))
            data = self.recv_bytes(msg_len).decode('utf-8')
#             print("ipc.recv.data : ", data, "|")
            if len(data) == msg_len:
                return data

    def recv_bytes(self, n):
        """
        Receive n bytes from a socket
        """
        data = ''.encode('utf-8')
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.pid)
