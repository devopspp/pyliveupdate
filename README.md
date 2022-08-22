# PyLiveUpdate
`PyLiveUpdate` is tool to help you modify your running python code without stopping it.
It is useful for modifying long-running server programs in production with zero downtime.
Some modification scenario includes: inject code to profile the runtime of certain lines of code;
inject code to print out a variable for debugging; apply a patch without restarting.

## Install

```
pip install pyliveupdate
```

## How to use
Put these two lines of code in your server program and run it. Try it out with `example/program1.py`. 
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
> FuncProfiler.profile(['__main__.**', 'module1.**']) # inject execution time profiling code into all functions in __main__ and module1
> LineProfiler.profile('__main__.bar', [11, 12]) # inject time profiling code into certain lines
> FuncDebugger.debug('__main__.bar') # inject code to print out function parameter and return value
> LineDebugger.debug('__main__.bar', [11, 12]) # inject code to print out variables in certain lines
> VarDebugger.debug('__main__.bar', 'b') # inject code to print out all values of a variable in different statements
```

These will print out corresponding profiling and debugging info in the program terminal and in `/tmp/pyliveupdate`.
You can also define your own customized modifications.

## Customized modification
There are in general two kinds of modification: instrument and redefine.
You can define them as following and apply with `patch('patch.py')`. Try it out with `example/patch.py`.

#### Instrument code into existing functions
```
from pyliveupdate.update import Instrument, UpdateManager

def _line_after(a):
    print(a)
    
update = Instrument('__main__.bar', 
                    {('line_after', [12, 14]): _line_after})
UpdateManager.apply_update(update)
```
The code injects a `print(a)` in line 12 and 14 in function `__main__.bar`.
#### Redefine (patch) existing functions
```
from pyliveupdate.update import Redefine, UpdateManager

def new_bar(a):
    print('new_bar', a)
    
update = Redefine('__main__', None, {'__main__.bar':new_bar})
UpdateManager.apply_update(update)
```
The code redefines `__main__.bar` with `new_bar`.

## Revert the modification
PyLiveUpdate also support to revert a modification on the fly:
```
> LU.ls() # list all modification
> LU.revert(1) # revert modifation with id 1
```
## Extended tools
PyLiveUpdate also comes with some handy tools based on it:

### Profiler
Dynamically choose functions or lines to profile and show the result with a flamegraph.
1. Start your program with PyLiveUpdate enabled, like `example/patch.py`.
2. Start a controller `pylu-controller -l 127.0.0.1:50050`
3. Start profiling functions with `FP.profile(['__main__.**', 'module1.**'])` or lines with `LineProfiler.profile('__main__.bar', [11, 12])`.
4. Process the logs with `pylu-processlogs -i /tmp/pyliveupdate.log` in another terminal
It will generated a flamegraph and a summary:

#### Flamegraph
![alt text](examples/pyliveupdate.log.svg)

#### Function call summary
The following summary gives in process `4510` thread `5`, `views.results` was called `10` times and each time takes `139 ms`, `views.results` called `manager.all` for `20` times.
```
4510-Thread-5
function  hit  time/hit (ms)
views.results 10  138.562
  -manager.all 20  14.212
    -__init__.__hash__ 10  0.035
    -manager.get_queryset 20  0.922
      -query.__init__ 20  0.616
        -query.__init__ 20  0.071
```

## Citation
Please kindly cite our work as follows if you want to refer to it in any writing:

```
@inproceedings{huang2021pylive,
  title={$\{$PYLIVE$\}$:$\{$On-the-Fly$\}$ Code Change for Python-based Online Services},
  author={Huang, Haochen and Xiang, Chengcheng and Zhong, Li and Zhou, Yuanyuan},
  booktitle={2021 USENIX Annual Technical Conference (USENIX ATC 21)},
  pages={349--363},
  year={2021}
}
```
