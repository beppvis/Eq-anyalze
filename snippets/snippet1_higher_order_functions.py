"""
SNIPPET 1: Higher-Order Functions — compose, pipe, curry, fixed_point
=====================================================================
Paste this into Python Tutor to visualize how functional combinators work.
"""

from functools import reduce

# ── compose: right-to-left function composition ──
def compose(*fns):
    def _composed(x):
        return reduce(lambda acc, f: f(acc), reversed(fns), x)
    return _composed

# ── pipe: left-to-right function composition ──
def pipe(*fns):
    def _piped(x):
        return reduce(lambda acc, f: f(acc), fns, x)
    return _piped

# ── curry: two-argument currying ──
def curry(fn):
    def _outer(a):
        def _inner(b):
            return fn(a, b)
        return _inner
    return _outer

# ── fixed_point: apply fn until output == input ──
def fixed_point(fn, x):
    for _ in range(100):
        result = fn(x)
        if result == x:
            return result
        x = result

# ═══ DEMO ═══════════════════════════════════════
add1   = lambda x: x + 1
double = lambda x: x * 2
square = lambda x: x * x

# compose: add1(double(3)) = add1(6) = 7
result1 = compose(add1, double)(3)
print(f"compose(add1, double)(3) = {result1}")  # 7

# pipe: double(add1(3)) = double(4) = 8
result2 = pipe(add1, double)(3)
print(f"pipe(add1, double)(3) = {result2}")      # 8

# curry: partial application
@curry
def add(a, b):
    return a + b

add5 = add(5)           # returns a function
result3 = add5(3)       # 5 + 3 = 8
print(f"add(5)(3) = {result3}")

# fixed_point: f(x) = x // 2 converges to 0
result4 = fixed_point(lambda x: x // 2, 100)
print(f"fixed_point(x // 2, 100) = {result4}")  # 0

# pipeline: chain three transforms
pipeline = pipe(add1, double, square)
result5 = pipeline(3)   # square(double(add1(3))) = square(8) = 64
print(f"pipe(add1, double, square)(3) = {result5}")
