"""Selection-only proof for a guarded method on a source-bound callable instance."""

import ast
from dataclasses import dataclass
from pathlib import PurePosixPath

from codeimpact.descriptor_binding import (
    Class,
    External,
    Function,
    Instance,
    Query,
    Scope,
    Stops,
    Unknown,
    Value,
)
from codeimpact.discovery import is_mixed_case_name
from codeimpact.partial_bindings import audit
from codeimpact.selection import References

PASSIVE_IMPORTS = {"datetime": "datetime", "contextlib": "contextmanager"}
SCALARS = {bool, int, float, str, bytes, type(None)}
MODULE_HOOKS = {
    "setUpModule",
    "tearDownModule",
    "load_tests",
    "setup_module",
    "teardown_module",
    "setup_function",
    "teardown_function",
    "pytestmark",
    "pytest_plugins",
}


def passive_import(node: ast.AST) -> str:
    if (
        isinstance(node, ast.ImportFrom)
        and not node.level
        and node.module is not None
        and len(node.names) == 1
        and node.names[0].asname is None
        and PASSIVE_IMPORTS.get(node.module) == node.names[0].name
    ):
        return node.module
    return ""


def statements(tree: ast.Module) -> list[ast.stmt]:
    """Normalize only adjacent independent imports with known passive bindings."""
    body = list(tree.body)
    # A repeated binding is left in order and will also decline the eager audit.
    for i, (first, second) in enumerate(zip(body, body[1:], strict=False)):
        a, b = passive_import(first), passive_import(second)
        if a and b and a > b:
            body[i : i + 2] = [second, first]
    return body


def header(node: ast.FunctionDef | ast.ClassDef) -> str:
    # Shallow copy keeps location-independent headers without mutating the index.
    return ast.dump(type(node)(**(dict(ast.iter_fields(node)) | {"body": []})))


@dataclass(frozen=True)
class GuardedEdit:
    target: ast.FunctionDef
    entry: ast.FunctionDef


def guarded_edit(cls: ast.ClassDef, target: ast.FunctionDef) -> GuardedEdit | None:
    if cls.bases or cls.keywords or cls.decorator_list or target.name.startswith("__"):
        return None
    params = target.args
    if (
        params.posonlyargs
        or len(params.args) != 1
        or params.vararg
        or params.kwarg
        or params.kwonlyargs
        or params.defaults
        or target.decorator_list
    ):
        return None
    for node in cls.body:
        if not isinstance(node, ast.FunctionDef) or not node.args.vararg or not node.args.args:
            continue
        receiver = node.args.args[0].arg
        for stmt in node.body:
            match stmt:
                case ast.If(test=ast.UnaryOp(op=ast.Not(), operand=ast.Name(id=name))):
                    if name != node.args.vararg.arg:
                        continue
                    for part in stmt.body:
                        expr = part.value if isinstance(part, (ast.Return, ast.Assign)) else part
                        match expr:
                            case ast.Call(func=ast.Attribute(value=ast.Name(id=obj), attr=attr)):
                                if obj == receiver and attr == target.name:
                                    return GuardedEdit(target, node)
    return None


def edits(
    before: References, after: References, path: str
) -> tuple[GuardedEdit, GuardedEdit] | None:
    sid = f"{path}::<module>"
    old, new = before.index.syntax.get(sid), after.index.syntax.get(sid)
    if not isinstance(old, ast.Module) or not isinstance(new, ast.Module):
        return None
    left, right = statements(old), statements(new)
    if len(left) != len(right):
        return None
    changed = [(a, b) for a, b in zip(left, right, strict=True) if ast.dump(a) != ast.dump(b)]
    if len(changed) != 1:
        return None
    a, b = changed[0]
    if (
        not isinstance(a, ast.ClassDef)
        or not isinstance(b, ast.ClassDef)
        or header(a) != header(b)
        or len(a.body) != len(b.body)
    ):
        return None
    members = [(x, y) for x, y in zip(a.body, b.body, strict=True) if ast.dump(x) != ast.dump(y)]
    if len(members) != 1:
        return None
    x, y = members[0]
    if (
        not isinstance(x, ast.FunctionDef)
        or not isinstance(y, ast.FunctionDef)
        or header(x) != header(y)
    ):
        return None
    prior, current = guarded_edit(a, x), guarded_edit(b, y)
    return (prior, current) if prior and current else None


class GuardQuery(Query):
    def __init__(self, refs: References, edit: GuardedEdit):
        super().__init__(refs, edit.target)
        self.entry = edit.entry
        self.calls: list[str] = []
        self.bypassed = False

    def imported(self, module: str, name: str = "") -> Value:
        # These two named standard-library imports commute. Everything else uses
        # the existing source module and eager initialization checks.
        if PASSIVE_IMPORTS.get(module) == name and module not in self.refs.modules:
            return External(f"{module}.{name}")
        return super().imported(module, name)

    def module(self, name: str) -> Scope:
        if name not in self.modules and (path := self.refs.modules.get(name)):
            side = self.refs.index.syntax.get(f"{path}::<module>")
            if not isinstance(side, ast.Module):
                raise Unknown("missing module source")
            bindings = audit(side.body)
            if bindings.wildcard or any(n > 1 for n in bindings.counts.values()):
                raise Unknown("ambiguous module namespace")
        return super().module(name)

    def class_definition(self, node: ast.ClassDef, scope: Scope) -> None:
        bindings = audit(node.body)
        if (
            node.decorator_list
            or any(n > 1 for n in bindings.counts.values())
            or any(
                not isinstance(member, (ast.Assign, ast.FunctionDef, ast.Pass))
                and not (
                    isinstance(member, ast.Expr)
                    and isinstance(member.value, ast.Constant)
                    and isinstance(member.value.value, str)
                )
                for member in node.body
            )
            or any(
                isinstance(member, ast.Assign)
                and not all(
                    isinstance(t, ast.Name) and not t.id.startswith("__") for t in member.targets
                )
                for member in node.body
            )
        ):
            raise Unknown("customized class namespace")
        super().class_definition(node, scope)

    def bind(self, target: ast.AST, value: Value, scope: Scope) -> None:
        if isinstance(target, ast.Attribute):
            # A write can update ordinary scalar state, but cannot replace a
            # bound method, descriptor or callable captured by construction.
            if not isinstance(target.value, ast.Name):
                raise Unknown("unproved receiver write")
            obj = scope.get(target.value.id)
            if not isinstance(obj, Instance) or obj.cls.custom or target.attr.startswith("__"):
                raise Unknown("unproved receiver write")
            member = self.member(obj.cls, target.attr)
            if target.attr in obj.attrs or member is not None:
                prior = obj.attrs.get(target.attr, member)
                if type(prior) not in SCALARS or type(value) not in SCALARS:
                    raise Unknown("non-scalar state change")
                obj.attrs[target.attr] = value
                return
        super().bind(target, value, scope)

    def call(self, fn: Function, args: list[Value], kwargs: dict[str, Value]) -> Value:
        self.calls.append(self.symbols.get(fn.node, ""))
        if (
            fn.node is self.entry
            and args
            and isinstance(args[0], Instance)
            and len(args) > len(fn.node.args.posonlyargs + fn.node.args.args)
        ):
            self.bypassed = True
        return super().call(fn, args, kwargs)

    def expr(self, node: ast.AST | None, scope: Scope) -> Value:
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            self.tick()
            return not self.truth(self.expr(node.operand, scope))
        return super().expr(node, scope)

    def test(self, sid: str) -> bool:
        # Construction, setUp and the test body are the only modeled entry points.
        path, _, name = sid.partition("::")
        owner, _, method = name.partition(".")
        if (
            not method
            or "." in method
            or any(PurePosixPath(p).name == "conftest.py" for p in self.refs.index.sources)
        ):
            return False
        module = self.refs.index.nodes[f"{path}::<module>"].name
        scope = self.module(module)
        if MODULE_HOOKS & scope.values.keys():
            return False
        cls = scope.values.get(owner)
        if (
            not isinstance(cls, Class)
            or cls.custom
            or len(cls.bases) != 1
            or not isinstance(cls.bases[0], External)
            or cls.bases[0].name != "unittest.TestCase"
        ):
            return False
        for key, fn in cls.attrs.items():
            if key != "setUp" and not (key.startswith("test_") or is_mixed_case_name(key)):
                return False
            if not isinstance(fn, Function) or fn.node.decorator_list:
                return False
            args = fn.node.args
            if (
                args.posonlyargs
                or len(args.args) != 1
                or args.vararg
                or args.kwarg
                or args.kwonlyargs
                or args.defaults
            ):
                return False
        test = cls.attrs.get(method)
        if not isinstance(test, Function) or test.node is not self.refs.index.syntax.get(sid):
            return False
        receiver = Instance(cls)
        setup = cls.attrs.get("setUp")
        if isinstance(setup, Function):
            self.call(setup, [receiver], {})
        self.call(test, [receiver], {})
        return self.bypassed


class VariadicFallback:
    def __init__(self, before: References, after: References, paths: set[str]):
        self.before, self.after = before, after
        shadowable = {*PASSIVE_IMPORTS, "unittest"}
        shadowed = any(
            candidate.stem in shadowable or bool(shadowable.intersection(candidate.parts[:-1]))
            for refs in (before, after)
            for path in refs.index.sources
            if (candidate := PurePosixPath(path))
        )
        self.changes = (
            {}
            if shadowed
            else {path: pair for path in sorted(paths) if (pair := edits(before, after, path))}
        )
        self.cache: dict[tuple[str, str], bool] = {}

    def allows(self, sid: str, path: str) -> bool:
        if path not in self.changes:
            return True
        key = (sid, path)
        if key not in self.cache:
            self.cache[key] = not self.excludes(sid, path)
        return self.cache[key]

    def excludes(self, sid: str, path: str) -> bool:
        try:
            old, new = self.changes[path]
            before, after = GuardQuery(self.before, old), GuardQuery(self.after, new)
            return (
                before.test(sid)
                and after.test(sid)
                and before.calls == after.calls
                and before.modules.keys() == after.modules.keys()
            )
        except (Unknown, Stops, KeyError, RecursionError):
            return False
