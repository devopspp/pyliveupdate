import os, logging, logging.handlers
from pyliveupdate.util import get_ip

# base directory path to put config and data
BASEDIR = os.path.expanduser("~/.pyliveupdate")
os.makedirs(BASEDIR, exist_ok=True)

# file that stores the list of stub address
STUBFILE = os.path.join(BASEDIR, 'stubs')

# file that stores controller command history
HISTORYFILE = os.path.join(BASEDIR, ".python_history")

thisip = '127.0.0.1'#get_ip()

# make sure this is a local ip, otherwise may open security holes
# controller address
PROXY_IP = thisip
PROXY_PORT = '50050'

# make sure this is a local ip, otherwise may open security holes
# controller address
CONTROLLER_IP = thisip
CONTROLLER_PORT = '50060'

# make sure this is a local ip, otherwise may open security holes
# stub address, recommend to leave this as default
STUB_IP = thisip
STUB_PORT = '0'

# log server address
LOG_SERVER_IP = thisip
LOG_SERVER_PORT = logging.handlers.DEFAULT_TCP_LOGGING_PORT

# log file path
LOG_FILE = '/tmp/pyliveupdate.log'

# rpc config
RPC_LONG_TIMEOUT=60
MAX_WORKERS=100
MAX_CONCURRENT_RPCS=100

# server_key = open('server.key','rb').read()
# server_cert = open('server.cert','rb').read()
# client_cert= open('client.cert','rb').read()
# client_key = open('client.key', 'rb').read()
