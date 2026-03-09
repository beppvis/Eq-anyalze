"""
Comprehensive tests for the Functional Equation Parser & Analyzer.

Run with:  pytest tests/ -v
"""

import math
import pytest
from equation_parser.tokenizer import tokenize, Token, NUMBER, IDENT, OP, LPAREN, RPAREN, EQUALS, EOF
from equation_parser.parser import parse
from equation_parser.ast_nodes import Number, Variable, BinOp, UnaryOp, FuncCall, Equation
from equation_parser.analyzer import to_string, evaluate, differentiate, simplify, variables, variable_set
from equation_parser.utils import compose, pipe, curry, fixed_point, fmap, ffilter, freduce


# ═══════════════════════════════════════════════════════════════════════════
#  Utility tests
# ═══════════════════════════════════════════════════════════════════════════

class TestUtils:
    def test_compose(self):
        add1 = lambda x: x + 1
        double = lambda x: x * 2
        assert compose(add1, double)(3) == 7   # add1(double(3))

    def test_pipe(self):
        add1 = lambda x: x + 1
        double = lambda x: x * 2
        assert pipe(add1, double)(3) == 8      # double(add1(3))

    def test_curry(self):
        @curry
        def add(a, b):
            return a + b
        assert add(2)(3) == 5

    def test_fixed_point_converges(self):
        # f(x) = x // 2 reaches 0 quickly
        result = fixed_point(lambda x: x // 2, 100)
        assert result == 0

    def test_fixed_point_identity(self):
        assert fixed_point(lambda x: x, 42) == 42

    def test_fmap(self):
        double = lambda x: x * 2
        result = list(fmap(double)([1, 2, 3]))
        assert result == [2, 4, 6]

    def test_ffilter(self):
        is_even = lambda x: x % 2 == 0
        result = list(ffilter(is_even)([1, 2, 3, 4]))
        assert result == [2, 4]

    def test_freduce(self):
        add = lambda a, b: a + b
        result = freduce(add)([1, 2, 3, 4])
        assert result == 10
        
    def test_pipeline_with_higher_order(self):
        # fmap, ffilter, and freduce all work smoothly with pipe
        add = lambda a, b: a + b
        is_even = lambda x: x % 2 == 0
        double = lambda x: x * 2
        
        sum_of_doubled_evens = pipe(
            ffilter(is_even),
            fmap(double),
            freduce(add)
        )
        assert sum_of_doubled_evens([1, 2, 3, 4, 5]) == 12  # filter gives [2, 4], map gives [4, 8], reduce gives 12


# ═══════════════════════════════════════════════════════════════════════════
#  Tokenizer tests
# ═══════════════════════════════════════════════════════════════════════════

class TestTokenizer:
    def test_simple_expression(self):
        tokens = list(tokenize("2*x + 3"))
        kinds = [t.kind for t in tokens]
        assert kinds == [NUMBER, OP, IDENT, OP, NUMBER, EOF]

    def test_float_literal(self):
        tokens = list(tokenize("3.14"))
        assert tokens[0] == Token(NUMBER, 3.14)

    def test_equation(self):
        tokens = list(tokenize("x = 5"))
        kinds = [t.kind for t in tokens]
        assert kinds == [IDENT, EQUALS, NUMBER, EOF]

    def test_parentheses(self):
        tokens = list(tokenize("(a + b)"))
        kinds = [t.kind for t in tokens]
        assert kinds == [LPAREN, IDENT, OP, IDENT, RPAREN, EOF]

    def test_function_call(self):
        tokens = list(tokenize("sin(x)"))
        kinds = [t.kind for t in tokens]
        assert kinds == [IDENT, LPAREN, IDENT, RPAREN, EOF]

    def test_unexpected_char(self):
        with pytest.raises(SyntaxError):
            list(tokenize("2 & 3"))

    def test_is_generator(self):
        gen = tokenize("1 + 2")
        assert hasattr(gen, "__next__")   # it's a generator


# ═══════════════════════════════════════════════════════════════════════════
#  Parser tests
# ═══════════════════════════════════════════════════════════════════════════

class TestParser:
    def test_number(self):
        assert parse("42") == Number(42)

    def test_variable(self):
        assert parse("x") == Variable("x")

    def test_addition(self):
        tree = parse("1 + 2")
        assert tree == BinOp("+", Number(1), Number(2))

    def test_precedence_mul_over_add(self):
        tree = parse("1 + 2 * 3")
        # should be 1 + (2*3)
        assert tree == BinOp("+", Number(1), BinOp("*", Number(2), Number(3)))

    def test_parentheses_override(self):
        tree = parse("(1 + 2) * 3")
        assert tree == BinOp("*", BinOp("+", Number(1), Number(2)), Number(3))

    def test_power(self):
        tree = parse("x ^ 3")
        assert tree == BinOp("^", Variable("x"), Number(3))

    def test_unary_minus(self):
        tree = parse("-x")
        assert tree == UnaryOp("-", Variable("x"))

    def test_function_call(self):
        tree = parse("sin(x)")
        assert tree == FuncCall("sin", Variable("x"))

    def test_equation(self):
        tree = parse("2*x + 1 = 5")
        assert isinstance(tree, Equation)

    def test_nested_functions(self):
        tree = parse("sin(cos(x))")
        assert tree == FuncCall("sin", FuncCall("cos", Variable("x")))

    def test_roundtrip(self):
        exprs = ["((2 * x) + 3)", "(x ^ 3)", "sin(x)", "(-x)"]
        for expr in exprs:
            assert to_string(parse(expr)) == expr


# ═══════════════════════════════════════════════════════════════════════════
#  Analyzer — to_string
# ═══════════════════════════════════════════════════════════════════════════

class TestToString:
    def test_number(self):
        assert to_string(Number(5)) == "5"

    def test_binop(self):
        assert to_string(BinOp("+", Number(1), Number(2))) == "(1 + 2)"

    def test_func(self):
        assert to_string(FuncCall("sin", Variable("x"))) == "sin(x)"


# ═══════════════════════════════════════════════════════════════════════════
#  Analyzer — variables (generator)
# ═══════════════════════════════════════════════════════════════════════════

class TestVariables:
    def test_no_variables(self):
        assert variable_set(parse("2 + 3")) == frozenset()

    def test_single_variable(self):
        assert variable_set(parse("x + 1")) == frozenset({"x"})

    def test_multiple_variables(self):
        assert variable_set(parse("x + y * z")) == frozenset({"x", "y", "z"})

    def test_variables_is_generator(self):
        gen = variables(parse("x + y"))
        assert hasattr(gen, "__next__")

    def test_function_variables(self):
        assert variable_set(parse("sin(x) + y")) == frozenset({"x", "y"})


# ═══════════════════════════════════════════════════════════════════════════
#  Analyzer — evaluate
# ═══════════════════════════════════════════════════════════════════════════

class TestEvaluate:
    def test_constant(self):
        assert evaluate(parse("2 + 3"), {}) == 5.0

    def test_variable(self):
        assert evaluate(parse("x + 1"), {"x": 4}) == 5.0

    def test_complex_expression(self):
        assert evaluate(parse("2 * x + 3"), {"x": 5}) == 13.0

    def test_power(self):
        assert evaluate(parse("x ^ 3"), {"x": 2}) == 8.0

    def test_sin(self):
        result = evaluate(parse("sin(x)"), {"x": 0})
        assert abs(result) < 1e-10

    def test_missing_variable_raises(self):
        with pytest.raises(NameError):
            evaluate(parse("x + 1"), {})

    def test_division(self):
        assert evaluate(parse("10 / 2"), {}) == 5.0

    def test_nested_functions(self):
        result = evaluate(parse("exp(ln(2))"), {})
        assert abs(result - 2.0) < 1e-10


# ═══════════════════════════════════════════════════════════════════════════
#  Analyzer — differentiation
# ═══════════════════════════════════════════════════════════════════════════

class TestDifferentiate:
    def test_constant(self):
        d = differentiate(parse("5"), "x")
        assert d == Number(0)

    def test_identity(self):
        d = simplify(differentiate(parse("x"), "x"))
        assert d == Number(1)

    def test_power_rule(self):
        d = simplify(differentiate(parse("x ^ 3"), "x"))
        # 3 * x^2
        expected_val = evaluate(d, {"x": 2})
        assert expected_val == 12.0   # 3 * 4

    def test_sum_rule(self):
        d = simplify(differentiate(parse("x + x"), "x"))
        assert evaluate(d, {"x": 0}) == 2.0

    def test_product_rule(self):
        # d/dx (x * x) = 2x
        d = simplify(differentiate(parse("x * x"), "x"))
        assert evaluate(d, {"x": 3}) == 6.0

    def test_chain_rule_sin(self):
        # d/dx sin(x) = cos(x)
        d = simplify(differentiate(parse("sin(x)"), "x"))
        result = evaluate(d, {"x": 0})
        assert abs(result - 1.0) < 1e-10   # cos(0) = 1

    def test_diff_wrt_other_var(self):
        d = differentiate(parse("x ^ 2"), "y")
        d = simplify(d)
        assert evaluate(d, {"x": 5}) == 0.0


# ═══════════════════════════════════════════════════════════════════════════
#  Analyzer — simplification
# ═══════════════════════════════════════════════════════════════════════════

class TestSimplify:
    def test_zero_plus_x(self):
        assert to_string(simplify(parse("0 + x"))) == "x"

    def test_x_plus_zero(self):
        assert to_string(simplify(parse("x + 0"))) == "x"

    def test_one_times_x(self):
        assert to_string(simplify(parse("1 * x"))) == "x"

    def test_x_times_one(self):
        assert to_string(simplify(parse("x * 1"))) == "x"

    def test_x_times_zero(self):
        assert to_string(simplify(parse("x * 0"))) == "0"

    def test_zero_times_x(self):
        assert to_string(simplify(parse("0 * x"))) == "0"

    def test_x_minus_x(self):
        assert to_string(simplify(parse("x - x"))) == "0"

    def test_x_to_power_1(self):
        assert to_string(simplify(parse("x ^ 1"))) == "x"

    def test_x_to_power_0(self):
        assert to_string(simplify(parse("x ^ 0"))) == "1"

    def test_constant_folding(self):
        assert to_string(simplify(parse("2 + 3"))) == "5"

    def test_nested_simplification(self):
        assert to_string(simplify(parse("0 + x * 1"))) == "x"

    def test_double_negation(self):
        tree = UnaryOp("-", UnaryOp("-", Variable("x")))
        assert to_string(simplify(tree)) == "x"


# ═══════════════════════════════════════════════════════════════════════════
#  Pipeline (pipe / compose) integration
# ═══════════════════════════════════════════════════════════════════════════

class TestPipeline:
    def test_parse_simplify_tostring(self):
        pipeline = pipe(parse, simplify, to_string)
        assert pipeline("0 + x * 1") == "x"

    def test_diff_pipeline(self):
        pipeline = pipe(
            parse,
            lambda n: differentiate(n, "x"),
            simplify,
            to_string,
        )
        result = pipeline("x ^ 2")
        # should be 2*x  (or equivalent)
        tree = parse(result)
        assert evaluate(tree, {"x": 3}) == 6.0
