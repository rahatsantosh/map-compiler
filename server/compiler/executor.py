import ast
from io import StringIO
from contextlib import redirect_stdout
from typing import Any


class ExecutionError(Exception):
    def __init__(self, message: str, line: int | None = None):
        self.line = line
        super().__init__(message)


class ScriptExecutor(ast.NodeVisitor):
    def __init__(self, env: dict[str, Any]):
        self.env = dict(env)
        self.stdout_buffer = StringIO()

    def execute(self, tree: ast.Module) -> dict[str, Any]:
        with redirect_stdout(self.stdout_buffer):
            for node in tree.body:
                self._exec_statement(node)

        return {
            "console": self.stdout_buffer.getvalue() or None,
            "response": self.env.get("response"),
            "graph": self.env.get("graph"),
        }

    def _exec_statement(self, node: ast.stmt):
        if isinstance(node, ast.Assign):
            value = self._eval(node.value)
            for target in node.targets:
                self._assign(target, value)
        elif isinstance(node, ast.AugAssign):
            current = self._eval(node.target)
            value = self._eval(node.value)
            result = self._apply_binop(node.op, current, value)
            self._assign(node.target, result)
        elif isinstance(node, ast.Expr):
            self._eval(node.value)
        elif isinstance(node, ast.If):
            if self._eval(node.test):
                for stmt in node.body:
                    self._exec_statement(stmt)
            else:
                for stmt in node.orelse:
                    self._exec_statement(stmt)
        elif isinstance(node, ast.For):
            iterable = self._eval(node.iter)
            for item in iterable:
                self._assign(node.target, item)
                for stmt in node.body:
                    self._exec_statement(stmt)
        elif isinstance(node, ast.While):
            while self._eval(node.test):
                for stmt in node.body:
                    self._exec_statement(stmt)
        elif isinstance(node, ast.Pass):
            pass
        elif isinstance(node, (ast.Break, ast.Continue)):
            raise ExecutionError(
                f"{type(node).__name__} outside loop", line=node.lineno
            )
        else:
            raise ExecutionError(
                f"Unsupported statement: {type(node).__name__}", line=node.lineno
            )

    def _assign(self, target: ast.AST, value: Any):
        if isinstance(target, ast.Name):
            self.env[target.id] = value
        elif isinstance(target, ast.Tuple | ast.List):
            for t, v in zip(target.elts, value):
                self._assign(t, v)
        elif isinstance(target, ast.Subscript):
            obj = self._eval(target.value)
            key = self._eval(target.slice)
            obj[key] = value
        elif isinstance(target, ast.Attribute):
            obj = self._eval(target.value)
            setattr(obj, target.attr, value)
        else:
            raise ExecutionError(
                f"Unsupported assignment target: {type(target).__name__}",
                line=getattr(target, "lineno", None),
            )

    def _eval(self, node: ast.expr) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            if node.id not in self.env:
                raise ExecutionError(f"Undefined variable '{node.id}'", line=node.lineno)
            return self.env[node.id]
        elif isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            return self._apply_binop(node.op, left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval(node.operand)
            return self._apply_unaryop(node.op, operand)
        elif isinstance(node, ast.BoolOp):
            return self._eval_boolop(node)
        elif isinstance(node, ast.Compare):
            return self._eval_compare(node)
        elif isinstance(node, ast.IfExp):
            return self._eval(node.body) if self._eval(node.test) else self._eval(node.orelse)
        elif isinstance(node, ast.Call):
            return self._eval_call(node)
        elif isinstance(node, ast.Attribute):
            obj = self._eval(node.value)
            return getattr(obj, node.attr)
        elif isinstance(node, ast.Subscript):
            obj = self._eval(node.value)
            key = self._eval(node.slice)
            return obj[key]
        elif isinstance(node, ast.Slice):
            lower = self._eval(node.lower) if node.lower else None
            upper = self._eval(node.upper) if node.upper else None
            step = self._eval(node.step) if node.step else None
            return slice(lower, upper, step)
        elif isinstance(node, ast.Tuple):
            return tuple(self._eval(e) for e in node.elts)
        elif isinstance(node, ast.List):
            return [self._eval(e) for e in node.elts]
        elif isinstance(node, ast.Dict):
            return {
                self._eval(k): self._eval(v)
                for k, v in zip(node.keys, node.values)
            }
        elif isinstance(node, ast.Set):
            return {self._eval(e) for e in node.elts}
        elif isinstance(node, ast.ListComp):
            return self._eval_listcomp(node)
        elif isinstance(node, ast.GeneratorExp):
            return self._eval_genexp(node)
        elif isinstance(node, ast.JoinedStr):
            return "".join(
                self._eval(v) if isinstance(v, ast.FormattedValue) else v.value
                for v in node.values
            )
        elif isinstance(node, ast.FormattedValue):
            value = self._eval(node.value)
            if node.format_spec:
                spec = self._eval(node.format_spec)
                return format(value, spec)
            return str(value)
        elif isinstance(node, ast.Starred):
            return self._eval(node.value)
        else:
            raise ExecutionError(
                f"Unsupported expression: {type(node).__name__}",
                line=getattr(node, "lineno", None),
            )

    def _eval_call(self, node: ast.Call) -> Any:
        func = self._eval(node.func)
        args = []
        for arg in node.args:
            if isinstance(arg, ast.Starred):
                args.extend(self._eval(arg.value))
            else:
                args.append(self._eval(arg))
        kwargs = {kw.arg: self._eval(kw.value) for kw in node.keywords if kw.arg is not None}
        star_kwargs = [kw for kw in node.keywords if kw.arg is None]
        for kw in star_kwargs:
            kwargs.update(self._eval(kw.value))
        return func(*args, **kwargs)

    def _eval_compare(self, node: ast.Compare) -> Any:
        left = self._eval(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right = self._eval(comparator)
            if not self._apply_cmpop(op, left, right):
                return False
            left = right
        return True

    def _eval_boolop(self, node: ast.BoolOp) -> Any:
        if isinstance(node.op, ast.And):
            result = True
            for value in node.values:
                result = self._eval(value)
                if not result:
                    return result
            return result
        else:
            result = False
            for value in node.values:
                result = self._eval(value)
                if result:
                    return result
            return result

    def _eval_listcomp(self, node: ast.ListComp) -> list:
        return list(self._eval_comprehension(node.elt, node.generators))

    def _eval_genexp(self, node: ast.GeneratorExp):
        return self._eval_comprehension(node.elt, node.generators)

    def _eval_comprehension(self, elt, generators, depth=0):
        if depth >= len(generators):
            yield self._eval(elt)
            return
        gen = generators[depth]
        iterable = self._eval(gen.iter)
        for item in iterable:
            self._assign(gen.target, item)
            if all(self._eval(if_clause) for if_clause in gen.ifs):
                yield from self._eval_comprehension(elt, generators, depth + 1)

    @staticmethod
    def _apply_binop(op: ast.operator, left: Any, right: Any) -> Any:
        ops = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
            ast.FloorDiv: lambda a, b: a // b,
            ast.Mod: lambda a, b: a % b,
            ast.Pow: lambda a, b: a ** b,
            ast.BitAnd: lambda a, b: a & b,
            ast.BitOr: lambda a, b: a | b,
            ast.BitXor: lambda a, b: a ^ b,
        }
        handler = ops.get(type(op))
        if handler is None:
            raise ExecutionError(f"Unsupported operator: {type(op).__name__}")
        return handler(left, right)

    @staticmethod
    def _apply_unaryop(op: ast.unaryop, operand: Any) -> Any:
        ops = {
            ast.UAdd: lambda x: +x,
            ast.USub: lambda x: -x,
            ast.Not: lambda x: not x,
            ast.Invert: lambda x: ~x,
        }
        handler = ops.get(type(op))
        if handler is None:
            raise ExecutionError(f"Unsupported unary operator: {type(op).__name__}")
        return handler(operand)

    @staticmethod
    def _apply_cmpop(op: ast.cmpop, left: Any, right: Any) -> Any:
        ops = {
            ast.Eq: lambda a, b: a == b,
            ast.NotEq: lambda a, b: a != b,
            ast.Lt: lambda a, b: a < b,
            ast.LtE: lambda a, b: a <= b,
            ast.Gt: lambda a, b: a > b,
            ast.GtE: lambda a, b: a >= b,
            ast.Is: lambda a, b: a is b,
            ast.IsNot: lambda a, b: a is not b,
            ast.In: lambda a, b: a in b,
            ast.NotIn: lambda a, b: a not in b,
        }
        handler = ops.get(type(op))
        if handler is None:
            raise ExecutionError(f"Unsupported comparison: {type(op).__name__}")
        return handler(left, right)
