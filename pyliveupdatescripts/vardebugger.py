from pyliveupdate.update import Instrument, UpdateManager
from pyliveupdate.stub import remote_logger, local_logger
from pyliveupdatescripts.updatebase import UpdateBase
import time

class VarDebugger(UpdateBase):
    @staticmethod
    def _var_use(_variable):
        local_logger.info('usevalues: {}'.format(_variable))
        remote_logger.info('usevalues: {}'.format(_variable))
        
    @staticmethod
    def _var_def(_variable):
        local_logger.info('defvalues: {}'.format(_variable))
        remote_logger.info('defvalues: {}'.format(_variable))
    
    @staticmethod
    def debug(scope, vars_=()):
        scopes = scope
        if isinstance(scope, str):
            scopes = [scope]
        if isinstance(vars_, str):
            vars_ = (vars_,)
            
        for scope in scopes:
            update = Instrument(scope, 
                            {('var_def', tuple(vars_)): VarDebugger._var_def, 
                             ('var_use', tuple(vars_)): VarDebugger._var_use})
            UpdateManager.apply_update(update)

VD = VarDebugger
UpdateBase.register_builtin(globals())