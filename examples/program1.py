import os, sys, time

## add these two lines to your own code
#from pyliveupdate import *
from pyliveupdatescripts import UpdateStub
UpdateStub().start()

from module1 import *

def bar(a):
    foo(a)
    b = a
    print('bar1', a)
    print('bar2', a)
    print('bar3', a)

class Foo:
    def print_object(self, a):
        print('Foo.print_object ', a)
        
    @classmethod
    def print_class(cls, a):
        print('Foo.print_clss ', a)
    
    @staticmethod
    def print_static(a):
        print('Foo.print_static ', a)

def main():
    print(time.time())
    time.sleep(1)
    foo(1)
    bar(2)
    Foo().print_object(3)
    Foo.print_class(4)
    Foo.print_static(5)
    
if __name__ == '__main__':
    while True:
        main()
