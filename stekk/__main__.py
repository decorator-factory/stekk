from . import console, loadf
import sys

if len(sys.argv) == 1:
    console()
elif len(sys.argv) == 2:
    filename = sys.argv[1]
    try:
        vm = loadf(filename)
    except FileNotFoundError:
        print("File not found:", filename)
    else:
        vm.run()
        console(vm)