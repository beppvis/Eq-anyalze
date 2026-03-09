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
  :plot     <expr> [lo:hi] Plot expression (e.g. :plot x^2 [-5:5])
  :plotm    <e1>, <e2>, …  Plot multiple expressions overlaid
  :plotd    <expr> [lo:hi] Plot expression and its derivative
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
from equation_parser.plotter import (
    plot_expression, plot_multiple, plot_with_derivative, parse_range,
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


def _cmd_plot(args):
    """Plot a single expression.  Optional range: :plot x^2 [-5:5]"""
    expr_str, rng = parse_range(args)
    if not expr_str:
        print("  Usage: :plot <expr> [lo:hi]")
        return
    try:
        kw = {"x_range": rng} if rng else {}
        plot_expression(expr_str, **kw)
    except Exception as exc:
        print(f"  Plot error: {exc}")


def _cmd_plotm(args):
    """Plot multiple comma-separated expressions overlaid."""
    exprs = [e.strip() for e in args.split(",") if e.strip()]
    if not exprs:
        print("  Usage: :plotm <expr1>, <expr2>, ...")
        return
    try:
        plot_multiple(exprs)
    except Exception as exc:
        print(f"  Plot error: {exc}")


def _cmd_plotd(args):
    """Plot an expression together with its derivative."""
    expr_str, rng = parse_range(args)
    if not expr_str:
        print("  Usage: :plotd <expr> [lo:hi]")
        return
    try:
        kw = {"x_range": rng} if rng else {}
        plot_with_derivative(expr_str, **kw)
    except Exception as exc:
        print(f"  Plot error: {exc}")


def _cmd_help(_args):
    print(__doc__)


# Higher-order dispatch table — maps command names to handler functions
_COMMANDS = {
    ":parse":    _cmd_parse,
    ":eval":     _cmd_eval,
    ":diff":     _cmd_diff,
    ":simplify": _cmd_simplify,
    ":vars":     _cmd_vars,
    ":plot":     _cmd_plot,
    ":plotm":    _cmd_plotm,
    ":plotd":    _cmd_plotd,
    ":help":     _cmd_help,
}


def _dispatch(line: str):
    """Route a REPL *line* to the appropriate handler using the dispatch table."""
    stripped = line.strip()
    if not stripped:
        return

    # check for commands — sort longest-first so :plotm/:plotd match before :plot
    for cmd, handler in sorted(_COMMANDS.items(), key=lambda c: -len(c[0])):
        if stripped.startswith(cmd) and (
            len(stripped) == len(cmd) or stripped[len(cmd)] == " "
        ):
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
╠══════════════════════════════════════════════════════════╣
║   📈  :plot x^2          Plot an expression              ║
║   📊  :plotm x^2, sin(x) Overlay multiple plots          ║
║   📉  :plotd x^3         Plot with derivative             ║
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
