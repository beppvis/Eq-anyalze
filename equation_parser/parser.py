"""
Recursive-descent parser — turns a token iterator into an AST.

Every grammar rule is a **pure function** that consumes tokens from a shared
peekable iterator and returns an AST node.  Operator-precedence levels are
handled via a **higher-order** ``_parse_binary`` function that is parameterised
with the operator set and the next-precedence parser.
"""

from functools import reduce
from typing import Iterator

from .tokenizer import Token, NUMBER, IDENT, OP, LPAREN, RPAREN, EQUALS, EOF, tokenize
from .ast_nodes import Number, Variable, BinOp, UnaryOp, FuncCall, Equation


# ── Peekable iterator (functional wrapper, not a class) ────────────────────

def _make_peekable(token_iter: Iterator[Token]):
    """Return a ``(peek, advance)`` pair of closures over *token_iter*.

    This avoids building a class while still giving us one-token lookahead.
    The mutable state is confined to a single-element list captured by the
    closures.
    """
    buffer = [next(token_iter)]

    def peek():
        return buffer[0]

    def advance():
        current = buffer[0]
        try:
            buffer[0] = next(token_iter)
        except StopIteration:
            buffer[0] = Token(EOF, None)
        return current

    return peek, advance


# ── Expect helper ──────────────────────────────────────────────────────────

def _expect(peek, advance, kind, value=None):
    """Consume the next token, asserting its *kind* (and optionally *value*)."""
    tok = advance()
    if tok.kind != kind:
        raise SyntaxError(f"Expected {kind} but got {tok}")
    if value is not None and tok.value != value:
        raise SyntaxError(f"Expected {value!r} but got {tok.value!r}")
    return tok


# ── Grammar rules ──────────────────────────────────────────────────────────

# Known function names (math builtins)
_FUNCTIONS = frozenset({"sin", "cos", "tan", "log", "ln", "sqrt", "abs", "exp"})


def _parse_atom(peek, advance):
    """atom → NUMBER | IDENT | FUNC '(' expr ')' | '(' expr ')'"""
    tok = peek()

    # Number literal
    if tok.kind == NUMBER:
        advance()
        return Number(tok.value)

    # Identifier — could be a function call or a plain variable
    if tok.kind == IDENT:
        advance()
        if tok.value in _FUNCTIONS and peek().kind == LPAREN:
            advance()  # consume '('
            arg = _parse_expr(peek, advance)
            _expect(peek, advance, RPAREN)
            return FuncCall(tok.value, arg)
        return Variable(tok.value)

    # Parenthesised sub-expression
    if tok.kind == LPAREN:
        advance()  # consume '('
        node = _parse_expr(peek, advance)
        _expect(peek, advance, RPAREN)
        return node

    raise SyntaxError(f"Unexpected token {tok}")


def _parse_unary(peek, advance):
    """unary → '-' unary | atom"""
    if peek().kind == OP and peek().value == "-":
        advance()
        operand = _parse_unary(peek, advance)
        return UnaryOp("-", operand)
    return _parse_atom(peek, advance)


def _parse_binary(operators, next_parser):
    """Higher-order factory: returns a parser for left-associative binary ops.

    *operators* is the set of operator characters at this precedence level.
    *next_parser* is the parser for the next-higher precedence level.

    This is the **key higher-order function** — the same factory produces
    parsers for addition/subtraction, multiplication/division, and
    exponentiation.
    """
    def _parser(peek, advance):
        left = next_parser(peek, advance)
        while peek().kind == OP and peek().value in operators:
            op_tok = advance()
            right = next_parser(peek, advance)
            left = BinOp(op_tok.value, left, right)
        return left
    return _parser


# Build precedence levels bottom-up via the higher-order factory.
_parse_power = _parse_binary({"^"}, _parse_unary)
_parse_term  = _parse_binary({"*", "/"}, _parse_power)
_parse_sum   = _parse_binary({"+", "-"}, _parse_term)


def _parse_expr(peek, advance):
    """expr → sum   (entry point for an expression without '=')"""
    return _parse_sum(peek, advance)


def _parse_equation(peek, advance):
    """equation → expr ('=' expr)?

    If an ``=`` is present we return an ``Equation`` node; otherwise just the
    expression.
    """
    lhs = _parse_expr(peek, advance)
    if peek().kind == EQUALS:
        advance()
        rhs = _parse_expr(peek, advance)
        return Equation(lhs, rhs)
    return lhs


# ── Public API ─────────────────────────────────────────────────────────────

def parse(text: str):
    """Parse *text* into an AST.

    Combines the tokenizer (generator) with the recursive-descent parser.

    >>> from equation_parser.analyzer import to_string
    >>> to_string(parse("2*x + 3"))
    '((2 * x) + 3)'
    """
    tokens = tokenize(text)            # generator — lazy
    peek, advance = _make_peekable(tokens)
    tree = _parse_equation(peek, advance)
    # make sure we consumed everything
    if peek().kind != EOF:
        raise SyntaxError(f"Unexpected trailing token {peek()}")
    return tree
