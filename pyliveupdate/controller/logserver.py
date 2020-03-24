import pickle, os
import logging, logging.handlers
import socketserver, struct
from pyliveupdate.config import LOG_SERVER_IP, LOG_SERVER_PORT, LOG_FILE

logger = logging.getLogger(__name__)

class LogRecordStreamHandler(socketserver.StreamRequestHandler):
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
            logger.handle(record)

    def unPickle(self, data):
        return pickle.loads(data)
        
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

def start_log_server(host=LOG_SERVER_IP, port=LOG_SERVER_PORT, logfile=LOG_FILE):
    # f_handler = logging.FileHandler(logfile, 'w')
    f_handler = logging.handlers.RotatingFileHandler(logfile, backupCount=50)
    f_handler.doRollover()
    f_handler.setLevel(logging.INFO)
    # f_format = logging.Formatter('''%(asctime)s - %(name)s - %(levelname)s\n\
    #     - %(processName)s - %(process)s - %(threadName)s\n\
    #     - %(pathname)s - %(module)s - %(funcName)s - %(lineno)s\n\
    #     - %(message)s\n''')
    f_format =logging.Formatter(
        '%(asctime)s; %(processName)s; %(process)d; %(threadName)s; %(thread)d; '+\
        '%(pathname)s; %(lineno)d; %(module)s; %(funcName)s; %(message)s')
    f_handler.setFormatter(f_format)
    logger.setLevel(logging.INFO)
    logger.addHandler(f_handler)
    
    tcpserver = LogRecordSocketReceiver(host, port, LogRecordStreamHandler)
    print('Start logging server: process {} listens on {}:{}'.format(os.getpid(), host, port))
    tcpserver.serve_until_stopped()
