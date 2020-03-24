import inspect, sys, time
from bytecode import UNSET, Label, Instr, Bytecode, BasicBlock, ControlFlowGraph
import copy, types, os
import pathlib
import logging, collections

logger = logging.getLogger(__name__)

class TargetFilter(object):
    @classmethod
    def filter_target(cls, name, obj, target):
        '''
        check if an obj is in an module under the target directory
        '''
#         if inspect.ismethod(obj) \
#             or inspect.isfunction(obj):
#             return True
       
        objmod = obj
        if inspect.isclass(obj) or inspect.ismethod(obj) \
            or inspect.isfunction(obj):
            
            if obj.__module__ in sys.modules:
                objmod = sys.modules[obj.__module__]
        elif inspect.ismodule(obj):
            objmod = obj
        else:
            objmod = sys.modules[type(obj).__module__]
        
        # keep __main__ 
        if objmod.__name__ == '__main__':
            return True
        # builtin moduel doesn't have __file__
        elif hasattr(objmod, '__file__') and objmod.__file__\
            and os.path.realpath(objmod.__file__).startswith(target):
            return True
        else:
            return False
        

class TargetFinder(object):
    @classmethod
    def _getmodulename(cls, obj):
        if inspect.ismodule(obj):
            return obj.__name__
        elif hasattr(obj, '__module__'):
            return obj.__module__
        else:
            return type(obj).__module__
        
    @classmethod
    def _getmembers(cls, obj, objname):
        members = []
        try:
            members = inspect.getmembers(obj)
        except:
            for name in dir(obj):
                try:
                    m = getattr(obj, name)
                    if inspect.ismodule(obj) \
                        and cls._getmodulename(m) == objname:    
                            members.append((name, m))
                    else:
                        members.append((name, m))
                except Exception as e:
                    logger.error(e)
        return members
                    
    @classmethod
    def _find_target_rec(cls, target_path, target_fpath, 
                         name_candidates, handled_candidates):
        result = set()
        new_candidates = []
        if len(target_path) <= 0 or len(name_candidates) <= 0:
            return result
        
        p = target_path[0]
        new_target_path = target_path[1:]
        
        # all matched
        if p == '*' or p == '**':
            for name, candidate in name_candidates:
                if id(candidate) not in handled_candidates\
                    and TargetFilter.filter_target(name, candidate, target_fpath):
                    handled_candidates.add(id(candidate))
                    if not inspect.ismethod(candidate) and not inspect.isfunction(candidate):
                        for new_name, new_candidate in cls._getmembers(candidate, name):
                            new_candidates.append((new_name, new_candidate))
                        
                    if len(target_path) == 1 and isinstance(candidate, collections.Hashable):
                        try:    
                            result.add(candidate)
                        except:
                            pass
            if p == '**':
                new_target_path = ['**']
        else:
            for name, candidate in name_candidates:
                if p == name:
                    if not inspect.ismethod(candidate) and not inspect.isfunction(candidate):
                        for new_name, new_candidate in cls._getmembers(candidate, name):
                            new_candidates.append((new_name, new_candidate))
                    if len(target_path) == 1 and isinstance(candidate, collections.Hashable):
                        try:
                            result.add(candidate)
                        except:
                            pass
        result.update(
            TargetFinder._find_target_rec(
                new_target_path, target_fpath, new_candidates, handled_candidates))
        return result
    
    @classmethod
    def _get_module_path(cls, module):
        try:
            path = pathlib.Path(module.__file__).absolute()
            if str(path).endswith('__init__.py'):
                return str(path.parent)
            else:
                return str(path)
        except:
            return '__path_not_found__'
        
    @classmethod
    def _extract_module_from_name(cls, name):
        '''
        given a name like 'package1.module1.func1'
        extract object which package1.module1 refers to
        '''
        modules = sys.modules
        path = name.split('.')
        if path[0] in ['**', '*']:
            return sys.modules['__main__']
        elif path[0] in sys.modules:
            candidate = sys.modules[path[0]]
            for p in path[1:]:
                if p in dir(candidate):
                    next_candidate = getattr(candidate, p)
                    
                    # make sure next candidate is a module
                    # and it is the submodule of candidate
                    # instead is imported in candidate
                    if inspect.ismodule(next_candidate) \
                        and next_candidate.__name__.startswith(candidate.__name__):
                        candidate = next_candidate
                    else:
                        break
                else:
                    break
            return candidate
        else:
            logger.error('Cannot find target name: {}'.format(name))
            return None
    
    @classmethod
    def _split_module_object(cls, target_name):
        '''
        split the target_name into module part 
        and object part
        '''
        path = target_name.split('.')
        target_module = cls._extract_module_from_name(target_name)
        
        target_module_path = target_module.__name__.split('.')
        assert(len(path)>=len(target_module_path))
        
        i = 0
        for i, p in enumerate(target_module_path):
            if p != path[i]:
                break
        
        if p == path[i]:
            i = i + 1
        path = path[i:]
        return target_module, path
        
    @classmethod
    def find(cls, target_name):
        '''
        find a target object (function, class, etc,) 
        with target_name (such as '__main__.foo') in sys.modules
        '''
        modules = sys.modules
        path = target_name.split('.')
        result = set()
        
        if len(path) <= 0:
            return list(result)
        
        target_modules = []
        if path[0] in ['**', '*']:
            target_filepath = os.getcwd()
            
            for n, m in sys.modules.items():
                if TargetFilter.filter_target(n, m, target_filepath):
                    target_modules.append(m)
                if path[0] == '**':
                    path = ['**']
                else:
                    path = []
        else:
            target_module, path = cls._split_module_object(target_name)
            if not target_module:
                return list(result)

            if path == []:
                result.add(target_module)
                return list(result)

            target_filepath = cls._get_module_path(target_module)
            target_modules = [target_module]
        
        for target_module in target_modules:
            name_candidates = cls._getmembers(target_module, target_module.__name__)
            result.update(TargetFinder._find_target_rec(path, target_filepath, name_candidates, set()))
        return list(result)
    
    