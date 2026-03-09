"""
SNIPPET 3: Recursive Descent Parser with Higher-Order Factory
=============================================================
Paste this into Python Tutor to visualize how _parse_binary builds
parsers for different precedence levels using the same factory.
"""

from collections import namedtuple

# ── AST Nodes (immutable namedtuples) ──
Number   = namedtuple("Number",   ["value"])
Variable = namedtuple("Variable", ["name"])
BinOp    = namedtuple("BinOp",    ["op", "left", "right"])
UnaryOp  = namedtuple("UnaryOp",  ["op", "operand"])

# ── Minimal Token ──
Token = namedtuple("Token", ["kind", "value"])
NUMBER, IDENT, OP, LPAREN, RPAREN, EOF = (
    "NUMBER", "IDENT", "OP", "LPAREN", "RPAREN", "EOF"
)

# ── Simple tokenizer (generator) ──
def tokenize(text):
    pos, n = 0, len(text)
    while pos < n:
        ch = text[pos]
        if ch.isspace():           pos += 1; continue
        if ch.isdigit():
            start = pos
            while pos < n and text[pos].isdigit(): pos += 1
            yield Token(NUMBER, int(text[start:pos])); continue
        if ch.isalpha():
            yield Token(IDENT, ch); pos += 1; continue
        if ch in "+-*/^":
            yield Token(OP, ch); pos += 1; continue
        if ch == "(":              yield Token(LPAREN, "("); pos += 1; continue
        if ch == ")":              yield Token(RPAREN, ")"); pos += 1; continue
        raise SyntaxError(f"Unexpected: {ch}")
    yield Token(EOF, None)

# ── Closure-based peekable iterator ──
def make_peekable(token_iter):
    buf = [next(token_iter)]
    def peek():    return buf[0]
    def advance():
        cur = buf[0]
        try:    buf[0] = next(token_iter)
        except: buf[0] = Token(EOF, None)
        return cur
    return peek, advance

# ── Parser: atom and unary ──
def parse_atom(peek, advance):
    tok = peek()
    if tok.kind == NUMBER:
        advance()
        return Number(tok.value)
    if tok.kind == IDENT:
        advance()
        return Variable(tok.value)
    if tok.kind == LPAREN:
        advance()
        node = parse_expr(peek, advance)
        advance()   # consume ')'
        return node
    raise SyntaxError(f"Unexpected: {tok}")

def parse_unary(peek, advance):
    if peek().kind == OP and peek().value == "-":
        advance()
        return UnaryOp("-", parse_unary(peek, advance))
    return parse_atom(peek, advance)

# ══════════════════════════════════════════════════════
#  THE KEY HIGHER-ORDER FUNCTION
# ══════════════════════════════════════════════════════
def parse_binary(operators, next_parser):
    """
    Higher-order factory: returns a NEW parser function
    for left-associative operators at one precedence level.

    operators   → set of operator chars (e.g. {"+", "-"})
    next_parser → the parser for the NEXT higher precedence
    """
    def _parser(peek, advance):
        left = next_parser(peek, advance)
        while peek().kind == OP and peek().value in operators:
            op = advance().value
            right = next_parser(peek, advance)
            left = BinOp(op, left, right)
        return left
    return _parser

# Build each precedence level — one line per level!
parse_power = parse_binary({"^"},      parse_unary)   # highest
parse_term  = parse_binary({"*", "/"}, parse_power)   # middle
parse_sum   = parse_binary({"+", "-"}, parse_term)    # lowest

def parse_expr(peek, advance):
    return parse_sum(peek, advance)

# ── Public parse function ──
def parse(text):
    peek, advance = make_peekable(tokenize(text))
    return parse_expr(peek, advance)

# ── Pretty-print ──
def to_string(node):
    if type(node) is Number:   return str(node.value)
    if type(node) is Variable: return node.name
    if type(node) is UnaryOp:  return f"(-{to_string(node.operand)})"
    if type(node) is BinOp:
        return f"({to_string(node.left)} {node.op} {to_string(node.right)})"

# ═══ DEMO ═══════════════════════════════════════
expressions = [
    "2 + 3",
    "2 + 3 * 4",        # precedence: 2 + (3*4)
    "(2 + 3) * 4",      # override with parens
    "x ^ 2 + 3 * x + 1",
    "-x + 5",
]

for expr in expressions:
    tree = parse(expr)
    print(f"  {expr:25s}  →  AST: {to_string(tree)}")
    print(f"  {'':25s}     Raw: {tree}")
    print()
