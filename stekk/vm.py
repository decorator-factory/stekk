from .parser import Expr, Stmt,\
                    NameExpr, AtExpr, GetitemExpr, RangeExpr,\
                    FcallExpr, CodeBlock, Stack, IfElseExpr,\
                    Const, StmtAssign,\
                    Lvalue, LvalueName, LvalueIndex,\
                    get_value

from .parser import parse

none = Const.get("N")

vm_builtins = {}

def vm_builtin(func):
    """add a function to VM builtins"""
    vm_builtins[func.__name__] = func
    return func

def vm_builtin_as(name):
    def wrapper(func):
        vm_builtins[name] = func
        return func
    return wrapper

def vm_onstack(n, addto=vm_builtins, name=None):
    """
    @vm_onstack(2)
    def moddiv(self, b, a):
        return [a%b, a//b]

    is equivalent to:

    @vm_builtin
    def moddiv(self):
        b = self.stack_pop()
        a = self.stack_pop()
        self.stack_push(a % b)
        self.stack_push(a // b)
    """
    def wrapper(func):
        def wrapped(vm):
            vm.register_operation()
            args = [vm.stack_pop() if vm.stack else none for _ in range(n)]
            ret = func(vm, *args)

            # If the function doesn't return anything,
            # don't add anything to stack
            if ret:
                for i in ret:
                    vm.stack_push(i)

        addto[name or func.__name__] = wrapped
        return wrapped
    return wrapper


class VM:
    def __init__(self, statements,
                 printer=print, reader=input,
                 operations_limit=1_000_000):
        self.statements = statements
        self.stack = []
        self.names = {**vm_builtins}
        self.printer = printer
        self.reader = reader
        self.operations = 0
        self.operations_limit = operations_limit
        self.history = []
        self.last_result = None

    def register_operation(self):
        self.history.append(self.stack.copy())
        self.operations += 1
        if self.operations > self.operations_limit:
            raise Exception("Too many operations")

    @vm_onstack(2, name="or")
    def _or(self, b, a): return [int(a or b)]

    @vm_onstack(2, name="and")
    def _and(self, b, a): return [int(a and b)]

    @vm_onstack(1)
    def parse_int(self, x):
        try:
            return [int(x)]
        except ValueError:
            return [none]

    @vm_onstack(2, name="+")
    def add(self, b, a): return [a + b]

    @vm_onstack(2, name="-")
    def sub(self, b, a): return [a - b]

    @vm_onstack(2, name="*")
    def mul(self, b, a): return [a * b]

    @vm_onstack(2, name="/f")
    def fdiv(self, b, a): return [a / b]

    @vm_onstack(2, name="/i")
    def idiv(self, b, a): return [a // b]

    @vm_onstack(1)
    def copy(self, a): return [a, a]

    @vm_onstack(2, name="=")
    def eq(self, b, a): return [int(a == b)]

    @vm_onstack(2, name="!=")
    def neq(self, b, a): return [int(a != b)]

    @vm_onstack(2, name="<")
    def lt(self, b, a): return [int(a < b)]

    @vm_onstack(2, name=">")
    def gt(self, b, a): return [int(a > b)]

    @vm_onstack(2, name="<=")
    def le(self, b, a): return [int(a <= b)]

    @vm_onstack(2, name=">=")
    def ge(self, b, a): return [int(a >= b)]

    @vm_onstack(1)
    def bloat(self, lst):
        # opposite of grab
        return [none, *lst]

    @vm_builtin
    def grab(self):
        # $N 1 2 3 4 -> [4 3 2 1]
        grabbed = []
        while True:
            x = self.stack_pop()
            if x == none:
                self.stack_push(grabbed)
                break
            else:
                grabbed.append(x)

    @vm_onstack(1)
    def rev(self, x):
        return [x[::-1]]

    @vm_onstack(1)
    def len(self, x):
        return [len(x)]

    @vm_onstack(1)
    def sum(self, x):
        return [sum(x)]

    @vm_onstack(2, name="+=")
    def push(self, x, lst):
        return [lst+[x]];

    @vm_onstack(1)
    def last(self, lst):
        return [lst[-1]];

    @vm_onstack(2)
    def str_join(self, string, lst):
        return [string.join(map(str, lst))]

    ["Strings"]

    @vm_onstack(1, name="ord")
    def ord_(self, string):
        return [ord(c) for c in string]

    @vm_onstack(1, name="chr")
    def chr_(self, n):
        return [chr(n)]

    ["I/O"]

    @vm_onstack(0)
    def read(self):
        return [self.reader()]

    @vm_onstack(1)
    def print(self, a):
        self.printer(a, end='')

    @vm_onstack(1)
    def println(self, a):
        self.printer(a, end='\n')


    ["Stack things"]

    @vm_onstack(2)
    def contains(self, item, container):
        return [int(item in container)]

    @vm_onstack(1, name="!")
    def rem(self, a):
        return []

    @vm_onstack(2)
    def swap(self, a, b):
        # (1 2 3 .swap) -> (1 3 2)
        return [a, b]

    @vm_onstack(0)
    def __stack(self):
        return [self.stack]

    @vm_onstack(1)
    def as_src(self, code):
        return [code.str_rec()]

    @vm_onstack(2, name="++")
    def codecat(self, code_b: CodeBlock, code_a: CodeBlock):
        return [CodeBlock(code_a.stmts + code_b.stmts)]

    @vm_onstack(1, name="--")
    def codesplit(self, code: CodeBlock):
        return [[CodeBlock([stmt]) for stmt in code.stmts]]

    @vm_onstack(2)
    def set_default(self, value, name):
        if name not in self.names:
            self.names[name] = value

    ["Functional stuff"]

    @vm_onstack(2)
    def foreach(self, function, iterable):
        for item in iterable:
            self.stack_push(item)
            self.function_call(function)


    ["region stuff"]

    def points_from_region(self, region):
        def process(v, lst):
            if isinstance(v, int):
                # (1, 2) -> [(1, 2)]
                lst.append(v)
            elif isinstance(v, RangeExpr):
                # (1..3, 2) -> [(1, 2), (2, 2), (3, 2)]
                left = v.left
                right = v.right
                if left > right:
                    left, right = right, left
                right += 1

                for i in range(left, right):
                    lst.append(i)
            elif isinstance(v, list):
                lst.extend(v)

        for x, y in region:
            xs = []
            ys = []
            process(x, xs)
            process(y, ys)
            for px in xs:
                for py in ys:
                    yield (px, py)

    def at_to_list(self, at_expr):
        return list(self.points_from_region(at_expr))


    def function_call(self, func):
        self.register_operation()
        func = get_value(func, self)
        if isinstance(func, CodeBlock):
            return func.run(self)
        else:
            return func(self)

    def run(self):
        self.execute_statements(self.statements)
        
    def execute_statements(self, statements):
        for stmt in statements:
            self.register_operation()
            if isinstance(stmt, (Expr, Stmt)):
                self.last_result = stmt.run(self)
            else:
                self.last_result = stmt
            

    def assign_name(self, name, value):
        self.register_operation()
        self.names[name] = value

    def setitem(self, obj, index, value):
        self.register_operation()
        obj[index] = value

    def getitem(self, obj, index):
        if isinstance(obj, (list, tuple)) and isinstance(index, tuple):
            return obj[slice(*index)]
        else:
            return obj[index]

    def get_name(self, name):
        self.register_operation()
        return self.names[name]

    def stack_push(self, x):
        self.register_operation()
        self.stack.append(x)

    def stack_pop(self):
        self.register_operation()
        return self.stack.pop()