import inspect
from bytecode import UNSET, Label, Instr, Bytecode, BasicBlock, ControlFlowGraph
import copy, types
import sys

class Update(object):
    '''
    define an update
    '''
    def __init__(self, update_id, update_type, target_name, jointpoint, payload, 
                 utrigger = None, rtrigger=None):
        '''
        utype: update type: instrument or replace
        upoint: which code point to apply update, like function begin, function end
        upoint_args: arguments related a upoint
        '''
        self.utype = utype
        self.upoint = upoint
        self.upoint_args = upoint_args
        self.upayload = upayload
        self.utrigger = utrigger
        self.rtrigger = rtrigger
        self.code = {} 

class Updater:
    def __init__(self, targets, updates):
        '''
        targets: objects to update, could be module, functions
        updates: a list of Update instance
        '''
        self.targets = targets
        self.updates = updates
        self.code = {}

    def apply_update(self):
        for target in self.targets:
            if inspect.ismodule(target):
                self.update_module(target, self.code)
            elif inspect.isclass(target):
                self.update_class(target, self.code)
            elif inspect.ismethod(target):
                self.update_method(target, self.code)
            elif inspect.isfunction(target):
                self.update_function(target, self.code)
            else:
                pass #TODO

    def update_module(self, target, code_dict):
        code_dict[target.__name__] = {}
        all_object_list = inspect.getmembers(target)
        func_list = [obj[1] for obj in all_object_list if inspect.isfunction(obj[1])]
        class_list = [obj[1] for obj in all_object_list if inspect.isclass(obj[1])]
        for func in func_list:
            self.update_function(func, code_dict[target.__name__])
        for class_obj in class_list:
            self.update_class(class_obj, code_dict[target.__name__])


    def update_function(self, target, code_dict):
        func_name = target.__name__
        func_bytecode = Bytecode.from_code(target.__code__)
        beginpoint = 0
        endpoint = -2
        for update in self.updates:
            ###-2 means remove return instr from the payload function###
            payload = Bytecode.from_code(update.upayload.__code__)[:-2]
            flag = False
            if update.utype =='instrument':
                if update.upoint == 'func_begin':
                    if update.upoint_args[0] == '*' or func_name in update.upoint_args:
                        for bc in payload:
                            bc.lineno = func_bytecode[beginpoint].lineno
                        func_bytecode[beginpoint:beginpoint] = payload
                        flag = True
                elif update.upoint == 'func_end':
                    if update.upoint_args[0] == '*' or func_name in update.upoint_args:
                        ###need to inject in an reversed order###
                        for endpoint in reversed(Updater.find_func_end(func_bytecode)):
                            for bc in payload:
                                bc.lineno = func_bytecode[endpoint].lineno
                            func_bytecode[endpoint:endpoint] = payload
                        flag = True
                else:
                    pass #TODO
            else:
                pass #TODO
        if flag:
            code_dict[func_name] = target.__code__
        target.__code__ = func_bytecode.to_code()

    def update_method(self, target, code_dict):
        method_name = target.__name__
        code_dict[method_name] = target.__code__
        new_fn = types.FunctionType(target.__code__, target.__globals__, target.__name__, target.__defaults__, target.__closure__)
        new_fn.__dict__ = copy.deepcopy(target.__dict__)
        new_mtd = types.MethodType(new_fn, target.__self__)
        self.update_function(new_fn)
        target.__self__.__setattr__(method_name,  new_mtd)

    def update_class(self, target, code_dict):
        code_dict[target.__name__] = {}
        member_list = inspect.getmembers(target)
        true_list = []
        for item in member_list:
            if hasattr(item[1], '__code__'):
                true_list.append(item[1])
        for item in true_list:
            self.update_function(item, code_dict[target.__name__])
    
    def revert(self):
        self.revert_tool(self.code, sys.modules)

    def revert_tool(self, code_dict, domain):
        for m1 in code_dict:
            item = code_dict[m1]
            key = m1
            target = domain[key]
            if(isinstance(item, dict)):
                target = dict(inspect.getmembers(target))
                self.revert_tool(item, target)
            else:
                target.__code__ = item

    @staticmethod
    def find_func_end(func_bytecode):
        end_l = []
        for i, instr in enumerate(func_bytecode):
            if isinstance(instr, Instr) and instr.name == 'RETURN_VALUE':
                end_l.append(i)
        return end_l
    
'''
# Example

from pyframe import *
def test(a):
    print(a)

def func_begin():
#     pass
    from time import time;
    global start
    start = time()
    print(time())
    
def func_end():
    from time import time;
    global start
    print(time()-start)
    
updater=Updater([test], [Update('instrument', 'func_begin', ['test'], func_begin),
              Update('instrument', 'func_end', ['test'], func_end)])
updater.apply_update()
updater.revert()
test(1)
'''
