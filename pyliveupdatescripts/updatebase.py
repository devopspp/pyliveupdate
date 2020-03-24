from pyliveupdate.update import UpdateManager
from collections.abc import Iterable

class UpdateBase():
    @staticmethod
    def apply(updateid):
        '''
        apply one or a list of update by id
        updateid: int or list of int
        '''
        if not isinstance(updateid, Iterable):
            updateid = [updateid]
        for id_ in updateid:
            UpdateManager.apply_update(id_)
    
    @staticmethod
    def revert(updateid):
        '''
        revert one or a list of update by id
        updateid: int or list of int
        '''
        if not isinstance(updateid, Iterable):
            updateid = [updateid]
        for id_ in updateid:
            UpdateManager.revert_update(id_)
    
    @staticmethod
    def ls():
        for updateid, update in UpdateManager.updates.items():
            if update.applied:
                print()
                print(updateid, ':', update)
    
    @staticmethod
    def register_builtin(vars_):
        '''
        register vars_ to builtin namespace 
        so that the updated target programs can access
        '''
        for item in vars_:
            if __builtins__.get(item) == None and item[:2] != '__':
#                 print('ADD TO BUILTIN:', item)
                __builtins__[item] = vars_[item]

LU = UpdateBase
UpdateBase.register_builtin(globals())