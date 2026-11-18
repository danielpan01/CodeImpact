"""Prove a bounded package export addition cannot affect a plain test."""

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

from codeimpact.partial_bindings import PartialBindings, audit, dotted

if TYPE_CHECKING:
    from codeimpact.analyzer import Index

MAX_NODES = 12000
BUILTINS = {"bool", "float", "int", "str", "bytes", "Exception", "ValueError"}
EXTERNAL_IMPORTS = {
    "__future__.absolute_import",
    "copy",
    "datetime",
    "decimal.Decimal",
    "hypothesis",
    "hypothesis.extra.pytz",
    "hypothesis.strategies",
    "pickle",
    "pytest",
    "re",
    "typing",
}
EXTERNAL_CALLS = {
    "datetime.datetime",
    "datetime.timedelta",
    "datetime.timezone",
    "datetime.tzinfo",
    "decimal.Decimal",
    "re.compile",
}
EXTERNAL_DATA = {"datetime.timezone.utc", "re.VERBOSE"}
ANNOTATIONS = {"datetime.datetime", "datetime.timezone", "typing.Dict", "typing.Optional"}
DATA_METHODS = {"get", "groupdict", "items", "match"}
HOOKS = {
    "setup_module",
    "teardown_module",
    "setup_function",
    "teardown_function",
    "setUpModule",
    "tearDownModule",
    "load_tests",
}
DATA_EXPRESSIONS = (
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.IfExp,
    ast.Subscript,
    ast.Slice,
    ast.JoinedStr,
    ast.FormattedValue,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Set,
)


class Unproved(Exception):
    """Keep the original fallback contribution."""


def require(condition: object) -> None:
    if not condition:
        raise Unproved


def passive_statement(node: ast.stmt) -> bool:
    return isinstance(node, ast.Pass) or (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def fingerprint(nodes: list[ast.stmt]) -> str:
    return ast.dump(ast.Module(body=nodes, type_ignores=[]))


@dataclass(frozen=True)
class Shape:
    package: str
    child: str
    import_path: str
    added: frozenset[str]
    reexports: frozenset[str]


def resolver(index: "Index") -> PartialBindings:
    if index.partials is None:
        raise Unproved
    return index.partials


def package_import(index: "Index", path: str) -> tuple[str, list[str]]:
    body = resolver(index).trees[path].body
    statements = [s for s in body if not passive_statement(s)]
    require(len(statements) == 2)
    export, names = statements
    if not (
        isinstance(export, ast.ImportFrom)
        and export.level == 1
        and export.module
        and export.module.isidentifier()
        and all(
            a.name.isidentifier() and not a.name.startswith("_") and not a.asname
            for a in export.names
        )
        and isinstance(names, ast.Assign)
        and len(names.targets) == 1
        and isinstance(names.targets[0], ast.Name)
        and names.targets[0].id == "__all__"
        and isinstance(names.value, (ast.List, ast.Tuple))
        and all(isinstance(e, ast.Constant) and type(e.value) is str for e in names.value.elts)
    ):
        raise Unproved
    exports = [a.name for a in export.names]
    require(len(exports) == len(set(exports)))
    return export.module, exports


def shape(before: "Index", after: "Index", path: str) -> Shape:
    package = before.nodes[f"{path}::<module>"].name
    # A top-level package avoids an unproved enclosing initializer.
    require(package.isidentifier() and package == after.nodes[f"{path}::<module>"].name)
    old_module, old_exports = package_import(before, path)
    new_module, new_exports = package_import(after, path)
    added_exports = set(new_exports) - set(old_exports)
    require(old_module == new_module and added_exports and old_module not in new_exports)
    require(not added_exports.intersection(BUILTINS))
    require([name for name in new_exports if name not in added_exports] == old_exports)
    import_path = f"{package}.{old_module}"
    child = resolver(before).modules.get(import_path)
    if child is None or child != path.removesuffix("__init__.py") + old_module + ".py":
        raise Unproved
    require(child == resolver(after).modules.get(import_path))
    old_body = resolver(before).trees[child].body
    new_body = resolver(after).trees[child].body
    added = frozenset(added_exports)
    functions = [s for s in new_body if isinstance(s, ast.FunctionDef) and s.name in added]
    require(len(functions) == len(added))
    require(fingerprint(old_body) == fingerprint([s for s in new_body if s not in functions]))
    for index in (before, after):
        scope = resolver(index).scopes[child]
        require(
            not scope.wildcard and not scope.blocked and all(n == 1 for n in scope.counts.values())
        )
        require(not any(name.startswith("__") and name != "__all__" for name in scope.counts))
        require(all(resolver(index).binding(child, name) for name in old_exports))
        require(all(scope.counts[name] == int(index is after) for name in added))
    # This slice models only passive builtin annotations and literal defaults
    # for added functions. The new bodies are never involved in exclusion.
    for fn in functions:
        require(not fn.decorator_list and not fn.type_params and not fn.name.startswith("_"))
        for n in [fn.returns, *(a.annotation for a in ast.walk(fn.args) if isinstance(a, ast.arg))]:
            require(
                n is None
                or isinstance(n, ast.Constant)
                and n.value is None
                or isinstance(n, ast.Name)
                and n.id in BUILTINS
                and resolver(after).binding(child, n.id) is None
            )
        require(
            all(
                isinstance(v, ast.Constant)
                for v in [*fn.args.defaults, *fn.args.kw_defaults]
                if v is not None
            )
        )
    return Shape(package, child, import_path, added, frozenset(old_exports))


@dataclass(frozen=True)
class Member:
    callable: bool = False


DATA = Member()
FUNCTION = Member(callable=True)


class SourceAudit:
    def __init__(self, index: "Index", pair: Shape, path: str, members: dict[str, Member]):
        self.index = index
        self.pair = pair
        self.path = path
        self.members = members
        self.names: dict[str, str | Member] = {}
        self.tree = resolver(index).trees[path]
        require(sum(1 for _ in ast.walk(self.tree)) <= MAX_NODES)
        scope = resolver(index).scopes[path]
        require(not scope.wildcard and not scope.blocked)
        require(
            not any(
                n in HOOKS
                or n.startswith(("pytest", "pytest_"))
                and n != "pytest"
                or n.startswith("__")
                and n != "__all__"
                for n in scope.counts
            )
        )

    def imported(self, stmt: ast.Import | ast.ImportFrom, *, implementation: bool) -> None:
        if isinstance(stmt, ast.ImportFrom) and stmt.level:
            # Check the relative import is within the captured top-level package.
            require(
                stmt.level == 1 and self.path.rsplit("/", 1)[0] == self.pair.child.rsplit("/", 1)[0]
            )
        bindings, _ = resolver(self.index).decode(stmt, self.path, resolver(self.index).modules)
        require(len(bindings) == len(stmt.names) and not any(a.asname for a in stmt.names))
        for (name, target), alias in zip(bindings, stmt.names, strict=True):
            declared = target if isinstance(stmt, ast.ImportFrom) else alias.name
            pair_member = self.member(target)
            if not implementation and (
                pair_member is not None or declared in {self.pair.package, self.pair.import_path}
            ):
                require(name not in self.names)
                self.names[name] = pair_member if pair_member is not None else target
                continue
            require(declared in EXTERNAL_IMPORTS)
            require(declared.split(".")[0] not in resolver(self.index).modules)
            if implementation:
                require(declared.split(".")[0] in {"datetime", "decimal", "re", "typing"})
            require(name not in self.names or self.names[name] == target)
            self.names[name] = target

    def member(self, target: str) -> Member | None:
        module, _, name = target.rpartition(".")
        if module == self.pair.import_path or (
            module == self.pair.package and name in self.pair.reexports
        ):
            return self.members.get(name)
        return None

    def qualified(self, node: ast.AST, local: set[str]) -> str:
        if name := dotted(node):
            root, rest = name.split(".")[0], name.partition(".")[2]
            if root not in local and isinstance(binding := self.names.get(root), str):
                return binding + (f".{rest}" if rest else "")
        return ""

    def value(self, node: ast.AST, local: set[str]) -> None:
        if isinstance(node, ast.Constant):
            return
        if isinstance(node, (ast.Name, ast.Attribute)):
            target = self.qualified(node, local)
            if target:
                require(target in EXTERNAL_DATA or self.member(target) == DATA)
            elif isinstance(node, ast.Name):
                require(node.id in local or self.names.get(node.id) == DATA)
            else:
                require(not node.attr.startswith("_"))
                self.value(node.value, local)
            return
        if isinstance(node, ast.Call):
            require(not any(k.arg is None for k in node.keywords))
            target = self.qualified(node.func, local)
            if target in EXTERNAL_CALLS or self.member(target) == FUNCTION:
                pass
            elif target:
                require(
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in DATA_METHODS
                    and self.member(target.rpartition(".")[0]) == DATA
                )
            elif isinstance(node.func, ast.Name):
                name = node.func.id
                require(
                    name not in local
                    and (
                        self.names.get(name) == FUNCTION
                        or name in BUILTINS
                        and name not in self.names
                    )
                )
            elif isinstance(node.func, ast.Attribute):
                require(node.func.attr in DATA_METHODS)
                self.value(node.func.value, local)
            else:
                raise Unproved
            for arg in [*node.args, *(k.value for k in node.keywords)]:
                self.value(arg, local)
            return
        if isinstance(node, ast.DictComp) and len(node.generators) == 1:
            generator = node.generators[0]
            require(not generator.is_async)
            self.value(generator.iter, local)
            local = local | self.targets(generator.target)
            for part in [*generator.ifs, node.key, node.value]:
                self.value(part, local)
            return
        if isinstance(node, DATA_EXPRESSIONS):
            require(not isinstance(node, ast.Dict) or None not in node.keys)
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.expr):
                    self.value(child, local)
            return
        raise Unproved

    def annotation(self, node: ast.expr | None) -> None:
        if node is None or isinstance(node, ast.Constant) and node.value is None:
            return
        if isinstance(node, ast.Name) and node.id in BUILTINS and node.id not in self.names:
            return
        target = self.qualified(node, set())
        if target in ANNOTATIONS:
            return
        if isinstance(node, ast.Subscript) and self.qualified(node.value, set()) in {
            "typing.Dict",
            "typing.Optional",
        }:
            for item in node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]:
                self.annotation(item)
            return
        raise Unproved

    def header(self, fn: ast.FunctionDef) -> set[str]:
        args = fn.args
        require(not fn.type_params and not args.vararg and not args.kwarg)
        parameters = [*args.posonlyargs, *args.args, *args.kwonlyargs]
        for arg in parameters:
            self.annotation(arg.annotation)
        self.annotation(fn.returns)
        for v in [*args.defaults, *args.kw_defaults]:
            if v is not None:
                self.value(v, set())
        return {a.arg for a in parameters}

    def decorator(self, node: ast.expr, parameters: set[str]) -> None:
        """Allow known collection expressions but never infer decorated execution."""
        if not isinstance(node, ast.Call):
            raise Unproved
        target = self.qualified(node.func, set())
        if target == "pytest.mark.parametrize":
            require(len(node.args) == 2 and not node.keywords)
            names = node.args[0]
            require(isinstance(names, ast.Constant) and isinstance(names.value, str))
            assert isinstance(names, ast.Constant) and isinstance(names.value, str)
            declared = [s.strip() for s in names.value.split(",")]
            require(set(declared) == parameters and len(declared) == len(parameters))
            rows = node.args[1]
            if not isinstance(rows, (ast.Tuple, ast.List)):
                raise Unproved
            for row in rows.elts:
                if not isinstance(row, (ast.Tuple, ast.List)) or len(row.elts) != len(declared):
                    raise Unproved
                for item in row.elts:
                    self.value(item, set())
        elif target == "hypothesis.given":
            require(not node.args and {k.arg for k in node.keywords} == parameters)
            for strategy in (k.value for k in node.keywords):
                if not isinstance(strategy, ast.Call):
                    raise Unproved
                require(self.qualified(strategy.func, set()) == "hypothesis.strategies.datetimes")
                require(not strategy.args and len(strategy.keywords) <= 1)
                for keyword in strategy.keywords:
                    call = keyword.value
                    if keyword.arg != "timezones" or not isinstance(call, ast.Call):
                        raise Unproved
                    require(self.qualified(call.func, set()) == "hypothesis.extra.pytz.timezones")
                    require(not call.args and not call.keywords)
        else:
            raise Unproved

    def module(self, *, implementation: bool) -> None:
        functions = []
        for stmt in self.tree.body:
            if passive_statement(stmt):
                continue
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                self.imported(stmt, implementation=implementation)
            elif isinstance(stmt, ast.FunctionDef):
                if implementation and stmt.name in self.pair.added:
                    continue
                require(stmt.name not in self.names and stmt.name not in BUILTINS)
                parameters = self.header(stmt)
                for decorator in stmt.decorator_list:
                    require(not implementation and stmt.name.startswith("test_"))
                    self.decorator(decorator, parameters)
                if implementation:
                    self.names[stmt.name] = FUNCTION
                    functions.append((stmt, parameters))
                else:
                    # Collection exposes the function, but a test may not call an
                    # uninspected sibling body to complete this proof.
                    self.names[stmt.name] = "<test function>"
            elif implementation and isinstance(stmt, ast.Assign):
                require(len(stmt.targets) == 1)
                target = stmt.targets[0]
                if not isinstance(target, ast.Name):
                    raise Unproved
                self.value(stmt.value, set())
                self.names[target.id] = DATA
            elif implementation and isinstance(stmt, ast.ClassDef):
                require(not stmt.decorator_list and not stmt.keywords and not stmt.type_params)
                require(len(stmt.bases) == 1 and isinstance(stmt.bases[0], ast.Name))
                base = stmt.bases[0]
                require(
                    isinstance(base, ast.Name)
                    and base.id in {"Exception", "ValueError"}
                    and base.id not in self.names
                    and all(passive_statement(s) for s in stmt.body)
                )
                self.names[stmt.name] = FUNCTION
            else:
                raise Unproved
        for fn, parameters in functions:
            self.function_body(fn, parameters)

    def function_body(self, fn: ast.FunctionDef, parameters: set[str]) -> None:
        scope = audit(fn.body, local=True)
        require(not scope.blocked and not scope.wildcard)
        local = parameters | set(scope.counts)
        require(not local.intersection(set(self.names) | BUILTINS))
        self.block(fn.body, local)

    def targets(self, node: ast.expr) -> set[str]:
        if isinstance(node, ast.Name):
            require(node.id not in self.names and node.id not in BUILTINS)
            return {node.id}
        if isinstance(node, (ast.List, ast.Tuple)):
            return set().union(*(self.targets(item) for item in node.elts))
        raise Unproved

    def block(self, statements: list[ast.stmt], local: set[str]) -> None:
        for stmt in statements:
            if isinstance(stmt, ast.Assign):
                self.value(stmt.value, local)
                for target in stmt.targets:
                    local.update(self.targets(target))
            elif isinstance(stmt, ast.AnnAssign):
                self.annotation(stmt.annotation)
                if stmt.value is not None:
                    self.value(stmt.value, local)
                    local.update(self.targets(stmt.target))
            elif isinstance(stmt, (ast.Return, ast.Expr, ast.Assert, ast.Raise)):
                for value in ast.iter_child_nodes(stmt):
                    if isinstance(value, ast.expr):
                        self.value(value, local)
            elif isinstance(stmt, ast.If):
                self.value(stmt.test, local)
                self.block(stmt.body, local.copy())
                self.block(stmt.orelse, local.copy())
            elif isinstance(stmt, ast.Try):
                self.block(stmt.body, local.copy())
                for handler in stmt.handlers:
                    self.annotation(handler.type)
                    extra = {handler.name} if handler.name else set()
                    require(not extra.intersection(set(self.names) | BUILTINS))
                    self.block(handler.body, local | extra)
                self.block(stmt.orelse, local.copy())
                self.block(stmt.finalbody, local.copy())
            elif not isinstance(stmt, ast.Pass):
                raise Unproved


class AdditiveExports:
    def __init__(self, before: "Index", after: "Index", paths: set[str]):
        self.indexes = before, after
        self.changes: dict[str, Shape] = {}
        self.members: dict[tuple[int, str], dict[str, Member]] = {}
        self.consumers: dict[tuple[int, str, str], SourceAudit | None] = {}
        if any(
            len(names := [n.name for n in index.nodes.values() if n.kind == "module"])
            != len(set(names))
            for index in self.indexes
        ):
            return
        for path in sorted(paths):
            if not path.endswith("/__init__.py") or any(
                path not in resolver(i).trees for i in self.indexes
            ):
                continue
            try:
                pair = shape(before, after, path)
                for i, index in enumerate(self.indexes):
                    proof = SourceAudit(index, pair, pair.child, {})
                    proof.module(implementation=True)
                    self.members[i, path] = {
                        k: v for k, v in proof.names.items() if isinstance(v, Member)
                    }
                    require(pair.reexports <= self.members[i, path].keys())
            except (Unproved, RecursionError):
                continue
            self.changes[path] = pair

    def allows(self, sid: str, package_path: str) -> bool:
        pair = self.changes[package_path]
        path, _, name = sid.partition("::")
        if "." in name:
            return True
        for i, index in enumerate(self.indexes):
            try:
                key = i, package_path, path
                if key not in self.consumers:
                    self.consumers[key] = None
                    if path not in resolver(index).trees or any(
                        p.rsplit("/", 1)[-1] == "conftest.py"
                        or (
                            p.endswith("/__init__.py")
                            and p != package_path
                            and path.startswith(p.removesuffix("__init__.py"))
                        )
                        for p in index.sources
                    ):
                        return True
                    proof = SourceAudit(index, pair, path, self.members[i, package_path])
                    proof.module(implementation=False)
                    self.consumers[key] = proof
                consumer = self.consumers[key]
                fn = index.syntax.get(sid)
                if consumer is None or not isinstance(fn, ast.FunctionDef) or fn.decorator_list:
                    return True
                if consumer.header(fn):
                    return True
                consumer.function_body(fn, set())
            except (Unproved, RecursionError):
                return True
        return False
