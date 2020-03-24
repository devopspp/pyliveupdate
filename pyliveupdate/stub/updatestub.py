import sys, os, time, logging, socket, subprocess
from concurrent import futures
from pyliveupdate.util import Render

import grpc
from pyliveupdate.grpc import updatestubproxy_pb2
from pyliveupdate.grpc import updatestubproxy_pb2_grpc
from pyliveupdate.grpc import updatestub_pb2
from pyliveupdate.grpc import updatestub_pb2_grpc
import threading
from code import InteractiveInterpreter
from io import StringIO
from pyliveupdate.util import get_ip, IORedirecter
from pyliveupdate.config import STUB_IP, STUB_PORT, PROXY_PORT
PROXYFILE = os.path.join(os.path.dirname(__file__),'updatestubproxy.py')

logger = logging.getLogger(__name__)

class RemoteEvaluator(updatestub_pb2_grpc.RemoteEvalServicer):
    def eval_(self, request, context):
        result = ''
        try:
            expression = request.expression
            self.redirect_out()
            InteractiveInterpreter(globals()).runsource(expression, '<console>', 'single')
            result = self.reset_out()
        except Exception as e:
            logger.error(e)
        return updatestub_pb2.EvalResponse(result=str(result), returncode="SUCCESS")
    
    def ping(self, request, context):
        return updatestub_pb2.PingResponse(result='ack', returncode="SUCCESS")
    
    def redirect_out(self):
        self.redirecter = IORedirecter()
        self.redirecter.enable_proxy()
        self.redirecter.redirect()

    def reset_out(self):
        value = self.redirecter.stop_redirect()
        self.redirecter.disable_proxy()
        return value

class UpdateStub(threading.Thread):
    def __init__(self, ip=STUB_IP, port=STUB_PORT):
        super(UpdateStub, self).__init__()
        self.daemon = True
        self.ip = str(ip)
        self.port = str(port)
    
    def register(self, proxy_address):
        '''
        register this stub with proxy
        '''
#         creds = grpc.ssl_channel_credentials(
#                 certificate_chain=client_cert, private_key=client_key,
#                 root_certificates=server_cert)
#         channel = grpc.secure_channel(address, creds)
#         with grpc.secure_channel(proxy_address, creds) as channel:
        with grpc.insecure_channel(proxy_address) as channel:
            stub = updatestubproxy_pb2_grpc.UpdateStubProxyStub(channel)
            try:
                request= updatestubproxy_pb2.RegisterRequest(
                                            ip=self.ip, port=self.port)
                response = stub.register(request)
                
                if response.returncode == 0:
                    logger.info('Update stub {}:{} registered at proxy {}'\
                                .format(self.ip, self.port, proxy_address))
                else:
                    logger.error('Update stub {}:{} failed to register at prxy {}'\
                                .format(self.ip, self.port, proxy_address))
            except Exception as e:
                logger.error(e)
                
    def ping_proxy(self, address):
#         creds = grpc.ssl_channel_credentials(
#                 certificate_chain=client_cert, private_key=client_key,
#                 root_certificates=server_cert)
#         channel = grpc.secure_channel(address, creds)
        
        channel = grpc.insecure_channel(address)
        stub = updatestubproxy_pb2_grpc.UpdateStubProxyStub(channel)
        
        try:
            request = updatestubproxy_pb2.PingRequest()
            response = stub.ping(request, timeout=2)
            if response.returncode == 0:
                return True
            else:
                return False
        except Exception as e:
            return False
    
    def start_grpc_server(self):
        stubserver = grpc.server(futures.ThreadPoolExecutor(max_workers=10), maximum_concurrent_rpcs=1)
        updatestub_pb2_grpc.add_RemoteEvalServicer_to_server(RemoteEvaluator(), stubserver)
        self.port = str(stubserver.add_insecure_port('[::]:0')) # set to 0 to let grpc select a port
        stubserver.start()
        return stubserver
        
    def start_proxy_if_not(self, address):
        if not self.ping_proxy(address):
            subprocess.Popen(['python', PROXYFILE], 
                             preexec_fn=os.setpgrp)
            time.sleep(1)
            if self.ping_proxy(address):
                print(Render.rend_correct(
                    'succeed to start proxy at {}'.format(address)))
            else:
                print(Render.rend_wrong(
                    'failed to start proxy at {}'.format(address)))
            
    def run(self):
        stubserver = self.start_grpc_server()
        
        proxy_address = '{}:{}'.format(self.ip, PROXY_PORT)
        self.start_proxy_if_not(proxy_address)
        self.register(proxy_address)
        
        stubserver.wait_for_termination()

if __name__ == '__main__':
    updatestub = UpdateStub()
    updatestub.start()
    updatestub.join()