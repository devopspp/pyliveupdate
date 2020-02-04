from pyliveupdate.server import UpdateServer, start_logger
import argparse, multiprocessing, os

def main():
    parser = argparse.ArgumentParser(description='Update server')
    parser.add_argument('-l', 
                        '--logserver', 
                        help='start log server to accept logs from client',
                        action="store_true")
    args = parser.parse_args()
    if args.logserver:
        multiprocessing.Process(target=start_logger).start()
    UpdateServer().start()
    
if __name__ == '__main__':
    main()