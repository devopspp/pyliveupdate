from pyliveupdate import *
import time, inspect

def func_begin():
    import time
    global start
    start = time.time()
    #print(time())
    
def func_end():
    from pyliveupdate import client
    import time, inspect
    global start
#     code_ = inspect.currentframe().f_code
#     func_name = '{} {}'.format(code_.co_filename, code_.co_name)
    time_ = (time.time()-start)*1000
#     print('{} execute time: {:.6f} ms'.format(func_name, time_))
    client.local_logger.info('execution time: {:.4f} ms'.format(time_))
    client.remote_logger.info('execution time: {:.4f} ms'.format(time_))

def instru(scope):
    update = Update('instrument', scope, 
                    {'func_begin':func_begin, 'func_end':func_end},
                   None, None, __name__)
    UpdateManager.apply_update(update)
    
def revert(updateid):
    UpdateManager.revert_update(updateid)

def listinstru():
    print(UpdateManager.updates)