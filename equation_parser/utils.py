"""
Functional utilities: compose, pipe, curry, and fixed-point combinator.
"""

from functools import reduce


def compose(*fns):
    """Right-to-left function composition.

    >>> add1 = lambda x: x + 1
    >>> double = lambda x: x * 2
    >>> compose(add1, double)(3)   # add1(double(3)) == 7
    7
    """
    def _composed(x):
        return reduce(lambda acc, f: f(acc), reversed(fns), x)
    return _composed


def pipe(*fns):
    """Left-to-right function composition.

    >>> add1 = lambda x: x + 1
    >>> double = lambda x: x * 2
    >>> pipe(add1, double)(3)   # double(add1(3)) == 8
    8
    """
    def _piped(x):
        return reduce(lambda acc, f: f(acc), fns, x)
    return _piped


def curry(fn):
    """Simple two-argument currying decorator.

    >>> @curry
    ... def add(a, b): return a + b
    >>> add(1)(2)
    3
    """
    def _outer(a):
        def _inner(b):
            return fn(a, b)
        return _inner
    return _outer


def fixed_point(fn, x, max_iterations=100):
    """Apply *fn* repeatedly until the output equals the input (a fixed point).

    Raises ``RuntimeError`` if convergence is not reached within
    *max_iterations* steps.
    """
    for _ in range(max_iterations):
        result = fn(x)
        if result == x:
            return result
        x = result
    raise RuntimeError("fixed_point did not converge")
