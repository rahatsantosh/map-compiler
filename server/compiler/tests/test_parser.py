import ast

import pytest

from compiler.parser import parse, ParseError


class TestParse:
    def test_valid_assignment(self):
        tree = parse("x = 1 + 2")
        assert isinstance(tree, ast.Module)
        assert len(tree.body) == 1

    def test_valid_multiline(self):
        tree = parse("x = 1\ny = x + 2\nprint(y)")
        assert len(tree.body) == 3

    def test_syntax_error_raises_parse_error(self):
        with pytest.raises(ParseError):
            parse("x = ")

    def test_parse_error_has_line_number(self):
        with pytest.raises(ParseError) as exc_info:
            parse("x = 1\ny = \n")
        assert exc_info.value.line is not None

    def test_empty_source(self):
        tree = parse("")
        assert isinstance(tree, ast.Module)
        assert len(tree.body) == 0

    def test_function_call(self):
        tree = parse("print('hello')")
        assert isinstance(tree.body[0], ast.Expr)
        assert isinstance(tree.body[0].value, ast.Call)
