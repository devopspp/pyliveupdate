from pyliveupdate.update import Instrument, UpdateManager
from pyliveupdate.stub import remote_logger, local_logger
from pyliveupdatescripts.updatebase import UpdateBase
from collections.abc import Iterable
import time

class LineDebugger(UpdateBase):
    @staticmethod
    def _line_before(_righthands):
        local_logger.info('usevalues: {}'.format(_righthands))
        remote_logger.info('usevalues: {}'.format(_righthands))
        
    @staticmethod
    def _line_after(_lefthands):
        local_logger.info('defvalues: {}'.format(_lefthands))
        remote_logger.info('defvalues: {}'.format(_lefthands))
    
    @staticmethod
    def debug(scope, lines=()):
        scopes = scope
        if isinstance(scope, str):
            scopes = [scope]
        if not isinstance(lines, Iterable):
            lines = (lines,)
        else:
            lines = tuple(lines)
            
        for scope in scopes:
            update = Instrument(scope, 
                            {('line_before', lines): LineDebugger._line_before, 
                             ('line_after', lines): LineDebugger._line_after})
            UpdateManager.apply_update(update)

LD = LineDebugger
UpdateBase.register_builtin(globals())