from . import console, loadf
from .parser import StekkSyntaxError
import sys

if len(sys.argv) == 1:
    console()
elif len(sys.argv) == 2:
    filename = sys.argv[1]
    try:
        vm = loadf(filename)
    except FileNotFoundError:
        print("File not found:", filename)
    except StekkSyntaxError as e:
        print(e.error)
    else:
        vm.run()
        console(vm)