from pyliveupdate.controller import UpdateController, start_logger
import argparse, multiprocessing, os
# from pyliveupdatescripts import *


def main():
    parser = argparse.ArgumentParser(description='Update server')
    parser.add_argument('-l', '--logserver', 
                        help='start log server to accept logs from client',
                        action="store_true")
#     parser.add_argument('--attachscript', type=str, 
#                         help='an update script to attach to the target program')
    parser.add_argument('-p', '--port', type=int, default=50050,
                        help='the controller listening port (default: 50050)')
    args = parser.parse_args()
    
    logprocess = None
    if args.logserver:
        logprocess = multiprocessing.Process(target=start_logger)
        logprocess.start()
    
#     startpayloads = ['exec("from pyliveupdatescripts import *")']  
#     if args.attachscript:
#         startpayloads.append(r"exec(r'''{}''')".format(open(args.attachscript).read()))

    UpdateController(args.port).start()
    if logprocess:
        logprocess.terminate()
    
if __name__ == '__main__':
    main()