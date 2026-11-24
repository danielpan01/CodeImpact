"""Resolve one literal import-and-call pattern from snapshot ASTs."""

import ast
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from codeimpact.call_arguments import CallBinding
from codeimpact.explicit_reexports import Proof, namespace_mutations, passive_definition
from codeimpact.models import SourceLocation
from codeimpact.partial_bindings import dotted

if TYPE_CHECKING:
    from codeimpact.analyzer import Index


def direct_importlib(statement: ast.AST | None) -> bool:
    return (
        isinstance(statement, ast.Import)
        and len(statement.names) == 1
        and statement.names[0].name == "importlib"
        and statement.names[0].asname is None
    )


class Initialization(Proof):
    def statement(self, path: str, stmt: ast.stmt) -> bool:
        return direct_importlib(stmt) or super().statement(path, stmt)


@dataclass(frozen=True)
class Lookup:
    module: str
    member: str
    load: ast.Call
    lookup: ast.Call
    invoke: ast.Call


def literal_lookup(node: ast.FunctionDef) -> Lookup | None:
    body = node.body[1:] if ast.get_docstring(node, clean=False) is not None else node.body
    if len(body) != 2:
        return None
    bind, returned = body
    match bind:
        case ast.Assign(targets=[ast.Name(id=local)], value=ast.Call() as load):
            if local in {"importlib", "getattr"}:
                return None
        case _:
            return None
    match load:
        case ast.Call(func=func, args=[ast.Constant(value=str(module))], keywords=[]):
            if dotted(func) != "importlib.import_module" or not module.isidentifier():
                return None
        case _:
            return None
    match returned:
        case ast.Return(value=ast.Call(func=ast.Call() as lookup, args=[], keywords=[]) as invoke):
            pass
        case _:
            return None
    match lookup:
        case ast.Call(
            func=ast.Name(id="getattr"),
            args=[ast.Name(id=binding), ast.Constant(value=str(member))],
            keywords=[],
        ) if binding == local and member.isidentifier():
            return Lookup(module, member, load, lookup, invoke)
        case _:
            return None


def top_level_file(module: str, path: str) -> bool:
    return module.isidentifier() and path in {f"{module}.py", f"src/{module}.py"}


def add_runtime_import_edges(index: "Index") -> set[ast.Call]:
    resolver = index.partials
    if not resolver or any(
        name == "importlib" or name.startswith("importlib.") for name in resolver.modules
    ):
        return set()
    proof = Initialization(resolver)
    # An unparseable initializer is represented in the index by an empty AST.
    proof.checked.update(
        (path, False)
        for path, source in index.sources.items()
        if source.parse_status == "unparseable"
    )
    candidates: list[tuple[str, str, Lookup]] = []
    for path, tree in resolver.trees.items():
        if not top_level_file(proof.modules[path], path) or not direct_importlib(
            resolver.binding(path, "importlib")
        ):
            continue
        scope = resolver.scopes[path]
        if "getattr" in scope.counts or "getattr" in scope.blocked:
            continue
        for node in tree.body:
            if (
                not isinstance(node, ast.FunctionDef)
                or resolver.binding(path, node.name) is not node
                or not passive_definition(node)
                or any(
                    n.arg in {"importlib", "getattr"}
                    for n in ast.walk(node.args)
                    if isinstance(n, ast.arg)
                )
            ):
                continue
            found = literal_lookup(node)
            if not found or not direct_importlib(resolver.binding(path, "importlib", found.load)):
                continue
            source = resolver.modules.get(found.module)
            if (
                found.module in sys.stdlib_module_names
                or source is None
                or not top_level_file(found.module, source)
                or source == path
                or not isinstance(resolver.binding(source, found.member), ast.FunctionDef)
                or not proof.initialized(path)
                or not proof.initialized(source)
            ):
                continue
            candidates.append((f"{path}::{node.name}", f"{source}::{found.member}", found))
    if not candidates:
        return set()

    # Ignore only the proven import and builtin lookup in each matched body.
    # Other reflection, module escapes or mutations can invalidate the binding.
    operations = frozenset(
        op for _, _, found in candidates for op in (found.load.func, found.lookup.func)
    )
    guarded = frozenset({"importlib", "builtins", "sys"})
    unsafe = namespace_mutations(resolver, proven_operations=operations, guarded_modules=guarded)
    if unsafe is None or guarded & unsafe:
        return set()

    resolved: set[ast.Call] = set()
    unsafe_sources = {resolver.modules[name] for name in unsafe if name in resolver.modules}
    for caller, target, found in candidates:
        path = index.nodes[caller].path
        if path in unsafe_sources or index.nodes[target].path in unsafe_sources:
            continue
        call = found.invoke
        index.call_bindings[call] = CallBinding(caller, target)
        index.add_edge(
            caller,
            target,
            "call",
            f"{path}:{call.lineno} calls {found.module}.{found.member} via literal "
            f"importlib.import_module at line {found.load.lineno} and builtin getattr",
            SourceLocation(path=path, line=call.lineno, end_line=call.end_lineno or call.lineno),
        )
        resolved.update((found.load, found.lookup, call))
    return resolved
