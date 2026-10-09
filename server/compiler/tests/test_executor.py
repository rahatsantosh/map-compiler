import pytest

from compiler.parser import parse
from compiler.executor import ScriptExecutor, ExecutionError


def run(source: str, env: dict | None = None) -> dict:
    tree = parse(source)
    executor = ScriptExecutor(env or {})
    return executor.execute(tree)


class TestExecutorBasic:
    def test_assignment(self):
        result = run("x = 42")
        assert result["response"] is None

    def test_arithmetic(self):
        executor = ScriptExecutor({})
        tree = parse("x = 2 + 3 * 4")
        executor.execute(tree)
        assert executor.env["x"] == 14

    def test_print_captured(self):
        result = run("print('hello')", {"print": print})
        assert result["console"] == "hello\n"

    def test_multiple_prints(self):
        result = run("print('a')\nprint('b')", {"print": print})
        assert result["console"] == "a\nb\n"

    def test_variable_reuse(self):
        executor = ScriptExecutor({})
        tree = parse("x = 10\ny = x + 5")
        executor.execute(tree)
        assert executor.env["y"] == 15

    def test_response_variable(self):
        result = run("response = 'tile_data'")
        assert result["response"] == "tile_data"

    def test_graph_variable(self):
        result = run("graph = {'type': 'bar'}")
        assert result["graph"] == {"type": "bar"}

    def test_no_console_output(self):
        result = run("x = 1")
        assert result["console"] is None


class TestExecutorOperators:
    def test_comparison(self):
        executor = ScriptExecutor({})
        tree = parse("x = 5 > 3")
        executor.execute(tree)
        assert executor.env["x"] is True

    def test_boolean_ops(self):
        executor = ScriptExecutor({})
        tree = parse("x = True and False")
        executor.execute(tree)
        assert executor.env["x"] is False

    def test_unary_ops(self):
        executor = ScriptExecutor({})
        tree = parse("x = -5\ny = not True")
        executor.execute(tree)
        assert executor.env["x"] == -5
        assert executor.env["y"] is False

    def test_augmented_assignment(self):
        executor = ScriptExecutor({})
        tree = parse("x = 10\nx += 5")
        executor.execute(tree)
        assert executor.env["x"] == 15

    def test_floor_division(self):
        executor = ScriptExecutor({})
        tree = parse("x = 7 // 2")
        executor.execute(tree)
        assert executor.env["x"] == 3

    def test_modulo(self):
        executor = ScriptExecutor({})
        tree = parse("x = 10 % 3")
        executor.execute(tree)
        assert executor.env["x"] == 1

    def test_power(self):
        executor = ScriptExecutor({})
        tree = parse("x = 2 ** 8")
        executor.execute(tree)
        assert executor.env["x"] == 256


class TestExecutorControlFlow:
    def test_if_true(self):
        executor = ScriptExecutor({})
        tree = parse("x = 0\nif True:\n  x = 1")
        executor.execute(tree)
        assert executor.env["x"] == 1

    def test_if_false_else(self):
        executor = ScriptExecutor({})
        tree = parse("if False:\n  x = 1\nelse:\n  x = 2")
        executor.execute(tree)
        assert executor.env["x"] == 2

    def test_for_loop(self):
        executor = ScriptExecutor({"range": range})
        tree = parse("total = 0\nfor i in range(5):\n  total += i")
        executor.execute(tree)
        assert executor.env["total"] == 10

    def test_while_loop(self):
        executor = ScriptExecutor({})
        tree = parse("x = 0\nwhile x < 5:\n  x += 1")
        executor.execute(tree)
        assert executor.env["x"] == 5

    def test_ternary(self):
        executor = ScriptExecutor({})
        tree = parse("x = 'yes' if True else 'no'")
        executor.execute(tree)
        assert executor.env["x"] == "yes"


class TestExecutorCollections:
    def test_list(self):
        executor = ScriptExecutor({})
        tree = parse("x = [1, 2, 3]")
        executor.execute(tree)
        assert executor.env["x"] == [1, 2, 3]

    def test_dict(self):
        executor = ScriptExecutor({})
        tree = parse("x = {'a': 1, 'b': 2}")
        executor.execute(tree)
        assert executor.env["x"] == {"a": 1, "b": 2}

    def test_tuple(self):
        executor = ScriptExecutor({})
        tree = parse("x = (1, 2)")
        executor.execute(tree)
        assert executor.env["x"] == (1, 2)

    def test_subscript(self):
        executor = ScriptExecutor({})
        tree = parse("x = [10, 20, 30]\ny = x[1]")
        executor.execute(tree)
        assert executor.env["y"] == 20

    def test_slice(self):
        executor = ScriptExecutor({})
        tree = parse("x = [1,2,3,4,5]\ny = x[1:3]")
        executor.execute(tree)
        assert executor.env["y"] == [2, 3]

    def test_list_comprehension(self):
        executor = ScriptExecutor({"range": range})
        tree = parse("x = [i * 2 for i in range(4)]")
        executor.execute(tree)
        assert executor.env["x"] == [0, 2, 4, 6]

    def test_dict_access(self):
        executor = ScriptExecutor({})
        tree = parse("d = {'key': 42}\nx = d['key']")
        executor.execute(tree)
        assert executor.env["x"] == 42


class TestExecutorFunctions:
    def test_builtin_call(self):
        executor = ScriptExecutor({"len": len})
        tree = parse("x = len([1, 2, 3])")
        executor.execute(tree)
        assert executor.env["x"] == 3

    def test_custom_function_in_env(self):
        def double(x):
            return x * 2

        executor = ScriptExecutor({"double": double})
        tree = parse("x = double(21)")
        executor.execute(tree)
        assert executor.env["x"] == 42

    def test_method_call(self):
        executor = ScriptExecutor({})
        tree = parse("x = [1, 2, 3]\ny = x.copy()")
        executor.execute(tree)
        assert executor.env["y"] == [1, 2, 3]

    def test_kwargs(self):
        def greet(name="world"):
            return f"hello {name}"

        executor = ScriptExecutor({"greet": greet})
        tree = parse("x = greet(name='test')")
        executor.execute(tree)
        assert executor.env["x"] == "hello test"


class TestExecutorErrors:
    def test_undefined_variable(self):
        with pytest.raises(ExecutionError, match="Undefined variable"):
            run("x = y + 1")

    def test_division_by_zero(self):
        with pytest.raises(ZeroDivisionError):
            run("x = 1 / 0")

    def test_attribute_on_none(self):
        with pytest.raises(AttributeError):
            run("x = None\ny = x.something")


class TestExecutorFString:
    def test_basic_fstring(self):
        executor = ScriptExecutor({})
        tree = parse("x = 42\ny = f'value is {x}'")
        executor.execute(tree)
        assert executor.env["y"] == "value is 42"

    def test_fstring_with_expr(self):
        executor = ScriptExecutor({})
        tree = parse("y = f'sum: {1 + 2}'")
        executor.execute(tree)
        assert executor.env["y"] == "sum: 3"
