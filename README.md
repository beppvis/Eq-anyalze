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

## Functional Iteration Utilities Walkthrough

This guide explains how to use the newly added higher-order functional utilities inside the Equation Parser: `fmap`, `ffilter`, and `freduce`.

These utilities are strictly pure, functionally curried, and designed to compose seamlessly with the `pipe` and `compose` functions.

### 1. Importing the Utilities

All functional utilities are accessible directly from the `equation_parser` package:

```python
from equation_parser import fmap, ffilter, freduce, pipe, compose
```

### 2. Basic Usage

Because these functions are **curried** (using the `@curry` decorator in `utils.py`), you must call them with the function/predicate *first*, which returns a new function waiting for the iterable.

#### `fmap` (Map)
`fmap` applies a transformation function to every item in an iterable.

```python
double = lambda x: x * 2

# Step 1: Partially apply the transformation
map_double = fmap(double)

# Step 2: Provide the iterable
result = map_double([1, 2, 3])

# Since fmap returns an iterator, cast to a list to view it
print(list(result))  # Output: [2, 4, 6]
```

#### `ffilter` (Filter)
`ffilter` keeps only elements from an iterable that satisfy a predicate function.

```python
is_even = lambda x: x % 2 == 0

# Partially applied
filter_evens = ffilter(is_even)

result = filter_evens([1, 2, 3, 4, 5])
print(list(result))  # Output: [2, 4]
```

#### `freduce` (Reduce)
`freduce` continuously applies a function of two arguments strictly left-to-right to the items of the iterable, reducing it to a single value.

```python
add = lambda a, b: a + b

sum_all = freduce(add)

result = sum_all([1, 2, 3, 4])
print(result)  # Output: 10
```

### 3. Advanced Usage: Pipelining

The true power of functionally curried parameters is that they integrate natively into data pipelines without lambda wrappers.

By combining them with `pipe` (left-to-right function application), you can build readable and expressive data processing pipelines.

```python
from equation_parser import pipe, fmap, ffilter, freduce

# 1. Define pure operational functions
add = lambda a, b: a + b
is_even = lambda x: x % 2 == 0
double = lambda x: x * 2

# 2. Construct the pipeline using pipe
sum_of_doubled_evens = pipe(
    ffilter(is_even),  # [1, 2, 3, 4, 5] -> [2, 4]
    fmap(double),      # [2, 4] -> [4, 8]
    freduce(add)       # [4, 8] -> 12
)

# 3. Execute the pipeline
print(sum_of_doubled_evens([1, 2, 3, 4, 5]))  
# Output: 12
```

### 4. Integration with Expression Trees

Because the `Analyzer` evaluates purely numeric values, you can run AST transformations before passing the variables to evaluating functions:

```python
from equation_parser import parse, simplify, pipe, fmap

# Suppose we parsed multiple equations and want to simplify them all
expressions = ["0 + x * 1", "y * 0", "z - z"]
parsed_trees = list(fmap(parse)(expressions))

# Apply simplification over all trees at once
simplified_trees = list(fmap(simplify)(parsed_trees))
```

This ensures the purity and data-in, data-out philosophy of the existing architecture is maintained across lists of operations natively!
