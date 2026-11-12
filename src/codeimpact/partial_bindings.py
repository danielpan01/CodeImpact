"""Syntax-only, bounded module partial bindings; never imports analyzed code.

This resolver is deliberately separate from ordinary call resolution. It recognizes
one immutable construction, not arbitrary factory execution or argument dispatch.
"""

import ast
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
ImportDecoder = Callable[
    [ast.Import | ast.ImportFrom, str, dict[str, str]],
    tuple[list[tuple[str, str]], list[str]],
]


def module_nodes(tree: ast.AST) -> list[ast.AST]:
    """Include compound statements but exclude separate definition/lambda bodies."""
    result = [tree]
    if not isinstance(tree, (*DEFINITIONS, ast.Lambda)):
        for child in ast.iter_child_nodes(tree):
            result.extend(module_nodes(child))
    return result


def dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute) and (parent := dotted(node.value)):
        return f"{parent}.{node.attr}"
    return None


def before(binding: ast.AST, use: ast.AST) -> bool:
    return (getattr(binding, "end_lineno", 0), getattr(binding, "end_col_offset", 0)) < (
        getattr(use, "lineno", 0),
        getattr(use, "col_offset", 0),
    )


def passive(node: ast.AST) -> bool:
    """Only small literal values; no evaluation, unpacking or arbitrary expression calls."""
    children = list(ast.walk(node))
    return len(children) <= 64 and all(
        isinstance(child, (ast.Constant, ast.Tuple, ast.Load, ast.UnaryOp, ast.UAdd, ast.USub))
        for child in children
    )


@dataclass
class Scope:
    counts: Counter[str] = field(default_factory=Counter)
    blocked: set[str] = field(default_factory=set)
    wildcard: bool = False


def audit(body: list[ast.stmt], *, local: bool = False) -> Scope:
    """Count bindings in this scope, including compound statements, but not inner locals."""
    result = Scope()

    def scan(node: ast.AST) -> None:
        if isinstance(node, DEFINITIONS):
            result.counts[node.name] += 1
            # Headers belong to the outer scope; bodies do not. Global/nonlocal
            # declarations and object mutations inside bodies still invalidate
            # precision, even when the function is never called.
            for child in ast.walk(node):
                if isinstance(child, (ast.Global, ast.Nonlocal)):
                    result.blocked.update(child.names)
                if isinstance(child, (ast.Attribute, ast.Subscript)) and isinstance(
                    child.ctx, (ast.Store, ast.Del)
                ):
                    mutation(child)
            for key, value in ast.iter_fields(node):
                if key != "body":
                    if isinstance(value, ast.AST):
                        scan(value)
                    elif isinstance(value, list):
                        for child in value:
                            if isinstance(child, ast.AST):
                                scan(child)
            return
        if isinstance(node, ast.Lambda):
            scan(node.args)
            return
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == "*":
                    result.wildcard = True
                else:
                    name = alias.asname or (
                        alias.name.split(".")[0] if isinstance(node, ast.Import) else alias.name
                    )
                    result.counts[name] += 1
            return
        if isinstance(node, ast.AnnAssign) and node.value is None:
            if local and isinstance(node.target, ast.Name):
                result.counts[node.target.id] += 1
            scan(node.annotation)
            return
        if isinstance(node, ast.comprehension):
            scan(node.iter)
            for condition in node.ifs:
                scan(condition)
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            result.counts[node.id] += 1
        elif isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(
            node.ctx, (ast.Store, ast.Del)
        ):
            mutation(node)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            result.blocked.update(node.names)
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
            result.counts[node.name] += 1
        elif isinstance(node, ast.MatchMapping) and node.rest:
            result.counts[node.rest] += 1
        for child in ast.iter_child_nodes(node):
            scan(child)

    def mutation(node: ast.AST) -> None:
        while isinstance(node, (ast.Attribute, ast.Subscript)):
            node = node.value
        if isinstance(node, ast.Name):
            result.blocked.add(node.id)

    for statement in body:
        scan(statement)
    return result


class PartialBindings:
    def __init__(
        self, trees: dict[str, ast.Module], modules: dict[str, str], decode: ImportDecoder
    ) -> None:
        self.modules = modules
        self.trees = trees
        self.decode = decode
        self.local_scopes: dict[ast.AST, Scope] = {}
        self.scopes = {path: audit(tree.body) for path, tree in trees.items()}
        self.direct: dict[str, dict[str, ast.AST]] = {}
        self.imports: dict[str, dict[str, tuple[str, ast.Import | ast.ImportFrom]]] = {}
        self.candidates: dict[str, dict[str, ast.Assign | ast.AnnAssign]] = {}
        for path, tree in trees.items():
            direct: dict[str, ast.AST] = {}
            imports: dict[str, tuple[str, ast.Import | ast.ImportFrom]] = {}
            candidates: dict[str, ast.Assign | ast.AnnAssign] = {}
            for node in tree.body:
                if isinstance(node, DEFINITIONS):
                    direct[node.name] = node
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    for name, target in decode(node, path, modules)[0]:
                        direct[name] = node
                        imports[name] = (target, node)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    if len(targets) == 1 and isinstance(targets[0], ast.Name):
                        direct[targets[0].id] = node
                        if isinstance(node.value, ast.Call):
                            candidates[targets[0].id] = node
            self.direct[path], self.imports[path] = direct, imports
            self.candidates[path] = candidates
        # Reserve even ambiguous partial names: they must not fall through to a
        # same-named definition. This syntactic check intentionally ignores rebinds.
        self.possible: dict[str, set[str]] = {}
        for path, tree in trees.items():
            nodes = module_nodes(tree)
            factories = {
                name + (".partial" if target == "functools" else "")
                for node in nodes
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for name, target in decode(node, path, modules)[0]
                if target in {"functools", "functools.partial"}
            }
            possible: set[str] = set()
            for potential in nodes:
                if not isinstance(potential, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
                    continue
                if (
                    not isinstance(potential.value, ast.Call)
                    or dotted(potential.value.func) not in factories
                ):
                    continue
                targets = (
                    potential.targets if isinstance(potential, ast.Assign) else [potential.target]
                )
                possible.update(
                    child.id
                    for target in targets
                    for child in ast.walk(target)
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)
                )
            self.possible[path] = possible

    def binding(self, path: str, name: str, use: ast.AST | None = None) -> ast.AST | None:
        scope = self.scopes[path]
        node = self.direct[path].get(name)
        if scope.wildcard or name in scope.blocked or scope.counts[name] != 1:
            return None
        if node is None or (use is not None and not before(node, use)):
            return None
        return node

    def exports(self, path: str) -> set[str] | None:
        """A complete, static export inventory for one wildcard source module."""
        scope = self.scopes[path]
        if scope.wildcard or "__getattr__" in scope.counts or "__dir__" in scope.counts:
            return None
        # Calls can mutate an export list or the module namespace without stores.
        for item in ast.walk(self.trees[path]):
            if (
                isinstance(item, ast.Name)
                and item.id == "__all__"
                and isinstance(item.ctx, ast.Load)
            ):
                return None
            if isinstance(item, ast.Call):
                call = dotted(item.func) or ""
                if call.startswith("__all__.") or call in {"globals", "locals", "vars", "exec"}:
                    return None
        if "__all__" not in scope.counts:
            return {name for name in scope.counts if not name.startswith("_")}
        node = self.binding(path, "__all__")
        value = getattr(node, "value", None)
        if not isinstance(value, (ast.List, ast.Tuple)) or len(value.elts) > 256:
            return None
        if not all(
            isinstance(item, ast.Constant) and isinstance(item.value, str) for item in value.elts
        ):
            return None
        return {
            item.value
            for item in value.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        }

    def exported_target(self, path: str, expression: str, depth: int) -> str | None:
        """Follow a unique wildcard export; an unknown star is never harmless."""
        if depth >= 16:
            return None
        root = expression.split(".")[0]
        scope = self.scopes[path]
        if root in scope.counts or root in scope.blocked:
            return None
        candidates = []
        for node in self.trees[path].body:
            if not isinstance(node, ast.ImportFrom) or not any(a.name == "*" for a in node.names):
                continue
            parent = next(mod for mod, source in self.modules.items() if source == path)
            levels = len(parent.split(".")) - (not path.endswith("__init__.py"))
            if node.level > levels:
                return None
            # Decode a synthetic named import as syntax using the shared rules.
            named = ast.ImportFrom(
                module=node.module, names=[ast.alias(name=root)], level=node.level
            )
            target = self.decode(named, path, self.modules)[0][0][1]
            module = target.rpartition(".")[0]
            source = self.modules.get(module)
            if source is None or (exports := self.exports(source)) is None:
                return None
            if root in exports:
                candidates.append(source)

        # Conditional stars are unknown (even in syntax-invalid source).
        def star(node: ast.AST) -> bool:
            return isinstance(node, ast.ImportFrom) and any(a.name == "*" for a in node.names)

        if sum(map(star, ast.walk(self.trees[path]))) != sum(map(star, self.trees[path].body)):
            return None
        if len(candidates) != 1:
            return None
        return self.resolve(candidates[0], expression, depth=depth + 1)

    def resolve(
        self, path: str, expression: str, use: ast.AST | None = None, depth: int = 0
    ) -> str | None:
        if depth >= 16:
            return None
        root, _, tail = expression.partition(".")
        if self.scopes[path].wildcard:
            return self.exported_target(path, expression, depth)
        node = self.binding(path, root, use)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return f"{path}::{root}" if not tail and not node.decorator_list else None
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            return None
        target, _ = self.imports[path][root]
        if isinstance(node, ast.ImportFrom):
            parent = next(mod for mod, source in self.modules.items() if source == path)
            levels = len(parent.split(".")) - (not path.endswith("__init__.py"))
            if node.level > levels:
                return None
            module, _, member = target.rpartition(".")
            suffix = member + ("." + tail if tail else "")
        else:
            module, suffix = target, tail
        if module == "functools" and suffix == "partial" and "functools" not in self.modules:
            return "functools.partial"
        # Prefer an explicit package export over a same-named submodule. A from
        # import carries its module/member boundary, unlike a flattened fqname.
        while module in self.modules:
            source = self.modules[module]
            first, _, rest = suffix.partition(".")
            if first in self.direct[source] or self.scopes[source].wildcard:
                return self.resolve(source, suffix, depth=depth + 1)
            module += "." + first
            suffix = rest
            if not suffix:
                break
        return None

    def call_target(
        self, path: str, call: str, use: ast.AST, scopes: list[ast.AST], allow: bool
    ) -> tuple[bool, str | None, str]:
        """handled reserves unsupported candidates without guessing another target."""
        if call not in self.possible[path]:
            return False, None, ""
        node = self.binding(path, call, use)
        if not allow or node is None or node is not self.candidates[path].get(call):
            return True, None, ""
        for scope in scopes:
            if scope not in self.local_scopes:
                local = audit(getattr(scope, "body", []), local=True)
                args = getattr(scope, "args", None)
                if args:
                    local.blocked.update(
                        item.arg for item in ast.walk(args) if isinstance(item, ast.arg)
                    )
                self.local_scopes[scope] = local
            local = self.local_scopes[scope]
            if local.wildcard or call in local.counts or call in local.blocked:
                return True, None, ""
        candidate = self.candidates[path][call]
        expression = candidate.value
        assert isinstance(expression, ast.Call)
        factory = dotted(expression.func)
        if not factory or self.resolve(path, factory, expression) != "functools.partial":
            return True, None, ""
        if not expression.args or any(k.arg is None for k in expression.keywords):
            return True, None, ""
        if not all(passive(arg) for arg in expression.args[1:]) or not all(
            passive(k.value) for k in expression.keywords
        ):
            return True, None, ""
        target_name = dotted(expression.args[0])
        target = self.resolve(path, target_name, expression) if target_name else None
        if target == "functools.partial":
            target = None
        return (
            True,
            target,
            f" via functools.partial binding {path}:{candidate.lineno} ({target_name})",
        )
