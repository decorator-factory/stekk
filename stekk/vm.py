from .parser import Expr, Stmt,\
                    NameExpr, AtExpr, GetitemExpr, RangeExpr,\
                    FcallExpr, CodeBlock, Stack, IfElseExpr,\
                    Const, StmtAssign,\
                    Lvalue, LvalueName, LvalueIndex,\
                    get_value

from .util import withrepr

from .parser import parse

import inspect

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

def builtin_function_repr(original_function):
    def repr_(func):
        spec = inspect.getfullargspec(original_function)
        arg_names = spec.args[1:][::-1]
        args_string = "(" + ", ".join(arg_names[::-1]) + ")"
        stack_diagram = spec.annotations.get("return", "")
        stack_diagram = f" : {stack_diagram}" if stack_diagram else ""
        return f"built-in function {func.name} {args_string}{stack_diagram}"
    return repr_


def vm_onstack(n, addto=vm_builtins, name=None, trustme=True):
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
            args = [vm.stack_pop() for _ in range(n)]
            ret = func(vm, *args)

            if ret:
                for i in ret:
                    vm.stack_push(i)
            elif (not trustme):
                vm.stack_push(none)

        nonlocal name
        if name is None:
            name = func.__name__

        wrapped.name = name

        wrapped = withrepr(builtin_function_repr(func))(wrapped)
        addto[name] = wrapped
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
        if len(self.history) >= 32:
            self.history = self.history[-32:]
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

    ["Containers"]

    @vm_onstack(2)
    def contains(self, item, container):
        return [int(item in container)]

    @vm_onstack(1)
    def rev(self, x):
        return [x[::-1]]

    @vm_onstack(1)
    def len(self, x):
        return [len(x)]

    @vm_onstack(1)
    def sum(self, x):
        return [sum(x)]

    @vm_onstack(2)
    def push(self, x, lst):
        return [lst+[x]]

    @vm_onstack(1)
    def last(self, lst):
        return [lst[-1]]

    ["Stack things"]

    @vm_onstack(1, name="?")
    def drop_if_none(self, a) -> '$N -- ; a -- a':
        return [] if (a == none) else [a]

    @vm_onstack(1)
    def drop(self, a) -> 'a -- ':
        return []

    @vm_onstack(2)
    def swap(self, a, b) -> 'a b -- b a':
        return [a, b]

    @vm_onstack(1)
    def dup(self, a) -> 'a -- a a':
        return [a, a]

    @vm_onstack(2)
    def over(self, b, a) -> 'a b -- a b a':
        return [a, b, a]

    @vm_onstack(3)
    def rot(self, c, b, a) -> 'a b c -- c b a':
        return [c, b, a]

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
        if self.stack:
            return self.stack.pop()
        else:
            return none