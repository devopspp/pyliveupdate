from pyliveupdate.update import Redefine, UpdateManager
from module2 import double

def predefine():
    from module2 import double

def new_foo(a):
    print('new foo', double(a))
    
update = Redefine('module1', predefine, {'module1.foo':new_foo})
UpdateManager.apply_update(update)