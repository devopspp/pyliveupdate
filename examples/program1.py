import os, sys, time

## add these two lines to your own code
from pyliveupdate import *
client.UpdateClient().start()

from module1 import foo

def bar(a):
    print('bar', a)

class Foo:
    def print_object(self, a):
        print('Foo.print_object ', a)
        
    @classmethod
    def print_class(cls, a):
        print('Foo.print_clss ', a)
    
    @staticmethod
    def print_static(a):
        print('Foo.print_static ', a)

    
if __name__ == '__main__':
    while True:
        time.sleep(1)
        foo(1)
        bar(2)
        Foo().print_object(3)
        Foo.print_class(4)
        Foo.print_static(5)