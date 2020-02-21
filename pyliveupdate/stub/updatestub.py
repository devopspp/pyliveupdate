import sys, os, time, logging, socket
from concurrent import futures

import grpc
from pyliveupdate.grpc import updateregister_pb2
from pyliveupdate.grpc import updateregister_pb2_grpc
from pyliveupdate.grpc import updatestub_pb2
from pyliveupdate.grpc import updatestub_pb2_grpc
import threading
from code import InteractiveInterpreter
from io import StringIO
from pyliveupdate.util import get_ip

logger = logging.getLogger(__name__)

class RemoteEvaluator(updatestub_pb2_grpc.RemoteEvalServicer):
    def send_eval(self, request, context):
        result = ''
        try:
            expression = request.expression
            self.redirect_out()
            InteractiveInterpreter(globals()).runsource(expression, '<console>', 'single')
            result = self.reset_out()
        except Exception as e:
            logger.error(e)
        return updatestub_pb2.SendEvalResponse(result=str(result), returncode="SUCCESS")
    
    def redirect_out(self):
        self.out_buffer = StringIO()
        sys.stdout = sys.stderr = self.out_buffer

    def reset_out(self):
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        value = self.out_buffer.getvalue()
        self.out_buffer.close()

        return value

class UpdateStub(threading.Thread):
    def __init__(self, controller_ip = '127.0.0.1', controller_port ='50050',
                ip = get_ip(), port = 0):
        super(UpdateStub, self).__init__()
        self.daemon = True
        self.controller_ip = controller_ip
        self.controller_port = controller_port
        self.ip = ip
        self.port = port
        self.port = 0
    
    def register(self, ip, port):
        '''
        register this stub with controller
        '''
        
        controller_address = '{}:{}'.format(self.controller_ip, self.controller_port)
        with grpc.insecure_channel(controller_address) as channel:
            stub = updateregister_pb2_grpc.StubRegisterStub(channel)
            try:
                response = stub.send_register(updateregister_pb2.SendRegisterRequest(ip=ip, port=port))
                
                if response.returncode == 0:
                    logger.info('Update stub {}:{} registered at controller {}'\
                                .format(ip, port, controller_address))
                else:
                    logger.error('Update stub {}:{} failed to register at controller {}'\
                                .format(ip, port, controller_address))
            except Exception as e:
                logger.error(e)
                
    def run(self):
        stubserver = grpc.server(futures.ThreadPoolExecutor(max_workers=10), maximum_concurrent_rpcs=1)
        updatestub_pb2_grpc.add_RemoteEvalServicer_to_server(RemoteEvaluator(), stubserver)
        self.port = str(stubserver.add_insecure_port('[::]:0')) ### set to 0 to let grpc select a port
        stubserver.start()
        
        self.register(self.ip, self.port)
        
        stubserver.wait_for_termination()

if __name__ == '__main__':
    updatestub = UpdateStub()
    updatestub.start()
    updatestub.join()