
from compiler.parser import parse
from compiler.validator import validate


class TestValidatorAllowed:
    def test_assignment(self):
        assert validate(parse("x = 1")) == []

    def test_arithmetic(self):
        assert validate(parse("x = 1 + 2 * 3")) == []

    def test_comparison(self):
        assert validate(parse("x = 1 > 0")) == []

    def test_allowed_function_call(self):
        assert validate(parse("print('hello')")) == []

    def test_allowed_builtin_functions(self):
        assert validate(parse("x = len([1,2,3])")) == []
        assert validate(parse("x = abs(-5)")) == []
        assert validate(parse("x = int(3.5)")) == []

    def test_list_dict_literals(self):
        assert validate(parse("x = [1, 2, 3]")) == []
        assert validate(parse("x = {'a': 1}")) == []

    def test_for_loop(self):
        assert validate(parse("for i in range(10):\n  x = i")) == []

    def test_if_statement(self):
        assert validate(parse("if True:\n  x = 1")) == []

    def test_fstring(self):
        assert validate(parse("x = f'value: {1 + 2}'")) == []

    def test_list_comprehension(self):
        assert validate(parse("x = [i * 2 for i in range(10)]")) == []

    def test_domain_functions(self):
        assert validate(parse("d = get_dataset()")) == []
        assert validate(parse("r = B(dataset=d, band_no=3)")) == []
        assert validate(parse("response = setup(r)")) == []

    def test_attribute_access(self):
        assert validate(parse("x = obj.band")) == []
        assert validate(parse("x = obj.mean()")) == []


class TestValidatorBlocked:
    def test_import(self):
        errors = validate(parse("import os"))
        assert len(errors) == 1
        assert "Import" in str(errors[0])

    def test_from_import(self):
        errors = validate(parse("from os import path"))
        assert len(errors) == 1

    def test_exec_call(self):
        errors = validate(parse("exec('print(1)')"))
        assert len(errors) >= 1

    def test_eval_call(self):
        errors = validate(parse("eval('1+1')"))
        assert len(errors) >= 1

    def test_open_call(self):
        errors = validate(parse("open('/etc/passwd')"))
        assert len(errors) >= 1

    def test_dunder_access(self):
        errors = validate(parse("x = obj.__class__"))
        assert len(errors) >= 1

    def test_private_attribute(self):
        errors = validate(parse("x = obj._private"))
        assert len(errors) >= 1

    def test_function_definition(self):
        errors = validate(parse("def foo():\n  pass"))
        assert len(errors) >= 1

    def test_class_definition(self):
        errors = validate(parse("class Foo:\n  pass"))
        assert len(errors) >= 1

    def test_globals_access(self):
        errors = validate(parse("x = globals()"))
        assert len(errors) >= 1

    def test_getattr_call(self):
        errors = validate(parse("x = getattr(obj, 'attr')"))
        assert len(errors) >= 1

    def test_multiple_errors(self):
        source = "import os\nexec('x')\neval('y')"
        errors = validate(parse(source))
        assert len(errors) >= 3

    def test_try_except(self):
        errors = validate(parse("try:\n  x = 1\nexcept:\n  pass"))
        assert len(errors) >= 1

    def test_raise(self):
        errors = validate(parse("raise ValueError()"))
        assert len(errors) >= 1

    def test_dunder_name(self):
        errors = validate(parse("x = __import__('os')"))
        assert len(errors) >= 1
