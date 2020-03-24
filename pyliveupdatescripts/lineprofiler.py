from pyliveupdate.update import Instrument, UpdateManager
from pyliveupdate.stub import remote_logger, local_logger
from pyliveupdatescripts.updatebase import UpdateBase
from collections.abc import Iterable
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
    def profile(scope, lines):
        scopes = scope
        if isinstance(scope, str):
            scopes = [scope] 
        if not isinstance(lines, Iterable):
            lines = (lines,)
        else:
            lines = tuple(lines)
            
        for scope in scopes:
            update = Instrument(scope, 
                            {('line_before', lines): LineProfiler._line_before, 
                             ('line_after', lines): LineProfiler._line_after})
            UpdateManager.apply_update(update)

LP = LineProfiler
UpdateBase.register_builtin(globals())