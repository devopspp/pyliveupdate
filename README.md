# pyliveupdate
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
> FuncProfiler.profile('__main__.bar') # inject the time profiling code into a function __main__.bar
> LineProfiler.profile('__main__.bar', [11, 12]) # inject time profiling code into certain lines
> FuncDebugger.debug('__main__.bar') # inject code to print out function parameter and return value
> LineDebugger.debug('__main__.bar', [11, 12]) # inject code to print out variables in certain lines
> VarDebugger.debug('__main__.bar', 'b') # inject code to print out all values of a variable in different statements
```
You can also use wildcard to match many, `*` means one-level nesting, `**` means any level of nesting. 
# Customized modification

## Instrument code into existing functions

## Redefine (patch) existing functions


