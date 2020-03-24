import inspect, sys, time
import copy, types, os
          
class Update(object):
    count_ = 0
    def __init__(self):
        Update.count_ += 1
        self.id = Update.count_
        # keep records of the old target code
        self.old_codes = {}  
        # keep track if the update has been applied or not
        self.applied = False 
    
    def apply(self):
        raise NotImplementedError
        
    def revert(self):
        raise NotImplementedError
    
    def _get_name(self, target):
        tname = ''
        if hasattr(target, '__name__'):
            if hasattr(target, '__qualname__'):
                if hasattr(target, '__module__'):
                    tname = '{}.{}'.format(target.__module__, target.__qualname__)
                else:
                    tname = '{}'.format(target.__qualname__)
            else:
                if hasattr(target, '__module__'):
                    tname = '{}.{}'.format(target.__module__, target.__name__)
                else:
                    tname = '{}'.format(target.__name__)
        else:
            target = type(target)
            if hasattr(target, '__qualname__'):
                if hasattr(target, '__module__'):
                    tname = '{}.{} obj'.format(target.__module__, target.__qualname__)
                else:
                    tname = '{} obj'.format(target.__qualname__)
            else:
                if hasattr(target, '__module__'):
                    tname = '{}.{} obj'.format(target.__module__, target.__name__)
                else:
                    tname = '{} obj'.format(target.__name__)
        return tname
    
    def revert(self):
        for target, codeobj in self.old_codes.items():
            assert(hasattr(target, '__code__'))
            target.__code__ = codeobj
        self.applied = False
        
class UpdateManager(object):
    updates = {}  #{update_id: update}
    
    @classmethod
    def add_update(cls, update):
        cls.updates[update.id] = update
        
    @classmethod
    def rm_update(cls, updateid):
        if updateid in cls.updates:
            del cls.updates[updateid]
    
    @classmethod
    def apply_update(cls, update_or_id):
        updateid = update_or_id
        if isinstance(update_or_id, Update):
            cls.add_update(update_or_id)
            updateid = update_or_id.id
            
        if updateid in cls.updates:
            update = cls.updates[updateid]
            if update.apply():
                print('Update {} applied'.format(updateid))
            else:
                print('Update {} not applied'.format(updateid))
        else:
            print('Update {} not found'.format(updateid))
        
    @classmethod
    def revert_update(cls, updateid):
        if updateid in cls.updates:
            cls.updates[updateid].revert()
            print('Update {} reverted'.format(updateid))
        else:
            print('Update {} not found'.format(updateid))
            