from pyliveupdate.update import Instrument, UpdateManager
from pyliveupdate.stub import remote_logger, local_logger
from pyliveupdatescripts.updatebase import UpdateBase
import time

class LineProfiler(UpdateBase):
    
    @staticmethod
    def _line_before(start):
        start = time.time()
    
    @staticmethod
    def _line_after(start):
        time_ = (time.time()-start)*1000
        local_logger.info('{:.4f} ms'.format(time_))
        remote_logger.info('{:.4f} ms'.format(time_))
    
    @staticmethod
    def profile(scope):
        scopes = scope
        if isinstance(scope, str):
            scopes = [scope]
        for scope in scopes:
            update = Instrument(scope, 
                            {'line_before': LineProfiler._line_before, 
                             'line_after': LineProfiler._line_after})
            UpdateManager.apply_update(update)

LP = LineProfiler
UpdateBase.register_builtin(globals())