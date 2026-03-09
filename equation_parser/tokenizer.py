"""
Generator-based tokenizer (lexer) for mathematical expressions.

The main entry point is ``tokenize(text)``, a **generator** that lazily yields
``Token`` namedtuples.  Internally it uses ``itertools`` helpers and higher-order
predicate functions for character classification.
"""

from collections import namedtuple
from itertools import dropwhile
from typing import Iterator

# ── Token type ──────────────────────────────────────────────────────────────
Token = namedtuple("Token", ["kind", "value"])

# Token kind constants
NUMBER = "NUMBER"
IDENT  = "IDENT"      # variable or function name
OP     = "OP"
LPAREN = "LPAREN"
RPAREN = "RPAREN"
EQUALS = "EQUALS"
EOF    = "EOF"

# ── Character predicates (higher-order-friendly) ───────────────────────────
is_whitespace = str.isspace
is_digit      = str.isdigit
is_alpha      = str.isalpha
is_alnum      = str.isalnum

OPERATORS = {"+", "-", "*", "/", "^"}

is_operator = lambda ch: ch in OPERATORS


# ── Helpers ─────────────────────────────────────────────────────────────────

def _consume_while(predicate, text, pos):
    """Consume characters from *text* starting at *pos* while *predicate* holds.

    Returns ``(collected_string, new_pos)``.  This is the functional replacement
    for a mutable ``StringBuilder`` — it uses higher-order predicates.
    """
    start = pos
    while pos < len(text) and predicate(text[pos]):
        pos += 1
    return text[start:pos], pos


def _read_number(text, pos):
    """Read an integer or float literal starting at *pos*.

    Returns ``(Token, new_pos)``.
    """
    num_str, pos = _consume_while(lambda ch: is_digit(ch) or ch == ".", text, pos)
    value = float(num_str) if "." in num_str else int(num_str)
    return Token(NUMBER, value), pos


def _read_identifier(text, pos):
    """Read an identifier (variable / function name) starting at *pos*.

    Identifiers may contain letters, digits, and underscores but must start
    with a letter or underscore.
    """
    ident, pos = _consume_while(lambda ch: is_alnum(ch) or ch == "_", text, pos)
    return Token(IDENT, ident), pos


# ── Main generator ─────────────────────────────────────────────────────────

def tokenize(text: str) -> Iterator[Token]:
    """Yield ``Token`` namedtuples from the input *text*.

    This is a **generator** — tokens are produced lazily, one at a time.

    Supported tokens:
      NUMBER   – integer or float (``3``, ``3.14``)
      IDENT    – variable or function name (``x``, ``sin``)
      OP       – ``+  -  *  /  ^``
      LPAREN   – ``(``
      RPAREN   – ``)``
      EQUALS   – ``=``
      EOF      – end-of-input sentinel

    Example::

        >>> list(tokenize("2*x + 3"))
        [Token('NUMBER', 2), Token('OP', '*'), Token('IDENT', 'x'),
         Token('OP', '+'), Token('NUMBER', 3), Token('EOF', None)]
    """
    pos = 0
    length = len(text)

    while pos < length:
        ch = text[pos]

        # skip whitespace
        if is_whitespace(ch):
            pos += 1
            continue

        # numbers
        if is_digit(ch) or (ch == "." and pos + 1 < length and is_digit(text[pos + 1])):
            token, pos = _read_number(text, pos)
            yield token
            continue

        # identifiers (variables / function names)
        if is_alpha(ch) or ch == "_":
            token, pos = _read_identifier(text, pos)
            yield token
            continue

        # operators
        if is_operator(ch):
            yield Token(OP, ch)
            pos += 1
            continue

        # parentheses
        if ch == "(":
            yield Token(LPAREN, "(")
            pos += 1
            continue

        if ch == ")":
            yield Token(RPAREN, ")")
            pos += 1
            continue

        # equals sign (for equations like  2*x + 1 = 5)
        if ch == "=":
            yield Token(EQUALS, "=")
            pos += 1
            continue

        raise SyntaxError(f"Unexpected character {ch!r} at position {pos}")

    # sentinel so the parser never falls off the end
    yield Token(EOF, None)
