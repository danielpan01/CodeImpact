"""Bounded AST data flow for changes confined to class default bindings.

This is an exclusion check, not a Python runtime or a source executor. Unknown
calls, reflective operations, unsupported control flow and exhausted budgets keep
recommendations. It adds no graph edges and never upgrades evidence to resolved.
"""

import ast
import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from codeimpact.selection import FUNCTIONS, References, outline

if TYPE_CHECKING:
    from codeimpact.analyzer import Index

MAX_STEPS = 12000
MAX_DEPTH = 24
MAX_STATES = 16
MAX_ITEMS = 64
MAX_TEXT = 4096
DIGEST_FUNCTIONS = {"md5", "sha1", "sha224", "sha256", "sha384", "sha512"}


def dump(node: ast.AST) -> str:
    return ast.dump(node, include_attributes=False)


def binding(node: ast.AST) -> tuple[str, ast.expr] | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target, value = node.targets[0], node.value
    elif isinstance(node, ast.AnnAssign) and node.value is not None:
        target, value = node.target, node.value
    else:
        return None
    return (target.id, value) if isinstance(target, ast.Name) else None


def passive(node: ast.AST) -> bool:
    if isinstance(node, (ast.Name, ast.Constant)):
        return True
    if isinstance(node, ast.Attribute):
        return passive(node.value)
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "staticmethod"
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], (ast.Name, ast.Attribute))
    )


def builtin_unbound(index: "Index", path: str, name: str) -> bool:
    return not any(
        isinstance(n, ast.Name)
        and n.id == name
        and isinstance(n.ctx, (ast.Store, ast.Del))
        or isinstance(n, (ast.FunctionDef, ast.ClassDef))
        and n.name == name
        or isinstance(n, (ast.Import, ast.ImportFrom))
        and any((a.asname or a.name) in {name, "*"} for a in n.names)
        for n in ast.walk(index.syntax[f"{path}::<module>"])
    )


def default_value(
    node: ast.expr, index: "Index", path: str, seen: frozenset[str] = frozenset()
) -> bool:
    """Do not hide descriptor construction or user-defined staticmethod effects."""
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Call):
        if not passive(node):
            return False
        if not builtin_unbound(index, path, "staticmethod"):
            return False
        return default_value(node.args[0], index, path, seen)
    spelling = References.dotted(node)
    if not spelling or spelling in seen or len(seen) > MAX_DEPTH:
        return False
    root, _, tail = spelling.partition(".")
    if root in index.ambiguous.get(path, set()):
        return False
    imported = index.aliases.get(path, {}).get(root)
    if imported:
        qualified = imported + ("." + tail if tail else "")
        module, _, member = qualified.rpartition(".")
        return module == "hashlib" and member in DIGEST_FUNCTIONS
    if isinstance(node, ast.Name):
        target = index.syntax.get(f"{path}::{node.id}")
        if isinstance(target, ast.FunctionDef):
            return not target.decorator_list
        tree = index.syntax[f"{path}::<module>"]
        assert isinstance(tree, ast.Module)
        values = [b[1] for n in tree.body if (b := binding(n)) and b[0] == node.id]
        return len(values) == 1 and default_value(values[0], index, path, seen | {spelling})
    return False


@dataclass
class DefaultChange:
    path: str
    fields: set[tuple[str, str]]
    helpers: set[str]


def default_change(before: "Index", after: "Index", path: str) -> DefaultChange | None:
    """Require the entire module difference to fit the supported change shape."""
    old = copy.deepcopy(before.syntax.get(f"{path}::<module>"))
    new = copy.deepcopy(after.syntax.get(f"{path}::<module>"))
    if not isinstance(old, ast.Module) or not isinstance(new, ast.Module):
        return None
    if any(
        not builtin_unbound(index, path, name)
        for index in (before, after)
        for name in ("staticmethod", "property")
    ):
        return None
    fields: set[tuple[str, str]] = set()
    referenced: set[str] = set()
    old_classes = {n.name: n for n in old.body if isinstance(n, ast.ClassDef)}
    new_classes = {n.name: n for n in new.body if isinstance(n, ast.ClassDef)}
    for tree, classes in ((old, old_classes), (new, new_classes)):
        if not passive_body(tree.body, classes, module=True):
            return None
    for name in sorted(old_classes.keys() & new_classes.keys()):
        left, right = old_classes[name], new_classes[name]
        if not plain_class(left, old_classes) or not plain_class(right, new_classes):
            continue
        pairs = [
            {entry[0]: (n, entry[1]) for n in c.body if (entry := binding(n))}
            for c in (left, right)
        ]
        for attr in sorted(pairs[0].keys() & pairs[1].keys()):
            a, b = pairs[0][attr], pairs[1][attr]
            if dump(a[1]) == dump(b[1]) or not passive(a[1]) or not passive(b[1]):
                continue
            if not default_value(a[1], before, path) or not default_value(b[1], after, path):
                continue
            # Repeated/conditional definitions and descriptor factories are not this proof.
            if any(
                sum(entry[0] == attr for n in c.body if (entry := binding(n)) is not None) != 1
                for c in (left, right)
            ):
                continue
            fields.add((f"{path}::{name}", attr))
            referenced.update(
                n.id for v in (a[1], b[1]) for n in ast.walk(v) if isinstance(n, ast.Name)
            )
            for node, _ in (a, b):
                assert isinstance(node, (ast.Assign, ast.AnnAssign))
                node.value = ast.Constant(value=None)
    if not fields:
        return None
    helpers: set[str] = set()
    old_functions = {n.name: n for n in old.body if isinstance(n, FUNCTIONS)}
    new_functions = {n.name: n for n in new.body if isinstance(n, FUNCTIONS)}
    for tree, other in ((old, new_functions), (new, old_functions)):
        for node in list(tree.body):
            if isinstance(node, FUNCTIONS) and node.name not in other and node.name in referenced:
                if node.decorator_list or any(
                    not isinstance(v, ast.Constant)
                    for v in [
                        *node.args.defaults,
                        *(d for d in node.args.kw_defaults if d is not None),
                    ]
                ):
                    return None
                annotations = [
                    a.annotation
                    for a in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
                    if a.annotation is not None
                ]
                if node.returns:
                    annotations.append(node.returns)
                if any(
                    isinstance(part, (ast.Call, ast.NamedExpr))
                    for annotation in annotations
                    for part in ast.walk(annotation)
                ):
                    return None
                helpers.add(f"{path}::{node.name}")
                tree.body.remove(node)
    if dump(old) != dump(new):
        return None
    return DefaultChange(path, fields, helpers)


def plain_class(
    node: ast.ClassDef, classes: dict[str, ast.ClassDef], seen: frozenset[str] = frozenset()
) -> bool:
    if node.name in seen or len(seen) > MAX_DEPTH or node.decorator_list or node.keywords:
        return False
    if not passive_body(node.body, classes):
        return False
    if any(isinstance(n, FUNCTIONS) and n.name == "__init_subclass__" for n in node.body):
        return False
    for statement in node.body:
        if isinstance(statement, ast.AnnAssign) and any(
            isinstance(part, (ast.Call, ast.NamedExpr)) for part in ast.walk(statement.annotation)
        ):
            return False
        if isinstance(statement, FUNCTIONS):
            if any(
                not isinstance(d, ast.Name) or d.id not in {"property", "staticmethod"}
                for d in statement.decorator_list
            ):
                return False
            defaults = [
                *statement.args.defaults,
                *(d for d in statement.args.kw_defaults if d is not None),
                *(
                    a.annotation
                    for a in [
                        *statement.args.posonlyargs,
                        *statement.args.args,
                        *statement.args.kwonlyargs,
                    ]
                    if a.annotation is not None
                ),
                *([statement.returns] if statement.returns is not None else []),
            ]
            if any(
                isinstance(part, (ast.Call, ast.NamedExpr))
                for value in defaults
                for part in ast.walk(value)
            ):
                return False
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id == "object":
            continue
        if not isinstance(base, ast.Name) or base.id not in classes:
            return False
        if not plain_class(classes[base.id], classes, seen | {node.name}):
            return False
    return True


def passive_body(
    body: list[ast.stmt], classes: dict[str, ast.ClassDef], *, module: bool = False
) -> bool:
    """The exclusion proof does not interpret arbitrary initialization effects."""
    for statement in body:
        if isinstance(statement, FUNCTIONS):
            if module and statement.decorator_list:
                return False
            if module:
                header = ast.ClassDef(
                    name="<header>",
                    bases=[],
                    keywords=[],
                    body=[statement],
                    decorator_list=[],
                    type_params=[],
                )
                if not plain_class(header, {}):
                    return False
        elif isinstance(statement, ast.ClassDef):
            if not module or not plain_class(statement, classes):
                return False
        elif isinstance(statement, (ast.Import, ast.ImportFrom)):
            if not module:
                return False
        elif isinstance(statement, ast.Expr):
            if not isinstance(statement.value, ast.Constant) or not isinstance(
                statement.value.value, str
            ):
                return False
        elif isinstance(statement, ast.Pass):
            continue
        elif (assigned := binding(statement)) is None or not passive(assigned[1]):
            return False
    return True


@dataclass(eq=False)
class Value:
    kind: str
    name: str = ""
    literal: str | bytes | int | float | bool | None = None
    items: tuple["Value", ...] = ()
    fields: dict[str, "Value"] = field(default_factory=dict)
    receiver: "Value | None" = None


UNKNOWN = Value("unknown")
OPAQUE = Value("opaque")
NONE = Value("literal")
RAISED = Value("raised")


def literal(value: str | bytes | int | float | bool | None) -> Value:
    return NONE if value is None else Value("literal", literal=value)


def contains(needle: object, haystack: object) -> bool:
    if isinstance(needle, str) and isinstance(haystack, str):
        return needle in haystack
    return isinstance(needle, bytes) and isinstance(haystack, bytes) and needle in haystack


def same_data(left: Value, right: Value, depth: int = 0) -> bool:
    if left is right:
        return True
    if depth > MAX_DEPTH or left.kind != right.kind:
        return False
    if left.kind in {"literal", "ref", "external", "unknown", "opaque"}:
        return (left.name, left.literal) == (right.name, right.literal)
    if left.kind in {"dict", "tuple", "list"}:
        return (
            left.fields.keys() == right.fields.keys()
            and len(left.items) == len(right.items)
            and all(same_data(left.fields[k], right.fields[k], depth + 1) for k in left.fields)
            and all(
                same_data(a, b, depth + 1) for a, b in zip(left.items, right.items, strict=True)
            )
        )
    return False


def join(values: list[Value]) -> Value:
    found: list[Value] = []
    for value in values:
        for item in value.items if value.kind == "choice" else (value,):
            if not any(same_data(item, prev) for prev in found):
                found.append(item)
    if len(found) > MAX_STATES:
        raise Uncertain("value alternatives")
    if len(found) > 1 and all(
        v.kind == "dict" and v.fields.keys() == found[0].fields.keys() for v in found
    ):
        return Value(
            "dict", fields={k: join([v.fields[k] for v in found]) for k in found[0].fields}
        )
    return found[0] if len(found) == 1 else Value("choice", items=tuple(found)) if found else NONE


class Uncertain(Exception):
    """Unsupported source semantics retain the existing recommendation."""


@dataclass
class Frame:
    sid: str
    env: dict[str, Value]
    flow: str = "live"
    result: Value = field(default_factory=lambda: NONE)
    yielded: list[Value] = field(default_factory=list)


class Query:
    def __init__(self, refs: References, change: DefaultChange):
        self.refs = refs
        self.index = refs.index
        self.change = change
        self.hit = False
        self.steps = 0
        self.depth = 0
        self.resolving: set[tuple[str, str]] = set()

    def tick(self) -> None:
        self.steps += 1
        if self.steps > MAX_STEPS or self.depth > MAX_DEPTH:
            raise Uncertain("argument tracking budget")

    def truth(self, value: Value) -> bool | None:
        if value.kind == "literal":
            return bool(value.literal)
        if value.kind in {"list", "tuple", "dict"}:
            return bool(value.items or value.fields)
        if value.kind in {"ref", "partial"} or self.known_external_callable(value):
            return True
        return None

    def known_external_callable(self, value: Value) -> bool:
        # Explicit standard-library digest functions are non-None callable values.
        # Arbitrary imported settings may be None and must keep both branches.
        module, _, name = value.name.rpartition(".")
        return (
            value.kind == "external"
            and module == "hashlib"
            and name in DIGEST_FUNCTIONS
            and name not in self.refs.foreign_fields
            and not self.refs.reflective_fields
        )

    def name(self, name: str, frame: Frame) -> Value:
        if name in frame.env:
            return frame.env[name]
        if name in self.refs.blocked[frame.sid]:
            return UNKNOWN
        sid = self.refs.lookup(name, frame.sid)
        if sid:
            if sid in self.change.helpers:
                self.hit = True
            return Value("ref", name=sid)
        path = self.index.nodes[frame.sid].path
        module = f"{path}::<module>"
        key = (module, name)
        if key in self.resolving:
            raise Uncertain("cyclic binding")
        expr = self.refs.expression_binding(name, module)
        if expr is not None:
            self.resolving.add(key)
            try:
                return self.expr(expr, Frame(module, {}))
            finally:
                self.resolving.remove(key)
        expanded = self.refs.expanded(name, frame.sid)
        if expanded and name in self.index.aliases.get(path, {}):
            module_name, _, attribute = expanded.rpartition(".")
            source_path = self.refs.modules.get(module_name)
            if source_path:
                source_module = f"{source_path}::<module>"
                imported = self.refs.expression_binding(attribute, source_module)
                if imported is not None:
                    imported_key = (source_module, attribute)
                    if imported_key in self.resolving:
                        raise Uncertain("cyclic imported binding")
                    self.resolving.add(imported_key)
                    try:
                        return self.expr(imported, Frame(source_module, {}))
                    finally:
                        self.resolving.remove(imported_key)
            return Value("external", name=expanded)
        if self.refs.is_builtin(name, frame.sid) and name in {
            "str",
            "bytes",
            "dict",
            "list",
            "tuple",
            "set",
            "isinstance",
            "staticmethod",
            "len",
            "bool",
            "reversed",
            "next",
            "object",
            "super",
            "ValueError",
            "TypeError",
            "NotImplementedError",
            "Exception",
        }:
            return Value("external", name=name)
        return UNKNOWN

    def class_member(
        self, cls: str, name: str, depth: int = 0
    ) -> tuple[str, ast.expr | str] | None:
        if depth > MAX_DEPTH:
            raise Uncertain("inheritance depth")
        node = self.index.syntax[cls]
        if not isinstance(node, ast.ClassDef):
            return None
        assignments = [entry[1] for n in node.body if (entry := binding(n)) and entry[0] == name]
        if len(assignments) > 1:
            raise Uncertain("competing class binding")
        if assignments:
            return cls, assignments[0]
        method = cls + "." + name
        if method in self.index.syntax:
            return cls, method
        for base in node.bases:
            if (
                isinstance(base, ast.Subscript)
                and self.refs.expanded(self.refs.dotted(base.value) or "", cls) == "typing.Generic"
            ):
                continue
            spelling = self.refs.dotted(base)
            target = self.refs.lookup(spelling, cls) if spelling else None
            if target and self.index.nodes[target].kind == "class":
                result = self.class_member(target, name, depth + 1)
                if result:
                    return result
            elif spelling not in {"object", "Exception"}:
                raise Uncertain("unknown base")
        return None

    def attr(self, value: Value, name: str, frame: Frame) -> Value:
        if value.kind == "raised":
            return RAISED
        if value.kind == "choice":
            return join([self.attr(v, name, frame) for v in value.items])
        if value.kind in {"instance", "request"} and name in value.fields:
            return value.fields[name]
        if value.kind in {"instance", "ref"} and self.index.nodes[value.name].kind == "class":
            member = self.class_member(value.name, name)
            if member:
                owner, target = member
                if (owner, name) in self.change.fields:
                    self.hit = True
                if isinstance(target, ast.expr):
                    return self.expr(target, Frame(owner, {}))
                node = self.index.syntax[target]
                decorators = getattr(node, "decorator_list", [])
                if any(isinstance(d, ast.Name) and d.id == "property" for d in decorators):
                    return self.invoke(Value("bound", name=target, receiver=value), [], {})
                static = any(isinstance(d, ast.Name) and d.id == "staticmethod" for d in decorators)
                return Value(
                    "ref" if static or value.kind == "ref" else "bound",
                    name=target,
                    receiver=None if static else value,
                )
            return UNKNOWN
        if value.kind == "external":
            return Value("external", name=f"{value.name}.{name}")
        if value.kind in {"literal", "text_parts", "list", "tuple", "dict", "opaque"}:
            return Value("builtin_method", name=name, receiver=value)
        return UNKNOWN

    def expr(self, node: ast.AST | None, frame: Frame) -> Value:
        self.tick()
        if node is None:
            return NONE
        if isinstance(node, ast.Constant):
            if node.value is None or isinstance(node.value, (str, bytes, int, float, bool)):
                if isinstance(node.value, (str, bytes)) and len(node.value) > MAX_TEXT:
                    raise Uncertain("literal size")
                return literal(node.value)
            return OPAQUE
        if isinstance(node, ast.Name):
            return self.name(node.id, frame)
        if isinstance(node, ast.Attribute):
            return self.attr(self.expr(node.value, frame), node.attr, frame)
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            if len(node.elts) > MAX_ITEMS:
                raise Uncertain("container size")
            return Value(
                "tuple" if isinstance(node, ast.Tuple) else "list",
                items=tuple(self.expr(n, frame) for n in node.elts),
            )
        if isinstance(node, ast.Dict):
            mapping_result: dict[str, Value] = {}
            for key_node, val in zip(node.keys, node.values, strict=True):
                if key_node is None:
                    mapping = self.expr(val, frame)
                    if mapping.kind != "dict":
                        return UNKNOWN
                    mapping_result.update(mapping.fields)
                else:
                    k = self.expr(key_node, frame)
                    if k.kind != "literal" or not isinstance(k.literal, str):
                        return UNKNOWN
                    mapping_result[k.literal] = self.expr(val, frame)
            return Value("dict", fields=mapping_result)
        if isinstance(node, ast.Call):
            callee = self.expr(node.func, frame)
            args: list[Value] = []
            kwargs: dict[str, Value] = {}
            for arg in node.args:
                if isinstance(arg, ast.Starred):
                    value = self.expr(arg.value, frame)
                    if value.kind not in {"list", "tuple"}:
                        raise Uncertain("unknown positional expansion")
                    args.extend(value.items)
                else:
                    args.append(self.expr(arg, frame))
            for keyword in node.keywords:
                value = self.expr(keyword.value, frame)
                if keyword.arg is None:
                    if value.kind != "dict":
                        raise Uncertain("unknown keyword expansion")
                    additions = value.fields
                else:
                    additions = {keyword.arg: value}
                if kwargs.keys() & additions.keys():
                    raise Uncertain("duplicate keyword")
                kwargs.update(additions)
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "super"
                and callee.name == "super"
            ):
                owner = self.refs.owner(frame.sid)
                if owner:
                    cls_node = self.index.syntax[owner]
                    assert isinstance(cls_node, ast.ClassDef)
                    if len(cls_node.bases) == 1:
                        spelling = self.refs.dotted(cls_node.bases[0])
                        base = self.refs.lookup(spelling, owner) if spelling else None
                        if base:
                            return Value(
                                "instance", name=base, fields=frame.env.get("self", UNKNOWN).fields
                            )
                return Value("external", name="object")
            return self.invoke(callee, args, kwargs)
        if isinstance(node, ast.BoolOp):
            result = self.expr(node.values[0], frame)
            for part in node.values[1:]:
                state = self.truth(result)
                if (isinstance(node.op, ast.Or) and state is True) or (
                    isinstance(node.op, ast.And) and state is False
                ):
                    return result
                right = self.expr(part, frame)
                result = join([result, right]) if state is None else right
            return result
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            a, b = self.expr(node.left, frame), self.expr(node.comparators[0], frame)
            op = node.ops[0]
            if isinstance(op, (ast.Is, ast.IsNot)) and b.kind == "literal" and b.literal is None:
                known = a.kind not in {
                    "unknown",
                    "opaque",
                    "choice",
                    "external",
                } or self.known_external_callable(a)
                return (
                    literal((a.kind == "literal" and a.literal is None) == isinstance(op, ast.Is))
                    if known
                    else UNKNOWN
                )
            if self.carries_source(a) or self.carries_source(b) or "unknown" in {a.kind, b.kind}:
                raise Uncertain("implicit comparison protocol")
            if a.kind == b.kind == "literal":
                if isinstance(op, (ast.Eq, ast.NotEq)):
                    return literal((a.literal == b.literal) == isinstance(op, ast.Eq))
                if (
                    isinstance(op, (ast.In, ast.NotIn))
                    and isinstance(a.literal, (str, bytes))
                    and isinstance(b.literal, type(a.literal))
                ):
                    return literal(contains(a.literal, b.literal) == isinstance(op, ast.In))
            if (
                isinstance(op, (ast.In, ast.NotIn))
                and a.kind == "literal"
                and b.kind == "text_parts"
            ):
                if any(
                    isinstance(a.literal, (str, bytes))
                    and isinstance(p.literal, type(a.literal))
                    and contains(a.literal, p.literal)
                    for p in b.items
                ):
                    return literal(isinstance(op, ast.In))
            return UNKNOWN
        if isinstance(node, ast.UnaryOp):
            value = self.expr(node.operand, frame)
            if isinstance(node.op, ast.Not) and (state := self.truth(value)) is not None:
                return literal(not state)
            return OPAQUE
        if isinstance(node, ast.BinOp):
            a, b = self.expr(node.left, frame), self.expr(node.right, frame)
            if self.carries_source(a) or self.carries_source(b) or "unknown" in {a.kind, b.kind}:
                raise Uncertain("implicit operator protocol")
            if (
                isinstance(node.op, ast.Add)
                and a.kind == b.kind == "literal"
                and isinstance(a.literal, (str, bytes))
                and isinstance(b.literal, type(a.literal))
            ):
                if len(a.literal) + len(b.literal) > MAX_TEXT:
                    raise Uncertain("literal size")
                return literal(a.literal + b.literal)  # type: ignore[operator]
            return OPAQUE
        if isinstance(node, ast.Subscript):
            value, key = self.expr(node.value, frame), self.expr(node.slice, frame)
            if value.kind == "dict" and key.kind == "literal" and isinstance(key.literal, str):
                return value.fields.get(key.literal, UNKNOWN)
            if (
                value.kind in {"tuple", "list"}
                and key.kind == "literal"
                and isinstance(key.literal, int)
                and -len(value.items) <= key.literal < len(value.items)
            ):
                return value.items[key.literal]
            return UNKNOWN if value.kind == "unknown" else OPAQUE
        if isinstance(node, ast.JoinedStr):
            parts = [
                self.expr(n.value if isinstance(n, ast.FormattedValue) else n, frame)
                for n in node.values
            ]
            if any(self.carries_source(part) or part.kind == "unknown" for part in parts):
                raise Uncertain("implicit formatting protocol")
            return Value(
                "text_parts",
                items=tuple(p for p in parts if p.kind == "literal" and isinstance(p.literal, str)),
            )
        if isinstance(node, ast.IfExp):
            condition = self.truth(self.expr(node.test, frame))
            if condition is not None:
                return self.expr(node.body if condition else node.orelse, frame)
            return join([self.expr(node.body, frame), self.expr(node.orelse, frame)])
        if isinstance(node, (ast.ListComp, ast.GeneratorExp)):
            scopes = [Frame(frame.sid, dict(frame.env))]
            uncertain_length = False
            for generator in node.generators:
                next_scopes = []
                for local in scopes:
                    for item in self.elements(self.expr(generator.iter, local)):
                        nested = Frame(frame.sid, dict(local.env))
                        self.assign(generator.target, item, nested)
                        conditions = [
                            self.truth(self.expr(condition, nested)) for condition in generator.ifs
                        ]
                        uncertain_length |= None in conditions
                        if False not in conditions:
                            next_scopes.append(nested)
                if len(next_scopes) > MAX_ITEMS:
                    raise Uncertain("comprehension budget")
                scopes = next_scopes
            return Value(
                "sequence" if uncertain_length else "list",
                items=tuple(self.expr(node.elt, local) for local in scopes),
            )
        if isinstance(node, (ast.Yield, ast.YieldFrom)):
            value = self.expr(node.value, frame)
            frame.yielded.extend(
                self.elements(value) if isinstance(node, ast.YieldFrom) else [value]
            )
            return NONE
        if isinstance(node, ast.Lambda):
            raise Uncertain("lambda callable")
        raise Uncertain(f"expression {type(node).__name__}")

    def elements(self, value: Value) -> list[Value]:
        if value.kind in {"list", "tuple", "choice"}:
            return list(value.items)
        raise Uncertain("unknown iteration")

    def assign(self, target: ast.AST, value: Value, frame: Frame) -> None:
        if isinstance(target, ast.Name):
            frame.env[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            items = (
                value.items
                if value.kind in {"list", "tuple"} and len(value.items) == len(target.elts)
                else (OPAQUE if value.kind == "opaque" else UNKNOWN,) * len(target.elts)
            )
            for part, item in zip(target.elts, items, strict=True):
                self.assign(part, item, frame)
        elif isinstance(target, ast.Attribute):
            receiver = self.expr(target.value, frame)
            if receiver.kind != "instance" or receiver is value:
                raise Uncertain("attribute mutation")
            receiver.fields[target.attr] = value
        elif isinstance(target, ast.Subscript):
            receiver, key = self.expr(target.value, frame), self.expr(target.slice, frame)
            if receiver.kind != "dict" or key.kind != "literal" or not isinstance(key.literal, str):
                raise Uncertain("mapping mutation")
            receiver.fields[key.literal] = value
        else:
            raise Uncertain("assignment target")

    def block(self, statements: list[ast.stmt], frames: list[Frame]) -> list[Frame]:
        for statement in statements:
            updated = []
            for frame in frames:
                self.tick()
                if frame.flow != "live":
                    updated.append(frame)
                    continue
                if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                    if statement.value is not None:
                        value = self.expr(statement.value, frame)
                        if value is RAISED:
                            frame.flow = "raise"
                        else:
                            for target in (
                                statement.targets
                                if isinstance(statement, ast.Assign)
                                else [statement.target]
                            ):
                                self.assign(target, value, frame)
                elif isinstance(statement, ast.Expr):
                    if self.expr(statement.value, frame) is RAISED:
                        frame.flow = "raise"
                elif isinstance(statement, ast.Return):
                    frame.result = self.expr(statement.value, frame)
                    frame.flow = "raise" if frame.result is RAISED else "return"
                elif isinstance(statement, ast.Raise):
                    self.expr(statement.exc, frame)
                    self.expr(statement.cause, frame)
                    frame.flow = "raise"
                elif isinstance(statement, ast.If):
                    condition = self.truth(self.expr(statement.test, frame))
                    if condition is None:
                        updated.extend(self.block(statement.body, [copy.deepcopy(frame)]))
                        updated.extend(self.block(statement.orelse, [copy.deepcopy(frame)]))
                    else:
                        updated.extend(
                            self.block(statement.body if condition else statement.orelse, [frame])
                        )
                    continue
                elif isinstance(statement, ast.For):
                    items = self.elements(self.expr(statement.iter, frame))
                    nested = [frame]
                    for item in items:
                        for current in nested:
                            self.assign(statement.target, item, current)
                        nested = self.block(statement.body, nested)
                    updated.extend(self.block(statement.orelse, nested))
                    continue
                elif isinstance(statement, ast.With):
                    catches = False
                    for context_item in statement.items:
                        expr = context_item.context_expr
                        if (
                            isinstance(expr, ast.Call)
                            and self.refs.expanded(self.refs.dotted(expr.func) or "", frame.sid)
                            == "pytest.raises"
                        ):
                            catches = True
                            for arg in expr.args:
                                self.expr(arg, frame)
                        else:
                            raise Uncertain("context manager")
                        if context_item.optional_vars:
                            self.assign(context_item.optional_vars, OPAQUE, frame)
                    nested = self.block(statement.body, [frame])
                    for current in nested:
                        if catches and current.flow == "raise":
                            current.flow = "live"
                    updated.extend(nested)
                    continue
                elif isinstance(statement, ast.Try):
                    start = copy.deepcopy(frame)
                    nested = self.block(statement.body, [frame])
                    nested = self.block(statement.orelse, nested)
                    for handler in statement.handlers:
                        caught = copy.deepcopy(start)
                        if handler.name:
                            caught.env[handler.name] = OPAQUE
                        nested.extend(self.block(handler.body, [caught]))
                    if statement.finalbody:
                        raise Uncertain("finally flow")
                    updated.extend(nested)
                    continue
                elif isinstance(statement, ast.Assert):
                    self.expr(statement.test, frame)
                    self.expr(statement.msg, frame)
                elif isinstance(statement, (ast.Import, ast.ImportFrom)):
                    local = self.index.local_bindings.get(frame.sid)
                    for alias in statement.names:
                        name = alias.asname or alias.name.split(".")[0]
                        if local and name in local.aliases:
                            imported_target = self.refs.lookup(name, frame.sid)
                            frame.env[name] = (
                                Value("ref", name=imported_target)
                                if imported_target
                                else Value("external", name=local.aliases[name][0])
                            )
                        else:
                            frame.env[name] = UNKNOWN
                elif isinstance(statement, ast.Pass):
                    pass
                elif isinstance(statement, ast.AugAssign):
                    self.expr(statement.value, frame)
                    self.assign(statement.target, OPAQUE, frame)
                else:
                    raise Uncertain(f"statement {type(statement).__name__}")
                updated.append(frame)
            if len(updated) > MAX_STATES:
                raise Uncertain("branch budget")
            frames = updated
        return frames

    def function(
        self, sid: str, args: list[Value], kwargs: dict[str, Value], *, provider: bool = False
    ) -> Value:
        self.tick()
        node = self.index.syntax[sid]
        if not isinstance(node, ast.FunctionDef):
            raise Uncertain("non-function target")
        if not provider and self.index.nodes[sid].kind != "test":
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Name) or decorator.id not in {
                    "staticmethod",
                    "property",
                }:
                    raise Uncertain("decorated callable")
        parameters = node.args.posonlyargs + node.args.args
        if len(args) > len(parameters) and node.args.vararg is None:
            raise Uncertain("excess positional arguments")
        env: dict[str, Value] = {}
        supplied = dict(kwargs)
        defaults = dict(
            zip(
                [p.arg for p in parameters[len(parameters) - len(node.args.defaults) :]],
                node.args.defaults,
                strict=True,
            )
        )
        for position, parameter in enumerate(parameters):
            if position < len(args):
                if parameter.arg in supplied:
                    raise Uncertain("duplicate argument")
                env[parameter.arg] = args[position]
            elif parameter.arg in supplied and parameter not in node.args.posonlyargs:
                env[parameter.arg] = supplied.pop(parameter.arg)
            elif parameter.arg in defaults:
                if not isinstance(defaults[parameter.arg], ast.Constant):
                    raise Uncertain("captured or mutable definition default")
                env[parameter.arg] = self.expr(defaults[parameter.arg], Frame(sid, {}))
            else:
                env[parameter.arg] = UNKNOWN
        for parameter, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True):
            if (
                parameter.arg not in supplied
                and default is not None
                and not isinstance(default, ast.Constant)
            ):
                raise Uncertain("captured or mutable definition default")
            env[parameter.arg] = (
                supplied.pop(parameter.arg)
                if parameter.arg in supplied
                else self.expr(default, Frame(sid, {}))
                if default is not None
                else UNKNOWN
            )
        if node.args.vararg:
            env[node.args.vararg.arg] = Value("tuple", items=tuple(args[len(parameters) :]))
        if node.args.kwarg:
            env[node.args.kwarg.arg] = Value("dict", fields=supplied)
        elif supplied:
            raise Uncertain("unexpected keyword")
        local = self.index.local_bindings.get(sid)
        if local:
            for name in sorted(local.bound - env.keys()):
                env[name] = UNKNOWN
        self.depth += 1
        try:
            frames = self.block(node.body, [Frame(sid, env)])
        finally:
            self.depth -= 1
        normal = [f for f in frames if f.flow != "raise"]
        # Branch copies must not lose receiver writes before subsequent method calls.
        for name, value in env.items():
            if value.kind in {"instance", "dict"}:
                receivers = [f.env.get(name, UNKNOWN) for f in normal]
                keys = {k for v in receivers for k in v.fields}
                for key in sorted(keys):
                    value.fields[key] = join([v.fields.get(key, UNKNOWN) for v in receivers])
        if any(f.yielded for f in frames):
            return Value("list", items=tuple(v for f in frames for v in f.yielded))
        return join([f.result for f in normal]) if normal else RAISED

    def invoke(self, callee: Value, args: list[Value], kwargs: dict[str, Value]) -> Value:
        self.tick()
        if callee.kind == "choice":
            return join([self.invoke(v, args, kwargs) for v in callee.items])
        if callee.kind == "partial":
            assert callee.receiver is not None
            return self.invoke(callee.receiver, [*callee.items, *args], callee.fields | kwargs)
        if callee.kind in {"bound", "ref"}:
            sid = callee.name
            if sid in self.change.helpers:
                self.hit = True
            if self.index.nodes[sid].kind == "class":
                node = self.index.syntax[sid]
                assert isinstance(node, ast.ClassDef)
                if node.decorator_list or node.keywords or len(node.bases) > 1:
                    raise Uncertain("class customization")
                for special in ("__new__", "__getattribute__", "__getattr__", "__setattr__"):
                    if self.class_member(sid, special):
                        raise Uncertain("custom instance semantics")
                obj = Value("instance", name=sid)
                init = self.class_member(sid, "__init__")
                if init:
                    if not isinstance(init[1], str):
                        raise Uncertain("non-method initializer")
                    result = self.function(init[1], [obj, *args], kwargs)
                    if result is RAISED:
                        return RAISED
                elif args or kwargs:
                    raise Uncertain("unknown constructor arguments")
                return obj
            return self.function(
                sid,
                ([callee.receiver] if callee.kind == "bound" and callee.receiver else []) + args,
                kwargs,
            )
        if callee.kind == "external":
            name = callee.name
            if name == "functools.partial":
                if not args:
                    raise Uncertain("empty partial")
                return Value("partial", receiver=args[0], items=tuple(args[1:]), fields=kwargs)
            if name == "staticmethod":
                return args[0] if len(args) == 1 else UNKNOWN
            if name in {"typing.cast", "typing_extensions.cast"}:
                return args[1] if len(args) == 2 else UNKNOWN
            if name == "isinstance" and len(args) == 2:
                value, kind = args
                types = self.elements(kind) if kind.kind == "tuple" else [kind]
                actual = type(value.literal).__name__ if value.kind == "literal" else value.kind
                if value.kind in {"literal", "list", "tuple", "dict"} and all(
                    t.kind == "external"
                    and t.name in {"str", "bytes", "int", "bool", "dict", "list", "tuple", "set"}
                    for t in types
                ):
                    return literal(actual in {t.name for t in types})
                return UNKNOWN
            if name in {"list", "tuple", "reversed"}:
                items = self.elements(args[0]) if args else []
                return Value(
                    "tuple" if name == "tuple" else "list",
                    items=tuple(reversed(items) if name == "reversed" else items),
                )
            if name == "next":
                return join(self.elements(args[0])) if args else UNKNOWN
            if name == "dict":
                return (
                    Value(
                        "dict",
                        fields=(args[0].fields if args and args[0].kind == "dict" else {}) | kwargs,
                    )
                    if not args or args[0].kind == "dict"
                    else UNKNOWN
                )
            if name in {"len", "bool"} and args:
                state = self.truth(args[0])
                return literal(state) if name == "bool" and state is not None else OPAQUE
            if any(self.carries_source(v) for v in [*args, *kwargs.values()]):
                raise Uncertain("source object escaped to external callable")
            return OPAQUE
        if callee.kind == "builtin_method" and callee.receiver:
            value = callee.receiver
            if callee.name in {"encode", "decode"}:
                if value.kind == "text_parts":
                    converted = [
                        self.invoke(
                            Value("builtin_method", name=callee.name, receiver=v), args, kwargs
                        )
                        for v in value.items
                    ]
                    return Value("text_parts", items=tuple(converted))
                encoding = args[0].literal if args and args[0].kind == "literal" else "utf-8"
                if not isinstance(encoding, str) or encoding not in {"ascii", "utf-8"}:
                    return OPAQUE
                if value.kind == "literal":
                    try:
                        if callee.name == "encode" and isinstance(value.literal, str):
                            return literal(value.literal.encode(encoding))
                        if callee.name == "decode" and isinstance(value.literal, bytes):
                            return literal(value.literal.decode(encoding))
                    except UnicodeError:
                        return RAISED
            if callee.name in {"append", "update", "extend", "pop", "clear", "setdefault"}:
                raise Uncertain("container mutation method")
            return OPAQUE
        if callee is RAISED:
            return RAISED
        raise Uncertain("unresolved callable")

    def carries_source(self, value: Value, depth: int = 0) -> bool:
        if depth > MAX_DEPTH:
            return True
        return value.kind in {"instance", "ref", "bound", "partial"} or any(
            self.carries_source(v, depth + 1) for v in [*value.items, *value.fields.values()]
        )

    def factory_provider(self, sid: str, name: str) -> Value:
        owner = self.refs.owner(sid)
        path = self.index.nodes[sid].path
        candidates = [f"{owner}.{name}"] if owner else []
        candidates.append(f"{path}::{name}")
        for candidate in candidates:
            node = self.index.syntax.get(candidate)
            if not isinstance(node, ast.FunctionDef):
                continue
            fixture = next(
                (
                    d
                    for d in node.decorator_list
                    if isinstance(d, ast.Call)
                    and self.refs.expanded(self.refs.dotted(d.func) or "", candidate)
                    == "pytest.fixture"
                ),
                None,
            )
            if fixture is None or len(node.decorator_list) != 1:
                return UNKNOWN
            body = [
                n
                for n in node.body
                if not (
                    isinstance(n, ast.Expr)
                    and isinstance(n.value, ast.Constant)
                    and isinstance(n.value.value, str)
                )
            ]
            if len(body) != 1 or not isinstance(body[0], ast.Return):
                return UNKNOWN
            parameters = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
            if any(p.arg not in {"self", "request"} for p in parameters):
                return UNKNOWN
            options = next((k.value for k in fixture.keywords if k.arg == "params"), None)
            params = self.expr(options, Frame(candidate, {})) if options else NONE
            if options and params.kind not in {"tuple", "list"}:
                return UNKNOWN
            request = Value(
                "request", fields={"param": join(list(params.items)) if options else UNKNOWN}
            )
            args = [
                Value("instance", name=owner) if p.arg == "self" and owner else request
                for p in parameters
            ]
            result = self.function(candidate, args, {}, provider=True)
            # A direct immutable/literal data fixture can supply argument values.
            # Calls and dependency-producing fixtures are not inferred this way.
            returned = body[0].value
            literal_data = returned is not None and all(
                isinstance(n, (ast.Constant, ast.Dict, ast.List, ast.Tuple, ast.Load))
                for n in ast.walk(returned)
            )
            return (
                result if result.kind in {"partial", "ref", "choice"} or literal_data else UNKNOWN
            )
        return UNKNOWN

    def depends(self, sid: str) -> bool:
        node = self.index.syntax.get(sid)
        if not isinstance(node, ast.FunctionDef):
            return True
        args = []
        for parameter in node.args.posonlyargs + node.args.args:
            owner = self.refs.owner(sid)
            if parameter.arg == "self" and owner:
                args.append(Value("instance", name=owner))
            else:
                args.append(self.factory_provider(sid, parameter.arg))
        self.function(sid, args, {})
        return self.hit


class ArgumentFallback:
    def __init__(self, before: "Index", after: "Index", paths: set[str]):
        self.changes = {p: c for p in sorted(paths) if (c := default_change(before, after, p))}
        self.refs = (References(before), References(after)) if self.changes else ()
        self.cache: dict[tuple[str, str], bool] = {}
        self.passive_import_modules: set[str] = set()
        if self.changes:
            helpers = {h for change in self.changes.values() for h in change.helpers}
            for path in sorted(before.sources.keys() & after.sources.keys()):
                trees = []
                for refs in self.refs:
                    tree = copy.deepcopy(refs.index.syntax.get(f"{path}::<module>"))
                    if not isinstance(tree, ast.Module):
                        break
                    for statement in list(tree.body):
                        if not isinstance(statement, ast.ImportFrom):
                            continue
                        retained = []
                        for alias in statement.names:
                            name = alias.asname or alias.name
                            target = refs.lookup(name, f"{path}::<module>")
                            source_path = target.split("::")[0] if target else ""
                            already_imported = all(
                                any(
                                    e.source == f"{path}::<module>"
                                    and e.target == f"{source_path}::<module>"
                                    and e.kind == "import"
                                    for e in index.edges.values()
                                )
                                for index in (before, after)
                            )
                            same_statement = any(
                                other is not alias
                                and (
                                    other_target := refs.lookup(
                                        other.asname or other.name, f"{path}::<module>"
                                    )
                                )
                                and other_target not in helpers
                                and other_target.split("::")[0] == source_path
                                for other in statement.names
                            )
                            already_imported = already_imported and (
                                same_statement
                                or self.imported_before(refs, path, source_path, statement.lineno)
                            )
                            if target not in helpers or not already_imported:
                                retained.append(alias)
                        statement.names = retained
                        if not retained:
                            tree.body.remove(statement)
                    trees.append(tree)
                if len(trees) == 2 and outline(trees[0]) == outline(trees[1]):
                    self.passive_import_modules.add(f"{path}::<module>")

    @staticmethod
    def imported_before(refs: References, path: str, dependency: str, line: int) -> bool:
        """Only eager module imports can establish prior initialization."""
        imports = [
            e
            for e in refs.index.edges.values()
            if e.kind == "import" and refs.index.nodes[e.source].kind == "module"
        ]
        todo = [
            e.target
            for e in imports
            if e.source == f"{path}::<module>"
            and any(item.location.line < line for item in e.evidence)
        ]
        seen = set()
        while todo:
            current = todo.pop()
            if current == f"{dependency}::<module>":
                return True
            if current not in seen:
                seen.add(current)
                todo.extend(
                    e.target for e in imports if e.source == current and e.target not in seen
                )
        return False

    def allows(self, sid: str, path: str) -> bool:
        key = (sid, path)
        if key not in self.cache:
            depends = False
            for refs in self.refs:
                if sid not in refs.index.syntax:
                    continue
                try:
                    depends |= Query(refs, self.changes[path]).depends(sid)
                except (Uncertain, RecursionError):
                    depends = True
            self.cache[key] = depends
        return self.cache[key]
