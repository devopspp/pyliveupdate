# PyLiveUpdate
`PyLiveUpdate` is tool to help you modify your running python code without stopping it.
It is useful for modifying long-running server programs in production with zero downtime.
Some modification scenario includes: inject code to profile the runtime of certain lines of code;
inject code to print out a variable for debugging; apply a patch without restarting.

# Install

```
pip install pyliveupdate
```

# How to use
Put these two lines of code in your server program and run it
```
from pyliveupdatescripts import UpdateStub
UpdateStub().start()
```
Start a controller to modify it!
```
> pylu-controller -l 127.0.0.1:50050
```
Some predefined modification available in the controller
```
> FuncProfiler.profile('__main__.**') # inject the time profiling code into all functions in __main__
> LineProfiler.profile('__main__.bar', [11, 12]) # inject time profiling code into certain lines
> FuncDebugger.debug('__main__.bar') # inject code to print out function parameter and return value
> LineDebugger.debug('__main__.bar', [11, 12]) # inject code to print out variables in certain lines
> VarDebugger.debug('__main__.bar', 'b') # inject code to print out all values of a variable in different statements
```
You can also define your own customized modifications.

# Customized modification
There are in general two kinds of modification: instrument and redefine.
You can define them as following and apply with `patch('patch.py')`.

## Instrument code into existing functions
```
from pyliveupdate.update import Instrument, UpdateManager
def _line_after(a):
    print(a)
update = Instrument('__main__.bar', 
                    {('line_after', [12, 14]): _line_after})
UpdateManager.apply_update(update)
```
The code injects a `print(a)` in line 12 and 14 in function `__main__.bar`.
## Redefine (patch) existing functions
```
from pyliveupdate.update import Instrument, UpdateManager
def new_bar(a):
    print('new_bar', a)
update = Redefine('__main__', None, {'__main__.bar':new_bar})
UpdateManager.apply_update(update)
```
The code redefines `__main__.bar` with `new_bar`.

# Revert the modification
PyLiveUpdate also support to revert a modification on the fly:
```
> LU.ls() # list all modification
> LU.revert(1) # revert modifation with id 1
```
