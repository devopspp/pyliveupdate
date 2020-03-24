from concurrent import futures
import time, datetime, threading, re
import sys, os, readline, logging, atexit
from pyliveupdate.util import Render

import grpc
from pyliveupdate.grpc import updatestubproxy_pb2
from pyliveupdate.grpc import updatestubproxy_pb2_grpc
from pyliveupdate.config import STUBFILE, HISTORYFILE
from pyliveupdate.config import PROXY_IP, PROXY_PORT
from pyliveupdate.config import RPC_LONG_TIMEOUT, MAX_WORKERS, MAX_CONCURRENT_RPCS
logger = logging.getLogger(__name__)
prompt = ">>> "

class UpdateController(object):
    def __init__(self):
        self.waiting_tasks = []
        self.controllee_address_stubs = {}
    
    def _add_controllees(self, addresses):
        for address in addresses:
#             creds = grpc.ssl_channel_credentials(
#                 certificate_chain=client_key, private_key=client_key,
#                 root_certificates=server_cert)
#             channel = grpc.secure_channel(address, creds)
            channel = grpc.insecure_channel(address)
            stub = updatestubproxy_pb2_grpc.UpdateStubProxyStub(channel)
            try:
                request = updatestubproxy_pb2.PingRequest()
                response = stub.ping(request, timeout=2)
                self.controllee_address_stubs[address] = stub
                print(Render.rend_correct(
                    'Connect to update proxy {}'.format(address)))
            except Exception as e:
                print(Render.rend_wrong(
                    'Cannot connect to update proxy {}'.format(address)))
    
    def _clear_controllees(self):
        self.controllee_address_stubs = \
                        {address:stub for address, stub \
                          in self.controllee_address_stubs.items()\
                          if stub != None}

    def _load_command_history(self, histfile = HISTORYFILE):
        try:
            readline.read_history_file(histfile)
            # default history len is -1 (infinite), which may grow unruly
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass
        atexit.register(readline.write_history_file, histfile)
        
    def _get_patch_expression(self, filepath):
        filepath=filepath.replace('\'','').replace('"', '')
        filepath=os.path.abspath(filepath)
        with open(filepath) as fin:
            filecontent=fin.read()
        expression = "exec('''{}''')".format(filecontent)
        return expression
    
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
                    request = updatestubproxy_pb2.PingRequest()
                    type_ = 'ping'
                elif re.match('patch\s*\((.*)\)', expression) != None:
                    patchfile = re.match('patch\s*\((.*)\)', expression)[1]
                    patch_expression = self._get_patch_expression(patchfile)
                    request = updatestubproxy_pb2.EvalRequest(expression=patch_expression)
                    type_ = 'eval_'
                else: # add compile here to test if the code is correct
                    request = updatestubproxy_pb2.EvalRequest(expression=expression)
                    type_ = 'eval_'
                
                for address, stub in self.controllee_address_stubs.items(): 
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
                        print(Render.rend_wrong(e))
                        
                while len(self.waiting_tasks) != 0:
                    time.sleep(0.5)
                
                # clear unregistrred stub
                self._clear_controllees()
                
            except Exception as e:
                print(Render.rend_wrong(e))
                sys.exit()
        
    def _get_response_handler(self, address):
        def handle_response(response_future):
            self.waiting_tasks.remove(response_future)
            if response_future.code() == grpc.StatusCode.OK:
                response = response_future.result()
                result = response.result
                if not result.endswith('\n'):
                    result = result+'\n'
                if response.returncode == 0:
                    print(Render.rend_correct('proxy {}:'.format(address)))
                    print(result, end='', flush=True)
                else:
                    print(Render.rend_wrong(
                        'proxy {} eval error: {}'.format(address, result)), 
                          end='', flush=True)
            else:
                print(Render.rend_wrong(response_future))
                print(Render.rend_wrong(
                    'proxy {} is unavialable and so disconnected'.format(address)))
                self.controllee_address_stubs[address] = None
        return handle_response
    
    def start(self, addresses):
        self._add_controllees(addresses)
        self._load_command_history()
        self._serve_input()
        
if __name__ == '__main__':
    addresses = ['{}:{}'.format(PROXY_IP, PROXY_PORT)]
    if len(sys.argv) > 1:
        addresses = sys.argv[1:]
    UpdateController().start(addresses)
