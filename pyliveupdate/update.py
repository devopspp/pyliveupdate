import inspect, sys, time
from bytecode import UNSET, Label, Instr, Bytecode, BasicBlock, ControlFlowGraph
import copy, types, os

def get_builtin_list():
    from stdlib_list import stdlib_list
    import sys, os
    import distutils.sysconfig as sysconfig
    
    builtin_list = stdlib_list()+dir(sys.modules['builtins'])
    
    std_lib_path = sysconfig.get_python_lib(standard_lib=True)
    for fname in os.listdir(std_lib_path):
        if fname[-3:] == '.py':
            fname = fname[:-3]
        builtin_list.append(fname)
    for fname in os.listdir(std_lib_path+'/site-packages'):
        if fname[-3:] == '.py':
            fname = fname[:-3]
        builtin_list.append(fname)
    builtin_list += ['pyliveupdate', 'bytecode']
    return list(set(builtin_list))

class TargetFilter(object):
    builtin_list = get_builtin_list()
    
    @classmethod
    def filter_builtin(cls, name, obj):
        '''check if an obj with name is a builtin type
        or and object of a builtin type
        '''
        name = name.split('.')[0]
        if name == '__main__':
            return False
        if name.startswith('_'):
            return True
        elif inspect.isbuiltin(obj):
            return True
        elif inspect.ismodule(obj):
            return (name in cls.builtin_list)
        elif inspect.isclass(obj) or inspect.ismethod(obj) \
            or inspect.isfunction(obj):
            modname = obj.__module__.split('.')[0]
            if modname == '__main__':
                return False
            else:
                return (name in cls.builtin_list)\
                    or (modname in cls.builtin_list)     
        else:
            typename = type(obj).__qualname__.split('.')[0]
            return typename in cls.builtin_list
        
    @classmethod
    def filter_target(cls, name, obj, target):
        '''check if an obj is in an module under the target directory
        '''
        objmod = obj
        if inspect.isclass(obj) or inspect.ismethod(obj) \
            or inspect.isfunction(obj):
            objmod = sys.modules[obj.__module__]
        elif inspect.ismodule(obj):
            objmod = obj
        else:
            objmod = sys.modules[type(obj).__module__]
        
        ### keep __main__ ###
        if objmod.__name__ == '__main__':
            return True
        ### builtin moduel doesn't have __file__###
        elif hasattr(objmod, '__file__') \
            and os.path.realpath(objmod.__file__).startswith(target):
            return True
        else:
            return False
        

class TargetFinder(object):
    @classmethod
    def _find_target_rec(cls, path, name_candidates, handled_candidates, target_path):
#         print(path)
#         print([n for n, c in name_candidates])
        if len(path) <= 0 or len(name_candidates) <= 0:
            return []
        result = []
        new_candidates = []
        p = path[0]
        path2 = path[1:]
        ### all matched ###
        if p == '*' or p == '**':
            for name, candidate in name_candidates:
                if candidate not in handled_candidates\
                and TargetFilter.filter_target(name, candidate, target_path):
                    handled_candidates.append(candidate)
                    for new_name, new_candidate in inspect.getmembers(candidate):
                        new_candidates.append((new_name, new_candidate))
                    if len(path) == 1:
                        result.append(candidate)
            if p == '**':
                path2 = ['**']
        else:
            for name, candidate in name_candidates:
                if p == name:
                    for new_name, new_candidate in inspect.getmembers(candidate):
                        new_candidates.append((new_name, new_candidate))
                    if len(path) == 1:
                        result.append(candidate)
        result.extend(TargetFinder._find_target_rec(
                      path2, new_candidates, handled_candidates, target_path))
        return result

    @classmethod
    def find(cls, target_name, target_path, bypass_module):
        '''
        find a target object (function, class, etc,) 
        with target_name (such as '__main__.foo') in sys.modules
        '''
        modules = sys.modules
        path = target_name.split('.')
        result = []
        if len(path) <=0:
            return result
        else:
            new_candidates = [(n, m) for n, m in modules.items() if n != bypass_module]
            result.extend(TargetFinder._find_target_rec(path, new_candidates,
                                                        [], target_path))

        return result

class Instrumenter(object):
    @staticmethod
    def _extract_payload(payload_func):
        ### -2 means remove return instr from the payload function
        return Bytecode.from_code(payload_func.__code__)[:-2]
    
    def _set_payload_lineno(payload_bytecode, lineno):
        for bc in payload_bytecode:
            bc.lineno = lineno
        return payload_bytecode
            
    @staticmethod
    def _instrument_func_begin(func_bytecode, payload_bytecode):
        beginpoint = 0
        lineno = func_bytecode[beginpoint].lineno
        payload_bytecode = Instrumenter._set_payload_lineno(payload_bytecode, lineno)
        func_bytecode[beginpoint:beginpoint] = payload_bytecode
        return func_bytecode
    
    @staticmethod
    def find_func_end(func_bytecode):
        endpoints = []
        for i, instr in enumerate(func_bytecode):
            if isinstance(instr, Instr) and instr.name == 'RETURN_VALUE':
                endpoints.append(i)
        return endpoints
    
    @staticmethod
    def _instrument_func_end(func_bytecode, payload_bytecode):
        for endpoint in reversed(Instrumenter.find_func_end(func_bytecode)):
            lineno = func_bytecode[endpoint].lineno
            payload_bytecode = Instrumenter._set_payload_lineno(
                payload_bytecode, lineno)
            func_bytecode[endpoint:endpoint] = payload_bytecode
        return func_bytecode
        
    @staticmethod
    def instrument_function(target, jointpoint_payload):
        func_bytecode = Bytecode.from_code(target.__code__)
        beginpoint = 0
        endpoint = -2
        for jointpoint, payload_func in jointpoint_payload.items():
            payload_bytecode = Instrumenter._extract_payload(payload_func)
            if jointpoint == 'func_begin':
                func_bytecode = Instrumenter._instrument_func_begin(func_bytecode, payload_bytecode)
            elif jointpoint == 'func_end':
                func_bytecode = Instrumenter._instrument_func_end(func_bytecode, payload_bytecode)
            else:
                #ToDo
                pass
        target.__code__ = func_bytecode.to_code()
                
class Update(object):
    '''
    define an update
    '''
    cnt = 0
    def __init__(self, update_type, target_name, jointpoint_payload, 
                 update_trigger = None, revert_trigger=None, bypass_module=None):
        '''
        update_type: instrument or replace
        jointpoint_payload: {jointpoint: payload}, such as {'func_begin': func_begin}
        jointpoint: which code point to apply update, like 'function begin', 'function end'
        payload: a function object whose body will be injected to the jointpoint
        update_trigger: when to trigger the update
        revert_trigger: when to revert the update
        '''
        self.cnt += 1
        self.id = self.cnt
        self.type = update_type
        self.target_name = target_name
        self.jointpoint_payload = jointpoint_payload
        self.update_trigger = update_trigger  ## ToDo
        self.revert_trigger = revert_trigger  ## ToDo
        
        self.targets = TargetFinder.find(target_name, os.getcwd(), bypass_module)
        self.old_codes = {}  ### keep records of the old target code
        self.applied = False ### keep track if the update has been applied or not
#         print(self.targets)
    
    def apply(self):
        if self.applied:
            return False
        else:
            if self.type == 'instrument':
                updated_targets = []
                for target in self.targets:
                    if inspect.isfunction(target) or inspect.ismethod(target):
                        target_func = target
                        if inspect.ismethod(target):
                            target_func = target.__func__
                            
                        if target_func not in updated_targets \
                               and hasattr(target_func, '__code__'):
                            codeobj = target_func.__code__
                            Instrumenter.instrument_function(target_func, 
                                                             self.jointpoint_payload)
                            updated_targets.append(target_func)
                            self.old_codes[target_func] = codeobj
                    else:
                        #ToDo
                        pass 
                else:
                    #ToDo
                    pass
            self.applied = True
            return True
        
    def revert(self):
        for target, codeobj in self.old_codes.items():
            if inspect.isfunction(target) and hasattr(target.__code__, '__code__'):
                target.__code__ = codeobj
            elif inspect.ismethod(target) and hasattr(target.__func__.__code__, '__code__'):
                target.__func__.__code__ = codeobj
        self.applied = False
    
    def __repr__(self):
        return '{}, {}, {}'.format(self.type, self.target_name, self.target)

class UpdateManager(object):
    updates = {}  #{update_id: update}
    
    @classmethod
    def apply_update(cls, update):
        cls.updates[update.id] = update
        update.apply()
        print('Update {} applied'.format(update.id))
        
    @classmethod
    def revert_update(cls, updateid):
        if updateid in cls.updates:
            cls.updates[updateid].revert()
            print('Update {} reverted'.format(updateid))
        else:
            print('Update {} not found'.format(updateid))