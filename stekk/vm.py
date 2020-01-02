from .parser import Expr, Stmt,\
                    NameExpr, AtExpr, GetitemExpr, RangeExpr,\
                    FcallExpr, CodeBlock, Stack, IfElseExpr,\
                    Const, StmtAssign,\
                    Lvalue, LvalueName, LvalueIndex,\
                    get_value

from .util import withrepr

from .parser import parse

import inspect

import os

none = Const.get("N")
error = Const.get("E")
type_error = Const.get("T")
ok = Const.get("OK")

def ensure_types(*value_types):
    for (value, type_) in value_types:
        if not isinstance(value, type_):
            return type_error
    return ok

def ensure_numbers(*values):
    return ensure_types(*((value, (int, float)) for value in values))

vm_builtins = {}

def vm_builtin(func):
    """add a function to VM builtins"""
    return vm_builtin_as(func.__name__)(func)

def vm_builtin_as(name):
    def wrapper(func):
        func.name = name
        new_func = withrepr(builtin_function_repr(func))(func)
        new_func.help = func.__doc__ or ""
        vm_builtins[name] = new_func
        return new_func
    return wrapper

def builtin_function_repr(original_function):
    def repr_(func):
        spec = inspect.getfullargspec(original_function)
        arg_names = spec.args[1:]
        args_string = "(" + ", ".join(arg_names) + ")"
        return f"built-in function {func.name} {args_string}"
    return repr_


def vm_onstack(n, name=None, trustme=True):
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
            args = reversed([vm.stack_pop() for _ in range(n)])
            try:
                ret = func(vm, *args)
            except TypeError as e:
                print(e)
                vm.stack_push(type_error)
                return
            except AttributeError:
                vm.stack_push(type_error)
                return

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
        wrapped.help = func.__doc__ or ""
        vm_builtins[name] = wrapped
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
    def _or(self, a, b):
        return [int(a or b)]

    @vm_onstack(2, name="and")
    def _and(self, a, b):
        return [int(a and b)]

    @vm_onstack(1, name="not")
    def _not(self, x):
        return [int(not x)]

    @vm_onstack(1)
    def parse_int(self, source):
        T = ensure_types((source, (str, float, int)))
        if not T:
            return [T]

        try:
            return [int(source)]
        except ValueError:
            return [error]

    @vm_onstack(2, name="+")
    def add(self, a, b):
        return [ensure_numbers(a, b) and a + b]

    @vm_onstack(2, name="-")
    def sub(self, a, b):
        return [ensure_numbers(a, b) and a - b]

    @vm_onstack(2, name="*")
    def mul(self, a, b):
        return [a * b]

    @vm_onstack(2, name="/f")
    def fdiv(self, a, b):
        return [a / b]

    @vm_onstack(2, name="/i")
    def idiv(self, a, b):
        return [a // b]

    @vm_onstack(2, name="=")
    def eq(self, a, b):
        return [int(a == b)]

    @vm_onstack(2, name="!=")
    def neq(self, a, b):
        return [int(a != b)]

    @vm_onstack(2, name="<")
    def lt(self, a, b):
        return [int(a < b)]

    @vm_onstack(2, name=">")
    def gt(self, a, b):
        return [int(a > b)]

    @vm_onstack(2, name="<=")
    def le(self, a, b):
        return [int(a <= b)]

    @vm_onstack(2, name=">=")
    def ge(self, a, b):
        return [int(a >= b)]

    @vm_onstack(1)
    def bloat(self, container) -> '[a, ..., b, c] -- $N c b ... a':
        return [none, *reversed(container)]

    @vm_builtin
    def grab(self) -> '$N a b c... -- [..., c, b, a]':
        grabbed = []
        while True:
            x = self.stack_pop()
            if x == none:
                self.stack_push(grabbed)
                break
            else:
                grabbed.append(x)

    @vm_onstack(2)
    def str_join(self, string, list_):
        return [string.join(map(str, list_))]

    ["Strings"]

    @vm_onstack(1, name="ord")
    def ord_(self, string):
        return [ord(c) for c in string]

    @vm_onstack(1, name="chr")
    def chr_(self, code):
        return [chr(code)]

    ["I/O"]

    @vm_onstack(0)
    def read(self):
        return [self.reader()]

    @vm_onstack(1)
    def print(self, x):
        self.printer(x, end='')

    @vm_onstack(1)
    def println(self, x):
        self.printer(x, end='\n')

    ["Containers"]

    @vm_onstack(2)
    def contains(self, container, item):
        return [int(item in container)]

    @vm_onstack(1)
    def rev(self, container):
        """[a, b, ..., c, d] -- [d, c, ..., b, a]"""
        return [container[::-1]]

    @vm_onstack(1, name="len")
    def len_(self, container):
        return [len(container)]

    @vm_onstack(1, name="sum")
    def sum_(self, container):
        return [sum(container)]

    @vm_onstack(2)
    def push(self, x, list_):
        """[..., a] b -- [..., a, b]"""
        return [list_ + [x]]

    @vm_onstack(1)
    def last(self, container):
        """[..., a] -- a"""
        return [container[-1]]

    ["Stack things"]

    @vm_onstack(1, name="?")
    def drop_if_none(self, a):
        """$N -- ; a -- a"""
        return [] if (a == none) else [a]

    @vm_onstack(1)
    def drop(self, a):
        """a -- """
        return []

    @vm_onstack(2)
    def swap(self, a, b):
        """a b -- b a"""
        return [b, a]

    @vm_onstack(1)
    def dup(self, a):
        """a -- a a"""
        return [a, a]

    @vm_onstack(2)
    def over(self, a, b):
        """a b -- a b a"""
        return [a, b, a]

    @vm_onstack(3)
    def rot(self, a, b, c):
        """a b c -- c b a"""
        return [c, b, a]

    @vm_onstack(0)
    def __stack(self):
        return [self.stack]

    @vm_onstack(1)
    def as_src(self, code):
        """convert code block to stekk source"""
        return [code.str_rec()]

    @vm_onstack(2, name="++")
    def concat(self, left, right):
        """create a new container by gluing two containers together"""
        if isinstance(left, CodeBlock):
            return [ensure_types(
                        (left, CodeBlock),
                        (right, CodeBlock)
                    ) and CodeBlock(left.stmts + right.stmts)]
        else:
            return [ensure_types(
                        (left, (str, list))
                    ) and left + right]

    @vm_onstack(1, name="--")
    def codesplit(self, code: CodeBlock):
        """convert a code block into a list of one-statement code blocks"""
        return [[CodeBlock([stmt]) for stmt in code.stmts]]

    ["Functional stuff"]

    @vm_onstack(1, name="help")
    def help_(self, function):
        return [function.help]

    @vm_onstack(2, name="set_help")
    def set_help(self, code_block, string):
        if not isinstance(code_block, CodeBlock):
            raise TypeError
        code_block.help = string
        return [code_block]

    @vm_onstack(2)
    def foreach(self, iterable, function):
        for item in iterable:
            self.stack_push(item)
            self.function_call(function)

    ["Metaprogramming"]

    @vm_onstack(1, name="eval")
    def eval_(self, value):
        """compute an expression object"""
        return [get_value(value, self)]

    @vm_onstack(1, name="import")
    def import_(self, module_name):
        with open(module_name + ".stekk") as file:
            source = file.read()
        statements = parse(source)
        _, stripped_name = os.path.split(module_name)
        self.names[stripped_name] = CodeBlock(statements)
        return [self.names[stripped_name]]


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
        if isinstance(obj, CodeBlock):
            if isinstance(index, int):
                return get_value(obj.stmts[index], self)
            elif isinstance(index, Const):
                for stmt in reversed(obj.stmts):
                    if (isinstance(stmt, StmtAssign)
                        and isinstance(stmt.lvalue, LvalueName)
                        and stmt.lvalue.name == index.name):
                       return get_value(stmt.expr, self)
                return none
            else:
                return type_error
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