from concurrent import futures
import time, datetime, threading
import sys, os, readline, logging, atexit
from pyliveupdate.util import Render

import grpc
from pyliveupdate.grpc import updatestubproxy_pb2
from pyliveupdate.grpc import updatestubproxy_pb2_grpc
from pyliveupdate.grpc import updatestub_pb2
from pyliveupdate.grpc import updatestub_pb2_grpc
from pyliveupdate.config import STUBFILE, HISTORYFILE
from pyliveupdate.config import PROXY_IP, PROXY_PORT
from pyliveupdate.config import RPC_LONG_TIMEOUT, MAX_WORKERS, MAX_CONCURRENT_RPCS
logger = logging.getLogger(__name__)
prompt = ''

class StubProxy(updatestubproxy_pb2_grpc.UpdateStubProxyServicer):
    def __init__(self):
        self.address_stubs = {}
        self.waiting_tasks = []
        self.eval_results = []
        self.load_stubs()
        
    def _register(self, address):
        channel = grpc.insecure_channel(address)
        stub = updatestub_pb2_grpc.RemoteEvalStub(channel)
 
        try:
            request = updatestub_pb2.PingRequest()
            response = stub.ping(request, timeout=2)
            self.address_stubs[address] = stub
            print(Render.rend_correct('Stub at {} registered'.format(address)))
            return True
        except Exception as e:
            return False
    
    def save_stubs(self, fname=STUBFILE):
        with open(fname, 'w') as fout:
            for address in self.address_stubs:
                fout.write('{}\n'.format(address))
    
    def load_stubs(self, fname=STUBFILE):
        if not os.path.exists(fname):
            return
        with open(fname) as fin:
            for address in fin:
                address = address.strip()
                self._register(address)
                
        self.save_stubs()
        
    def clear_stubs(self, fname=STUBFILE):
        '''
        clear stubs that are none and save the new stubs in file
        '''
        self.address_stubs = {address:stub for address, stub \
                              in self.address_stubs.items()\
                              if stub != None}
        self.save_stubs(fname)
        
    def register(self, request, context):
        '''
        rpc UpdateStubProxyServicer.register
        '''
        address = '{}:{}'.format(request.ip, request.port)
        self._register(address)
        self.save_stubs()
        return updatestubproxy_pb2.RegisterResponse(returncode='SUCCESS')
    
    def eval_(self, request, context):
        '''
        rpc UpdateStubProxyServicer.eval_
        '''
        expression = request.expression
        request = updatestub_pb2.EvalRequest(expression=expression)

        for address, stub in self.address_stubs.items(): 
            try:
                response = stub.eval_.future(request, timeout=RPC_LONG_TIMEOUT)
                if response:
                    self.waiting_tasks.append(response)
                    response.add_done_callback(
                        self._get_response_handler(address))
            except Exception as e:
                self.eval_results.append('{}: {}'.format(address, e))

        while len(self.waiting_tasks) != 0:
            time.sleep(0.5)

        # clear unregistrred stub
        self.clear_stubs()
        result = ''.join(self.eval_results)
        self.eval_results = []
        return updatestubproxy_pb2.EvalResponse(result=result, returncode="SUCCESS")
    
    def _get_response_handler(self, address):
        def handle_response(response_future):
            self.waiting_tasks.remove(response_future)
            if response_future.code() == grpc.StatusCode.OK:
                response = response_future.result()
                result = response.result
                if not result.endswith('\n'):
                    result = result+'\n'
                if response.returncode == 0:
                    self.eval_results.append(
                        '{}: {}'.format(Render.rend_correct(address), result)) 
                else:
                    self.eval_results.append(
                        '{} eval error: {}'.format(Render.rend_wrong(address), result))
            else:
                self.eval_results.append(
                    Render.rend_wrong(
                        '{} is unavailable and so unregistered\n'.format(address)))
                self.address_stubs[address] = None
        return handle_response
    
    def ping(self, request, context):
        '''
        rpc UpdateStubProxyServicer.ping
        '''
        return updatestubproxy_pb2.PingResponse(result='ack', returncode="SUCCESS")
    
    def upload(self, request, context):
        try:
            with open(request.filename, 'w') as fout:
                fout.write(request.filecontent)
            return updatestubproxy_pb2.UploadResponse(returncode="SUCCESS")
        except:
            return updatestubproxy_pb2.UploadResponse(returncode="FAILURE")
    
    def download(self, request, context):
        try:
            filecontent = ''
            with open(request.filename) as fin:
                filecontent = fin.read()
            return updatestubproxy_pb2.DownloadResponse(
                returncode="SUCCESS", filename=request.filename,
                filecontent=filecontent)
        except:
            return updatestubproxy_pb2.DownloadResponse(
                returncode="FAILURE", filename=request.filename,
                filecontent='')
    
class ProxyServer(object):
    def __init__(self, ip=PROXY_IP, port=PROXY_PORT):
        self.ip = str(ip)
        self.port = str(port)
        self.proxyserver = None
        self.stubproxy = None
        
    def start(self):
        self.proxyserver = grpc.server(
            futures.ThreadPoolExecutor(max_workers=MAX_WORKERS), 
            maximum_concurrent_rpcs=MAX_CONCURRENT_RPCS)
        self.stubproxy = StubProxy()
        updatestubproxy_pb2_grpc.add_UpdateStubProxyServicer_to_server(
            self.stubproxy, self.proxyserver)
        
#         server_credentials = grpc.ssl_server_credentials(((server_key, server_cert),), 
#                                               client_cert, require_client_auth=True)
#         port = self.proxyserver.add_secure_port('{}:{}'.format(self.ip, self.port), server_credentials)
        port = self.proxyserver.add_insecure_port('[::]:{}'.format(self.port))
        if port != 0:
            self.proxyserver.start()
            print(Render.rend_correct(
                'Start update proxy: process {} listens on {}:{}'.format(
                    os.getpid(), self.ip, self.port)))
            self.proxyserver.wait_for_termination()
        else:
            print(Render.rend_wrong(
                 'Failed to start update proxy: process {} listens on {}:{}'.format(
                    os.getpid(), self.ip, self.port)))

def start_proxy():
    ProxyServer().start()
        
if __name__ == '__main__':
    start_proxy()
