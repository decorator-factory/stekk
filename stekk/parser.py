import json
import os
from lark import Lark, Transformer, v_args, UnexpectedInput

def joinr(s, x):
    return s.join(map(repr, x))

def joins(s, x):
    return s.join(map(str, x))

def str_rec(x, depth=0, indent="    "):
    try:
        return x.str_rec(depth, indent)
    except AttributeError:
        return depth * indent + repr(x)

class Stmt:
    def run(self, vm):
        raise NotImplementedError

    def __getitem__(self, index):
        if isinstance(index, Const):
            if hasattr(self, index.name):
                return getattr(self, index.name)
            else:
                return Const.get("N")
        else:
            raise TypeError(index)

    @property
    def dir(self):
        return dir(self)

    def str_rec(self, depth=0, indent="    "):
        return indent * depth + repr(self)


class Expr(Stmt):
    def get_value(self, vm):
        raise NotImplementedError

    def run(self, vm):
        return self.get_value(vm)


def get_value(x, vm):
    if isinstance(x, Expr):
        return x.get_value(vm)
    else:
        return x

["Expression"]

class ListExpr(Expr):
    def __init__(self, exprs):
        self.exprs = exprs

    def get_value(self, vm):
        return [get_value(x, vm) for x in self.exprs]

    __repr__ = lambda self: f"List{self.exprs}"

    def str_rec(self, depth=0, indent="    "):
        prefix = indent * depth
        output = prefix + "[\n"
        for expr in self.exprs:
            output += str_rec(expr, depth + 1, indent) + ",\n"
        output += prefix + "]"
        output = output.replace(",\n"+prefix+")", prefix+")")
        return output


class TupleExpr(Expr):
    def __init__(self, exprs):
        self.exprs = exprs

    def get_value(self, vm):
        return tuple((get_value(x, vm) for x in self.exprs))

    __repr__ = lambda self: f"Tuple{self.exprs}"

    def str_rec(self, depth=0, indent="    "):
        prefix = indent * depth
        output = prefix + "(\n"
        for expr in self.exprs:
            output += str_rec(expr, depth + 1, indent) + ",\n"
        output += prefix + ")"
        output = output.replace(",\n"+prefix+")", prefix+")")
        return output


class NameExpr(Expr):
    def __init__(self, name):
        self.name = name

    def get_value(self, vm):
        return vm.get_name(self.name)

    __repr__ = lambda self: f"Name[{self.name}]"

    def str_rec(self, depth=0, indent="    "):
        prefix = indent * depth
        return prefix + self.name


class FcallExpr(Expr):
    def __init__(self, func):
        self.func = func

    def get_value(self, vm):
        return vm.function_call(get_value(self.func, vm))

    __repr__ = lambda self: f"fcall({self.func})"

    def str_rec(self, depth=0, indent="    "):
        prefix = indent * depth
        return prefix + "." +str_rec(self.func, depth, indent)[len(prefix):]


class CodeBlock(Expr):
    def __init__(self, stmts):
        self.stmts = stmts

    def get_value(self, vm):
        return self

    def __getitem__(self, i):
        return self.stmts[i]

    def __bool__(self):
        return bool(self.stmts)

    def run(self, vm):
        for stmt in self.stmts:
            stmt.run(vm)

    __repr__ = lambda self: "{" + joinr('; ', self.stmts) + "}"

    def str_rec(self, depth=0, indent="    "):
        prefix = indent * depth
        output = prefix + "{\n"
        for stmt in self.stmts:
            output += str_rec(stmt, depth+1, indent) + ";\n"
        output += prefix + "}"
        return output


class Stack(Expr):
    def __init__(self, exprs):
        self.exprs = exprs

    def get_value(self, vm):
        for expr in self.exprs:
            value = get_value(expr, vm)
            if value is not None:
                vm.stack_push(value)
        if vm.stack:
            return vm.stack.pop()
        else:
            return Const.get("N")

    __repr__ = lambda self: f"Stack({joinr(' ', self.exprs)})"

    def str_rec(self, depth=0, indent="    "):
        prefix = indent * depth
        output = prefix + "(\n"
        for expr in self.exprs:
            output +=str_rec(expr, depth+1, indent) + "\n"
        output += prefix + ")"
        return output


class IfElseExpr(Expr):
    def __init__(self, condition, branch_then, branch_else):
        self.condition = condition
        self.branch_then = branch_then
        self.branch_else = branch_else

    def get_value(self, vm):
        #print("call if", repr(self))
        cond_value = bool(get_value(self.condition, vm))
        if cond_value:
            return get_value(self.branch_then, vm)
        else:
            return get_value(self.branch_else, vm)


    __repr__ = lambda self: "If({0.condition})=>({0.branch_then})/({0.branch_else})".format(self)

    def str_rec(self, depth=0, indent="    "):
        prefix = depth * indent
        cond =str_rec(self.condition, depth, indent)[len(prefix):]
        then =str_rec(self.branch_then, depth+1, indent)
        elze =str_rec(self.branch_else, depth+1, indent)
        return prefix + cond + " => \n" + then + "\n" + prefix + "else\n" + elze

class WhileExpr(Expr):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

    def get_value(self, vm):
        ret = Const.get("N")
        while get_value(self.condition, vm) == 1:
            ret = get_value(self.body, vm)
        return ret

    __repr__ = lambda self: "While({0.condition})=>({0.body})".format(self)

    def str_rec(self, depth=0, indent="    "):
        prefix = depth * indent
        cond = str_rec(self.condition, depth, indent)[len(prefix):]
        bod = str_rec(self.body, depth + 1, indent)
        return prefix + "while " + cond + " => \n" + bod

["Constants"]

class Const(Expr):
    const = {}
    def __init__(self, name, desc=""):
        if isinstance(name, NameExpr):
            self.name = name.name
        else:
            self.name = name

        assert isinstance(self.name, str)

        Const.const[self.name] = self
        self.description = desc

    __repr__ = lambda self: "$" + self.name

    @staticmethod
    def get(name, desc=""):
        if name in Const.const:
            return Const.const[name]
        else:
            return Const(name, desc=desc)

    def get_value(self, vm):
        return self

    def __eq__(self, other):
        if not isinstance(other, Const):
            return False
        else:
            return other.name == self.name

Const("N", "null")


["Assignment"]

class Lvalue:
    def assign(self, vm, value):
        raise NotImplementedError

    def str_rec(self, depth=0, indent="    "):
        prefix = depth * indent
        return prefix + repr(self)

class LvalueName(Lvalue):
    def __init__(self, name):
        self.name = name.name

    def assign(self, vm, value):
        vm.assign_name(self.name, value)

    __repr__ = lambda self: f"LvalueName({self.name})"

    def str_rec(self, depth=0, indent="    "):
        prefix = depth * indent
        return prefix + self.name


class StmtAssign(Stmt):
    def __init__(self, lvalue: Lvalue, expr: Expr):
        self.lvalue = lvalue
        self.expr = expr

    def run(self, vm):
        value = get_value(self.expr, vm)
        if value is None:
            raise ValueError(f"value of {self.expr} in {self} is None")
        self.lvalue.assign(vm, value)

    __repr__ = lambda self: f"Assign({self.lvalue})=({self.expr})"

    def str_rec(self, depth=0, indent="    "):
        prefix = indent * depth
        return prefix +str_rec(self.lvalue, depth, indent)[len(prefix):]\
               + " = " +str_rec(self.expr, depth, indent)[len(prefix):]

["Items"]

class LvalueIndex(Lvalue):
    def __init__(self, subexpr, index):
        self.index = index
        self.subexpr = subexpr

    def assign(self, vm, value):
        vm.setitem(get_value(self.subexpr, vm),
                   get_value(self.index, vm),
                   value)

    __repr__ = lambda self: f"LvalueIndex({self.subexpr})[{self.index}]"

    def str_rec(self, depth=0, indent="    "):
        prefix = depth * indent
        return prefix + str_rec(self.subexpr, depth, indent)[len(prefix):] \
               + "[" + str_rec(self.index, depth, indent)[len(prefix):] + "]"


class GetitemExpr(Expr):
    def __init__(self, subexpr, index):
        self.index = index
        self.subexpr = subexpr

    def get_value(self, vm):
        return vm.getitem(get_value(self.subexpr, vm),
                          get_value(self.index, vm))

    __repr__ = lambda self: f"Getitem({self.subexpr})[{self.index}]"

    def str_rec(self, depth=0, indent="    "):
        prefix = depth * indent
        return prefix + str_rec(self.subexpr, depth, indent)[len(prefix):] \
               + "<" + str_rec(self.index, depth, indent)[len(prefix):] + ">"


class AtExpr(Expr):
    def __init__(self, expr):
        self.expr = expr

    def get_value(self, vm):
        return vm.at_to_list(get_value(self.expr, vm))

    __repr__ = lambda self: f"@({self.expr})"

    def str_rec(self, depth=0, indent="    "):
        prefix = indent * depth
        return prefix + "@" +str_rec(self.expr, depth, indent)[len(prefix):]


class RangeExpr(Expr):
    def __init__(self, left_expr, right_expr):
        self.left_expr = left_expr
        self.right_expr = right_expr
        self.left = None
        self.right = None

    def get_value(self, vm):
        self.left = get_value(self.left_expr, vm)
        self.right = get_value(self.right_expr, vm)
        return self

    def __contains__(self, item):
        return (item in range(self.left, self.right+1))

    def __iter__(self):
        left = self.left
        right = self.right
        while left <= right:
            yield left
            left += 1

    __repr__ = lambda self: f"Range[{self.left}..{self.right}]"



["Transformation"]

def trav(x, *indices):
    for i in indices:
        x = x.children[i]
    return x

ID = lambda _: _

STAR = lambda f: lambda self, *args: f(args)

@v_args(inline=True)
class Tranny(Transformer):
    def lvalue_name(self, name):
        return LvalueName(name)

    def lvalue_index(self, expr, index):
        return LvalueIndex(expr, index)

    ["Statements"]

    def stmt_assign(self, lvalue, expr):
        return StmtAssign(lvalue, expr)

    ["Conditionals"]

    expr_while = WhileExpr

    # statement and expr ifelses are
    # really only syntacticly enforced
    expr_ifelse = IfElseExpr

    # and if with no else if also just
    # syntactic sugar
    def stmt_if(self, _if, _then):
        return IfElseExpr(_if, _then, CodeBlock([]))

    ["Expressions"]

    at_expr = AtExpr
    expr_index = GetitemExpr

    fcall = FcallExpr

    stack = STAR(Stack)

    code_block = STAR(CodeBlock)



    def name(self, name):
        return NameExpr(name.value)

    def string(self, string):
        return string.value[1:-1] # remove quotation marks

    int = int
    float = float

    expr_list = STAR(ListExpr)
    expr_tuple = STAR(TupleExpr)

    range = RangeExpr

    def const(self, name):
        return Const.get(name)


class StekkSyntaxError(SyntaxError):
    def __init__(self, error):
        self.error = error





LAST_EXC = None
ERROR_LOOKUP = [
    ("Syntax error (maybe missing ';' ?)", {'LESSTHAN', 'SEMICOLON', '__ANON_0', '__ANON_1'}),
    ("Missing ]", {'RSQB'}),
    ("Missing )", {'RPAR'}),
]

_path, _ = os.path.split(__file__)

with open(os.path.join(_path, "lang_grammar.lark")) as file:
    parser = Lark(file)

def parse(program):
    error = False
    try:
        x = parser.parse(program)
    except UnexpectedInput as u:
        global LAST_EXC
        LAST_EXC = u
        for message, subset in ERROR_LOOKUP:
            if subset <= u.allowed: # is subset?
                error = f"{message} at line {u.line}:\n{u.get_context(program)}"
                error += str(u.allowed)
                break
        else:
            error = f"Syntax error at line {u.line}::{u.allowed}"

    if error:
        raise StekkSyntaxError(error)
    statements = Tranny().transform(x).children
    return statements
