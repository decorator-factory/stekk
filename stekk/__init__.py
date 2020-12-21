__all__ = ['loads', 'loadf', 'console']

version = "0.0.1"

import lark
from .vm import VM
from .interactive import console

def loads(string):
    error = False
    statements = vm.parse(string)
    return vm.VM(statements, operations_limit=(10**8))

def loadf(filename):
    with open(filename, 'r') as file:
        source = file.read()
    return loads(source)
