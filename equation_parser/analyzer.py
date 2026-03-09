"""
Analyzer — evaluate, differentiate, simplify, and pretty-print AST nodes.

Every operation is a **pure function** dispatching on node type via
dictionaries of handlers (the higher-order *dispatch table* pattern).
Recursive traversal uses **generators** where appropriate (e.g. collecting
variables).
"""

import math
from functools import reduce
from typing import Iterator

from .ast_nodes import Number, Variable, BinOp, UnaryOp, FuncCall, Equation
from .utils import fixed_point


# ═══════════════════════════════════════════════════════════════════════════
#  Pretty-printing
# ═══════════════════════════════════════════════════════════════════════════

def _str_number(node):   return str(node.value)
def _str_variable(node): return node.name
def _str_binop(node):    return f"({to_string(node.left)} {node.op} {to_string(node.right)})"
def _str_unary(node):    return f"(-{to_string(node.operand)})"
def _str_func(node):     return f"{node.name}({to_string(node.arg)})"
def _str_eq(node):       return f"{to_string(node.lhs)} = {to_string(node.rhs)}"

_TO_STRING_DISPATCH = {
    Number:   _str_number,
    Variable: _str_variable,
    BinOp:    _str_binop,
    UnaryOp:  _str_unary,
    FuncCall: _str_func,
    Equation: _str_eq,
}


def to_string(node) -> str:
    """Convert an AST *node* back to a human-readable string."""
    handler = _TO_STRING_DISPATCH.get(type(node))
    if handler is None:
        raise TypeError(f"Unknown node type: {type(node)}")
    return handler(node)


# ═══════════════════════════════════════════════════════════════════════════
#  Collecting variables  (generator)
# ═══════════════════════════════════════════════════════════════════════════

def _vars_number(node):   return; yield   # noqa — make it a generator
def _vars_variable(node): yield node.name
def _vars_binop(node):    yield from variables(node.left);  yield from variables(node.right)
def _vars_unary(node):    yield from variables(node.operand)
def _vars_func(node):     yield from variables(node.arg)
def _vars_eq(node):       yield from variables(node.lhs); yield from variables(node.rhs)

_VARS_DISPATCH = {
    Number:   _vars_number,
    Variable: _vars_variable,
    BinOp:    _vars_binop,
    UnaryOp:  _vars_unary,
    FuncCall: _vars_func,
    Equation: _vars_eq,
}


def variables(node) -> Iterator[str]:
    """**Generator** that yields every variable name found in *node* (may repeat)."""
    handler = _VARS_DISPATCH.get(type(node))
    if handler is None:
        raise TypeError(f"Unknown node type: {type(node)}")
    yield from handler(node)


def variable_set(node) -> frozenset:
    """Return the *set* of unique variable names in *node*."""
    return frozenset(variables(node))


# ═══════════════════════════════════════════════════════════════════════════
#  Evaluation
# ═══════════════════════════════════════════════════════════════════════════

_MATH_FUNCS = {
    "sin":  math.sin,
    "cos":  math.cos,
    "tan":  math.tan,
    "log":  math.log10,
    "ln":   math.log,
    "sqrt": math.sqrt,
    "abs":  abs,
    "exp":  math.exp,
}

_BIN_OPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "^": lambda a, b: a ** b,
}


def evaluate(node, env: dict) -> float:
    """Evaluate *node* numerically given variable bindings in *env*.

    *env* is a plain ``dict`` mapping variable names to float values.

    Example::

        >>> from equation_parser.parser import parse
        >>> evaluate(parse("2*x + 1"), {"x": 5})
        11.0
    """
    dispatch = {
        Number:   lambda n: float(n.value),
        Variable: lambda n: _lookup_var(n, env),
        BinOp:    lambda n: _BIN_OPS[n.op](evaluate(n.left, env), evaluate(n.right, env)),
        UnaryOp:  lambda n: -evaluate(n.operand, env),
        FuncCall: lambda n: _MATH_FUNCS[n.name](evaluate(n.arg, env)),
        Equation: lambda n: evaluate(n.lhs, env) - evaluate(n.rhs, env),  # residual
    }
    handler = dispatch.get(type(node))
    if handler is None:
        raise TypeError(f"Unknown node type: {type(node)}")
    return handler(node)


def _lookup_var(node, env):
    if node.name not in env:
        raise NameError(f"Variable '{node.name}' is not defined")
    return float(env[node.name])


# ═══════════════════════════════════════════════════════════════════════════
#  Symbolic differentiation
# ═══════════════════════════════════════════════════════════════════════════

# Derivative rules for known functions (each returns dF/du as an AST)
_DIFF_FUNCS = {
    # sin(u)' = cos(u)
    "sin":  lambda u: FuncCall("cos", u),
    # cos(u)' = -sin(u)
    "cos":  lambda u: UnaryOp("-", FuncCall("sin", u)),
    # tan(u)' = 1 / cos(u)^2
    "tan":  lambda u: BinOp("/", Number(1), BinOp("^", FuncCall("cos", u), Number(2))),
    # ln(u)' = 1 / u
    "ln":   lambda u: BinOp("/", Number(1), u),
    # log(u)' = 1 / (u * ln(10))
    "log":  lambda u: BinOp("/", Number(1), BinOp("*", u, FuncCall("ln", Number(10)))),
    # sqrt(u)' = 1 / (2 * sqrt(u))
    "sqrt": lambda u: BinOp("/", Number(1), BinOp("*", Number(2), FuncCall("sqrt", u))),
    # exp(u)' = exp(u)
    "exp":  lambda u: FuncCall("exp", u),
    # abs not differentiable in general — provide |u|/u as a proxy
    "abs":  lambda u: BinOp("/", FuncCall("abs", u), u),
}


def differentiate(node, var: str):
    """Return the symbolic derivative of *node* with respect to *var*.

    Uses the **sum rule**, **product rule**, **quotient rule**, **power rule**,
    and **chain rule** — all encoded as pure recursive functions.

    >>> from equation_parser.parser import parse
    >>> to_string(differentiate(parse("x^3"), "x"))
    '(3 * (x ^ 2))'
    """
    t = type(node)

    if t is Number:
        return Number(0)

    if t is Variable:
        return Number(1) if node.name == var else Number(0)

    if t is UnaryOp:
        return UnaryOp("-", differentiate(node.operand, var))

    if t is BinOp:
        return _diff_binop(node, var)

    if t is FuncCall:
        # chain rule: f(g(x))' = f'(g(x)) * g'(x)
        inner_deriv = differentiate(node.arg, var)
        outer_deriv = _DIFF_FUNCS[node.name](node.arg)
        return BinOp("*", outer_deriv, inner_deriv)

    if t is Equation:
        return Equation(differentiate(node.lhs, var), differentiate(node.rhs, var))

    raise TypeError(f"Cannot differentiate node type {t}")


def _diff_binop(node, var):
    op = node.op
    l, r = node.left, node.right
    dl, dr = differentiate(l, var), differentiate(r, var)

    if op == "+":
        return BinOp("+", dl, dr)

    if op == "-":
        return BinOp("-", dl, dr)

    if op == "*":
        # product rule: (l*r)' = l'*r + l*r'
        return BinOp("+", BinOp("*", dl, r), BinOp("*", l, dr))

    if op == "/":
        # quotient rule: (l/r)' = (l'*r - l*r') / r^2
        numerator = BinOp("-", BinOp("*", dl, r), BinOp("*", l, dr))
        denominator = BinOp("^", r, Number(2))
        return BinOp("/", numerator, denominator)

    if op == "^":
        # power rule (simplified — assumes exponent is constant)
        # d/dx [u^n] = n * u^(n-1) * u'
        if type(r) is Number:
            return BinOp("*", BinOp("*", r, BinOp("^", l, Number(r.value - 1))), dl)
        # general case: u^v = exp(v * ln(u))
        # d/dx = u^v * (v' * ln(u) + v * u' / u)
        return BinOp("*",
            BinOp("^", l, r),
            BinOp("+",
                BinOp("*", dr, FuncCall("ln", l)),
                BinOp("*", r, BinOp("/", dl, l)),
            ),
        )

    raise ValueError(f"Unknown operator {op!r}")


# ═══════════════════════════════════════════════════════════════════════════
#  Simplification
# ═══════════════════════════════════════════════════════════════════════════

def _simplify_once(node):
    """Apply algebraic simplification rules **one pass** over *node*.

    Uses the dispatch-table pattern with a fallback for each node type.
    """
    t = type(node)

    if t is Number or t is Variable:
        return node

    if t is UnaryOp:
        operand = _simplify_once(node.operand)
        # --x → x
        if type(operand) is UnaryOp and operand.op == "-":
            return operand.operand
        # -0 → 0
        if operand == Number(0):
            return Number(0)
        # fold constant
        if type(operand) is Number:
            return Number(-operand.value)
        return UnaryOp(node.op, operand)

    if t is FuncCall:
        return FuncCall(node.name, _simplify_once(node.arg))

    if t is Equation:
        return Equation(_simplify_once(node.lhs), _simplify_once(node.rhs))

    if t is BinOp:
        return _simplify_binop(node)

    return node


def _simplify_binop(node):
    l = _simplify_once(node.left)
    r = _simplify_once(node.right)
    op = node.op

    zero, one = Number(0), Number(1)

    # constant folding
    if type(l) is Number and type(r) is Number:
        return Number(_BIN_OPS[op](l.value, r.value))

    # ── Addition ────────────────────────────────────────────────────────
    if op == "+":
        if l == zero: return r
        if r == zero: return l

    # ── Subtraction ─────────────────────────────────────────────────────
    if op == "-":
        if r == zero: return l
        if l == r:    return zero

    # ── Multiplication ──────────────────────────────────────────────────
    if op == "*":
        if l == zero or r == zero: return zero
        if l == one:  return r
        if r == one:  return l

    # ── Division ────────────────────────────────────────────────────────
    if op == "/":
        if l == zero: return zero
        if r == one:  return l

    # ── Exponentiation ──────────────────────────────────────────────────
    if op == "^":
        if r == zero: return one
        if r == one:  return l

    return BinOp(op, l, r)


def simplify(node):
    """Simplify *node* by repeatedly applying algebraic rules until stable.

    Uses the ``fixed_point`` combinator so simplification converges
    automatically.

    >>> from equation_parser.parser import parse
    >>> to_string(simplify(parse("0 + x * 1")))
    'x'
    """
    return fixed_point(_simplify_once, node)
