import ast


class ParseError(Exception):
    def __init__(self, message: str, line: int | None = None):
        self.line = line
        super().__init__(message)


def parse(source: str) -> ast.Module:
    try:
        return ast.parse(source, mode="exec")
    except SyntaxError as e:
        raise ParseError(str(e), line=e.lineno) from e
