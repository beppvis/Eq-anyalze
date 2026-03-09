"""
SNIPPET 6: Full Pipeline — pipe(parse, differentiate, simplify, to_string)
==========================================================================
Paste this into Python Tutor to see the entire equation-processing
pipeline from raw text to simplified derivative, using pipe().
"""

from collections import namedtuple
from functools import reduce

# ── AST Nodes ──
Number   = namedtuple("Number",   ["value"])
Variable = namedtuple("Variable", ["name"])
BinOp    = namedtuple("BinOp",    ["op", "left", "right"])
UnaryOp  = namedtuple("UnaryOp",  ["op", "operand"])
Token    = namedtuple("Token", ["kind", "value"])

NUMBER, IDENT, OP, LPAREN, RPAREN, EOF = (
    "NUMBER", "IDENT", "OP", "LPAREN", "RPAREN", "EOF")

# ── pipe combinator ──
def pipe(*fns):
    def _piped(x):
        return reduce(lambda acc, f: f(acc), fns, x)
    return _piped

# ── Minimal tokenizer (generator) ──
def tokenize(text):
    pos, n = 0, len(text)
    while pos < n:
        ch = text[pos]
        if ch.isspace():  pos += 1; continue
        if ch.isdigit():
            s = pos
            while pos < n and text[pos].isdigit(): pos += 1
            yield Token(NUMBER, int(text[s:pos])); continue
        if ch.isalpha():  yield Token(IDENT, ch); pos += 1; continue
        if ch in "+-*/^": yield Token(OP, ch); pos += 1; continue
        if ch == "(":     yield Token(LPAREN, "("); pos += 1; continue
        if ch == ")":     yield Token(RPAREN, ")"); pos += 1; continue
        raise SyntaxError(ch)
    yield Token(EOF, None)

# ── Peekable iterator (closure pair) ──
def make_peekable(it):
    buf = [next(it)]
    def peek():    return buf[0]
    def advance():
        cur = buf[0]
        try:    buf[0] = next(it)
        except: buf[0] = Token(EOF, None)
        return cur
    return peek, advance

# ── Parser ──
def parse_atom(p, a):
    t = p()
    if t.kind == NUMBER:  a(); return Number(t.value)
    if t.kind == IDENT:   a(); return Variable(t.value)
    if t.kind == LPAREN:
        a(); node = parse_expr(p, a); a(); return node

def parse_unary(p, a):
    if p().kind == OP and p().value == "-":
        a(); return UnaryOp("-", parse_unary(p, a))
    return parse_atom(p, a)

def parse_binary(ops, nxt):
    def _p(p, a):
        left = nxt(p, a)
        while p().kind == OP and p().value in ops:
            op = a().value; left = BinOp(op, left, nxt(p, a))
        return left
    return _p

parse_power = parse_binary({"^"},      parse_unary)
parse_term  = parse_binary({"*", "/"}, parse_power)
parse_sum   = parse_binary({"+", "-"}, parse_term)
def parse_expr(p, a): return parse_sum(p, a)

def parse(text):
    p, a = make_peekable(tokenize(text))
    return parse_expr(p, a)

# ── to_string ──
def to_string(n):
    t = type(n)
    if t is Number:   return str(n.value)
    if t is Variable: return n.name
    if t is UnaryOp:  return f"(-{to_string(n.operand)})"
    if t is BinOp:    return f"({to_string(n.left)} {n.op} {to_string(n.right)})"

# ── differentiate ──
def diff(node, var):
    t = type(node)
    if t is Number:   return Number(0)
    if t is Variable: return Number(1) if node.name == var else Number(0)
    if t is UnaryOp:  return UnaryOp("-", diff(node.operand, var))
    if t is BinOp:
        l, r, dl, dr = node.left, node.right, diff(node.left, var), diff(node.right, var)
        if node.op == "+": return BinOp("+", dl, dr)
        if node.op == "-": return BinOp("-", dl, dr)
        if node.op == "*": return BinOp("+", BinOp("*", dl, r), BinOp("*", l, dr))
        if node.op == "^" and type(r) is Number:
            return BinOp("*", BinOp("*", r, BinOp("^", l, Number(r.value - 1))), dl)

# ── simplify with fixed_point ──
_OPS = {"+": lambda a,b: a+b, "*": lambda a,b: a*b,
        "-": lambda a,b: a-b, "^": lambda a,b: a**b}

def simp(node):
    t = type(node)
    if t in (Number, Variable): return node
    if t is UnaryOp:
        inner = simp(node.operand)
        if type(inner) is Number: return Number(-inner.value)
        return UnaryOp("-", inner)
    if t is BinOp:
        l, r = simp(node.left), simp(node.right)
        z, o = Number(0), Number(1)
        if type(l) is Number and type(r) is Number:
            return Number(_OPS[node.op](l.value, r.value))
        if node.op == "+":
            if l == z: return r
            if r == z: return l
        if node.op == "*":
            if l == z or r == z: return z
            if l == o: return r
            if r == o: return l
        if node.op == "^":
            if r == z: return o
            if r == o: return l
        return BinOp(node.op, l, r)
    return node

def simplify(node):
    for _ in range(50):
        result = simp(node)
        if result == node: return result
        node = result
    return node

# ═══════════════════════════════════════════════════
#  THE PIPELINE — pipe connects everything together
# ═══════════════════════════════════════════════════

# Pipeline: text → parse → differentiate → simplify → string
diff_x = pipe(
    parse,                          # Step 1: text → AST
    lambda n: diff(n, "x"),         # Step 2: AST  → derivative AST
    simplify,                       # Step 3: simplify the derivative
    to_string,                      # Step 4: AST  → readable string
)

# Another pipeline: text → parse → simplify → string
simplify_expr = pipe(parse, simplify, to_string)

# ═══ DEMO ═══════════════════════════════════════
print("=== FULL PIPELINE DEMO ===")
print()

test_cases = [
    ("x ^ 3",         "x"),
    ("2 * x + 5",     "x"),
    ("x * x",         "x"),
    ("x ^ 2 + x + 1", "x"),
]

for expr, var in test_cases:
    # Show each pipeline stage
    ast       = parse(expr)
    deriv_ast = diff(ast, var)
    simp_ast  = simplify(deriv_ast)
    result    = to_string(simp_ast)

    print(f"  Input:       {expr}")
    print(f"  Parsed:      {to_string(ast)}")
    print(f"  d/d{var} raw:  {to_string(deriv_ast)}")
    print(f"  Simplified:  {result}")

    # Verify the pipe gives the same answer
    piped = diff_x(expr)
    print(f"  pipe() =     {piped}")
    print()

print("=== SIMPLIFY PIPELINE ===")
simpl_cases = ["0 + x", "1 * x", "x * 0", "x ^ 1", "2 + 3"]
for expr in simpl_cases:
    print(f"  {expr:10s}  →  {simplify_expr(expr)}")
