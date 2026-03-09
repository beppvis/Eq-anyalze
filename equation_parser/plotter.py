"""
Plotter — MATLAB-style equation plotting using matplotlib.

Provides pure functions for plotting parsed expressions over a variable range.
Integrates with the existing parser, evaluator, and differentiator.
"""

import numpy as np
import matplotlib.pyplot as plt

from .parser import parse
from .analyzer import evaluate, differentiate, simplify, to_string, variable_set


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _safe_eval(tree, var, x_val):
    """Evaluate *tree* at a single point, returning np.nan on math errors."""
    try:
        return evaluate(tree, {var: float(x_val)})
    except (ValueError, ZeroDivisionError, OverflowError, NameError):
        return np.nan


def _vectorized_eval(tree, var, xs):
    """Evaluate *tree* over a NumPy array *xs*, handling domain errors gracefully."""
    return np.array([_safe_eval(tree, var, x) for x in xs])


def _resolve_variable(tree, var=None):
    """Determine which variable to plot against.

    If *var* is given, use it.  Otherwise, auto-detect from the expression
    (must contain exactly one variable).
    """
    if var is not None:
        return var
    vs = variable_set(tree)
    if len(vs) == 0:
        return "x"  # constant expression — still plottable
    if len(vs) == 1:
        return next(iter(vs))
    raise ValueError(
        f"Expression has multiple variables {set(vs)}. "
        "Specify which one to plot against."
    )


def _apply_style(ax, title=None):
    """Apply a consistent MATLAB-inspired visual style to *ax*."""
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.axvline(0, color="black", linewidth=0.5)
    if title:
        ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.legend(fontsize=10, framealpha=0.9)


# ═══════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════

def plot_expression(expr_str, var=None, x_range=(-10, 10), num_points=500):
    """Plot a single expression string.

    Parameters
    ----------
    expr_str : str
        The mathematical expression, e.g. ``"x^2 - 3*x + 2"``.
    var : str or None
        Variable to sweep.  Auto-detected if the expression has one variable.
    x_range : tuple(float, float)
        ``(x_min, x_max)`` range for the independent variable.
    num_points : int
        Number of sample points across the range.

    Returns
    -------
    matplotlib.figure.Figure
        The figure object (also shown via ``plt.show``).
    """
    tree = parse(expr_str)
    var = _resolve_variable(tree, var)

    xs = np.linspace(x_range[0], x_range[1], num_points)
    ys = _vectorized_eval(tree, var, xs)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(xs, ys, linewidth=2, label=f"f({var}) = {expr_str}")
    ax.set_xlabel(var, fontsize=12)
    ax.set_ylabel(f"f({var})", fontsize=12)
    _apply_style(ax, title=expr_str)
    plt.tight_layout()
    plt.show()
    return fig


def plot_multiple(expr_list, var=None, x_range=(-10, 10), num_points=500):
    """Overlay multiple expressions on one plot (like MATLAB ``hold on``).

    Parameters
    ----------
    expr_list : list[str]
        List of expression strings to plot.
    var : str or None
        Variable to sweep (auto-detected from first expression if None).
    x_range : tuple(float, float)
        ``(x_min, x_max)`` range.
    num_points : int
        Number of sample points across the range.

    Returns
    -------
    matplotlib.figure.Figure
    """
    if not expr_list:
        raise ValueError("Need at least one expression to plot.")

    trees = [parse(e.strip()) for e in expr_list]

    # resolve variable from the first expression with a variable
    if var is None:
        for t in trees:
            vs = variable_set(t)
            if vs:
                var = next(iter(vs))
                break
        if var is None:
            var = "x"

    xs = np.linspace(x_range[0], x_range[1], num_points)

    fig, ax = plt.subplots(figsize=(9, 6))
    colors = plt.cm.Set1.colors  # vivid color cycle
    for i, (expr_str, tree) in enumerate(zip(expr_list, trees)):
        ys = _vectorized_eval(tree, var, xs)
        color = colors[i % len(colors)]
        ax.plot(xs, ys, linewidth=2, color=color,
                label=f"{expr_str.strip()}")

    ax.set_xlabel(var, fontsize=12)
    ax.set_ylabel(f"f({var})", fontsize=12)
    _apply_style(ax, title="Multiple Expressions")
    plt.tight_layout()
    plt.show()
    return fig


def plot_with_derivative(expr_str, var=None, x_range=(-10, 10), num_points=500):
    """Plot an expression **and** its symbolic derivative on the same axes.

    Parameters
    ----------
    expr_str : str
        The mathematical expression.
    var : str or None
        Variable to differentiate with respect to.
    x_range : tuple(float, float)
        ``(x_min, x_max)`` range.
    num_points : int
        Number of sample points across the range.

    Returns
    -------
    matplotlib.figure.Figure
    """
    tree = parse(expr_str)
    var = _resolve_variable(tree, var)

    d_tree = simplify(differentiate(tree, var))
    d_str = to_string(d_tree)

    xs = np.linspace(x_range[0], x_range[1], num_points)
    ys = _vectorized_eval(tree, var, xs)
    dys = _vectorized_eval(d_tree, var, xs)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(xs, ys, linewidth=2, label=f"f({var}) = {expr_str}", color="#2563EB")
    ax.plot(xs, dys, linewidth=2, linestyle="--",
            label=f"f'({var}) = {d_str}", color="#DC2626")

    ax.set_xlabel(var, fontsize=12)
    ax.set_ylabel("y", fontsize=12)
    _apply_style(ax, title=f"{expr_str}  and its derivative")
    plt.tight_layout()
    plt.show()
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  Range parser  (used by the REPL)
# ═══════════════════════════════════════════════════════════════════════════

def parse_range(text):
    """Parse an optional ``[-5:5]`` suffix from a REPL argument string.

    Returns ``(expression_str, (x_min, x_max))`` or ``(expression_str, None)``
    if no range was given.

    >>> parse_range("x^2 [-5:5]")
    ('x^2', (-5.0, 5.0))
    >>> parse_range("sin(x)")
    ('sin(x)', None)
    """
    text = text.strip()
    if text.endswith("]"):
        bracket_start = text.rfind("[")
        if bracket_start != -1:
            range_str = text[bracket_start + 1 : -1]
            parts = range_str.split(":")
            if len(parts) == 2:
                try:
                    lo, hi = float(parts[0]), float(parts[1])
                    return text[:bracket_start].strip(), (lo, hi)
                except ValueError:
                    pass
    return text, None
