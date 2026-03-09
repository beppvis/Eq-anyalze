"""
SNIPPET 5: Symbolic Differentiation & Simplification
=====================================================
Paste this into Python Tutor to watch differentiation rules
(power, product, chain) and fixed-point simplification step by step.
"""

from collections import namedtuple

# ── AST Nodes ──
Number   = namedtuple("Number",   ["value"])
Variable = namedtuple("Variable", ["name"])
BinOp    = namedtuple("BinOp",    ["op", "left", "right"])
UnaryOp  = namedtuple("UnaryOp",  ["op", "operand"])
FuncCall = namedtuple("FuncCall",  ["name", "arg"])

# ── Pretty-printer ──
def to_string(node):
    t = type(node)
    if t is Number:   return str(node.value)
    if t is Variable: return node.name
    if t is UnaryOp:  return f"(-{to_string(node.operand)})"
    if t is FuncCall:  return f"{node.name}({to_string(node.arg)})"
    if t is BinOp:
        return f"({to_string(node.left)} {node.op} {to_string(node.right)})"

# ═══════════════════════════════════════════════
#  DIFFERENTIATION — pure recursive functions
# ═══════════════════════════════════════════════
def differentiate(node, var):
    t = type(node)

    # d/dx(c) = 0
    if t is Number:
        return Number(0)

    # d/dx(x) = 1, d/dx(y) = 0
    if t is Variable:
        return Number(1) if node.name == var else Number(0)

    # d/dx(-u) = -(du/dx)
    if t is UnaryOp:
        return UnaryOp("-", differentiate(node.operand, var))

    # Chain rule for functions: d/dx f(u) = f'(u) * du/dx
    if t is FuncCall:
        du = differentiate(node.arg, var)
        if node.name == "sin":
            return BinOp("*", FuncCall("cos", node.arg), du)
        if node.name == "cos":
            return BinOp("*", UnaryOp("-", FuncCall("sin", node.arg)), du)

    if t is BinOp:
        l, r = node.left, node.right
        dl = differentiate(l, var)
        dr = differentiate(r, var)

        # Sum rule: d/dx(l + r) = dl + dr
        if node.op == "+":
            return BinOp("+", dl, dr)

        # Product rule: d/dx(l * r) = dl*r + l*dr
        if node.op == "*":
            return BinOp("+",
                BinOp("*", dl, r),
                BinOp("*", l, dr))

        # Power rule: d/dx(u^n) = n * u^(n-1) * du
        if node.op == "^" and type(r) is Number:
            return BinOp("*",
                BinOp("*", r, BinOp("^", l, Number(r.value - 1))),
                dl)

    raise ValueError(f"Cannot differentiate: {node}")

# ═══════════════════════════════════════════════
#  SIMPLIFICATION — fixed-point combinator
# ═══════════════════════════════════════════════
_OPS = {"+": lambda a,b: a+b, "-": lambda a,b: a-b,
        "*": lambda a,b: a*b, "/": lambda a,b: a/b,
        "^": lambda a,b: a**b}

def simplify_once(node):
    t = type(node)
    if t is Number or t is Variable:
        return node
    if t is UnaryOp:
        inner = simplify_once(node.operand)
        if inner == Number(0): return Number(0)
        if type(inner) is Number: return Number(-inner.value)
        return UnaryOp("-", inner)
    if t is BinOp:
        l = simplify_once(node.left)
        r = simplify_once(node.right)
        zero, one = Number(0), Number(1)
        # Constant folding
        if type(l) is Number and type(r) is Number:
            return Number(_OPS[node.op](l.value, r.value))
        if node.op == "+":
            if l == zero: return r
            if r == zero: return l
        if node.op == "*":
            if l == zero or r == zero: return zero
            if l == one: return r
            if r == one: return l
        if node.op == "^":
            if r == zero: return one
            if r == one:  return l
        return BinOp(node.op, l, r)
    return node

def fixed_point(fn, x):
    """Apply fn until output == input."""
    for _ in range(50):
        result = fn(x)
        if result == x:
            return result
        x = result
    return x

def simplify(node):
    return fixed_point(simplify_once, node)

# ═══ DEMO ═══════════════════════════════════════
print("=== DIFFERENTIATION DEMO ===")
print()

# Example 1: d/dx(x^3) → 3x^2
expr1 = BinOp("^", Variable("x"), Number(3))
d1_raw = differentiate(expr1, "x")
d1 = simplify(d1_raw)
print(f"  d/dx({to_string(expr1)})")
print(f"    raw:        {to_string(d1_raw)}")
print(f"    simplified: {to_string(d1)}")
print()

# Example 2: d/dx(2*x + 5) → 2
expr2 = BinOp("+", BinOp("*", Number(2), Variable("x")), Number(5))
d2_raw = differentiate(expr2, "x")
d2 = simplify(d2_raw)
print(f"  d/dx({to_string(expr2)})")
print(f"    raw:        {to_string(d2_raw)}")
print(f"    simplified: {to_string(d2)}")
print()

# Example 3: d/dx(x * x) = 2x  (product rule)
expr3 = BinOp("*", Variable("x"), Variable("x"))
d3_raw = differentiate(expr3, "x")
d3 = simplify(d3_raw)
print(f"  d/dx({to_string(expr3)})")
print(f"    raw:        {to_string(d3_raw)}")
print(f"    simplified: {to_string(d3)}")
print()

print("=== SIMPLIFICATION DEMO ===")
print()

cases = [
    BinOp("+", Number(0), Variable("x")),
    BinOp("*", Number(1), Variable("x")),
    BinOp("*", Number(0), Variable("x")),
    BinOp("^", Variable("x"), Number(0)),
    BinOp("+", Number(2), Number(3)),
]

for expr in cases:
    result = simplify(expr)
    print(f"  {to_string(expr):20s}  →  {to_string(result)}")
