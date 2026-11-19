"""Evidence for a qualified call through a passive explicit package re-export."""

import ast
from collections import Counter, defaultdict
from collections.abc import Iterator
from typing import TYPE_CHECKING

from codeimpact.call_arguments import CallBinding
from codeimpact.models import SourceLocation
from codeimpact.partial_bindings import PartialBindings, audit, passive
from codeimpact.selection import DEFINITIONS

if TYPE_CHECKING:
    from codeimpact.analyzer import Index

MAX_IMPORT_DEPTH = 16
MAX_NAMESPACE_NODES = 12000
DYNAMIC_NAMES = {
    "__import__",
    "eval",
    "exec",
    "getattr",
    "setattr",
    "delattr",
    "vars",
    "globals",
    "locals",
    "import_module",
    "reload",
}
NAMESPACE_ATTRS = {
    "__builtins__",
    "__dict__",
    "__globals__",
    "__code__",
    "__getattribute__",
    "__setattr__",
    "modules",
    "meta_path",
    "path_hooks",
}
INNER_SCOPES = (ast.Lambda, ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)


def literal_value(node: ast.AST) -> bool:
    return passive(node) and not any(isinstance(n, ast.UnaryOp) for n in ast.walk(node))


def passive_definition(node: ast.FunctionDef) -> bool:
    return (
        not node.decorator_list
        and not node.type_params
        and all(
            item is None or isinstance(item, ast.Constant)
            for item in [
                node.returns,
                *(p.annotation for p in ast.walk(node.args) if isinstance(p, ast.arg)),
            ]
        )
        and all(
            default is None or literal_value(default)
            for default in [*node.args.defaults, *node.args.kw_defaults]
        )
    )


def literal_assignment(stmt: ast.Assign) -> bool:
    if len(stmt.targets) != 1 or not isinstance(target := stmt.targets[0], ast.Name):
        return False
    if target.id == "__all__":
        return (
            isinstance(stmt.value, (ast.List, ast.Tuple))
            and len(stmt.value.elts) <= 256
            and all(
                isinstance(item, ast.Constant) and isinstance(item.value, str)
                for item in stmt.value.elts
            )
        )
    return not target.id.startswith("__") and literal_value(stmt.value)


class Proof:
    def __init__(self, resolver: PartialBindings):
        self.resolver = resolver
        self.modules = {path: name for name, path in resolver.modules.items()}
        self.checked: dict[str, bool] = {}
        self.targets: dict[tuple[str, str], tuple[str, str] | None] = {}
        self.stack: set[str] = set()
        self.steps = 0

    def import_dependencies(self, path: str, stmt: ast.Import | ast.ImportFrom) -> set[str] | None:
        modules = self.resolver.modules
        if isinstance(stmt, ast.Import):
            if not all(a.name in modules and "." not in a.name for a in stmt.names):
                return None
            return {modules[a.name] for a in stmt.names}
        nesting = len(self.modules[path].split(".")) - (not path.endswith("/__init__.py"))
        if not stmt.module or stmt.level > nesting or any(a.name == "*" for a in stmt.names):
            return None
        bindings, _ = self.resolver.decode(stmt, path, modules)
        dependencies = set()
        for _, qualified in bindings:
            module, _, member = qualified.rpartition(".")
            source = modules.get(module)
            if source is None or self.resolver.binding(source, member) is None:
                return None
            dependencies.add(source)
        return dependencies

    def initialized(self, path: str) -> bool:
        if path in self.stack or len(self.stack) >= MAX_IMPORT_DEPTH:
            return False
        if path in self.checked:
            return self.checked[path]
        tree = self.resolver.trees.get(path)
        if tree is None:
            return False
        scope = self.resolver.scopes[path]
        if scope.wildcard or scope.blocked or any(count != 1 for count in scope.counts.values()):
            return False
        self.stack.add(path)
        try:
            parent = self.resolver.modules.get(self.modules[path].rpartition(".")[0])
            # Python initializes the enclosing package before its child. An
            # explicit import back into a running module is checked separately.
            result = (not parent or parent in self.stack or self.initialized(parent)) and all(
                self.statement(path, stmt) for stmt in tree.body
            )
        finally:
            self.stack.remove(path)
        self.checked[path] = result
        return result

    def statement(self, path: str, stmt: ast.stmt) -> bool:
        self.steps += 1
        if self.steps > MAX_NAMESPACE_NODES:
            return False
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            if any((alias.asname or alias.name).startswith("__") for alias in stmt.names):
                return False
            dependencies = self.import_dependencies(path, stmt)
            return dependencies is not None and all(
                self.initialized(p) for p in sorted(dependencies)
            )
        if isinstance(stmt, ast.FunctionDef):
            return not stmt.name.startswith("__") and passive_definition(stmt)
        if isinstance(stmt, ast.Assign):
            return literal_assignment(stmt)
        return isinstance(stmt, ast.Pass) or (
            isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str)
        )

    def target(self, package: str, member: str) -> tuple[str, str] | None:
        key = (package, member)
        if key not in self.targets:
            self.targets[key] = self.exported_function(package, member)
        return self.targets[key]

    def exported_function(self, package: str, member: str) -> tuple[str, str] | None:
        packages = self.resolver.modules
        path = packages.get(package)
        if (
            not path
            or "." in package
            or not path.endswith("/__init__.py")
            or f"{package}.{member}" in packages
        ):
            return None
        if not isinstance(self.resolver.binding(path, member), ast.ImportFrom):
            return None
        target, _ = self.resolver.imports[path][member]
        module, _, name = target.rpartition(".")
        source = packages.get(module)
        if (
            not source
            or source.endswith("/__init__.py")
            or module.rpartition(".")[0] != package
            or not isinstance(fn := self.resolver.binding(source, name), ast.FunctionDef)
            or not passive_definition(fn)
            or not self.initialized(path)
        ):
            return None
        # The defining function may be called, including recursively, but its
        # function object may not escape through another binding.
        tree = self.resolver.trees[source]
        parents = {
            child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
        }
        if any(
            isinstance(n, ast.Name)
            and n.id == name
            and isinstance(n.ctx, ast.Load)
            and not direct_use(n, parents, module=False)
            for n in parents
        ):
            return None
        return source, name


def direct_use(node: ast.Name, parents: dict[ast.AST, ast.AST], *, module: bool) -> bool:
    callee: ast.AST = node
    if module:
        parent = parents.get(node)
        if not isinstance(parent, ast.Attribute) or parent.value is not node:
            return False
        callee = parent
    call = parents.get(callee)
    return isinstance(call, ast.Call) and call.func is callee


def namespace_mutations(resolver: PartialBindings) -> set[str] | None:
    """Reject observed namespace escapes, field writes and reflective access."""
    unsafe: set[str] = set()
    steps = 0
    for path, tree in resolver.trees.items():
        parents: dict[ast.AST, ast.AST] = {}
        loaded: dict[str, list[tuple[str, bool]]] = defaultdict(list)
        for node in ast.walk(tree):
            steps += 1
            if steps > MAX_NAMESPACE_NODES:
                return None
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id in DYNAMIC_NAMES
            ):
                return None
            if isinstance(node, ast.Attribute) and node.attr in DYNAMIC_NAMES | NAMESPACE_ATTRS:
                return None
            parents.update((child, node) for child in ast.iter_child_nodes(node))
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for name, target in resolver.decode(node, path, resolver.modules)[0]:
                    package = target.split(".")[0]
                    if package in resolver.modules:
                        loaded[name].append((package, isinstance(node, ast.Import)))
        for node in parents:
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                for package, module in loaded.get(node.id, ()):
                    if not direct_use(node, parents, module=module):
                        unsafe.add(package)
    return unsafe


def calls(body: list[ast.stmt]) -> Iterator[tuple[ast.Call, str, str]]:
    todo: list[ast.AST] = list(reversed(body))
    while todo:
        node = todo.pop()
        if isinstance(node, DEFINITIONS + INNER_SCOPES):
            continue
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            yield node, node.func.value.id, node.func.attr
        todo.extend(reversed(list(ast.iter_child_nodes(node))))


def add_reexport_edges(index: "Index") -> set[tuple[str, str, str]]:
    resolver = index.partials
    if not resolver:
        return set()
    if len(resolver.modules) != sum(n.kind == "module" for n in index.nodes.values()):
        return set()
    proof = Proof(resolver)
    additions: set[tuple[str, str, str]] = set()
    resolved_warnings: Counter[str] = Counter()
    namespace: set[str] | None = None
    for sid, node in index.syntax.items():
        path, _, name = sid.partition("::")
        if not isinstance(node, ast.FunctionDef) or "." in name or node.decorator_list:
            continue
        scope = audit(node.body, local=True)
        local = (
            scope.counts.keys()
            | scope.blocked
            | {arg.arg for arg in ast.walk(node.args) if isinstance(arg, ast.arg)}
        )
        if scope.wildcard:
            continue
        for call, root, member in calls(node.body):
            binding = resolver.binding(path, root)
            if root in local or call in index.call_bindings or not isinstance(binding, ast.Import):
                continue
            package, _ = resolver.imports[path][root]
            if not any(a.name == package and (a.asname or a.name) == root for a in binding.names):
                continue
            target = proof.target(package, member)
            if not target or not proof.initialized(path):
                continue
            if namespace is None:
                namespace = namespace_mutations(resolver)
                if namespace is None:
                    return set()
            if package in namespace:
                continue
            file, function = target
            callee = f"{file}::{function}"
            if callee not in index.nodes or callee == sid:
                continue
            edge: tuple[str, str, str] = (sid, callee, "call")
            additions.add(edge)
            index.call_bindings[call] = CallBinding(sid, callee)
            index.add_edge(
                sid,
                callee,
                "call",
                f"{path}:{call.lineno} calls {root}.{member} via explicit re-export "
                f"in {resolver.modules[package]}",
                SourceLocation(
                    path=path, line=call.lineno, end_line=call.end_lineno or call.lineno
                ),
            )
            resolved_warnings[f"Unresolved call {root}.{member}: {path}:{call.lineno}"] += 1
    if resolved_warnings:
        remaining = []
        for warning in index.warnings:
            if resolved_warnings[warning]:
                resolved_warnings[warning] -= 1
            else:
                remaining.append(warning)
        index.warnings = remaining
    return additions
