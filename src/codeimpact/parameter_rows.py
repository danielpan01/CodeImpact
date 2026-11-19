"""Isolate a single added row in a supported, inline pytest parametrization."""

import ast
import copy
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from codeimpact.discovery import is_test_file
from codeimpact.module_data import (
    DATA,
    MAX_LITERAL_NODES,
    SCALAR,
    Data,
    External,
    Function,
    Query,
    ReadsTable,
    Scope,
    Unknown,
    Value,
    deferred_body_edit,
)
from codeimpact.partial_bindings import dotted

if TYPE_CHECKING:
    from codeimpact.analyzer import Index

TIMEDELTA_OPTIONS = {"days", "seconds", "microseconds", "milliseconds", "minutes", "hours", "weeks"}


def inline_decorator(fn: ast.FunctionDef) -> tuple[ast.Call, ast.List | ast.Tuple] | None:
    if len(fn.decorator_list) != 1:
        return None
    dec = fn.decorator_list[0]
    if (
        isinstance(dec, ast.Call)
        and dotted(dec.func) == "pytest.mark.parametrize"
        and len(dec.args) == 2
        and not dec.keywords
        and isinstance(rows := dec.args[1], (ast.List, ast.Tuple))
    ):
        return dec, rows
    return None


def changed_parameter_rows(before: "Index", after: "Index", path: str) -> str | None:
    """Require one row addition and no other module edit."""
    if not is_test_file(path):
        return None
    old, new = (i.syntax.get(f"{path}::<module>") for i in (before, after))
    if not isinstance(old, ast.Module) or not isinstance(new, ast.Module):
        return None
    if len(old.body) != len(new.body):
        return None
    diffs = [(a, b) for a, b in zip(old.body, new.body, strict=True) if ast.dump(a) != ast.dump(b)]
    if len(diffs) != 1:
        return None
    a, b = diffs[0]
    if not (
        isinstance(a, ast.FunctionDef)
        and isinstance(b, ast.FunctionDef)
        and a.name.startswith("test_")
        and (left := inline_decorator(a))
        and (right := inline_decorator(b))
        and type(left[1]) is type(right[1])
    ):
        return None
    new_fn, new_dec = copy.copy(b), copy.copy(right[0])
    new_dec.args = [right[0].args[0], left[1]]
    new_fn.decorator_list = [new_dec]
    if ast.dump(a) != ast.dump(new_fn):
        return None
    old_rows, new_rows = ([ast.dump(r) for r in part[1].elts] for part in (left, right))
    if len(new_rows) != len(old_rows) + 1:
        return None
    first = next(
        (i for i, (x, y) in enumerate(zip(old_rows, new_rows, strict=False)) if x != y),
        len(old_rows),
    )
    return a.name if old_rows[first:] == new_rows[first + 1 :] else None


def numeric_literal(node: ast.expr) -> bool:
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        node = node.operand
    # Finite, small numeric literals guarantee no callback or overflow, even
    # when combining every supported unit. No constructor is invoked.
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
        and abs(node.value) <= 1_000_000
    )


class RowQuery(Query):
    def __init__(
        self, index: "Index", path: str, owner: str, stable: set[str], edited: dict[str, str]
    ):
        super().__init__(index, path, set(), stable, edited)
        self.owner = (path, owner)
        self.calls: set[tuple[str, str]] = set()

    def imports(self, node: ast.Import | ast.ImportFrom, scope: Scope) -> None:
        if (
            isinstance(node, ast.Import)
            and len(node.names) == 1
            and node.names[0].name == "datetime"
        ):
            name = node.names[0].asname or "datetime"
            if name in scope.values:
                raise Unknown("competing datetime binding")
            scope.values[name] = External("datetime")
            return
        super().imports(node, scope)

    def header(self, fn: ast.FunctionDef, scope: Scope, eager: bool) -> None:
        if not fn.decorator_list:
            super().header(fn, scope, eager)
            return
        plain = copy.copy(fn)
        plain.decorator_list = []
        super().header(plain, scope, eager)
        shape = inline_decorator(fn)
        args = fn.args
        if not (
            fn.name.startswith("test_")
            and shape
            and not (
                args.posonlyargs or args.kwonlyargs or args.vararg or args.kwarg or args.defaults
            )
        ):
            raise Unknown("unproved collection decorator")
        dec, rows = shape
        if self.expr(dec.func, scope, eager) != External("pytest.mark.parametrize"):
            raise Unknown("unproved pytest binding")
        names = dec.args[0]
        if isinstance(names, ast.Constant) and isinstance(names.value, str):
            columns = [n.strip() for n in names.value.split(",")]
        elif isinstance(names, (ast.Tuple, ast.List)):
            columns = [
                c.value
                for c in names.elts
                if isinstance(c, ast.Constant) and isinstance(c.value, str)
            ]
            if len(columns) != len(names.elts):
                raise Unknown("unproved parameter names")
        else:
            raise Unknown("unproved parameter names")
        if (
            len(columns) < 2
            or len(columns) != len(args.args)
            or set(columns) != {a.arg for a in args.args}
        ):
            raise Unknown("unproved parameter arity")
        if not rows.elts or sum(1 for _ in ast.walk(rows)) > MAX_LITERAL_NODES:
            raise Unknown("row budget")
        for row in rows.elts:
            if not isinstance(row, (ast.Tuple, ast.List)) or len(row.elts) != len(columns):
                raise Unknown("malformed parameter row")
            for cell in row.elts:
                self.cell(cell, scope)

    def cell(self, cell: ast.expr, scope: Scope) -> None:
        self.tick()
        if isinstance(cell, ast.Constant) and type(cell.value) in SCALAR:
            return
        if isinstance(cell, ast.Tuple):
            for child in cell.elts:
                self.cell(child, scope)
            return
        if (
            isinstance(cell, ast.Call)
            and not cell.args
            and isinstance(cell.func, ast.Attribute)
            and cell.func.attr == "timedelta"
            and isinstance(cell.func.value, ast.Name)
            and self.lookup(cell.func.value.id, scope, True) == External("datetime")
            and {kw.arg for kw in cell.keywords} <= TIMEDELTA_OPTIONS
            and len({kw.arg for kw in cell.keywords}) == len(cell.keywords)
            and all(numeric_literal(kw.value) for kw in cell.keywords)
        ):
            return
        raise Unknown("opaque or effectful parameter cell")

    def function(
        self, fn: Function, args: list[Value], kwargs: dict[str, Value], eager: bool
    ) -> Data:
        if isinstance(fn.node, ast.FunctionDef):
            if fn.node.decorator_list or self.body_edits.get(fn.scope.path) == fn.node.name:
                # A changed callable can need the test-module path when the
                # production call cannot be resolved in the original graph.
                raise ReadsTable()
            self.calls.add((fn.scope.path, fn.node.name))
        return super().function(fn, args, kwargs, eager)

    def excludes(self, sid: str) -> bool:
        node = self.index.syntax.get(sid)
        path, _, name = sid.partition("::")
        if (
            not isinstance(node, ast.FunctionDef)
            or "." in name
            or path != self.owner[0]
            or (path, name) == self.owner
        ):
            return False
        args = node.args
        if not node.decorator_list and (
            args.args or args.posonlyargs or args.kwonlyargs or args.vararg or args.kwarg
        ):
            return False
        scope = self.module(path)
        function = scope.values.get(name)
        if not isinstance(function, Function):
            return False
        super().function(function, [DATA] * len(node.args.args), {}, False)
        return not self.mutated_tables


class ParameterRows:
    def __init__(self, before: "Index", after: "Index", paths: set[str]):
        self.indexes = before, after
        self.changes: dict[str, str] = {}
        self.cache: dict[tuple[str, str], bool] = {}
        self.stable: set[str] = set()
        self.edited: dict[str, str] = {}
        blocked = {"pytest", "datetime"}
        if not paths or any(
            p.name == "conftest.py" or p.stem in blocked or blocked.intersection(p.parts[:-1])
            for index in self.indexes
            for p in map(PurePosixPath, index.sources)
        ):
            return
        if any(
            len(names := [n.name for n in index.nodes.values() if n.kind == "module"])
            != len(set(names))
            for index in self.indexes
        ):
            return
        self.changes = {
            p: name for p in sorted(paths) if (name := changed_parameter_rows(before, after, p))
        }
        if self.changes:
            self.stable = {
                p
                for p in before.sources.keys() & after.sources.keys()
                if before.sources[p] == after.sources[p]
            }
            self.edited = {
                p: name for p in sorted(paths) if (name := deferred_body_edit(before, after, p))
            }

    def allows(self, sid: str, path: str) -> bool:
        if path not in self.changes or sid.partition("::")[0] != path:
            return True
        key = sid, path
        if key not in self.cache:
            stable = self.stable | {path}
            try:
                before, after = (
                    RowQuery(index, path, self.changes[path], stable, self.edited)
                    for index in self.indexes
                )
                self.cache[key] = not (
                    before.excludes(sid)
                    and after.excludes(sid)
                    and before.calls == after.calls
                    and before.modules.keys() == after.modules.keys()
                )
            except (ReadsTable, Unknown, RecursionError):
                self.cache[key] = True
        return self.cache[key]
