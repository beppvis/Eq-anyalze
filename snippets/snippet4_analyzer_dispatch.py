"""
SNIPPET 4: Analyzer — Evaluate, Variables (Generator), Dispatch Tables
======================================================================
Paste this into Python Tutor to see dispatch-table pattern, generator
variable collection, and numeric evaluation in action.
"""

import math
from collections import namedtuple

# ── AST Nodes ──
Number   = namedtuple("Number",   ["value"])
Variable = namedtuple("Variable", ["name"])
BinOp    = namedtuple("BinOp",    ["op", "left", "right"])
UnaryOp  = namedtuple("UnaryOp",  ["op", "operand"])
FuncCall = namedtuple("FuncCall",  ["name", "arg"])

# ═══════════════════════════════════════════════
#  DISPATCH TABLE: to_string
# ═══════════════════════════════════════════════
# Maps each node TYPE to a handler FUNCTION
_TO_STRING = {
    Number:   lambda n: str(n.value),
    Variable: lambda n: n.name,
    BinOp:    lambda n: f"({to_string(n.left)} {n.op} {to_string(n.right)})",
    UnaryOp:  lambda n: f"(-{to_string(n.operand)})",
    FuncCall: lambda n: f"{n.name}({to_string(n.arg)})",
}

def to_string(node):
    return _TO_STRING[type(node)](node)

# ═══════════════════════════════════════════════
#  GENERATOR: collecting variables via yield
# ═══════════════════════════════════════════════
def variables(node):
    """Generator — yields variable names via recursive yield from."""
    t = type(node)
    if t is Number:
        return                          # no variables in a number
    if t is Variable:
        yield node.name                 # yield the name
    elif t is BinOp:
        yield from variables(node.left)   # recurse left
        yield from variables(node.right)  # recurse right
    elif t is UnaryOp:
        yield from variables(node.operand)
    elif t is FuncCall:
        yield from variables(node.arg)

# ═══════════════════════════════════════════════
#  EVALUATION with dispatch table
# ═══════════════════════════════════════════════
_BIN_OPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "^": lambda a, b: a ** b,
}

_MATH_FUNCS = {
    "sin": math.sin, "cos": math.cos,
    "sqrt": math.sqrt, "exp": math.exp,
}

def evaluate(node, env):
    """Evaluate an AST node given variable bindings env."""
    dispatch = {
        Number:   lambda n: float(n.value),
        Variable: lambda n: float(env[n.name]),
        BinOp:    lambda n: _BIN_OPS[n.op](
                      evaluate(n.left, env), evaluate(n.right, env)),
        UnaryOp:  lambda n: -evaluate(n.operand, env),
        FuncCall: lambda n: _MATH_FUNCS[n.name](evaluate(n.arg, env)),
    }
    return dispatch[type(node)](node)

# ═══ DEMO ═══════════════════════════════════════
# Build AST for: 2 * x + sin(y)
tree = BinOp("+",
    BinOp("*", Number(2), Variable("x")),
    FuncCall("sin", Variable("y"))
)

# 1) Pretty-print
print(f"Expression: {to_string(tree)}")

# 2) Collect variables (generator!)
var_gen = variables(tree)
print(f"\nIs generator? {hasattr(var_gen, '__next__')}")
v1 = next(var_gen)
print(f"First variable:  {v1}")
v2 = next(var_gen)
print(f"Second variable: {v2}")

# Get all at once
all_vars = frozenset(variables(tree))
print(f"All variables: {all_vars}")

# 3) Evaluate with env
env = {"x": 5, "y": 0}
result = evaluate(tree, env)
print(f"\nEvaluate with x=5, y=0: {result}")
# Expected: 2*5 + sin(0) = 10 + 0 = 10.0

env2 = {"x": 3, "y": 3.14159}
result2 = evaluate(tree, env2)
print(f"Evaluate with x=3, y=π: {result2}")
# Expected: 2*3 + sin(π) ≈ 6.0
