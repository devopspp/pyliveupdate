from concurrent import futures
import time, datetime, threading
import sys, os, readline, logging, atexit
from pyliveupdate.util import get_ip

import grpc
from pyliveupdate.grpc import updateregister_pb2
from pyliveupdate.grpc import updateregister_pb2_grpc
from pyliveupdate.grpc import updatestub_pb2
from pyliveupdate.grpc import updatestub_pb2_grpc

logger = logging.getLogger(__name__)
prompt = ">>> "

class StubRegister(updateregister_pb2_grpc.StubRegisterServicer):
    def __init__(self):
        self.address_stubs = {}

    def send_register(self, request, context):
        address = '{}:{}'.format(request.ip, request.port)
        print(address)
#         address = '{}:{}'.format('127.0.0.1', request.port)
        channel = grpc.insecure_channel(address)
        stub = updatestub_pb2_grpc.RemoteEvalStub(channel)
        self.address_stubs[address] = stub
        print('Stub at {} registered'.format(address))
        print(prompt, end='', flush=True)
        return updateregister_pb2.SendRegisterResponse(returncode='SUCCESS')

class UpdateController(object):
    def __init__(self, port):
        self.ip = get_ip()
        self.port = str(port)
        self.stubregister = None
        self.waitingtasks = []
    
    def start(self):
        ### start grpc server
        registerserver = grpc.server(futures.ThreadPoolExecutor(max_workers=100), maximum_concurrent_rpcs=100)
        self.stubregister = StubRegister()
        updateregister_pb2_grpc.add_StubRegisterServicer_to_server(self.stubregister, registerserver)
        registerserver.add_insecure_port('[::]:{}'.format(self.port)) ### set to 0 to let grpc select a port
        registerserver.start()
        print('Start update controller: process {} listens on {}:{}'.format(os.getpid(), self.ip, self.port))
        
        ### read command history
        histfile = os.path.join(os.path.expanduser("~"), ".python_history")
        try:
            readline.read_history_file(histfile)
            # default history len is -1 (infinite), which may grow unruly
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass
        atexit.register(readline.write_history_file, histfile)
        
        ### serve user commands
        while True:
            try:
                expression = str(input(prompt))
                if expression == '' or expression.startswith('#'):
                    continue
                if expression in ['exit', 'exit()', 'quit', 'quit()']:
                    break
                request = updatestub_pb2.SendEvalRequest(expression=expression)

                for address, stub in self.stubregister.address_stubs.items(): 
                    try:
                        response = stub.send_eval.future(request, timeout=30)
                        response.add_done_callback(self.get_response_handler(address))
                        self.waitingtasks.append(response)
                    except Exception as e:
                        print(e)
                while len(self.waitingtasks) != 0:
                    time.sleep(0.2)
            except Exception as e:
                print(e)
                sys.exit()
        #registerserver.wait_for_termination()
        
    def get_response_handler(self, address):
        def handle_response(response_future):
            self.waitingtasks.remove(response_future)
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
        return handle_response
if __name__ == '__main__':
    UpdateController('50050').start()
