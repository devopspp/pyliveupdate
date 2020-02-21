from pyliveupdate import *
from pyliveupdatescripts import *

class UpdateBase():
    @staticmethod
    def apply(updateid):
        UpdateManager.apply_update(updateid)
    
    @staticmethod
    def revert(updateid):
        UpdateManager.revert_update(updateid)
    
    @staticmethod
    def ls():
        for updateid, update in UpdateManager.updates.items():
            if update.applied:
                print()
                print(updateid, ':', update)
            print()
    
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
                
UpdateBase.register_builtin(globals())