"""Narrow aggregate fallback for body-only edits within source mapping classes.

This query follows possible references with bounded receiver context. It does not
execute operations, synthesize protocol edges or prove that omitted tests are safe.
Unknown receivers, customization and budget exhaustion retain existing evidence.
"""

import ast
import copy
from typing import TYPE_CHECKING

from codeimpact.selection import (
    FUNCTIONS,
    MAX_DEPTH,
    MAX_VISITS,
    OTHER,
    PROTOCOLS,
    References,
    own_nodes,
)

if TYPE_CHECKING:
    from codeimpact.analyzer import Index

ITEM_METHODS = frozenset({"__getitem__", "__setitem__", "__delitem__"})
MAPPING_METHODS = ITEM_METHODS | {
    "__contains__",
    "__iter__",
    "__len__",
    "get",
    "keys",
    "items",
    "values",
    "pop",
    "popitem",
    "clear",
    "update",
    "setdefault",
}
ABC_BASES = {"collections.abc.Mapping", "collections.abc.MutableMapping"}


def methods_in(tree: ast.AST, prefix: str = "") -> dict[str, ast.FunctionDef]:
    found = {}
    names: set[str] = set()
    for child in ast.iter_child_nodes(tree):
        if isinstance(child, (ast.ClassDef, *FUNCTIONS)):
            if child.name in names:
                raise ValueError("Ambiguous definition")
            names.add(child.name)
        if isinstance(child, ast.ClassDef):
            found.update(methods_in(child, f"{prefix}.{child.name}" if prefix else child.name))
        elif isinstance(child, ast.FunctionDef) and prefix:
            found[f"{prefix}.{child.name}"] = child
    return found


def changed_roots(before: "Index", after: "Index", path: str) -> set[str]:
    """Require the whole module difference to be existing method bodies only."""
    trees = [copy.deepcopy(i.syntax.get(f"{path}::<module>")) for i in (before, after)]
    if not isinstance(trees[0], ast.Module) or not isinstance(trees[1], ast.Module):
        return set()
    try:
        methods = [methods_in(trees[0]), methods_in(trees[1])]
    except ValueError:
        return set()
    roots = set()
    item_edit = False
    for name in sorted(methods[0].keys() & methods[1].keys()):
        old, new = methods[0][name], methods[1][name]
        if ast.dump(old) == ast.dump(new):
            continue
        leaf = name.rsplit(".", 1)[-1]
        if (
            old.decorator_list
            or new.decorator_list
            or (
                leaf.startswith("__")
                and leaf.endswith("__")
                and leaf not in ITEM_METHODS | {"__init__"}
            )
        ):
            return set()
        old.body = new.body = [ast.Pass()]
        if ast.dump(old) != ast.dump(new):
            return set()
        item_edit |= leaf in ITEM_METHODS
        roots.add(f"{path}::{name.split('.')[0]}")
    return roots if item_edit and ast.dump(trees[0]) == ast.dump(trees[1]) else set()


class MappingReferences(References):
    def __init__(self, index: "Index"):
        super().__init__(index)
        self.collection_bindings: dict[tuple[str, str], bool] = {}
        self.global_writes = {
            name
            for tree in index.syntax.values()
            for part in ast.walk(tree)
            if isinstance(part, (ast.Global, ast.Nonlocal))
            for name in part.names
        }

    def collections_name(self, expr: ast.AST, sid: str) -> str | None:
        """Recognize compatible eager stdlib imports without executing them.

        `import collections; import collections.abc` binds the same root twice.
        Normalize that one form here; ordinary call resolution keeps its audit.
        """
        from codeimpact.analyzer import ambiguous_module_imports

        spelling = self.dotted(expr)
        if not spelling or "collections" in self.modules or "collections.abc" in self.modules:
            return None
        root, _, tail = spelling.partition(".")
        path = self.index.nodes[sid].path
        local = self.index.local_bindings.get(sid)
        if (
            root in self.global_writes
            or root in self.blocked[sid]
            or (local and root in local.bound)
        ):
            return None
        imported = self.index.aliases.get(path, {}).get(root)
        qualified = imported + ("." + tail if tail else "") if imported else None
        if not qualified or not qualified.startswith("collections."):
            return None
        if self.reflective_fields or self.foreign_fields & {
            "abc",
            "Mapping",
            "MutableMapping",
            "OrderedDict",
            "namedtuple",
        }:
            return None
        if root in self.index.ambiguous.get(path, set()):
            key = path, root
            if key in self.collection_bindings:
                return qualified if self.collection_bindings[key] else None
            tree = copy.deepcopy(self.index.syntax[f"{path}::<module>"])
            assert isinstance(tree, ast.Module)
            retained = False
            for statement in tree.body:
                if not isinstance(statement, ast.Import):
                    continue
                aliases = []
                for alias in statement.names:
                    if (
                        alias.asname is None
                        and alias.name in {"collections", "collections.abc"}
                        and root == "collections"
                    ):
                        if not retained:
                            aliases.append(ast.alias(name="collections"))
                            retained = True
                    else:
                        aliases.append(alias)
                statement.names = aliases
            self.collection_bindings[key] = retained and root not in ambiguous_module_imports(tree)
            if not self.collection_bindings[key]:
                return None
        return qualified

    def abc_base(self, expr: ast.AST, sid: str) -> bool:
        return self.collections_name(expr, sid) in ABC_BASES

    def safe_instance(self, cls: str, depth: int = 0) -> bool:
        if depth > MAX_DEPTH:
            return False
        node = self.index.syntax[cls]
        if (
            not isinstance(node, ast.ClassDef)
            or node.decorator_list
            or node.keywords
            or len(node.bases) > 1
        ):
            return False
        if self.reflective_fields or self.foreign_fields & {
            "__class__",
            "__bases__",
            "__new__",
            "__class_getitem__",
            "__getattribute__",
            "__getattr__",
            "__setattr__",
            "__delattr__",
            "__init_subclass__",
        }:
            return False
        custom = {
            "__new__",
            "__getattribute__",
            "__getattr__",
            "__setattr__",
            "__delattr__",
            "__init_subclass__",
        }
        if any(self.member(cls, name) for name in custom) or any(
            isinstance(part, ast.Name) and isinstance(part.ctx, ast.Store) and part.id in custom
            for part in self.scope_nodes[cls]
        ):
            return False
        for base in node.bases:
            spelling = self.dotted(base)
            parent = self.lookup(spelling, cls) if spelling else None
            if parent and self.index.nodes[parent].kind == "class":
                if not self.safe_instance(parent, depth + 1):
                    return False
            elif not self.abc_base(base, cls) and not (
                isinstance(base, ast.Name)
                and base.id in {"object", "dict", "list", "tuple"}
                and self.is_builtin(base.id, cls)
            ):
                return False
        return True

    def generic_class(self, expr: ast.Subscript, sid: str) -> str | None:
        spelling = self.dotted(expr.value)
        cls = self.lookup(spelling, sid) if spelling else None
        if not cls or self.index.nodes[cls].kind != "class" or not self.safe_instance(cls):
            return None
        current = cls
        seen: set[str] = set()
        while current not in seen and len(seen) <= MAX_DEPTH:
            seen.add(current)
            node = self.index.syntax[current]
            if (
                not isinstance(node, ast.ClassDef)
                or self.member(current, "__class_getitem__")
                or any(
                    isinstance(part, ast.Name)
                    and part.id == "__class_getitem__"
                    and isinstance(part.ctx, ast.Store)
                    for part in self.scope_nodes[current]
                )
            ):
                return None
            if len(node.bases) != 1:
                return None
            base = node.bases[0]
            if self.abc_base(base, current):
                return cls
            spelling = self.dotted(base)
            parent = self.lookup(spelling, current) if spelling else None
            if not parent or self.index.nodes[parent].kind != "class":
                return None
            current = parent
        return None

    def assigned_member(self, cls: str, name: str, depth: int = 0) -> bool:
        """Class-stored callables/descriptors need more than method lookup."""
        if depth > MAX_DEPTH or self.reflective_fields or name in self.foreign_fields:
            return True
        stores = sum(
            isinstance(part, ast.Name) and part.id == name and isinstance(part.ctx, ast.Store)
            for part in self.scope_nodes[cls]
        )
        if stores:
            return not (
                stores == 1 and isinstance(self.expression_binding(name, cls), ast.Constant)
            )
        node = self.index.syntax[cls]
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                spelling = self.dotted(base)
                parent = self.lookup(spelling, cls) if spelling else None
                if (
                    parent
                    and self.index.nodes[parent].kind == "class"
                    and self.assigned_member(parent, name, depth + 1)
                ):
                    return True
        return False

    def call_target(
        self, expr: ast.AST, sid: str, depth: int = 0, receiver: str | None = None
    ) -> str | None:
        if depth > MAX_DEPTH:
            return None
        if isinstance(expr, ast.Subscript):
            return self.generic_class(expr, sid)
        if isinstance(expr, ast.Attribute):
            spelling = self.dotted(expr)
            direct = self.lookup(spelling, sid) if spelling else None
            if direct:
                return direct
            cls = self.class_of(expr.value, sid, depth + 1, receiver)
            return self.member(cls, expr.attr) if cls and cls != OTHER else None
        return super().call_target(expr, sid, depth)

    def _class_of(self, expr: ast.AST, sid: str, depth: int, receiver: str | None) -> str | None:
        # The receiver of a literal-container subscription is the container, not
        # an element. A value retrieved from that container remains unknown.
        if isinstance(expr, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
            return OTHER
        if isinstance(expr, ast.Call):
            if self.collections_name(expr.func, sid) == "collections.OrderedDict":
                return OTHER
            if (
                isinstance(expr.func, ast.Name)
                and expr.func.id in {"iter", "reversed"}
                and self.is_builtin(expr.func.id, sid)
                and expr.args
                and self.class_of(expr.args[0], sid, depth + 1, receiver) == OTHER
            ):
                return OTHER
            target = self.call_target(expr.func, sid, depth + 1, receiver)
            if target:
                if self.index.nodes[target].kind == "class":
                    return target if self.safe_instance(target) else None
                cls = (
                    self.class_of(expr.func.value, sid, depth + 1, receiver)
                    if isinstance(expr.func, ast.Attribute)
                    else None
                )
                return self.returns_type(target, cls if cls != OTHER else None, depth + 1)
            if (
                isinstance(expr.func, ast.Name)
                and expr.func.id
                in {"dict", "list", "tuple", "set", "len", "bool", "str", "int", "float"}
                and self.is_builtin(expr.func.id, sid)
            ):
                return OTHER
        if (
            isinstance(expr, ast.Attribute)
            and expr.attr.startswith("__")
            and not expr.attr.endswith("__")
        ):
            # Private fields belong to the lexical defining class, including in
            # inherited bodies; Base.__data and Child.__data are distinct fields.
            owner = self.owner(sid)
            node = self.index.syntax[sid]
            if (
                owner
                and isinstance(node, FUNCTIONS)
                and node.args.args
                and isinstance(expr.value, ast.Name)
                and expr.value.id == node.args.args[0].arg
                and not self.reflective_fields
                and expr.attr not in self.foreign_fields
            ):
                mangled = "_" + self.index.nodes[owner].name.split(".")[-1].lstrip("_") + expr.attr
                if mangled in self.foreign_fields:
                    return None
                values = []
                stores = 0
                for key, method in self.index.syntax.items():
                    if self.owner(key) != owner or not isinstance(method, FUNCTIONS):
                        continue
                    parameters = method.args.posonlyargs + method.args.args
                    if not parameters:
                        continue

                    def field(target: ast.AST, parameter: str = parameters[0].arg) -> bool:
                        return (
                            isinstance(target, ast.Attribute)
                            and isinstance(target.value, ast.Name)
                            and target.value.id == parameter
                            and target.attr == expr.attr
                        )

                    for part in self.scope_nodes[key]:
                        if field(part) and isinstance(
                            getattr(part, "ctx", None), (ast.Store, ast.Del)
                        ):
                            stores += 1
                        if isinstance(part, (ast.Assign, ast.AnnAssign)):
                            targets = (
                                part.targets if isinstance(part, ast.Assign) else [part.target]
                            )
                            for field_target in targets:
                                if field(field_target):
                                    values.append(self.class_of(part.value, key, depth + 1, owner))
                if values and stores == len(values) and len(set(values)) == 1:
                    return values[0]
            return None
        return super()._class_of(expr, sid, depth, receiver)


class MappingQuery:
    def __init__(self, refs: MappingReferences, roots: set[str]):
        self.refs = refs
        self.roots = roots
        self.todo: list[tuple[str, str | None]] = []
        self.seen: set[tuple[str, str | None]] = set()

    def related(self, cls: str, depth: int = 0) -> bool:
        if depth > MAX_DEPTH:
            return True
        if any(cls == root or cls.startswith(root + ".") for root in self.roots):
            return True
        node = self.refs.index.syntax.get(cls)
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                spelling = self.refs.dotted(base)
                parent = self.refs.lookup(spelling, cls) if spelling else None
                if parent and self.related(parent, depth + 1):
                    return True
        return False

    def add(self, target: str, receiver: str | None = None) -> bool:
        node = self.refs.index.nodes[target]
        if node.kind == "class":
            if self.related(target) or not self.refs.safe_instance(target):
                return True
            init = self.refs.member(target, "__init__")
            if init:
                self.todo.append((init, target))
            return False
        owner = self.refs.owner(target)
        if owner and self.related(receiver or owner):
            return True
        self.todo.append((target, receiver))
        return False

    def member(self, expr: ast.AST, name: str, sid: str, receiver: str | None) -> bool:
        cls = self.refs.class_of(expr, sid, receiver=receiver)
        if cls == OTHER:
            return False
        if cls:
            if self.related(cls):
                return True
            if self.refs.assigned_member(cls, name):
                return True
            target = self.refs.member(cls, name)
            if target:
                return self.add(target, cls)
            return False
        if name in MAPPING_METHODS:
            return True
        # Existing spelling fallback remains conservative for unknown receivers.
        return any(
            self.add(target)
            for target in self.refs.by_name[name]
            if self.refs.index.nodes[target].path in self.refs.scope_modules(sid)
        )

    def depends(self, sid: str) -> bool:
        if sid not in self.refs.index.syntax:
            return False
        owner = self.refs.owner(sid)
        entry = self.refs.index.syntax[sid]
        if self.refs.index.nodes[sid].kind == "test" and isinstance(entry, FUNCTIONS):
            parameters = [*entry.args.posonlyargs, *entry.args.args, *entry.args.kwonlyargs]
            if (
                entry.args.vararg
                or entry.args.kwarg
                or any(p.arg != "self" or not owner for p in parameters)
            ):
                return True
        # One discovered inherited definition represents all its subclass contexts.
        if owner and self.refs.class_children[owner]:
            return True
        if self.add(sid, owner):
            return True
        while self.todo:
            current, receiver = self.todo.pop()
            key = current, receiver
            if key in self.seen:
                continue
            self.seen.add(key)
            if len(self.seen) > MAX_VISITS:
                return True
            node = self.refs.index.syntax[current]
            if not isinstance(node, FUNCTIONS):
                return True
            if any(
                not isinstance(d, ast.Name)
                or d.id not in {"staticmethod", "property"}
                or not self.refs.is_builtin(d.id, current)
                for d in node.decorator_list
            ) or any(isinstance(n, (ast.Global, ast.Nonlocal)) for n in ast.walk(node)):
                return True
            # Nested callbacks can escape through returned functions/decorators.
            if any(isinstance(n, (*FUNCTIONS, ast.ClassDef)) for n in list(ast.walk(node))[1:]):
                return True
            callees = {id(p.func) for p in own_nodes(node) if isinstance(p, ast.Call)}
            defaults = {id(p) for p in node.args.defaults}
            for part in own_nodes(node):
                if isinstance(part, ast.Name) and isinstance(part.ctx, ast.Load):
                    target = self.refs.lookup(part.id, current)
                    if (
                        target
                        and self.refs.index.nodes[target].kind in {"function", "test", "class"}
                        and self.add(target)
                    ):
                        return True
                elif isinstance(part, ast.Attribute) and isinstance(part.ctx, ast.Load):
                    if id(part) in callees:
                        continue  # The call below supplies its receiver context.
                    spelling = self.refs.dotted(part)
                    target = self.refs.lookup(spelling, current) if spelling else None
                    if target and self.refs.index.nodes[target].kind in {
                        "function",
                        "test",
                        "class",
                    }:
                        if self.add(target, receiver if id(part) in defaults else None):
                            return True
                    elif self.member(part.value, part.attr, current, receiver):
                        return True
                elif isinstance(part, ast.Subscript):
                    if self.refs.generic_class(part, current):
                        continue
                    method = (
                        "__setitem__"
                        if isinstance(part.ctx, ast.Store)
                        else "__delitem__"
                        if isinstance(part.ctx, ast.Del)
                        else "__getitem__"
                    )
                    if self.member(part.value, method, current, receiver):
                        return True
                elif isinstance(part, ast.Call):
                    if isinstance(part.func, ast.Attribute):
                        cls = self.refs.class_of(part.func.value, current, receiver=receiver)
                        if cls and cls != OTHER and self.refs.assigned_member(cls, part.func.attr):
                            return True
                    target = self.refs.call_target(part.func, current, receiver=receiver)
                    if target:
                        context = None
                        if isinstance(part.func, ast.Attribute):
                            context = self.refs.class_of(
                                part.func.value, current, receiver=receiver
                            )
                            # An explicit Base.method(self, ...) retains the derived receiver.
                            if context is None and part.args:
                                context = self.refs.class_of(
                                    part.args[0], current, receiver=receiver
                                )
                        if self.add(target, context if context != OTHER else None):
                            return True
                    elif isinstance(part.func, ast.Attribute) and self.member(
                        part.func.value, part.func.attr, current, receiver
                    ):
                        return True
                    if (
                        isinstance(part.func, ast.Name)
                        and self.refs.is_builtin(part.func.id, current)
                        and part.args
                    ):
                        protocols = PROTOCOLS.get(part.func.id, ())
                        if part.func.id in {"list", "dict", "tuple", "set", "reversed"}:
                            protocols = ("__iter__", "__getitem__")
                        if (
                            protocols
                            and self.refs.class_of(part.args[0], current, receiver=receiver) is None
                        ):
                            return True
                        if any(self.member(part.args[0], p, current, receiver) for p in protocols):
                            return True
                    if isinstance(part.func, ast.Name) and part.func.id in {
                        "getattr",
                        "setattr",
                        "delattr",
                        "vars",
                        "globals",
                        "locals",
                        "eval",
                        "exec",
                    }:
                        return True
                elif isinstance(part, (ast.For, ast.AsyncFor, ast.comprehension)):
                    if self.member(part.iter, "__iter__", current, receiver):
                        return True
                elif isinstance(part, ast.Compare):
                    for operation, value in zip(part.ops, part.comparators, strict=True):
                        if isinstance(operation, (ast.In, ast.NotIn)) and self.member(
                            value, "__contains__", current, receiver
                        ):
                            return True
        return False


class MappingFallback:
    def __init__(self, before: "Index", after: "Index", paths: set[str]):
        self.changes = {
            p: roots for p in sorted(paths) if (roots := changed_roots(before, after, p))
        }
        self.refs = (MappingReferences(before), MappingReferences(after)) if self.changes else ()
        self.changes = {
            path: roots
            for path, roots in self.changes.items()
            if all(initialization_safe(refs, path) for refs in self.refs)
        }
        self.cache: dict[tuple[str, str], bool] = {}

    def allows(self, sid: str, path: str) -> bool:
        key = sid, path
        if key not in self.cache:
            try:
                self.cache[key] = any(
                    MappingQuery(refs, self.changes[path]).depends(sid) for refs in self.refs
                )
            except RecursionError:
                self.cache[key] = True
        return self.cache[key]


def initialization_safe(refs: MappingReferences, path: str) -> bool:
    """Decline effectful module/class initialization even when its text is unchanged."""
    sid = f"{path}::<module>"

    def visit(node: ast.AST) -> bool:
        if isinstance(node, FUNCTIONS):
            if any(
                not isinstance(d, ast.Name)
                or d.id not in {"property", "staticmethod", "classmethod"}
                or not refs.is_builtin(d.id, sid)
                for d in node.decorator_list
            ):
                return False
            return all(
                visit(p)
                for p in [
                    *node.decorator_list,
                    node.args,
                    *([node.returns] if node.returns is not None else []),
                ]
            )
        if isinstance(node, ast.ClassDef):
            if node.keywords:
                return False
            for decorator in node.decorator_list:
                spelling = refs.dotted(decorator)
                # The stdlib decorator fills comparison methods on a plain class;
                # it does not invoke those method bodies. Other decorators decline.
                if (
                    node.bases
                    or not spelling
                    or refs.expanded(spelling, sid) != "functools.total_ordering"
                    or "functools" in refs.modules
                    or spelling.split(".")[0] in refs.global_writes
                    or refs.reflective_fields
                    or "total_ordering" in refs.foreign_fields
                ):
                    return False
        if isinstance(
            node,
            (
                ast.Subscript,
                ast.BinOp,
                ast.UnaryOp,
                ast.BoolOp,
                ast.Compare,
                ast.For,
                ast.AsyncFor,
                ast.With,
                ast.AsyncWith,
                ast.comprehension,
            ),
        ):
            return False
        if isinstance(node, ast.Call):
            plain_object = (
                isinstance(node.func, ast.Name)
                and node.func.id == "object"
                and refs.is_builtin("object", sid)
                and not node.args
                and not node.keywords
            )
            namedtuple = (
                refs.collections_name(node.func, sid) == "collections.namedtuple"
                and len(node.args) == 2
                and not node.keywords
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and isinstance(node.args[1], (ast.List, ast.Tuple))
                and all(
                    isinstance(p, ast.Constant) and isinstance(p.value, str)
                    for p in node.args[1].elts
                )
            )
            if not plain_object and not namedtuple:
                return False
        return all(visit(child) for child in ast.iter_child_nodes(node))

    return visit(refs.index.syntax[sid])
