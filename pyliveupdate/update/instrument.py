import inspect, sys, time
import copy, types, os

from pyliveupdate.update.targetfinder import TargetFinder
from pyliveupdate.update.instrumenter import Instrumenter
from pyliveupdate.update.update import Update
                
class Instrument(Update):
    def __init__(self, target_scope, jointpoint_payload, 
                 update_trigger=None, revert_trigger=None):
        '''
        target_scope: the scope in which the instrumentation will happen, 
                      like a function, a class, or a module
        jointpoint_payload: {jointpoint: payload}, such as {'func_begin': func_begin}
        jointpoint: which code point to apply update, like 'function begin', 'function end'
        payload: a function object whose body will be injected to the jointpoint
        update_trigger: when to trigger the update
        revert_trigger: when to revert the update
        '''
        super(Instrument, self).__init__()
        self.target_scope = target_scope
        self.jointpoint_payload = jointpoint_payload
        self.update_trigger = update_trigger  # ToDo
        self.revert_trigger = revert_trigger  # ToDo
        
        self.targets = TargetFinder.find(target_scope)
    
    def _get_func(self, func_or_method):
        if hasattr(func_or_method, '__func__'):
            return func_or_method.__func__
        elif hasattr(func_or_method, '__code__'):
            return func_or_method
        else:
            return None
        
    def apply(self):
        if self.applied or self.targets == []:
            return False
        
        # instrument code object
        instrumented_targets = {}
        for target in self.targets:
            target = self._get_func(target)
            # only instrument function
            if target and target not in instrumented_targets \
                       and hasattr(target, '__code__'):
                codeobj = target.__code__
                new_codeobj = Instrumenter.instrument(codeobj, 
                                                      self.jointpoint_payload)
                instrumented_targets[target] = new_codeobj
                self.old_codes[target] = codeobj
        
        # TODO: checking the dependency here
        # replace the old code with new code
        for target, new_codeobj in instrumented_targets.items():
            target.__code__ = new_codeobj
            
        self.applied = True
        return True
        
    def revert(self):
        for target, codeobj in self.old_codes.items():
            assert(hasattr(target, '__code__'))
            target.__code__ = codeobj
        self.applied = False
    
    def __repr__(self):
        if self.applied:
            status = 'applied'
        else:
            status = 'not applied'
        
        applied_targets = []
        for t in self.targets:
            applied_targets.append(self._get_name(t))
        applied_targets = sorted(applied_targets)
        return '{{type: instrument, status: {}, scope: {}, \ninstrumented: [{}]}}'\
                .format(status, self.target_scope, 
                        '\n'.join(applied_targets))
