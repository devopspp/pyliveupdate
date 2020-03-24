from pyliveupdate.update import Instrument, UpdateManager
from pyliveupdate.stub import remote_logger, local_logger
from pyliveupdatescripts.updatebase import UpdateBase
import time

class FuncDebugger(UpdateBase):
    
    @staticmethod
    def _func_begin(_parameters):
        local_logger.info('parameters: {}'.format(_parameters))
        remote_logger.info('parameters: {}'.format(_parameters))
        
    @staticmethod
    def _func_end(_returnvalues):
        local_logger.info('returnvalues: {}'.format(_returnvalues))
        remote_logger.info('returnvalues: {}'.format(_returnvalues))
    
    @staticmethod
    def debug(scope):
        scopes = scope
        if isinstance(scope, str):
            scopes = [scope]
            
        for scope in scopes:
            update = Instrument(scope, 
                            {('func_begin',): FuncDebugger._func_begin, 
                             ('func_end',): FuncDebugger._func_end})
            UpdateManager.apply_update(update)

FD = FuncDebugger
UpdateBase.register_builtin(globals())