import pickle, os
import logging, logging.handlers
import socketserver, struct

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    server_logger = logging.getLogger(__name__)
    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
#             print('received', record)
            self.handleLogRecord(record)

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
#         if self.server.logname is not None:
#             name = self.server.logname
#         else:
#             name = record.name
#         logger = logging.getLogger(name)
        
#         if (logger.handlers == []):
#             # print(logger.name, logger.propagate , logger.handlers )
#             f_handler = logging.FileHandler(self.logfile)
#             f_handler.setLevel(logging.INFO)
# #             f_format = logging.Formatter('''%(asctime)s - %(name)s - %(levelname)s\n\
# #                 - %(processName)s - %(process)s - %(threadName)s\n\
# #                 - %(pathname)s - %(module)s - %(funcName)s - %(lineno)s\n\
# #                 - %(message)s\n''')
#             f_format =logging.Formatter(
#                 '%(asctime)s, %(processName)s, %(process)s, %(threadName)s, '+\
#                 '%(pathname)s, %(lineno)s, %(module)s, %(funcName)s, %(message)s\n')
#             f_handler.setFormatter(f_format)
#             logger.addHandler(f_handler)
        
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        self.server_logger.handle(record)

class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, host, port, handler):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [], self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort

def start_logger(host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT, logfile = '/tmp/instru.log'):
#     logging.basicConfig(
#         format='%(relativeCreated)5d %(name)-15s %(levelname)-8s %(message)s')
    server_logger = logging.getLogger(__name__)
    f_handler = logging.FileHandler(logfile)
    f_handler.setLevel(logging.INFO)
    f_format =logging.Formatter(
        '%(asctime)s, %(processName)s, %(process)s, %(threadName)s, '+\
        '%(pathname)s, %(lineno)s, %(module)s, %(funcName)s, %(message)s\n')
    f_handler.setFormatter(f_format)
    server_logger.addHandler(f_handler)
    LogRecordStreamHandler.server_logger = server_logger
    tcpserver = LogRecordSocketReceiver(host, port, LogRecordStreamHandler)
    print('Start logging server: process {} listens on {}:{} '.format(os.getpid(), host, port))

    tcpserver.serve_until_stopped()
