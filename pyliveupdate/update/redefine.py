import inspect, sys, time
import copy, types, os
from bytecode import Bytecode

from pyliveupdate.update.targetfinder import TargetFinder
from pyliveupdate.update.instrumenter import Instrumenter
from pyliveupdate.update.update import Update

class Redefine(Update):    
    def __init__(self, module, predefine, func_defines, 
             update_trigger=None, revert_trigger=None):
        '''
        module: which module this redefine will happen
        predefine: operations need to be done before the redefine,
                   like import a module
        func_defines: functions and their new definitions in a dict
        '''
        super(Redefine, self).__init__()
        self.module = module
        self.predefine = predefine
        self.func_defines = func_defines
    
    def _get_predefine_code(self, predefine):
        bytecode_ = Bytecode.from_code(predefine.__code__)
        for bc in bytecode_:
            # stubstitute *_FAST to *_NAME such as STORE_FAST to STORE_NAME
            # so that variable will be stored in given namespace
            bc.name = bc.name.replace('_FAST', '_NAME')
            
        # there is a mysterious bug with 'return bytecode_.to_code()'
        return Bytecode(bytecode_).to_code()
    
    def apply(self):
        if self.applied:
            return False
        modules = TargetFinder.find(self.module)
        if len(modules) == 1:
            module = modules[0]
        else:
            print('Module {} not found'. format(self.module))
            return False
        
        # execute predefine in the target module namespace
        exec(self._get_predefine_code(self.predefine), vars(module))
        
        for fname, new_func in self.func_defines.items():
            targets = TargetFinder.find(fname)
            if len(targets) == 1:
                target = targets[0]
                self.old_codes[target] = target.__code__
                target.__code__ = new_func.__code__
                self.applied = True
            else:
                print('Target {} not found'.format(fname))
        return self.applied
    
    def __repr__(self):
        if self.applied:
            status = 'applied'
        else:
            status = 'not applied'
        
        applied_targets = []
        for t in self.func_defines:
            applied_targets.append(t)
        applied_targets = sorted(applied_targets)
        return '{{type: redefine, status: {}, module: {}, \nredefined: [{}]}}'\
                .format(status, self.module, '\n'.join(applied_targets))
    