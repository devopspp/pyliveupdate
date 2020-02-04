import logging, logging.handlers, queue, time, os

class mysocketHandler(logging.handlers.SocketHandler):
    def emit(self, record):
        try:
            s = self.makePickle(record)
            print(s)
            self.send(s)
        except Exception:
            self.handleError(record)
            
def get_remote_logger(host='localhost', port=logging.handlers.DEFAULT_TCP_LOGGING_PORT):
    que = queue.Queue(-1)  # no limit on size
    queue_handler = logging.handlers.QueueHandler(que)

    socketHandler = logging.handlers.SocketHandler(host, port)
#     socketHandler = mysocketHandler(host, port)
    socketHandler.setLevel(logging.INFO)
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    socketHandler.setFormatter(c_format)

    listener = logging.handlers.QueueListener(que, socketHandler)
    listener.start()
    
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(queue_handler)
    return logger

remote_logger = get_remote_logger()