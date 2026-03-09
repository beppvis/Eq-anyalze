#!/usr/bin/env python3
"""
Interactive REPL for the Functional Equation Parser & Analyzer.

Commands
--------
  :parse    <expr>         Show the AST
  :eval     <expr>         Evaluate (prompts for variable values)
  :diff     <expr>  <var>  Symbolic derivative w.r.t. <var>
  :simplify <expr>         Simplify expression
  :vars     <expr>         List variables
  :help                    Show this help
  :quit / :q               Exit

Plain input is parsed, simplified, and printed.
"""

import sys
from functools import reduce

from equation_parser.parser import parse
from equation_parser.analyzer import (
    to_string, evaluate, differentiate, simplify, variables, variable_set,
)
from equation_parser.utils import pipe


# ── Higher-order command dispatch ──────────────────────────────────────────

def _cmd_parse(args):
    tree = parse(args)
    print(f"  AST : {tree}")
    print(f"  Repr: {to_string(tree)}")


def _cmd_eval(args):
    tree = parse(args)
    vs = variable_set(tree)
    env = {}
    for v in sorted(vs):
        raw = input(f"  {v} = ")
        env[v] = float(raw)
    result = evaluate(tree, env)
    print(f"  = {result}")


def _cmd_diff(args):
    parts = args.rsplit(maxsplit=1)
    if len(parts) != 2:
        print("  Usage: :diff <expr> <variable>")
        return
    expr_str, var = parts
    tree = parse(expr_str)
    derivative = pipe(
        lambda n: differentiate(n, var),
        simplify,
        to_string,
    )(tree)
    print(f"  d/d{var} = {derivative}")


def _cmd_simplify(args):
    result = pipe(parse, simplify, to_string)(args)
    print(f"  = {result}")


def _cmd_vars(args):
    tree = parse(args)
    vs = variable_set(tree)
    print(f"  Variables: {{{', '.join(sorted(vs))}}}" if vs else "  (no variables)")


def _cmd_help(_args):
    print(__doc__)


# Higher-order dispatch table — maps command names to handler functions
_COMMANDS = {
    ":parse":    _cmd_parse,
    ":eval":     _cmd_eval,
    ":diff":     _cmd_diff,
    ":simplify": _cmd_simplify,
    ":vars":     _cmd_vars,
    ":help":     _cmd_help,
}


def _dispatch(line: str):
    """Route a REPL *line* to the appropriate handler using the dispatch table."""
    stripped = line.strip()
    if not stripped:
        return

    # check for commands
    for cmd, handler in _COMMANDS.items():
        if stripped.startswith(cmd):
            handler(stripped[len(cmd):].strip())
            return

    # default: parse → simplify → print
    try:
        result = pipe(parse, simplify, to_string)(stripped)
        print(f"  → {result}")
    except (SyntaxError, ValueError, TypeError) as exc:
        print(f"  Error: {exc}")


# ── REPL loop ─────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════╗
║   Functional Equation Parser & Analyzer                  ║
║   Type an expression, or :help for commands.             ║
║   :quit to exit.                                         ║
╚══════════════════════════════════════════════════════════╝
"""


def _repl_lines():
    """Generator that yields user input lines until :quit or EOF."""
    while True:
        try:
            line = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line.strip() in (":quit", ":q"):
            return
        yield line


def main():
    print(BANNER)
    # consume the generator of REPL lines, dispatching each one
    # using the higher-order ``_dispatch`` function
    consume = lambda gen: reduce(lambda _, line: _dispatch(line), gen, None)
    consume(_repl_lines())
    print("Goodbye!")


if __name__ == "__main__":
    main()
