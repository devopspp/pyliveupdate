from pyliveupdate import *
from pyliveupdatescripts import *
import time

class FuncProfiler(UpdateBase):
    start = 0
    
    @staticmethod
    def _func_begin():
        FuncProfiler.start = time.time()
    
    @staticmethod
    def _func_end():
        time_ = (time.time()-FuncProfiler.start)*1000
        local_logger.info('execution time: {:.4f} ms'.format(time_))
        remote_logger.info('execution time: {:.4f} ms'.format(time_))
    
    @staticmethod
    def profile(scope):
        scopes = scope
        if isinstance(scope, str):
            scopes = [scope]
        for scope in scopes:
            update = Update('instrument', scope, 
                            {'func_begin': FuncProfiler._func_begin, 
                             'func_end': FuncProfiler._func_end},
                           None, None, __name__)
            UpdateManager.apply_update(update)

FP = FuncProfiler
FuncProfiler.register_builtin(globals())