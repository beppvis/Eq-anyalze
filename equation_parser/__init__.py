"""
Functional Equation Parser & Analyzer
======================================
A purely functional equation parser built with higher-order functions,
iterators, and generators — no classes for logic.
"""

from .tokenizer import tokenize
from .parser import parse
from .analyzer import evaluate, differentiate, simplify, to_string, variables
from .utils import pipe, compose

__all__ = [
    "tokenize", "parse", "evaluate", "differentiate",
    "simplify", "to_string", "variables", "pipe", "compose",
]
