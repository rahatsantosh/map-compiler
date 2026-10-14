from typing import Any

from .executor import ExecutionError, ScriptExecutor
from .parser import ParseError, parse
from .validator import validate


class CompilationError(Exception):
    def __init__(self, message: str, line: int | None = None):
        self.line = line
        super().__init__(message)


def compile_and_execute(
    source: str,
    env: dict[str, Any],
) -> dict[str, Any]:
    try:
        tree = parse(source)
    except ParseError as e:
        return {"console": str(e), "response": None, "graph": None, "error": True}

    errors = validate(tree)
    if errors:
        messages = [f"Line {e.line}: {e}" if e.line else str(e) for e in errors]
        return {
            "console": "\n".join(messages),
            "response": None,
            "graph": None,
            "error": True,
        }

    executor = ScriptExecutor(env)
    try:
        result = executor.execute(tree)
        result["error"] = False
        return result
    except ExecutionError as e:
        msg = f"Line {e.line}: {e}" if e.line else str(e)
        return {"console": msg, "response": None, "graph": None, "error": True}
    except Exception as e:
        return {"console": str(e), "response": None, "graph": None, "error": True}
