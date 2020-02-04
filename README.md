# pyliveupdate
`PyLiveUpdate` is a Python runtime monitoring, profiling, debugging and bugfixing tool under development.

PyLiveUpdate allows developers to profile, troubleshoot and fix production issues for Python applications without restarting the programs.

### Key features (under developing)

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
pip install pyliveupdate
```

### How to use
We currently implemented function profiling and are implementing more.
Please feel free to let us know if you find other features useful: https://github.com/devopspp/pyliveupdate/issues/2.

#### profile function call time

1. Start pyliveupdate server
```
pylu-server --logserver
```
2. In your program (like examples/program1.py) main module add 
```	
from pyliveupdate import *
client.UpdateClient().start()
```
3. Run your program (make sure in the correct directory)
```
cd examples
python program1.py
```
4. Start profile one function on the server side
```
instru('__main__.bar')
```
or any functions
```
instru('**')
```
5. Check output in either your program output or `/tmp/instru.log`
6. List applied profiling
```
listinstru
```
7. Stop a profiling by its id without stop your program
```
revert(1)
```


### Known Users
Welcome to register your company name here: https://github.com/devopspp/pyliveupdate/issues/1

### Credit
#### Projects
* [pyrasite](https://github.com/lmacken/pyrasite): Inject code into running Python processes.
