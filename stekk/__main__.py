from . import loadf
from .interactive import console
from .parser import StekkSyntaxError, parse
from .vm import VM
import sys

if len(sys.argv) == 1:
    console()
elif len(sys.argv) > 1:
    filenames = sys.argv[1:]
    vm = VM([])
    for filename in filenames:
        try:
            statements = loadf(filename).statements
            vm.statements.extend(statements)
        except FileNotFoundError:
            print("File not found:", filename)
            exit(1)
        except StekkSyntaxError as e:
            print(e.error)
            exit(2)
    vm.run()
    console(vm)