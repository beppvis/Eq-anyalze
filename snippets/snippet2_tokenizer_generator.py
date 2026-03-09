"""
SNIPPET 2: Generator-Based Tokenizer
=====================================
Paste this into Python Tutor to see how the generator yields tokens lazily.
"""

from collections import namedtuple

# ── Token definition ──
Token = namedtuple("Token", ["kind", "value"])

NUMBER, IDENT, OP, LPAREN, RPAREN, EQUALS, EOF = (
    "NUMBER", "IDENT", "OP", "LPAREN", "RPAREN", "EQUALS", "EOF"
)

# ── Higher-order predicates ──
is_digit = str.isdigit
is_alpha = str.isalpha
is_alnum = str.isalnum

def _consume_while(predicate, text, pos):
    """Consume chars while predicate holds (higher-order function)."""
    start = pos
    while pos < len(text) and predicate(text[pos]):
        pos += 1
    return text[start:pos], pos

# ── Generator tokenizer ──
def tokenize(text):
    """Generator — yields Token namedtuples lazily, one at a time."""
    pos = 0
    length = len(text)

    while pos < length:
        ch = text[pos]

        if ch.isspace():
            pos += 1
            continue

        if is_digit(ch):
            num_str, pos = _consume_while(
                lambda c: is_digit(c) or c == ".", text, pos
            )
            value = float(num_str) if "." in num_str else int(num_str)
            yield Token(NUMBER, value)
            continue

        if is_alpha(ch) or ch == "_":
            ident, pos = _consume_while(
                lambda c: is_alnum(c) or c == "_", text, pos
            )
            yield Token(IDENT, ident)
            continue

        if ch in "+-*/^":
            yield Token(OP, ch)
            pos += 1
            continue

        if ch == "(":
            yield Token(LPAREN, "(")
            pos += 1
            continue

        if ch == ")":
            yield Token(RPAREN, ")")
            pos += 1
            continue

        if ch == "=":
            yield Token(EQUALS, "=")
            pos += 1
            continue

        raise SyntaxError(f"Unexpected character {ch!r}")

    yield Token(EOF, None)   # sentinel


# ═══ DEMO ═══════════════════════════════════════
expr = "2 * x + sin(3.14)"

print(f"Tokenizing: '{expr}'")
print("-" * 40)

# The generator yields tokens lazily — watch it step through!
token_gen = tokenize(expr)

for token in token_gen:
    print(f"  {token.kind:8s}  →  {token.value!r}")

# Verify it's truly a generator
print()
gen = tokenize("1 + 2")
print(f"Is generator? {hasattr(gen, '__next__')}")  # True
t1 = next(gen)   # lazily get first token
print(f"First token:  {t1}")
t2 = next(gen)   # lazily get second token
print(f"Second token: {t2}")
