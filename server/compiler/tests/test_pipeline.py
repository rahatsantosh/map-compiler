from compiler.pipeline import compile_and_execute


class TestPipelineSuccess:
    def test_simple_assignment(self):
        result = compile_and_execute("x = 1 + 2", {})
        assert result["error"] is False

    def test_print_output(self):
        result = compile_and_execute("print('hello')", {"print": print})
        assert result["console"] == "hello\n"
        assert result["error"] is False

    def test_response_captured(self):
        result = compile_and_execute("response = 'tile'", {})
        assert result["response"] == "tile"
        assert result["error"] is False

    def test_graph_captured(self):
        result = compile_and_execute("graph = {'type': 'bar'}", {})
        assert result["graph"] == {"type": "bar"}
        assert result["error"] is False

    def test_env_functions_available(self):
        result = compile_and_execute("x = len([1, 2, 3])\nresponse = x", {"len": len})
        assert result["response"] == 3
        assert result["error"] is False


class TestPipelineErrors:
    def test_syntax_error(self):
        result = compile_and_execute("x = ", {})
        assert result["error"] is True
        assert result["console"] is not None

    def test_validation_error_import(self):
        result = compile_and_execute("import os", {})
        assert result["error"] is True
        assert "Import" in result["console"]

    def test_validation_error_exec(self):
        result = compile_and_execute("exec('print(1)')", {})
        assert result["error"] is True

    def test_runtime_error(self):
        result = compile_and_execute("x = undefined_var", {})
        assert result["error"] is True
        assert "Undefined" in result["console"]

    def test_multiple_validation_errors(self):
        result = compile_and_execute("import os\nimport sys", {})
        assert result["error"] is True
        assert result["console"].count("Import") == 2


class TestPipelineSecurity:
    def test_blocks_file_access(self):
        result = compile_and_execute("f = open('/etc/passwd')", {})
        assert result["error"] is True

    def test_blocks_eval(self):
        result = compile_and_execute("x = eval('1+1')", {})
        assert result["error"] is True

    def test_blocks_dunder(self):
        result = compile_and_execute("x = ''.__class__", {})
        assert result["error"] is True

    def test_blocks_import(self):
        result = compile_and_execute("import subprocess", {})
        assert result["error"] is True

    def test_blocks_globals(self):
        result = compile_and_execute("x = globals()", {})
        assert result["error"] is True
