from pyliveupdate.controller import UpdateController, start_log_server
import argparse, multiprocessing, os
from pyliveupdate.config import CONTROLLER_IP, CONTROLLER_PORT

def main():
    parser = argparse.ArgumentParser(description='Update server')
    parser.add_argument('-l', '--logserver', 
                        help='start log server to accept logs from client',
                        action="store_true")
    parser.add_argument('targets', type=str,
          help='target addresses separated with ";", example: 127.0.0.1:50050;127.0.0.2:50050')
    args = parser.parse_args()
    
    logprocess = None
    if args.logserver:
        logprocess = multiprocessing.Process(target=start_log_server)
        logprocess.start()
    
#     startpayloads = ['exec("from pyliveupdatescripts import *")']  
#     if args.attachscript:
#         startpayloads.append(r"exec(r'''{}''')".format(open(args.attachscript).read()))
    
    addresses = []
    for t in args.targets.split(';'):
        addresses.append(t.strip())
    UpdateController().start(addresses)
    if logprocess:
        logprocess.terminate()
    
if __name__ == '__main__':
    main()