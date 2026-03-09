"""
AST Node definitions using namedtuples — lightweight, immutable, functional data.
"""

from collections import namedtuple

# ── Leaf nodes ──────────────────────────────────────────────────────────────
Number   = namedtuple("Number",   ["value"])
Variable = namedtuple("Variable", ["name"])

# ── Composite nodes ─────────────────────────────────────────────────────────
BinOp    = namedtuple("BinOp",    ["op", "left", "right"])
UnaryOp  = namedtuple("UnaryOp",  ["op", "operand"])
FuncCall = namedtuple("FuncCall",  ["name", "arg"])
Equation = namedtuple("Equation", ["lhs", "rhs"])
