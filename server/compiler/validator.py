import ast

ALLOWED_FUNCTIONS = frozenset({
    "get_dataset",
    "B",
    "setup",
    "rasterPlot",
    "RandomForest",
    "RasterPCA",
    "print",
    "dict",
    "list",
    "int",
    "float",
    "str",
    "range",
    "len",
    "abs",
    "round",
    "min",
    "max",
    "sum",
    "sorted",
    "enumerate",
    "zip",
    "map",
    "filter",
    "bool",
    "tuple",
    "type",
})

ALLOWED_METHODS = frozenset({
    "mean",
    "max",
    "min",
    "std",
    "band",
    "conv2D",
    "fit",
    "transform",
    "fit_transform",
    "predict",
    "prediction_map",
    "append",
    "keys",
    "values",
    "items",
    "update",
    "get",
    "copy",
    "reshape",
    "ravel",
    "flatten",
    "T",
    "shape",
    "size",
    "dtype",
    "astype",
    "tolist",
})

BLOCKED_NAMES = frozenset({
    "exec",
    "eval",
    "compile",
    "open",
    "input",
    "__import__",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
    "hasattr",
    "breakpoint",
    "exit",
    "quit",
})

ALLOWED_NODE_TYPES = (
    ast.Module,
    ast.Expr,
    ast.Assign,
    ast.AugAssign,
    ast.AnnAssign,
    ast.Call,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.BoolOp,
    ast.IfExp,
    ast.If,
    ast.For,
    ast.While,
    ast.Break,
    ast.Continue,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Del,
    ast.Constant,
    ast.Attribute,
    ast.Subscript,
    ast.Index,
    ast.Slice,
    ast.Tuple,
    ast.List,
    ast.Dict,
    ast.Set,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.comprehension,
    ast.Starred,
    ast.keyword,
    ast.FormattedValue,
    ast.JoinedStr,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.BitAnd,
    ast.BitOr,
    ast.BitXor,
    ast.Invert,
    ast.Not,
    ast.UAdd,
    ast.USub,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Is,
    ast.IsNot,
    ast.In,
    ast.NotIn,
    ast.And,
    ast.Or,
    ast.Pass,
)


class ValidationError(Exception):
    def __init__(self, message: str, line: int | None = None):
        self.line = line
        super().__init__(message)


class ScriptValidator(ast.NodeVisitor):
    def __init__(self):
        self.errors: list[ValidationError] = []

    def _reject(self, message: str, node: ast.AST):
        line = getattr(node, "lineno", None)
        self.errors.append(ValidationError(message, line=line))

    def generic_visit(self, node: ast.AST):
        if not isinstance(node, ALLOWED_NODE_TYPES):
            self._reject(f"Disallowed syntax: {type(node).__name__}", node)
            return
        super().generic_visit(node)

    def visit_Import(self, node: ast.Import):
        self._reject("Import statements are not allowed", node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self._reject("Import statements are not allowed", node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._reject("Function definitions are not allowed", node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._reject("Async function definitions are not allowed", node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self._reject("Class definitions are not allowed", node)

    def visit_Delete(self, node: ast.Delete):
        self._reject("Delete statements are not allowed", node)

    def visit_Global(self, node: ast.Global):
        self._reject("Global statements are not allowed", node)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        self._reject("Nonlocal statements are not allowed", node)

    def visit_Raise(self, node: ast.Raise):
        self._reject("Raise statements are not allowed", node)

    def visit_Try(self, node: ast.Try):
        self._reject("Try/except blocks are not allowed", node)

    def visit_TryStar(self, node: ast.TryStar):
        self._reject("Try/except blocks are not allowed", node)

    def visit_With(self, node: ast.With):
        self._reject("With statements are not allowed", node)

    def visit_Assert(self, node: ast.Assert):
        self._reject("Assert statements are not allowed", node)

    def visit_Yield(self, node: ast.Yield):
        self._reject("Yield expressions are not allowed", node)

    def visit_YieldFrom(self, node: ast.YieldFrom):
        self._reject("Yield expressions are not allowed", node)

    def visit_Await(self, node: ast.Await):
        self._reject("Await expressions are not allowed", node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_NAMES:
                self._reject(f"Function '{node.func.id}' is not allowed", node)
            elif node.func.id not in ALLOWED_FUNCTIONS:
                self._reject(f"Unknown function '{node.func.id}'", node)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr.startswith("_"):
            self._reject(f"Access to private attribute '{node.attr}' is not allowed", node)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id.startswith("__") and node.id.endswith("__"):
            self._reject(f"Access to dunder name '{node.id}' is not allowed", node)
        if isinstance(node.ctx, ast.Load) and node.id in BLOCKED_NAMES:
            self._reject(f"Access to '{node.id}' is not allowed", node)
        self.generic_visit(node)


def validate(tree: ast.Module) -> list[ValidationError]:
    validator = ScriptValidator()
    validator.visit(tree)
    return validator.errors
