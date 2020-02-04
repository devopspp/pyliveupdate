# pyupdate
`PyUpdate` is a Python online bugfixing, debugging and profiling tool open sourced by devopspp.

PyUpdate allows developers to profile, troubleshoot and fix production issues for Python applications without restarting the servers.

We are under heavy developing. 

![image](https://github.com/EvonX/pyframe/blob/master/image/ep1.png)

### Key features

* Profile specific (by name) Python functions call time.
* Check the function invocation details such as function parameters, return object, local variables and etc.
* Add logs to specific functions
* Dynamic patching a function

### Quick start

#### Requirements
* [bytecode](https://github.com/vstinner/bytecode)

#### Compatibility
* Supports Python 3.6+ on Linux. 

#### Install

```
pip install pyupdate
```

#### import our library in your main module
```	
from pyupdate import *
// Your python code
```

### Feature Showcase

#### profile function call time

```	
from pyupdate_server import *
updater = Update([func_name],  "call time")
updater.apply_update()
```

#### add logs to a function 

```	
from pyupdate_server import *
log_statement = '"Debug info: ", variable'
updater = Update("add_log", "func_end", [func_name], log_statement)
updater.apply_update()
```

#### create your own payload

```	
from pyupdate_server install *

def func_begin():
    from time import time;
    global start
    start = time()
    print(time())
    
def func_end():
    from time import time;
    global start
    print(time()-start)

updater=Update([func_name], func_begin, func_end)
updater.apply_update()
```


### Known Users
Welcome to register your company name here: https://github.com/EvonX/pyframe/issues/23

### Credit
#### Projects
* [pyrasite](https://github.com/lmacken/pyrasite): Inject code into running Python processes.
