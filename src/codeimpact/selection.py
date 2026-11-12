"""Bounded source-only checks for aggregate class/module change propagation.

The graph and visible changes keep their existing identities. Deferred method and
function bodies do not by themselves change module initialization. Unresolved
member references can still justify conservative module paths; they never become
precise call edges merely because their spelling matches.
"""

import ast
import copy
from collections import defaultdict
from collections.abc import Iterator
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from codeimpact.analyzer import Index

FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
DEFINITIONS = (*FUNCTIONS, ast.ClassDef)
OTHER = "<non-instance>"
MAX_DEPTH = 24
MAX_VISITS = 2000
PROTOCOLS = {
    "repr": ("__repr__",),
    "str": ("__str__", "__repr__"),
    "len": ("__len__",),
    "bool": ("__bool__", "__len__"),
    "iter": ("__iter__", "__getitem__"),
    "next": ("__next__",),
}


def own_nodes(node: ast.AST) -> Iterator[ast.AST]:
    yield node
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, DEFINITIONS):
            yield from own_nodes(child)


def outline(node: ast.AST, *, constructor: bool = False, property_builtin: bool = True) -> str:
    """Retain initialization effects, excluding deferred definition bodies.

    Definition names/signatures remain visible changes and callable seeds. Only
    decorators and potentially effectful default expressions affect this outline.
    Class assignments, bases, metaclasses and compound-statement guards remain.
    """

    class Outline(ast.NodeTransformer):
        def visit_FunctionDef(
            self, fn: ast.FunctionDef | ast.AsyncFunctionDef
        ) -> ast.AST | list[ast.stmt]:
            if constructor and fn.name in {"__init__", "__new__"}:
                return fn
            decorators = [
                d
                for d in fn.decorator_list
                if not (property_builtin and isinstance(d, ast.Name) and d.id == "property")
            ]
            expressions = [
                *decorators,
                *fn.args.defaults,
                *(v for v in fn.args.kw_defaults if v is not None),
            ]
            effects = [
                value
                for value in expressions
                if value in decorators
                or any(
                    isinstance(n, (ast.Call, ast.NamedExpr, ast.Await, ast.Yield))
                    for n in ast.walk(value)
                )
            ]
            return [ast.Expr(value=value) for value in effects]

        def visit_AsyncFunctionDef(self, fn: ast.AsyncFunctionDef) -> ast.AST | list[ast.stmt]:
            return self.visit_FunctionDef(fn)

        def visit_Pass(self, node: ast.Pass) -> None:
            return None

        def visit_ClassDef(self, cls: ast.ClassDef) -> ast.ClassDef:
            # A class body executes now, unlike its method bodies.
            if property_builtin:
                cls.body = [s for s in cls.body if not property_binding(s)]
            self.generic_visit(cls)
            return cls

    return ast.dump(Outline().visit(copy.deepcopy(node)), include_attributes=False)


def property_binding(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "property"
        and bool(node.value.args)
        and not node.value.keywords
        and all(isinstance(a, (ast.Name, ast.Constant)) for a in node.value.args)
    )


def builtin_property(index: "Index", path: str) -> bool:
    tree = index.syntax[f"{path}::<module>"]
    return not any(
        isinstance(n, ast.Name)
        and n.id == "property"
        and isinstance(n.ctx, (ast.Store, ast.Del))
        or isinstance(n, DEFINITIONS)
        and n.name == "property"
        or isinstance(n, (ast.Import, ast.ImportFrom))
        and any((a.asname or a.name) in {"property", "*"} for a in n.names)
        for n in ast.walk(tree)
    )


def propagation_changes(before: "Index", after: "Index", changed: list[str]) -> list[str]:
    result = []
    for sid in changed:
        old, new = before.nodes.get(sid), after.nodes.get(sid)
        node = new or old
        assert node is not None
        if old is None or new is None or node.kind not in {"module", "class"}:
            result.append(sid)
        elif (
            before.sources[node.path].parse_status != "parsed"
            or after.sources[node.path].parse_status != "parsed"
        ):
            result.append(sid)
        elif outline(
            before.syntax[sid],
            constructor=node.kind == "class",
            property_builtin=builtin_property(before, node.path),
        ) != outline(
            after.syntax[sid],
            constructor=node.kind == "class",
            property_builtin=builtin_property(after, node.path),
        ):
            result.append(sid)
    return result


def declarations(index: "Index", path: str) -> dict[str, list[str]]:
    """Include conditional declarations without claiming they are resolvable."""
    result: dict[str, list[str]] = defaultdict(list)

    def visit(node: ast.AST, prefix: str = "") -> None:
        if isinstance(node, DEFINITIONS):
            prefix = f"{prefix}.{node.name}" if prefix else node.name
            if isinstance(node, FUNCTIONS):
                result[prefix].append(ast.dump(node, include_attributes=False))
        elif property_binding(node):
            assert isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
            result[f"{prefix}.{node.targets[0].id}"].append(
                ast.dump(node, include_attributes=False)
            )
        for child in ast.iter_child_nodes(node):
            visit(child, prefix)

    if tree := index.syntax.get(f"{path}::<module>"):
        visit(tree)
    return dict(result)


class References:
    """Possible source references, never proof of runtime receiver dispatch."""

    def __init__(self, index: "Index"):
        self.index = index
        self.module_cache: dict[str, frozenset[str]] = {}
        self.use_cache: dict[str, tuple[set[str], set[str]]] = {}
        self.type_cache: dict[tuple[ast.AST, str, str | None], str | None] = {}
        self.typing: set[tuple[ast.AST, str, str | None]] = set()
        self.scope_nodes = {sid: tuple(own_nodes(node)) for sid, node in index.syntax.items()}
        self.blocked: dict[str, set[str]] = {}
        self.binding_cache: dict[tuple[str, str], ast.expr | None] = {}
        self.spelling_cache: dict[tuple[str, str], str | None] = {}
        for sid, syntax_node in index.syntax.items():
            args = syntax_node.args if isinstance(syntax_node, FUNCTIONS) else None
            bound = (
                {a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]}
                if args
                else set()
            )
            if args:
                bound.update(a.arg for a in (args.vararg, args.kwarg) if a)
            bound.update(
                n.id
                for n in self.scope_nodes[sid]
                if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del))
            )
            self.blocked[sid] = bound
        self.names: dict[str, str] = {}
        self.modules: dict[str, str] = {}
        self.by_name: dict[str, list[str]] = defaultdict(list)
        self.module_imports: dict[str, set[str]] = defaultdict(set)
        self.property_names: dict[str, list[str]] = defaultdict(list)
        self.foreign_fields: set[str] = set()
        self.reflective_fields = False
        self.class_children: dict[str, set[str]] = defaultdict(set)
        for node in index.nodes.values():
            if node.kind == "module":
                self.modules[node.name] = node.path
        for sid, node in index.nodes.items():
            mod = index.nodes[f"{node.path}::<module>"].name
            self.names[mod if node.kind == "module" else f"{mod}.{node.name}"] = sid
            if node.kind in {"function", "test"}:
                self.by_name[node.name.split(".")[-1]].append(sid)
        for edge in index.edges.values():
            if edge.kind == "import":
                self.module_imports[index.nodes[edge.source].path].add(
                    index.nodes[edge.target].path
                )
        for sid, syntax in index.syntax.items():
            if isinstance(syntax, ast.ClassDef):
                for base in syntax.bases:
                    spelling = self.dotted(base)
                    parent = self.lookup(spelling, sid) if spelling else None
                    if parent and index.nodes[parent].kind == "class":
                        self.class_children[parent].add(sid)
                for statement in syntax.body:
                    if property_binding(statement):
                        assert isinstance(statement, ast.Assign) and isinstance(
                            statement.targets[0], ast.Name
                        )
                        self.property_names[statement.targets[0].id].append(sid)
            owner = self.owner(sid)
            parameters = (
                syntax.args.posonlyargs + syntax.args.args if isinstance(syntax, FUNCTIONS) else []
            )
            for part in self.scope_nodes[sid]:
                if isinstance(part, ast.Attribute) and isinstance(part.ctx, (ast.Store, ast.Del)):
                    if not (
                        owner
                        and parameters
                        and isinstance(part.value, ast.Name)
                        and part.value.id == parameters[0].arg
                    ):
                        self.foreign_fields.add(part.attr)
                elif (
                    isinstance(part, ast.Call)
                    and isinstance(part.func, ast.Name)
                    and part.func.id in {"setattr", "delattr"}
                ):
                    if (
                        len(part.args) > 1
                        and isinstance(part.args[1], ast.Constant)
                        and isinstance(part.args[1].value, str)
                    ):
                        self.foreign_fields.add(part.args[1].value)
                    else:
                        self.reflective_fields = True

    def available(self, path: str) -> frozenset[str]:
        if path in self.module_cache:
            return self.module_cache[path]
        found = {path}
        todo = [path]
        while todo:
            current = todo.pop()
            for dep in self.module_imports[current] - found:
                found.add(dep)
                todo.append(dep)
        self.module_cache[path] = frozenset(found)
        return self.module_cache[path]

    def owner(self, sid: str) -> str | None:
        path, name = sid.split("::")
        while "." in name:
            name = name.rsplit(".", 1)[0]
            candidate = f"{path}::{name}"
            if candidate in self.index.nodes and self.index.nodes[candidate].kind == "class":
                return candidate
        return None

    def scope_modules(self, sid: str) -> set[str]:
        available = set(self.available(self.index.nodes[sid].path))
        owner = self.owner(sid)
        todo = [owner] if owner else []
        seen = set()
        while todo:
            cls = todo.pop()
            if cls in seen:
                continue
            seen.add(cls)
            available.update(self.available(self.index.nodes[cls].path))
            todo.extend(sorted(self.class_children[cls] - seen))
        return available

    def expanded(self, name: str, sid: str) -> str | None:
        """Resolve lexical/import spelling without trusting shadowed bindings."""
        key = (name, sid)
        if key not in self.spelling_cache:
            self.spelling_cache[key] = self._expanded(name, sid)
        return self.spelling_cache[key]

    def _expanded(self, name: str, sid: str) -> str | None:
        path, qualified = sid.split("::")
        root, _, tail = name.partition(".")
        local = self.index.local_bindings.get(sid)
        if local and root in local.bound:
            binding = local.aliases.get(root)
            return binding[0] + ("." + tail if tail else "") if binding else None
        if root in self.blocked[sid] or root in self.index.ambiguous.get(path, set()):
            return None
        aliases = self.index.aliases.get(path, {})
        if root in aliases:
            return aliases[root] + ("." + tail if tail else "")
        mod = self.index.nodes[f"{path}::<module>"].name
        scope = qualified.split(".")
        while scope:
            possible = ".".join([mod, *scope, name])
            if possible in self.names:
                return possible
            scope.pop()
        return f"{mod}.{name}"

    def lookup(self, name: str, sid: str) -> str | None:
        expanded = self.expanded(name, sid)
        seen = set()
        while expanded and expanded not in seen:
            if expanded in self.names:
                return self.names[expanded]
            seen.add(expanded)
            parent, _, member = expanded.rpartition(".")
            if parent not in self.modules:
                return None
            path = self.modules[parent]
            if member in self.index.ambiguous.get(path, set()):
                return None
            imported = self.index.aliases.get(path, {}).get(member)
            if imported:
                expanded = imported
            else:
                module = f"{path}::<module>"
                value = self.expression_binding(member, module)
                spelling = self.dotted(value) if value is not None else None
                # An assignment alias is a possible reference, never a new call edge.
                expanded = self._expanded(spelling, module) if spelling else None
        return None

    @staticmethod
    def dotted(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = References.dotted(node.value)
            if parent:
                return parent + "." + node.attr
        return None

    def expression_binding(self, name: str, sid: str) -> ast.expr | None:
        key = (name, sid)
        if key in self.binding_cache:
            return self.binding_cache[key]
        candidates = []
        for part in self.scope_nodes[sid]:
            if isinstance(part, (ast.Assign, ast.AnnAssign)):
                targets = part.targets if isinstance(part, ast.Assign) else [part.target]
                if any(isinstance(t, ast.Name) and t.id == name for t in targets):
                    candidates.append(part.value)
        result = candidates[0] if len(candidates) == 1 else None
        self.binding_cache[key] = result
        return result

    def local_value_types(
        self, name: str, sid: str, depth: int, receiver: str | None
    ) -> str | None:
        node = self.index.syntax[sid]
        if isinstance(node, FUNCTIONS):
            args = node.args
            if name in {
                a.arg
                for a in [
                    *args.posonlyargs,
                    *args.args,
                    *args.kwonlyargs,
                    *([args.vararg] if args.vararg else []),
                    *([args.kwarg] if args.kwarg else []),
                ]
            }:
                return None
        values: list[ast.expr | None] = []
        stores = 0
        for part in self.scope_nodes[sid]:
            if isinstance(part, (ast.Global, ast.Nonlocal)) and name in part.names:
                return None
            if (
                isinstance(part, ast.Name)
                and part.id == name
                and isinstance(part.ctx, (ast.Store, ast.Del))
            ):
                stores += 1
            if isinstance(part, (ast.Assign, ast.AnnAssign)):
                targets = part.targets if isinstance(part, ast.Assign) else [part.target]
                values.extend(
                    part.value
                    for target in targets
                    if isinstance(target, ast.Name) and target.id == name
                )
        if not values or stores != len(values):
            return None
        kinds = {self.class_of(value, sid, depth + 1, receiver) for value in values}
        return next(iter(kinds)) if len(kinds) == 1 else None

    def member(self, cls: str, name: str, depth: int = 0) -> str | None:
        if depth > MAX_DEPTH:
            return None
        sid = cls + "." + name
        if sid in self.index.syntax:
            return sid
        node = self.index.syntax[cls]
        if not isinstance(node, ast.ClassDef):
            return None
        assignment = self.expression_binding(name, cls)
        if (
            isinstance(assignment, ast.Call)
            and isinstance(assignment.func, ast.Name)
            and assignment.func.id == "property"
            and assignment.args
        ):
            getter = assignment.args[0]
            if isinstance(getter, ast.Name) and cls + "." + getter.id in self.index.syntax:
                return cls + "." + getter.id
        # Multiple inheritance is ambiguous for this small receiver proof.
        if len(node.bases) == 1:
            base_name = self.dotted(node.bases[0])
            base = self.lookup(base_name, cls) if base_name else None
            if base and self.index.nodes[base].kind == "class":
                return self.member(base, name, depth + 1)
        return None

    def is_property(self, cls: str, attr: str, member: str) -> bool:
        node = self.index.syntax[member]
        return any(
            isinstance(d, ast.Name) and d.id == "property"
            for d in getattr(node, "decorator_list", [])
        ) or isinstance(self.expression_binding(attr, cls), ast.Call)

    def safe_instance(self, cls: str, depth: int = 0) -> bool:
        if depth > MAX_DEPTH:
            return False
        node = self.index.syntax[cls]
        if not isinstance(node, ast.ClassDef) or node.decorator_list or node.keywords:
            return False
        for base in node.bases:
            spelling = self.dotted(base)
            target = self.lookup(spelling, cls) if spelling else None
            if target and self.index.nodes[target].kind == "class":
                if not self.safe_instance(target, depth + 1):
                    return False
            elif not (
                isinstance(base, ast.Name)
                and base.id
                in {"object", "str", "bytes", "int", "float", "tuple", "list", "dict", "set"}
                and base.id not in self.index.aliases.get(self.index.nodes[cls].path, {})
            ):
                return False
        new = self.member(cls, "__new__")
        if new:
            returns = [
                n.value for n in own_nodes(self.index.syntax[new]) if isinstance(n, ast.Return)
            ]
            # Conventional immutable builtin subclass allocation is type preserving.
            if not returns or not all(
                isinstance(v, ast.Call)
                and isinstance(v.func, ast.Attribute)
                and v.func.attr == "__new__"
                and v.args
                and isinstance(v.args[0], ast.Name)
                and v.args[0].id == "cls"
                and isinstance(v.func.value, ast.Call)
                and isinstance(v.func.value.func, ast.Name)
                and v.func.value.func.id == "super"
                for v in returns
            ):
                return False
        return True

    def call_target(self, expr: ast.AST, sid: str, depth: int = 0) -> str | None:
        if depth > MAX_DEPTH:
            return None
        spelling = self.dotted(expr)
        target = self.lookup(spelling, sid) if spelling else None
        if target:
            return target
        if isinstance(expr, ast.Name):
            value = self.expression_binding(expr.id, sid)
            if isinstance(value, ast.Call) and (spelling := self.dotted(value.func)):
                expanded = self.expanded(spelling, sid)
                if expanded == "functools.partial" and value.args:
                    return self.call_target(value.args[0], sid, depth + 1)
            if value is not None:
                return self.call_target(value, sid, depth + 1)
        if isinstance(expr, ast.Attribute):
            cls = self.class_of(expr.value, sid, depth + 1)
            if cls and cls != OTHER:
                return self.member(cls, expr.attr)
        return None

    def returns_type(self, target: str, receiver: str | None, depth: int) -> str | None:
        node = self.index.syntax[target]
        if not isinstance(node, FUNCTIONS):
            return None
        # Only a terminal return is proof of no implicit fallthrough.
        if not node.body or not isinstance(node.body[-1], ast.Return):
            return None
        returns = [n.value for n in own_nodes(node) if isinstance(n, ast.Return)]
        types = {self.class_of(v, target, depth + 1, receiver) for v in returns if v is not None}
        return next(iter(types)) if len(types) == 1 and len(returns) > 0 else None

    def class_of(
        self, expr: ast.AST | None, sid: str, depth: int = 0, receiver: str | None = None
    ) -> str | None:
        if expr is None or depth > MAX_DEPTH:
            return None
        key = (expr, sid, receiver)
        if key in self.typing:
            return None
        if key not in self.type_cache:
            self.typing.add(key)
            try:
                self.type_cache[key] = self._class_of(expr, sid, depth, receiver)
            finally:
                self.typing.remove(key)
        return self.type_cache[key]

    def _class_of(self, expr: ast.AST, sid: str, depth: int, receiver: str | None) -> str | None:
        if depth > MAX_DEPTH or expr is None:
            return None
        if isinstance(expr, (ast.Constant, ast.Lambda)):
            return OTHER
        # Container protocols may dispatch on their elements. Keep those receivers
        # unknown instead of treating a container of source instances as independent.
        if isinstance(expr, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
            return None
        if isinstance(expr, ast.Name):
            node = self.index.syntax[sid]
            args = node.args if isinstance(node, FUNCTIONS) else None
            if (
                args
                and args.args
                and expr.id == args.args[0].arg
                and self.owner(sid)
                and not any(
                    isinstance(d, ast.Name) and d.id == "staticmethod"
                    for d in getattr(node, "decorator_list", [])
                )
            ):
                owner = self.owner(sid)
                return receiver or (owner if owner and not self.class_children[owner] else None)
            if expr.id in self.blocked[sid]:
                return self.local_value_types(expr.id, sid, depth, receiver)
            target = self.lookup(expr.id, sid)
            if target:
                # Class objects can expose static/class methods through aliases.
                # Keep their attributes unresolved rather than proving no dependency.
                return None if self.index.nodes[target].kind == "class" else OTHER
            path = self.index.nodes[sid].path
            module = f"{path}::<module>"
            if sid != module:
                value = self.expression_binding(expr.id, module)
                if value is not None:
                    return self.class_of(value, module, depth + 1)
        if isinstance(expr, ast.Call):
            spelling = self.dotted(expr.func)
            if spelling and self.expanded(spelling, sid) == "functools.partial":
                return OTHER
            target = self.call_target(expr.func, sid, depth + 1)
            if target:
                if self.index.nodes[target].kind == "class":
                    return target if self.safe_instance(target) else None
                cls = (
                    self.class_of(expr.func.value, sid, depth + 1, receiver)
                    if isinstance(expr.func, ast.Attribute)
                    else None
                )
                return self.returns_type(target, cls if cls != OTHER else None, depth + 1)
        if isinstance(expr, ast.Attribute):
            # Imported module singleton, e.g. api.default_scheduler.
            spelling = self.dotted(expr)
            expanded = self.expanded(spelling, sid) if spelling else None
            if expanded:
                mod, _, name = expanded.rpartition(".")
                if mod in self.modules:
                    module = f"{self.modules[mod]}::<module>"
                    value = self.expression_binding(name, module)
                    if value is not None:
                        return self.class_of(value, module, depth + 1)
            cls = self.class_of(expr.value, sid, depth + 1, receiver)
            if cls and cls != OTHER:
                member = self.member(cls, expr.attr)
                if member and self.is_property(cls, expr.attr, member):
                    return self.returns_type(member, cls, depth + 1)
                # Simple class-owned field assignments, not arbitrary data flow.
                if expr.attr in self.foreign_fields or self.reflective_fields:
                    return None
                values = []
                for key, node in self.index.syntax.items():
                    if self.owner(key) != cls or not isinstance(node, FUNCTIONS):
                        continue
                    parameters = node.args.posonlyargs + node.args.args
                    if not parameters:
                        continue
                    for n in self.scope_nodes[key]:
                        if isinstance(n, (ast.Assign, ast.AnnAssign)):
                            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                            if any(
                                isinstance(t, ast.Attribute)
                                and t.attr == expr.attr
                                and isinstance(t.value, ast.Name)
                                and t.value.id == parameters[0].arg
                                for t in targets
                            ):
                                values.append(self.class_of(n.value, key, depth + 1, cls))
                if values and len(set(values)) == 1:
                    return values[0]
        return None

    def possible(self, sid: str) -> tuple[set[str], set[str]]:
        if sid not in self.use_cache:
            self.use_cache[sid] = self._possible(sid)
        return self.use_cache[sid]

    def is_builtin(self, name: str, sid: str) -> bool:
        path = self.index.nodes[sid].path
        local = self.index.local_bindings.get(sid)
        module = f"{path}::<module>"
        return not (
            name in self.blocked[sid]
            or (local and name in local.bound)
            or name in self.blocked[module]
            or name in self.index.aliases.get(path, {})
            or name in self.index.ambiguous.get(path, set())
            or self.lookup(name, sid)
        )

    def _possible(self, sid: str) -> tuple[set[str], set[str]]:
        node = self.index.syntax[sid]
        available = self.scope_modules(sid)
        targets = set()
        hints: set[str] = set()
        if isinstance(node, ast.ClassDef):
            return {m for name in ("__init__", "__new__") if (m := self.member(sid, name))}, hints
        for part in self.scope_nodes[sid]:
            if isinstance(part, ast.Name) and isinstance(part.ctx, ast.Load):
                target = self.lookup(part.id, sid)
                if target:
                    if self.index.nodes[target].kind in {"function", "test"}:
                        targets.add(target)
                else:
                    expanded = self.expanded(part.id, sid)
                    if expanded:
                        hints.add(expanded)
            if isinstance(part, ast.Attribute) and isinstance(part.ctx, ast.Load):
                spelling = self.dotted(part)
                target = self.lookup(spelling, sid) if spelling else None
                if target and self.index.nodes[target].kind in {"function", "test"}:
                    targets.add(target)
                cls = self.class_of(part.value, sid)
                if cls == OTHER:
                    continue
                if cls:
                    member = self.member(cls, part.attr)
                    class_node = self.index.syntax[cls]
                    cls_node = self.index.nodes[cls]
                    module_name = self.index.nodes[f"{cls_node.path}::<module>"].name
                    hints.add(f"{module_name}.{cls_node.name}.{part.attr}")
                    if member:
                        targets.add(member)
                    elif isinstance(class_node, ast.ClassDef) and len(class_node.bases) > 1:
                        targets.update(
                            c
                            for c in self.by_name[part.attr]
                            if self.index.nodes[c].path in available
                        )
                else:
                    targets.update(
                        c for c in self.by_name[part.attr] if self.index.nodes[c].path in available
                    )
                    for owner in self.property_names[part.attr]:
                        cls_node = self.index.nodes[owner]
                        if cls_node.path in available:
                            module_name = self.index.nodes[f"{cls_node.path}::<module>"].name
                            hints.add(f"{module_name}.{cls_node.name}.{part.attr}")
            if isinstance(part, ast.Call):
                target = self.call_target(part.func, sid)
                if target:
                    if self.index.nodes[target].kind == "class":
                        targets.update(
                            m
                            for name in ("__init__", "__new__")
                            if (m := self.member(target, name))
                        )
                    else:
                        targets.add(target)
                if (
                    isinstance(part.func, ast.Name)
                    and part.func.id in PROTOCOLS
                    and self.is_builtin(part.func.id, sid)
                    and part.args
                ):
                    class_object = self.call_target(part.args[0], sid)
                    if (
                        class_object
                        and self.index.nodes[class_object].kind == "class"
                        and self.safe_instance(class_object)
                    ):
                        continue  # repr(C) dispatches on type, not C.__repr__.
                    protocols = PROTOCOLS[part.func.id]
                    cls = self.class_of(part.args[0], sid)
                    if cls == OTHER:
                        continue
                    if cls:
                        for protocol in protocols:
                            if member := self.member(cls, protocol):
                                targets.add(member)
                                break
                    else:
                        targets.update(
                            c
                            for position, protocol in enumerate(protocols)
                            for c in self.by_name[protocol]
                            if self.index.nodes[c].path in available
                            and (
                                not (protocol_owner := self.owner(c))
                                or not any(
                                    self.member(protocol_owner, prior)
                                    for prior in protocols[:position]
                                )
                                or isinstance(
                                    part.args[0], (ast.List, ast.Tuple, ast.Set, ast.Dict)
                                )
                            )
                        )
        return targets, hints


class AggregateFallback:
    def __init__(self, before: "Index", after: "Index", paths: set[str]) -> None:
        self.before = References(before)
        self.after = References(after)
        self.changed = {}
        self.broad: set[str] = set()
        for path in sorted(paths):
            old, new = declarations(before, path), declarations(after, path)
            self.changed[path] = {
                name for name in old.keys() | new.keys() if old.get(name) != new.get(name)
            }
            modeled = {p for protocols in PROTOCOLS.values() for p in protocols}
            modeled.update({"__init__", "__new__"})
            if any(
                (leaf := name.rsplit(".", 1)[-1]).startswith("__")
                and leaf.endswith("__")
                and leaf not in modeled
                for name in self.changed[path]
            ):
                self.broad.add(path)
                after.warnings.append(
                    f"Conservative fallback retained: unmodeled protocol change in {path}"
                )
        self.cache: dict[tuple[str, str], bool] = {}

    def allows(self, sid: str, path: str) -> bool:
        if path in self.broad:
            return True
        key = (sid, path)
        if key in self.cache:
            return self.cache[key]
        result = self.reaches(self.before, sid, path) or self.reaches(self.after, sid, path)
        self.cache[key] = result
        return result

    def reaches(self, refs: References, sid: str, path: str) -> bool:
        todo = [sid]
        seen = set()
        changed = self.changed[path]
        while todo:
            current = todo.pop()
            if current in seen or current not in refs.index.syntax:
                continue
            seen.add(current)
            if len(seen) > MAX_VISITS:
                refs.index.warnings.append(
                    f"Conservative fallback retained: reference budget exceeded for {sid}"
                )
                return True  # Budget uncertainty retains fallback.
            current_path, name = current.split("::")
            if current_path == path and name in changed:
                return True
            targets, hints = refs.possible(current)
            module = refs.index.nodes.get(f"{path}::<module>")
            if module and any(f"{module.name}.{name}" in hints for name in changed):
                return True
            todo.extend(sorted(targets - seen))
        return False
