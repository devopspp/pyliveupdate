from concurrent import futures
import time, datetime, threading
import sys, os, readline, logging, atexit
from pyliveupdate.util import get_ip

import grpc
from pyliveupdate.grpc import updateregister_pb2
from pyliveupdate.grpc import updateregister_pb2_grpc
from pyliveupdate.grpc import updatestub_pb2
from pyliveupdate.grpc import updatestub_pb2_grpc
from pyliveupdate.config import STUBFILE, HISTORYFILE
from pyliveupdate.config import CONTROLLER_IP, CONTROLLER_PORT, STUB_IP, STUB_PORT
from pyliveupdate.config import RPC_LONG_TIMEOUT, MAX_WORKERS, MAX_CONCURRENT_RPCS
logger = logging.getLogger(__name__)
prompt = ">>> "

class StubRegister(updateregister_pb2_grpc.StubRegisterServicer):
    def __init__(self):
        self.address_stubs = {}
        self.load_stubs()
        
    def _register(self, address):
        channel = grpc.insecure_channel(address)
        stub = updatestub_pb2_grpc.RemoteEvalStub(channel)
 
        try:
            request = updatestub_pb2.PingRequest()
            response = stub.ping(request, timeout=2)
            self.address_stubs[address] = stub
            print('Stub at {} registered'.format(address))
            return True
        except Exception as e:
            return False

    def register(self, request, context):
        address = '{}:{}'.format(request.ip, request.port)
        self._register(address)
        print(prompt, end='', flush=True)
        self.save_stubs()
        return updateregister_pb2.RegisterResponse(returncode='SUCCESS')
    
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
        print(prompt, end='', flush=True)
        
    def clear_stubs(self, fname=STUBFILE):
        '''
        clear stubs that are none and save the new stubs in file
        '''
        self.address_stubs = {address:stub for address, stub \
                              in self.address_stubs.items()\
                              if stub != None}
        self.save_stubs(fname)
        
        
class UpdateController(object):
    def __init__(self, ip=CONTROLLER_IP, port=CONTROLLER_PORT):
        self.ip = str(ip)
        self.port = str(port)
        self.stub_register = None
        self.waiting_tasks = []
        self.register_server = None
    
    def _start_grpcserver(self):
        self.register_server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=MAX_WORKERS), 
            maximum_concurrent_rpcs=MAX_CONCURRENT_RPCS)
        self.stub_register = StubRegister()
        updateregister_pb2_grpc.add_StubRegisterServicer_to_server(
            self.stub_register, self.register_server)
        self.register_server.add_insecure_port('[::]:{}'.format(self.port))
        self.register_server.start()
        print('Start update controller: process {} listens on {}:{}'.format(
            os.getpid(), self.ip, self.port))

    def _load_command_history(self, histfile = HISTORYFILE):
        try:
            readline.read_history_file(histfile)
            # default history len is -1 (infinite), which may grow unruly
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass
        atexit.register(readline.write_history_file, histfile)
    
    def _serve_input(self):
        while True:
            try:
                type_ = 'eval_'
                expression = str(input(prompt))
                if expression == '' or expression.startswith('#'):
                    continue
                if expression in ['exit', 'exit()', 'quit', 'quit()']:
                    break
                elif expression in ['ping', 'ping()']:
                    request = updatestub_pb2.PingRequest()
                    type_ = 'ping'
                else:
                    request = updatestub_pb2.EvalRequest(expression=expression)
                    type_ = 'eval_'
                
                for address, stub in self.stub_register.address_stubs.items(): 
                    try:
                        response = None
                        if type_ == 'ping':
                            response = stub.ping.future(request, timeout=2)
                        elif type_ == 'eval_':
                            response = stub.eval_.future(request, timeout=RPC_LONG_TIMEOUT)
                            
                        if response:
                            self.waiting_tasks.append(response)
                            response.add_done_callback(
                                self._get_response_handler(address))
                    except Exception as e:
                        print(e)
                        
                while len(self.waiting_tasks) != 0:
                    time.sleep(0.5)
                
                # clear unregistrred stub
                self.stub_register.clear_stubs()
                
            except Exception as e:
                print(e)
                sys.exit()
        #self.register_server.wait_for_termination()
        
    def _get_response_handler(self, address):
        def handle_response(response_future):
            self.waiting_tasks.remove(response_future)
            if response_future.code() == grpc.StatusCode.OK:
                response = response_future.result()
                result = response.result
                if not result.endswith('\n'):
                    result = result+'\n'
                if response.returncode == 0:
                    print('{}: {}'.format(address, result), 
                          end='', flush=True)
                else:
                    print("{} eval error: {}".format(address, result), 
                          end='', flush=True)
            else:
                print('{} is unavailable and so unregistered'.format(address))
                self.stub_register.address_stubs[address] = None
        return handle_response
    
    def start(self):
        self._start_grpcserver()
        
        self._load_command_history()
        self._serve_input()
        
if __name__ == '__main__':
    UpdateController().start()
