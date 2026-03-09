# Functional Equation Parser & Analyzer

A purely functional Python equation parser and analyzer built with **higher-order functions**, **iterators**, and **generators** — no classes for logic.

## Features

| Feature | Functional Technique |
|---|---|
| **Tokenize** | Generator (`yield`) lazily produces tokens |
| **Parse** | Higher-order `_parse_binary` factory for operator precedence |
| **Evaluate** | Dispatch-table of `type → handler` lambdas |
| **Variables** | Generator with `yield from` recursive traversal |
| **Differentiate** | Pure recursive function (sum, product, quotient, power, chain rules) |
| **Simplify** | `fixed_point` combinator applies rules until stable |
| **Pipeline** | `pipe()` / `compose()` chain transformations |

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

### REPL Commands

```
>>> 2 * x + 3                 # parse → simplify → print
>>> :eval 2 * x + 3           # evaluate (prompts for x)
>>> :diff x^3 + 2*x  x        # symbolic derivative
>>> :simplify 0 + x * 1       # simplify
>>> :vars sin(x) + y^2        # list variables
>>> :parse (1 + 2) * 3        # show AST
>>> :help                      # show help
>>> :quit                      # exit
```

## Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```
equation_parser/
├── __init__.py      # public API
├── ast_nodes.py     # namedtuple AST definitions
├── tokenizer.py     # generator-based lexer
├── parser.py        # recursive descent (higher-order)
├── analyzer.py      # eval, diff, simplify, to_string
└── utils.py         # compose, pipe, curry, fixed_point
main.py              # interactive REPL
tests/
└── test_equation.py # pytest suite
```

## Functional Programming Highlights

- **No classes** for logic — only `namedtuple` for data and pure functions for behavior
- **Generators** for lazy tokenization and recursive variable collection
- **Higher-order functions** everywhere: dispatch tables, `_parse_binary` factory, `pipe`/`compose`, `curry`, `fixed_point`
- **Immutable data** — AST nodes are namedtuples (frozen), environment dicts are never mutated
