"""Bounded aggregate exclusion for literal dispatch into a closed source module."""

import ast
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Any

from codeimpact.arguments import MAX_STEPS as MAX_AUDIT_STEPS
from codeimpact.call_arguments import (
    MAX_DEPTH,
    UNKNOWN,
    CallArgumentFilter,
    CallBinding,
    Query,
    Uncertain,
)
from codeimpact.partial_bindings import audit, dotted
from codeimpact.partial_bindings import before as precedes

if TYPE_CHECKING:
    from codeimpact.analyzer import Index

STDLIB = {
    "__future__",
    "argparse",
    "collections.abc",
    "contextlib",
    "functools",
    "html.entities",
    "importlib",
    "io",
    "re",
    "sys",
    "typing",
    "unicodedata",
    "unittest",
}
DATA_NAMES = {
    "html.entities.name2codepoint",
    "sys.version_info.major",
}
DATA_BUILTINS = {
    "str",
    "bytes",
    "bytearray",
    "bool",
    "int",
    "float",
    "isinstance",
    "type",
    "len",
    "chr",
    "TypeError",
    "ValueError",
    "OverflowError",
    "ModuleNotFoundError",
    "ImportError",
}
DATA_METHODS = {
    "upper",
    "lower",
    "capitalize",
    "format",
    "strip",
    "replace",
    "split",
    "join",
    "decode",
    "isascii",
    "sub",
    "group",
    "append",
    "insert",
}
DATA_CALLS = {"re.compile", "re.sub", "unicodedata.normalize"}


def plain_data(value: Any) -> bool:
    if isinstance(value, (list, tuple)):
        return all(plain_data(item) for item in value)
    if isinstance(value, dict):
        return all(type(k) is str and plain_data(v) for k, v in value.items())
    return value is None or type(value) in {str, bytes, int, float, bool}


def binding_names(expr: ast.AST) -> Iterator[str]:
    if isinstance(expr, ast.Name):
        yield expr.id
    elif isinstance(expr, (ast.Tuple, ast.List)):
        for part in expr.elts:
            yield from binding_names(part)
    else:
        raise Uncertain("nonlocal mutation")


class Proof:
    def __init__(self, query: Query, changed: str, stable: set[str]):
        self.query = query
        self.index = query.index
        resolver = self.index.partials
        assert resolver is not None
        self.resolver = resolver
        self.changed = changed
        self.stable = stable
        self.data: dict[str, dict[str, Any]] = {}
        self.initializing: set[str] = set()
        self.parents = {path: name for name, path in resolver.modules.items()}
        self.hits = 0
        self.steps = 0

    def tick(self, cost: int = 1) -> None:
        self.steps += cost
        if self.steps > MAX_AUDIT_STEPS:
            raise Uncertain("dispatch audit budget")

    def qualified(self, path: str, expr: ast.AST, use: ast.AST | None = None) -> str:
        root, dot, tail = (dotted(expr) or "").partition(".")
        entry = self.resolver.imports[path].get(root)
        if entry is None:
            return ""
        target, statement = entry
        scope = self.resolver.scopes[path]
        # At eager sites only already audited effects may have run. A later
        # function body that mutates an attribute is irrelevant at that point.
        if use is not None:
            known = not scope.wildcard and scope.counts[root] == 1 and precedes(statement, use)
        else:
            known = self.resolver.binding(path, root) is statement
        if not known or target.split(".")[0] in self.resolver.modules:
            return ""
        return target + dot + tail

    def import_paths(self, node: ast.Import | ast.ImportFrom, path: str) -> Iterator[str]:
        if isinstance(node, ast.ImportFrom):
            levels = len(self.parents[path].split(".")) - (not path.endswith("__init__.py"))
            if node.level > levels:
                raise Uncertain("relative import boundary")
        for module in self.resolver.decode(node, path, self.resolver.modules)[1]:
            if module in self.resolver.modules:
                yield self.resolver.modules[module]
            elif module not in STDLIB or module.split(".")[0] in self.resolver.modules:
                raise Uncertain("unavailable eager import")

    def module(self, path: str) -> None:
        self.tick()
        if path in self.initializing or len(self.initializing) >= MAX_DEPTH:
            raise Uncertain("eager import cycle or depth")
        if path in self.data:
            return
        if path != self.changed and path not in self.stable:
            raise Uncertain("changed eager dependency")
        if "__getattr__" in self.resolver.scopes[path].counts:
            raise Uncertain("module attribute hook")
        self.initializing.add(path)
        try:
            parent = self.parents[path].rpartition(".")[0]
            parent_path = self.resolver.modules.get(parent)
            if parent_path and parent_path not in self.initializing:
                self.module(parent_path)
            values: dict[str, Any] = {}
            self.eager(self.resolver.trees[path].body, path, values)
            self.data[path] = values
        finally:
            self.initializing.remove(path)

    def eager(
        self, body: list[ast.stmt], path: str, values: dict[str, Any], *, cls: bool = False
    ) -> None:
        # Eager code can access only established data and specific passive imports.
        for stmt in body:
            self.tick()
            if isinstance(stmt, (ast.Import, ast.ImportFrom)) and not cls:
                for dep in self.import_paths(stmt, path):
                    self.module(dep)
            elif isinstance(stmt, ast.FunctionDef):
                uses_future = any(
                    isinstance(n, ast.ImportFrom)
                    and n.module == "__future__"
                    and not n.level
                    and any(a.name == "annotations" for a in n.names)
                    for n in self.resolver.trees[path].body
                )
                annotations = [
                    stmt.returns,
                    *(n.annotation for n in ast.walk(stmt.args) if isinstance(n, ast.arg)),
                ]
                if stmt.type_params or (
                    not uses_future
                    and any(n is not None and not isinstance(n, ast.Constant) for n in annotations)
                ):
                    raise Uncertain("eager annotation")
                for default in [*stmt.args.defaults, *stmt.args.kw_defaults]:
                    if default is not None:
                        self.eager_value(default, path, values)
                for decorator in stmt.decorator_list:
                    if self.qualified(path, decorator, stmt) != "contextlib.contextmanager":
                        raise Uncertain("eager decorator")
            elif isinstance(stmt, ast.ClassDef) and not cls:
                if (
                    stmt.decorator_list
                    or stmt.keywords
                    or stmt.type_params
                    or not (
                        not stmt.bases
                        or len(stmt.bases) == 1
                        and self.qualified(path, stmt.bases[0], stmt) == "unittest.TestCase"
                    )
                ):
                    raise Uncertain("class creation hook")
                self.eager(stmt.body, path, dict(values), cls=True)
            elif (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
            ):
                name = stmt.targets[0].id
                if name in {"__name__", "__builtins__", "__package__", "__path__"} or (
                    cls and name.startswith("__")
                ):
                    raise Uncertain("namespace customization")
                self.eager_value(stmt.value, path, values)
                values[name] = self.query.value(stmt.value, values, f"{path}::<module>")
            elif (
                isinstance(stmt, ast.If)
                and not cls
                and not stmt.orelse
                and (
                    isinstance(stmt.test, ast.Compare)
                    and isinstance(stmt.test.left, ast.Name)
                    and stmt.test.left.id == "__name__"
                    and len(stmt.test.ops) == 1
                    and isinstance(stmt.test.ops[0], ast.Eq)
                    and isinstance(stmt.test.comparators[0], ast.Constant)
                    and stmt.test.comparators[0].value == "__main__"
                )
            ):
                continue
            elif isinstance(stmt, ast.Pass) or (
                isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
            ):
                continue
            else:
                raise Uncertain("eager effect")

    def eager_value(self, expr: ast.AST, path: str, values: dict[str, Any]) -> None:
        self.tick()
        if isinstance(expr, ast.Constant) and plain_data(expr.value):
            return
        if isinstance(expr, ast.Name) and expr.id in values:
            return
        if self.qualified(path, expr, expr) in DATA_NAMES:
            return
        if isinstance(expr, (ast.Tuple, ast.List, ast.Dict)):
            for child in ast.iter_child_nodes(expr):
                if not isinstance(child, ast.Load):
                    self.eager_value(child, path, values)
            if isinstance(expr, ast.Dict) and None in expr.keys:
                raise Uncertain("eager unpacking")
            return
        if isinstance(expr, (ast.BinOp, ast.Compare)):
            if isinstance(expr, ast.BinOp):
                if not isinstance(expr.op, (ast.Add, ast.Mod)):
                    raise Uncertain("eager operator")
                operands = [expr.left, expr.right]
            else:
                operands = [expr.left, *expr.comparators]
            for operand in operands:
                self.eager_value(operand, path, values)
            return
        if isinstance(expr, ast.Subscript) and (
            self.qualified(path, expr.value, expr) == "typing.Literal"
        ):
            self.eager_value(expr.slice, path, values)
            return
        if isinstance(expr, ast.Call) and not expr.keywords:
            for arg in expr.args:
                self.eager_value(arg, path, values)
            if self.qualified(path, expr.func, expr) == "re.compile":
                return
            if (
                isinstance(expr.func, ast.Attribute)
                and expr.func.attr == "join"
                and isinstance(expr.func.value, ast.Constant)
                and isinstance(expr.func.value.value, str)
            ):
                return
            target = self.resolver.resolve(path, dotted(expr.func) or "", expr)
            if target and target.startswith(path + "::"):
                self.closed(target, [UNKNOWN] * len(expr.args), {}, values, imports=False)
                return
        raise Uncertain("unsupported eager value")

    def resolve_call(self, path: str, call: ast.Call, sid: str, env: dict[str, Any]) -> CallBinding:
        target = dotted(call.func) or ""
        if not target or target.split(".")[0] in env:
            raise Uncertain("dynamic binding")
        symbol = self.resolver.resolve(path, target)
        if not symbol or symbol not in self.index.syntax:
            raise Uncertain("unproved source binding")
        return CallBinding(sid, symbol)

    def function(self, sid: str) -> ast.FunctionDef:
        node = self.index.syntax[sid]
        path = self.index.nodes[sid].path
        if (
            not isinstance(node, ast.FunctionDef)
            or node.decorator_list
            or self.resolver.binding(path, node.name) is not node
        ):
            raise Uncertain("nonplain function")
        return node

    def bound(self, sid: str, args: list[Any], kwargs: dict[str, Any]) -> dict[str, Any]:
        node = self.function(sid)
        env = self.query.bind(sid, node, args, kwargs)
        params = node.args.posonlyargs + node.args.args
        supplied = {p.arg for p in params[: len(args)]} | kwargs.keys()
        path = self.index.nodes[sid].path
        for param, default in [
            *zip(params[len(params) - len(node.args.defaults) :], node.args.defaults, strict=True),
            *zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True),
        ]:
            if not isinstance(default, ast.Name) or param.arg in supplied:
                continue
            binding = self.resolver.binding(path, default.id, node)
            if isinstance(binding, ast.Assign) and isinstance(binding.value, ast.Constant):
                env[param.arg] = self.query.value(binding.value, {}, sid)
        return env

    def dispatch(self, sid: str, call: ast.Call, env: dict[str, Any]) -> None:
        self.tick()
        path = self.index.nodes[sid].path
        binding = self.resolve_call(path, call, sid, env)
        if self.index.nodes[binding.target].path != self.changed:
            raise Uncertain("call outside edited dispatcher")
        args, kwargs = self.query.supplied(call, binding, env)
        if not all(plain_data(v) for v in [*args, *kwargs.values()]):
            raise Uncertain("unknown or active argument")
        node = self.function(binding.target)
        bound = self.bound(binding.target, args, kwargs)
        if not all(plain_data(v) for v in bound.values()):
            raise Uncertain("unknown default")
        body = [
            n
            for n in node.body
            if not (
                isinstance(n, ast.Expr)
                and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str)
            )
        ]
        # Permit a literal membership check that can only reject options.
        if len(body) == 3:
            validation = body.pop(0)
            if not (
                isinstance(validation, ast.If)
                and not validation.orelse
                and len(validation.body) == 1
                and isinstance(validation.body[0], ast.Raise)
                and self.guard(validation.test, bound, binding.target, ast.NotIn) is False
            ):
                raise Uncertain("unproved validation")
        if len(body) != 2:
            raise Uncertain("nonterminal dispatcher shape")
        branch, otherwise = body
        if not (
            isinstance(branch, ast.If)
            and not branch.orelse
            and len(branch.body) == 1
            and self.guard(branch.test, bound, binding.target, ast.Eq) is True
            and isinstance(otherwise, ast.Return)
            and isinstance(otherwise.value, ast.Call)
            and isinstance(selected := branch.body[0], ast.Return)
            and isinstance(selected.value, ast.Call)
        ):
            raise Uncertain("no known alternate dispatch")
        forwards = self.resolve_call(self.changed, selected.value, binding.target, bound)
        unselected = self.resolve_call(self.changed, otherwise.value, binding.target, bound)
        leaf = self.index.nodes[forwards.target].path
        if (
            leaf == self.changed
            or leaf not in self.stable
            or unselected.target not in self.query.relevant
        ):
            raise Uncertain("selected module or edited branch unproved")
        args, kwargs = self.query.supplied(selected.value, forwards, bound)
        if not all(plain_data(v) for v in [*args, *kwargs.values()]):
            raise Uncertain("dynamic forwarded argument")
        self.closed(forwards.target, args, kwargs, self.data[leaf], imports=True)
        self.hits += 1

    def guard(self, expr: ast.AST, env: dict[str, Any], sid: str, op: type[ast.cmpop]) -> Any:
        if (
            not isinstance(expr, ast.Compare)
            or len(expr.ops) != 1
            or not isinstance(expr.ops[0], op)
            or not isinstance(expr.left, ast.Name)
            or type(env.get(expr.left.id)) not in {str, int, bool}
            or not self.query.immutable(expr.comparators[0])
        ):
            return UNKNOWN
        return self.query.value(expr, env, sid)

    def closed(
        self,
        sid: str,
        args: list[Any],
        kwargs: dict[str, Any],
        values: dict[str, Any],
        *,
        imports: bool,
    ) -> None:
        """Audit a data-only function and its same-module calls."""
        self.tick()
        if sid in self.query.targets:
            raise Uncertain("edited callable reached")
        node = self.function(sid)
        path = self.index.nodes[sid].path
        if sid in self.query.stack or len(self.query.stack) >= MAX_DEPTH:
            raise Uncertain("closed branch recursion")
        env = self.bound(sid, args, kwargs)
        scope = audit(node.body, local=True)
        if scope.blocked or scope.wildcard:
            # Data-only assignment into local element slots is outside this slice.
            raise Uncertain("binding or namespace mutation")
        env = {
            name: value
            if type(value) in {str, int, bool, bytes, float} or value is None
            else UNKNOWN
            for name, value in env.items()
        }
        env.update(dict.fromkeys(scope.counts, UNKNOWN))
        self.query.stack.add(sid)
        try:
            self.closed_tree(
                node.body,
                path,
                sid,
                dict.fromkeys(values, UNKNOWN) | env,
                set(scope.counts),
                imports,
            )
        finally:
            self.query.stack.remove(sid)

    def closed_tree(
        self,
        body: list[ast.stmt],
        path: str,
        sid: str,
        env: dict[str, Any],
        locals_: set[str],
        imports: bool,
    ) -> None:
        # Imported handles may only be consumed by an immediate external data call.
        tree = self.index.syntax[sid]
        nodes = list(ast.walk(tree))
        self.tick(len(nodes))
        parents = {child: node for node in nodes for child in ast.iter_child_nodes(node)}
        assigned = {
            n.value: n.targets[0]
            for n in nodes
            if isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and isinstance(n.targets[0], ast.Name)
            and isinstance(n.value, ast.Call)
            and self.qualified(path, n.value.func) == "importlib.import_module"
        }
        stores = set(assigned.values())
        handles = {target.id for target in stores}
        if any(
            isinstance(n, ast.Name)
            and n.id in handles
            and isinstance(n.ctx, ast.Store)
            and n not in stores
            for n in nodes
        ):
            raise Uncertain("competing import handle")
        if any(isinstance(n, ast.ExceptHandler) and n.name in handles for n in nodes):
            raise Uncertain("competing exception binding")
        loaded = {n.id for n in nodes if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        if not handles <= loaded:
            raise Uncertain("unused external import")

        def external(expr: ast.AST) -> str:
            root = (dotted(expr) or "").partition(".")[0]
            return "" if root in locals_ or root in env else self.qualified(path, expr)

        def visit(part: ast.AST) -> None:
            self.tick()
            if isinstance(part, ast.If):
                visit(part.test)
                choice = self.guard(part.test, env, sid, ast.Eq)
                children = (
                    part.body + part.orelse
                    if choice is UNKNOWN
                    else part.body
                    if choice
                    else part.orelse
                )
                for statement in children:
                    visit(statement)
                return
            if isinstance(part, ast.Call):
                name = external(part.func)
                if name == "importlib.import_module":
                    if not imports or part not in assigned or len(part.args) != 1 or part.keywords:
                        raise Uncertain("dynamic import")
                    dest = self.query.value(part.args[0], env, sid)
                    if (
                        not isinstance(dest, str)
                        or not dest.isidentifier()
                        or any(m == dest or m.startswith(dest + ".") for m in self.resolver.modules)
                    ):
                        raise Uncertain("dynamic or project import")
                    return
                if isinstance(part.func, ast.Call):
                    getter = part.func
                    assignment = parents.get(part)
                    if not (
                        imports
                        and isinstance(assignment, ast.AnnAssign)
                        and isinstance(assignment.target, ast.Name)
                        and isinstance(assignment.annotation, ast.Name)
                        and assignment.annotation.id == "str"
                        and self.query.builtin(sid, "str")
                        and "str" not in locals_
                        and "str" not in env
                        and len(part.args) == 1
                        and not part.keywords
                        and isinstance(getter.func, ast.Name)
                        and getter.func.id == "getattr"
                        and getter.func.id not in locals_
                        and self.query.builtin(sid, "getattr")
                        and len(getter.args) == 2
                        and not getter.keywords
                        and isinstance(getter.args[0], ast.Name)
                        and getter.args[0].id in handles
                        and self.external_member(getter.args[1], visit)
                    ):
                        raise Uncertain("dynamic callable")
                elif isinstance(part.func, ast.Name):
                    key = part.func.id
                    target = (
                        None if key in locals_ or key in env else self.resolver.resolve(path, key)
                    )
                    if target and target.startswith(path + "::"):
                        binding = CallBinding(sid, target)
                        args, kwargs = self.query.supplied(part, binding, env)
                        self.closed(target, args, kwargs, self.data.get(path, {}), imports=imports)
                    elif (
                        key not in DATA_BUILTINS
                        or key in locals_
                        or key in env
                        or not (self.query.builtin(sid, key))
                    ):
                        raise Uncertain("unknown leaf call")
                elif name not in DATA_CALLS:
                    if (
                        not isinstance(part.func, ast.Attribute)
                        or part.func.attr not in DATA_METHODS
                    ):
                        raise Uncertain("effectful member call")
                    visit(part.func.value)
                for arg in [*part.args, *(kw.value for kw in part.keywords)]:
                    visit(arg)
                return
            if isinstance(part, ast.Name) and isinstance(part.ctx, ast.Load):
                if external(part) in DATA_NAMES:
                    return
                if (
                    part.id in handles
                    or part.id not in env
                    and part.id not in locals_
                    and not (part.id in DATA_BUILTINS and self.query.builtin(sid, part.id))
                ):
                    raise Uncertain("undeclared or escaping leaf value")
            elif isinstance(part, ast.Attribute):
                if external(part) in DATA_NAMES:
                    return
                if part.attr != "name" and not (
                    part.attr == "__name__"
                    and isinstance(part.value, ast.Call)
                    and isinstance(part.value.func, ast.Name)
                    and part.value.func.id == "type"
                ):
                    raise Uncertain("unsupported namespace access")
            elif isinstance(
                part,
                (
                    ast.Import,
                    ast.ImportFrom,
                    ast.Global,
                    ast.Nonlocal,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.With,
                    ast.AsyncWith,
                    ast.Yield,
                    ast.YieldFrom,
                    ast.Await,
                    ast.NamedExpr,
                    ast.Delete,
                    ast.Starred,
                ),
            ):
                raise Uncertain("unsupported leaf effect")
            elif isinstance(part, ast.Lambda):
                if (
                    part.args.defaults
                    or part.args.kw_defaults
                    or part.args.kwarg
                    or part.args.vararg
                ):
                    raise Uncertain("callback header")
                bound = {a.arg for a in part.args.args + part.args.posonlyargs}
                if bound & handles:
                    raise Uncertain("callback shadowing")
                with_scope(bound, lambda: visit(part.body))
                return
            elif isinstance(part, ast.AnnAssign):
                # Local variable annotations are not evaluated.
                visit(part.target)
                if part.value is not None:
                    visit(part.value)
                return
            if isinstance(part, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                captured = {
                    n for generator in part.generators for n in binding_names(generator.target)
                }
                if captured & handles:
                    raise Uncertain("comprehension shadows an import handle")
                with_scope(captured, lambda: visit_children(part))
                return
            visit_children(part)

        def visit_children(part: ast.AST) -> None:
            for child in ast.iter_child_nodes(part):
                visit(child)

        def with_scope(names: set[str], action: Callable[[], None]) -> None:
            prior = {k: env[k] for k in names & env.keys()}
            added = names - locals_
            locals_.update(added)
            env.update(dict.fromkeys(names, UNKNOWN))
            try:
                action()
            finally:
                for k in names:
                    env.pop(k)
                env.update(prior)
                locals_.difference_update(added)

        for stmt in body:
            visit(stmt)

    @staticmethod
    def external_member(expr: ast.AST, visit: Callable[[ast.AST], None]) -> bool:
        if isinstance(expr, ast.Constant):
            return (
                isinstance(expr.value, str)
                and expr.value.isidentifier()
                and not expr.value.startswith("_")
            )
        if isinstance(expr, ast.IfExp):
            visit(expr.test)
            return Proof.external_member(expr.body, visit) and Proof.external_member(
                expr.orelse, visit
            )
        return False

    def plain_testcase(self, path: str, owner: str, test: ast.FunctionDef) -> bool:
        """Require a plain TestCase namespace for loader, run and cleanup behavior."""
        cls = self.index.syntax.get(f"{path}::{owner}")
        if not (
            isinstance(cls, ast.ClassDef)
            and self.resolver.binding(path, cls.name) is cls
            and len(cls.bases) == 1
            and self.qualified(path, cls.bases[0], cls) == "unittest.TestCase"
            and test in cls.body
        ):
            return False
        # Unittest dispatches through more than setUp, the test and tearDown.
        # Prove the namespace contains only test methods and passive statements
        # instead of trying to enumerate every hook and state attribute.
        methods: set[str] = set()
        for member in cls.body:
            self.tick()
            if isinstance(member, ast.Pass) or (
                isinstance(member, ast.Expr)
                and isinstance(member.value, ast.Constant)
                and isinstance(member.value.value, str)
            ):
                continue
            if (
                not isinstance(member, ast.FunctionDef)
                or not member.name.startswith("test_")
                or member.decorator_list
                or member.name in methods
            ):
                return False
            methods.add(member.name)
        return True

    def test(self, sid: str) -> bool:
        node = self.index.syntax.get(sid)
        if not isinstance(node, ast.FunctionDef) or node.decorator_list:
            return False
        path, _, name = sid.partition("::")
        args = node.args
        if args.posonlyargs or args.kwonlyargs or args.vararg or args.kwarg or args.defaults:
            return False
        method = "." in name
        if [a.arg for a in args.args] != (["self"] if method else []):
            return False
        if method:
            owner, _, _ = name.rpartition(".")
            if not self.plain_testcase(path, owner, node):
                return False
        if {"setUpModule", "tearDownModule", "load_tests"} & self.resolver.scopes[
            path
        ].counts.keys():
            return False
        self.module(path)
        env: dict[str, Any] = {}
        # Local binding sites may never overwrite a source callable or unittest receiver.
        locals_ = audit(node.body, local=True)
        if (
            locals_.blocked
            or locals_.wildcard
            or (locals_.counts.keys() & (self.resolver.direct[path].keys() | {"self"}))
        ):
            return False

        def value(expr: ast.AST) -> Any:
            if isinstance(expr, ast.Call):
                self.dispatch(sid, expr, env)
                return UNKNOWN
            if isinstance(expr, ast.Name) and expr.id in env:
                return env[expr.id]
            data = self.query.value(expr, env, sid)
            if plain_data(data):
                return data
            raise Uncertain("unsupported test value")

        for stmt in node.body:
            self.tick()
            if (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
            ):
                env[stmt.targets[0].id] = value(stmt.value)
            elif isinstance(stmt, ast.Expr):
                expr = stmt.value
                if (
                    method
                    and isinstance(expr, ast.Call)
                    and dotted(expr.func) == "self.assertEqual"
                    and len(expr.args) == 2
                    and not expr.keywords
                ):
                    for arg in expr.args:
                        value(arg)
                else:
                    value(expr)
            elif (
                isinstance(stmt, ast.Assert)
                and isinstance(stmt.test, ast.Compare)
                and (
                    len(stmt.test.ops) == 1
                    and isinstance(stmt.test.ops[0], (ast.Eq, ast.NotEq))
                    and stmt.msg is None
                )
            ):
                value(stmt.test.left)
                value(stmt.test.comparators[0])
            else:
                raise Uncertain("unsupported test statement")
        return bool(self.hits)


class DispatchFallback:
    def __init__(self, before: "Index", after: "Index", guards: CallArgumentFilter):
        self.guards = guards
        self.unique_modules = all(
            len(names := [n.name for n in index.nodes.values() if n.kind == "module"])
            == len(set(names))
            for index in (before, after)
        )
        self.stable = {
            p
            for p in before.sources.keys() & after.sources.keys()
            if before.sources[p] == after.sources[p]
        }

    def allows(self, sid: str, path: str) -> bool:
        if not self.unique_modules or len(self.guards.changes.get(path, ())) != 1:
            return True
        for query in self.guards.queries[path]:
            if query.customized_functions:
                return True
            query.steps = 0
            try:
                if not Proof(query, path, self.stable).test(sid):
                    return True
            except (Uncertain, RecursionError, KeyError):
                return True
        return False
