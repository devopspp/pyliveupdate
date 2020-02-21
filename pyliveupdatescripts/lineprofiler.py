from pyliveupdate import *
from pyliveupdatescripts import *
import time

class LineProfiler(UpdateBase):
    
    @staticmethod
    def _line_begin(start):
        start = time.time()
    
    @staticmethod
    def _line_end(start):
        time_ = (time.time()-start)*1000
        local_logger.info('{:.4f} ms'.format(time_))
        remote_logger.info('{:.4f} ms'.format(time_))
    
    @staticmethod
    def profile(scope):
        scopes = scope
        if isinstance(scope, str):
            scopes = [scope]
        for scope in scopes:
            update = Update('instrument', scope, 
                            {'line_begin': LineProfiler._line_begin, 
                             'line_end': LineProfiler._line_end},
                           None, None, __name__)
            UpdateManager.apply_update(update)

LP = LineProfiler
UpdateBase.register_builtin(globals())