"""Bounded AST indexing, conservative call resolution and reverse graph traversal.

Edge direction: caller/dependent -> callee/dependency. Impact flows in reverse.
No analyzed code is imported, compiled, installed or executed.
"""

import ast
import hashlib
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Literal

from codeimpact.additive_exports import AdditiveExports
from codeimpact.arguments import ArgumentFallback
from codeimpact.call_arguments import CallArgumentFilter, CallBinding
from codeimpact.descriptor_binding import DescriptorFallback
from codeimpact.discovery import (
    CURRENT_POLICY,
    DiscoveryPolicy,
    is_test_file,
    mixed_case_methods,
    shadows_unittest,
)
from codeimpact.dispatch_fallback import DispatchFallback
from codeimpact.equality import EqualityMode, add_comparison_edges, add_keyed_extrema_edges
from codeimpact.explicit_reexports import add_reexport_edges
from codeimpact.models import (
    AnalysisRequest,
    DependencyEvidence,
    Edge,
    EdgeKind,
    Recommendation,
    Report,
    Snapshot,
    SourceFile,
    SourceLocation,
    SourceRange,
    SourceRevision,
    Symbol,
    SymbolChange,
)
from codeimpact.module_data import ModuleDataFallback
from codeimpact.parameter_rows import ParameterRows
from codeimpact.partial_bindings import PartialBindings
from codeimpact.pytest_fixtures import add_fixture_edges
from codeimpact.runtime_imports import add_runtime_import_edges
from codeimpact.selection import AggregateFallback, propagation_changes
from codeimpact.variadic_fallback import VariadicFallback

DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def digest(node: ast.AST) -> str:
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


def module_name(path: str) -> str:
    parts = list(PurePosixPath(path).with_suffix("").parts)
    if parts[0] == "src":
        parts.pop(0)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted(node.value)
        return f"{parent}.{node.attr}" if parent else None
    return None


def import_targets(
    node: ast.Import | ast.ImportFrom, path: str, modules: dict[str, str]
) -> tuple[list[tuple[str, str]], list[str]]:
    """Decode syntax only; returned targets never trigger a Python import."""
    if isinstance(node, ast.Import):
        return (
            [
                (
                    alias.asname or alias.name.split(".")[0],
                    alias.name if alias.asname else alias.name.split(".")[0],
                )
                for alias in node.names
            ],
            [alias.name for alias in node.names],
        )
    mod = module_name(path)
    parent = mod.split(".") if path.endswith("__init__.py") else mod.split(".")[:-1]
    base = node.module or ""
    if node.level:
        base = ".".join(parent[: len(parent) - node.level + 1] + ([base] if base else []))
    bindings = [
        (alias.asname or alias.name, f"{base}.{alias.name}".lstrip("."))
        for alias in node.names
        if alias.name != "*"
    ]
    imported = [
        base,
        *(
            f"{base}.{a.name}"
            for a in node.names
            if a.name != "*" and f"{base}.{a.name}" in modules
        ),
    ]
    return bindings, imported


def ambiguous_module_imports(tree: ast.Module) -> set[str]:
    """Suppress import names with competing module-scope bindings.

    This is flow-insensitive, not execution-order analysis: require exactly one
    direct import and no competing binding anywhere in the module's own scope.
    Function/class/lambda bodies and comprehension targets have separate scopes.
    """
    imported: dict[str, int] = defaultdict(int)
    rebound: set[str] = set()
    direct = set(tree.body)
    wildcard = False

    def scan(node: ast.AST) -> None:
        nonlocal wildcard
        if isinstance(node, DEFINITIONS):
            rebound.add(node.name)
            # Headers execute outside the body: defaults, decorators, bases and
            # annotations may contain assignments in the enclosing scope.
            for field_name, value in ast.iter_fields(node):
                if field_name == "body":
                    continue
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
                    wildcard = True
                    continue
                binding = alias.asname or (
                    alias.name.split(".")[0] if isinstance(node, ast.Import) else alias.name
                )
                imported[binding] += 1
                if node not in direct:
                    rebound.add(binding)
            return
        if isinstance(node, ast.AnnAssign) and node.value is None:
            # `name: Type` does not assign to name at module scope.
            scan(node.annotation)
            if not isinstance(node.target, ast.Name):
                scan(node.target)
            return
        if isinstance(node, ast.comprehension):
            # Iteration targets do not leak; named expressions in the iter/ifs
            # or result expression can bind in the enclosing scope.
            scan(node.iter)
            for condition in node.ifs:
                scan(condition)
            return
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            # Attribute/subscript stores leave their root Name in Load context.
            rebound.add(node.id)
        elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
            rebound.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            rebound.add(node.rest)
        for child in ast.iter_child_nodes(node):
            scan(child)

    scan(tree)
    return {name for name, count in imported.items() if count != 1 or name in rebound or wildcard}


@dataclass
class LocalImports:
    # bound includes unsupported imports, so they cannot fall through to globals.
    bound: set[str] = field(default_factory=set)
    aliases: dict[str, tuple[str, ast.Import | ast.ImportFrom]] = field(default_factory=dict)
    imports: list[tuple[str, ast.Import | ast.ImportFrom]] = field(default_factory=list)
    wildcard: bool = False


def local_imports(node: ast.AST, path: str, modules: dict[str, str]) -> LocalImports:
    """Recognize one direct, unambiguous binding per name within a function.

    Rebinding is deliberately flow-insensitive: any competing binding suppresses
    that alias throughout this scope. Closures and branch-dependent imports are
    not resolved. Nested functions are indexed separately.
    """
    result = LocalImports()
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return result
    args = node.args
    blocked = {a.arg for a in [*args.posonlyargs, *args.args, *args.kwonlyargs]}
    blocked.update(a.arg for a in (args.vararg, args.kwarg) if a)
    candidates: dict[str, list[tuple[str, ast.Import | ast.ImportFrom]]] = defaultdict(list)
    direct = set(node.body)

    def mutation_root(current: ast.AST) -> str | None:
        while isinstance(current, (ast.Attribute, ast.Subscript)):
            current = current.value
        return current.id if isinstance(current, ast.Name) else None

    def scan(current: ast.AST) -> None:
        if isinstance(current, DEFINITIONS):
            blocked.add(current.name)
            # Defaults/decorators/bases execute in this enclosing scope. Do not
            # confuse their stores with ordinary assignments in the nested body.
            for field_name, value in ast.iter_fields(current):
                if field_name == "body":
                    continue
                if isinstance(value, ast.AST):
                    scan(value)
                elif isinstance(value, list):
                    for child in value:
                        if isinstance(child, ast.AST):
                            scan(child)
            # An inner nonlocal declaration or attribute mutation can invalidate
            # the outer alias. Ordinary inner name assignments cannot.
            for child in ast.walk(current):
                if isinstance(child, ast.Nonlocal):
                    blocked.update(child.names)
                elif isinstance(child, (ast.Attribute, ast.Subscript)) and isinstance(
                    child.ctx, (ast.Store, ast.Del)
                ):
                    if root := mutation_root(child):
                        blocked.add(root)
            return
        if isinstance(current, ast.Lambda):
            # Lambda defaults also run now; the lambda body has its own bindings.
            scan(current.args)
            return
        if isinstance(current, (ast.Import, ast.ImportFrom)):
            bindings, imported = import_targets(current, path, modules)
            parent = module_name(path).split(".")
            if not path.endswith("__init__.py"):
                parent = parent[:-1]
            valid_relative = not isinstance(current, ast.ImportFrom) or current.level <= len(parent)
            eligible = current in direct and valid_relative
            for binding, target in bindings:
                result.bound.add(binding)
                candidates[binding].append((target, current))
                if not eligible:
                    blocked.add(binding)
            result.wildcard |= any(alias.name == "*" for alias in current.names)
            if eligible:
                result.imports.extend((target, current) for target in imported)
            return
        if isinstance(current, ast.Name) and isinstance(current.ctx, (ast.Store, ast.Del)):
            blocked.add(current.id)
        elif isinstance(current, (ast.Attribute, ast.Subscript)) and isinstance(
            current.ctx, (ast.Store, ast.Del)
        ):
            if root := mutation_root(current):
                blocked.add(root)
        elif isinstance(current, (ast.Global, ast.Nonlocal)):
            blocked.update(current.names)
        elif isinstance(current, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and current.name:
            blocked.add(current.name)
        elif isinstance(current, ast.MatchMapping) and current.rest:
            blocked.add(current.rest)
        for child in ast.iter_child_nodes(current):
            scan(child)

    for statement in node.body:
        scan(statement)
    result.aliases = {
        binding: values[0]
        for binding, values in candidates.items()
        if len(values) == 1 and binding not in blocked and not result.wildcard
    }
    return result


@dataclass
class IndexedEdge:
    source: str
    target: str
    kind: EdgeKind
    evidence: list[DependencyEvidence] = field(default_factory=list)
    evidence_keys: set[tuple[int, int, str]] = field(default_factory=set)


@dataclass
class Index:
    call_bindings: dict[ast.Call, CallBinding] = field(default_factory=dict)
    partials: PartialBindings | None = None
    nodes: dict[str, Symbol] = field(default_factory=dict)
    edges: dict[tuple[str, str, str], IndexedEdge] = field(default_factory=dict)
    ranges: dict[str, SourceRange] = field(default_factory=dict)
    sources: dict[str, SourceRevision] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    # Internal source data for bounded selection; never serialized or executed.
    syntax: dict[str, ast.AST] = field(default_factory=dict)
    aliases: dict[str, dict[str, str]] = field(default_factory=dict)
    ambiguous: dict[str, set[str]] = field(default_factory=dict)
    local_bindings: dict[str, LocalImports] = field(default_factory=dict)

    def add_edge(
        self,
        source: str,
        target: str,
        kind: EdgeKind,
        evidence: str,
        location: SourceLocation,
    ) -> None:
        if target in self.nodes and source != target:
            edge = self.edges.setdefault((source, target, kind), IndexedEdge(source, target, kind))
            key = (location.line, location.end_line, evidence)
            if key in edge.evidence_keys:
                return
            edge.evidence_keys.add(key)
            item = DependencyEvidence(
                text=evidence,
                location=location,
                target_location=SourceLocation(
                    path=self.nodes[target].path, **self.ranges[target].model_dump()
                ),
            )
            edge.evidence.append(item)


def build_index(
    snapshot: Snapshot,
    *,
    policy: DiscoveryPolicy = CURRENT_POLICY,
    reexports: bool = True,
    fixtures: bool = True,
    runtime_imports: bool = True,
    equality: EqualityMode = True,
) -> Index:
    index = Index()
    trees: dict[str, ast.Module] = {}
    modules: dict[str, str] = {}
    names: dict[str, str] = {}
    definitions: dict[str, list[tuple[str, ast.AST, str]]] = defaultdict(list)
    source_lines: dict[str, list[str]] = {}

    expand = policy == CURRENT_POLICY and not shadows_unittest(snapshot.files)

    def collect(
        path: str,
        nodes: list[ast.stmt],
        test_file: bool,
        mixed: set[ast.FunctionDef],
        prefix: str = "",
    ) -> None:
        for node in nodes:
            if isinstance(node, DEFINITIONS):
                name = f"{prefix}.{node.name}" if prefix else node.name
                sid = f"{path}::{name}"
                index.syntax[sid] = node
                is_test = (
                    test_file
                    and (node.name.startswith("test_") or node in mixed)
                    and not isinstance(node, ast.ClassDef)
                )
                kind: Literal["test", "class", "function"] = (
                    "test" if is_test else "class" if isinstance(node, ast.ClassDef) else "function"
                )
                index.nodes[sid] = Symbol(
                    id=sid,
                    name=name,
                    path=path,
                    line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                    kind=kind,
                    fingerprint=digest(node),
                )
                start = min([node.lineno, *(d.lineno for d in node.decorator_list)])
                # AST decorator expressions omit the @ token and wrapping parentheses.
                # Walk back through that prefix to retain the complete first decorator.
                if node.decorator_list:
                    while start > 1 and not source_lines[path][start - 1].lstrip().startswith("@"):
                        start -= 1
                index.ranges[sid] = SourceRange(
                    line=start,
                    end_line=node.end_lineno or node.lineno,
                )
                names[f"{module_name(path)}.{name}"] = sid
                definitions[path].append((sid, node, name))
                collect(path, node.body, test_file, mixed, name)

    for path, source in sorted(snapshot.files.items()):
        # Match Python's universal physical newlines, not str.splitlines()'s extra
        # Unicode separators (which can occur inside a string on a single code line).
        lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if lines[-1] == "":
            lines.pop()
        source_lines[path] = lines
        parse_status: Literal["parsed", "unparseable"] = "parsed"
        try:
            tree = ast.parse(source, filename=path)
        except (SyntaxError, ValueError, RecursionError) as exc:
            index.warnings.append(f"Cannot parse {path}: {type(exc).__name__}")
            # Keep failed modules in the graph and distinguish invalid source revisions.
            tree = ast.Module(body=[], type_ignores=[])
            fingerprint = hashlib.sha256(source.encode()).hexdigest()
            parse_status = "unparseable"
        else:
            # Successful parses use AST semantics, even for empty/comment-only modules.
            fingerprint = digest(tree)
        index.sources[path] = SourceRevision(text=source, parse_status=parse_status)
        trees[path] = tree
        mod = module_name(path)
        if mod in modules:
            raise ValueError(f"Ambiguous module layout: {path} and {modules[mod]}")
        modules[mod] = path
        sid = f"{path}::<module>"
        index.syntax[sid] = tree
        # Module fingerprints include all source semantics. Module dependency edges are
        # conservative fallbacks; the UI labels them separately from resolved calls.
        index.nodes[sid] = Symbol(
            id=sid,
            name=mod or "<root>",
            path=path,
            line=1,
            end_line=max(1, len(lines)),
            kind="module",
            fingerprint=fingerprint,
        )
        index.ranges[sid] = SourceRange(line=1, end_line=index.nodes[sid].end_line)
        names[mod] = sid
        test_file = is_test_file(path, policy=policy)
        mixed = mixed_case_methods(tree) if expand and test_file else set()
        collect(path, tree.body, test_file, mixed)

    partials = PartialBindings(trees, modules, import_targets)
    index.partials = partials
    runtime_calls = add_runtime_import_edges(index) if runtime_imports else set()
    for path, tree in trees.items():
        mod = module_name(path)
        module_id = f"{path}::<module>"
        aliases: dict[str, str] = {}
        imports: list[tuple[str, ast.Import | ast.ImportFrom]] = []
        # Retain conservative direct-import edges even when a name is rebound.
        # Only precise calls are suppressed by the module binding audit below.
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                bindings, imported_modules = import_targets(node, path, modules)
                aliases.update(bindings)
                imports.extend((target, node) for target in imported_modules)
                for alias in node.names:
                    if alias.name == "*":
                        index.warnings.append(
                            f"Wildcard import is unresolved: {path}:{node.lineno}"
                        )
        for imported, statement in imports:
            if imported in modules:
                target = f"{modules[imported]}::<module>"
                index.add_edge(
                    module_id,
                    target,
                    "import",
                    f"{path}:{statement.lineno} imports {imported}",
                    SourceLocation(
                        path=path,
                        line=statement.lineno,
                        end_line=statement.end_lineno or statement.lineno,
                    ),
                )

        ambiguous = ambiguous_module_imports(tree)
        index.aliases[path] = aliases
        index.ambiguous[path] = ambiguous
        if ambiguous:
            index.warnings.append(
                f"Ambiguous module import binding: {module_id}: {', '.join(sorted(ambiguous))}"
            )
        scopes = {
            name: local_imports(definition, path, modules)
            for _, definition, name in definitions[path]
        }
        for sid, definition, name in definitions[path]:
            index.add_edge(
                sid,
                module_id,
                "module",
                "Conservative dependency on module initialization",
                SourceLocation(path=path, **index.ranges[sid].model_dump()),
            )
            local = scopes[name]
            index.local_bindings[sid] = local
            for imported, statement in local.imports:
                if imported in modules:
                    index.add_edge(
                        sid,
                        f"{modules[imported]}::<module>",
                        "import",
                        f"{path}:{statement.lineno} imports {imported}",
                        SourceLocation(
                            path=path,
                            line=statement.lineno,
                            end_line=statement.end_lineno or statement.lineno,
                        ),
                    )
            if local.wildcard:
                index.warnings.append(f"Wildcard local import is unresolved: {sid}")
            if unresolved := local.bound - local.aliases.keys():
                index.warnings.append(
                    f"Ambiguous or unsupported local import binding: {sid}: "
                    f"{', '.join(sorted(unresolved))}"
                )
            parents = name.split(".")[:-1]
            enclosing = set().union(
                *(
                    scopes[".".join(parents[:i])].bound
                    for i in range(1, len(parents) + 1)
                    if ".".join(parents[:i]) in scopes
                )
            )
            connect_calls(
                index,
                definition,
                sid,
                name,
                path,
                mod,
                aliases,
                names,
                local,
                enclosing,
                ambiguous,
                partials,
                [
                    other
                    for _, other, qualified in definitions[path]
                    if name == qualified or name.startswith(qualified + ".")
                ],
                runtime_calls,
            )
    if reexports:
        add_reexport_edges(index)
    if fixtures:
        add_fixture_edges(index)
    if equality:
        add_comparison_edges(index, mode=equality)
    if equality is True:
        add_keyed_extrema_edges(index)
    return index


def connect_calls(
    index: Index,
    node: ast.AST,
    sid: str,
    name: str,
    path: str,
    mod: str,
    aliases: dict[str, str],
    names: dict[str, str],
    local: LocalImports,
    enclosing_imports: set[str],
    ambiguous_imports: set[str],
    partials: PartialBindings,
    partial_scopes: list[ast.AST],
    runtime_calls: set[ast.Call],
) -> None:
    args = getattr(node, "args", None)
    shadowed = {a.arg for a in (args.posonlyargs + args.args + args.kwonlyargs)} if args else set()
    if args:
        shadowed.update(a.arg for a in (args.vararg, args.kwarg) if a)

    def visit(
        current: ast.AST, allow_local: bool = True, partial_shadowed: frozenset[str] = frozenset()
    ) -> None:
        if current is not node and isinstance(current, DEFINITIONS):
            return
        if isinstance(
            current, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)
        ):
            allow_local = False
            # A global partial can be used in a comprehension/lambda only when
            # the inner scope does not shadow it. Local imports retain their
            # existing more conservative handling.
            partial_shadowed = (
                partial_shadowed
                | frozenset(
                    child.id
                    for child in ast.walk(current)
                    if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del))
                )
                | frozenset(child.arg for child in ast.walk(current) if isinstance(child, ast.arg))
            )
        if isinstance(current, ast.Call) and current not in runtime_calls:
            call = dotted(current.func)
            target: str | None = None
            if call:
                root, _, tail = call.partition(".")
                handled, partial_target, detail = partials.call_target(
                    path, call, current, partial_scopes, root not in partial_shadowed
                )
                if local.wildcard:
                    pass
                elif root in local.bound:
                    binding = local.aliases.get(root)
                    if allow_local and binding:
                        target_name, statement = binding
                        # Source positions include columns for imports/calls on one line.
                        if (current.lineno, current.col_offset) > (
                            statement.end_lineno or statement.lineno,
                            statement.end_col_offset or 0,
                        ):
                            target = names.get(target_name + (f".{tail}" if tail else ""))
                elif handled:
                    target = partial_target
                elif root in shadowed or root in enclosing_imports or root in ambiguous_imports:
                    pass
                elif root in aliases:
                    target = names.get(aliases[root] + (f".{tail}" if tail else ""))
                else:
                    scope = name.split(".")
                    # Resolve nested lexical functions, then module-level functions.
                    while target is None:
                        target = names.get(".".join([mod, *scope, call]))
                        if not scope:
                            break
                        scope.pop()
                if target:
                    call_binding = CallBinding(sid, target)
                    if partial_target:
                        construction = partials.candidates[path][call].value
                        assert isinstance(construction, ast.Call)
                        call_binding = CallBinding(
                            sid,
                            target,
                            tuple(construction.args[1:]),
                            tuple(construction.keywords),
                            call,
                        )
                    index.call_bindings[current] = call_binding
                    index.add_edge(
                        sid,
                        target,
                        "call",
                        f"{path}:{current.lineno} calls {call}{detail if partial_target else ''}",
                        SourceLocation(
                            path=path,
                            line=current.lineno,
                            end_line=current.end_lineno or current.lineno,
                        ),
                    )
                elif call not in {
                    "len",
                    "str",
                    "int",
                    "float",
                    "bool",
                    "list",
                    "dict",
                    "set",
                    "range",
                    "print",
                    "min",
                    "max",
                    "sum",
                    "round",
                    "abs",
                }:
                    index.warnings.append(f"Unresolved call {call}: {path}:{current.lineno}")
            else:
                index.warnings.append(f"Dynamic call: {path}:{current.lineno}")
        for child in ast.iter_child_nodes(current):
            visit(child, allow_local, partial_shadowed)

    # Assignments can rebind a global/imported callable. Avoid claiming a
    # precise edge in this case (module fallback can still select tests).
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            shadowed.add(child.id)
    visit(node)


def merge_edges(before: Index, after: Index) -> dict[tuple[str, str, str], Edge]:
    result = {}
    for key in sorted(before.edges.keys() | after.edges.keys()):
        old, new = before.edges.get(key), after.edges.get(key)
        edge = new or old
        assert edge is not None
        result[key] = Edge(
            id=hashlib.sha256(json.dumps(key, ensure_ascii=True).encode()).hexdigest(),
            source=edge.source,
            target=edge.target,
            kind=edge.kind,
            revision="both" if old and new else "before" if old else "after",
            before=sorted(
                old.evidence, key=lambda e: (e.location.line, e.location.end_line, e.text)
            )
            if old
            else [],
            after=sorted(new.evidence, key=lambda e: (e.location.line, e.location.end_line, e.text))
            if new
            else [],
        )
    return result


def analyze(
    request: AnalysisRequest,
    *,
    policy: DiscoveryPolicy = CURRENT_POLICY,
    variadic: bool = True,
    parameter_rows: bool = True,
    reexports: bool = True,
    fixtures: bool = True,
    runtime_imports: bool = True,
    equality: EqualityMode = True,
) -> Report:
    started = time.perf_counter()
    before = build_index(
        request.base,
        policy=policy,
        reexports=False,
        fixtures=False,
        runtime_imports=runtime_imports,
        equality=False,
    )
    after = build_index(
        request.head,
        policy=policy,
        reexports=False,
        fixtures=False,
        runtime_imports=runtime_imports,
        equality=False,
    )
    nodes = before.nodes | after.nodes
    edges = merge_edges(before, after)
    changed = sorted(
        sid
        for sid in nodes
        if (
            sid not in before.nodes
            or sid not in after.nodes
            or before.nodes[sid].fingerprint != after.nodes[sid].fingerprint
        )
    )
    reverse: dict[str, set[str]] = defaultdict(set)
    typed_pairs: dict[tuple[str, str], list[Edge]] = defaultdict(list)
    for edge in edges.values():
        reverse[edge.target].add(edge.source)
        typed_pairs[(edge.source, edge.target)].append(edge)

    # A second traversal over call edges supplies stronger evidence when available.
    active = propagation_changes(before, after, changed)
    arguments = ArgumentFallback(before, after, {nodes[sid].path for sid in active})
    active = [sid for sid in active if sid not in arguments.passive_import_modules]
    aggregate = [sid for sid in changed if nodes[sid].kind == "module" and sid not in active]
    aggregate_paths = {nodes[sid].path for sid in aggregate}
    fallback = AggregateFallback(before, after, aggregate_paths)
    descriptors = DescriptorFallback(fallback.before, fallback.after, aggregate_paths)
    call_arguments = CallArgumentFilter(before, after, {nodes[sid].path for sid in active})

    dispatch = DispatchFallback(before, after, call_arguments)
    module_data = ModuleDataFallback(before, after, {nodes[sid].path for sid in active})
    exports = AdditiveExports(before, after, {nodes[sid].path for sid in active})
    rows = ParameterRows(
        before, after, {nodes[sid].path for sid in active} if parameter_rows else set()
    )
    guarded = VariadicFallback(
        fallback.before,
        fallback.after,
        {nodes[sid].path for sid in changed if nodes[sid].kind == "module"} if variadic else set(),
    )

    def module_allows(sid: str, seed: str) -> bool:
        path = nodes[seed].path
        return guarded.allows(sid, path) and rows.allows(sid, path)

    def walk(
        seeds: list[str],
        calls_only: bool,
        aggregate_path: str | None = None,
        initialization_path: str | None = None,
        body_path: str | None = None,
        revision: Literal["before", "after"] | None = None,
    ) -> dict[str, list[str]]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in edges.values():
            if revision is not None and not getattr(edge, revision):
                continue
            if not calls_only or edge.kind == "call":
                if (
                    body_path is not None
                    and edge.kind == "call"
                    and nodes[edge.source].kind == "test"
                    and edge.source not in changed
                    and not call_arguments.allows(edge.source, edge.target, body_path)
                ):
                    continue
                if (
                    initialization_path is not None
                    and nodes[edge.source].kind == "test"
                    and not arguments.allows(edge.source, initialization_path)
                ):
                    continue
                if (
                    aggregate_path is not None
                    and (
                        edge.kind == "module"
                        or (edge.kind == "import" and nodes[edge.source].kind != "module")
                    )
                    and not fallback.allows(edge.source, aggregate_path)
                ):
                    continue
                adjacency[edge.target].add(edge.source)
        paths = {sid: [sid] for sid in seeds}
        queue = deque(seeds)
        while queue:
            dependency = queue.popleft()
            for dependent in sorted(adjacency[dependency]):
                if dependent not in paths:
                    paths[dependent] = [dependent, *paths[dependency]]
                    queue.append(dependent)
        return paths

    def active_paths(calls_only: bool) -> dict[str, list[str]]:
        seeds = [sid for sid in active if not calls_only or nodes[sid].kind != "module"]
        ordinary = [
            sid
            for sid in seeds
            if nodes[sid].path not in arguments.changes
            and nodes[sid].path not in call_arguments.changes
            and nodes[sid].path not in module_data.changes
            and not (nodes[sid].kind == "module" and nodes[sid].path in exports.changes)
        ]
        result = walk(ordinary, calls_only)
        filtered_seeds = {
            sid
            for sid in ordinary
            if nodes[sid].kind == "module"
            and (nodes[sid].path in guarded.changes or nodes[sid].path in rows.changes)
        }
        excluded = {
            sid
            for sid, path in result.items()
            if nodes[sid].kind == "test"
            and path[-1] in filtered_seeds
            and not module_allows(sid, path[-1])
        }
        if excluded:
            # Reroute only tests whose winning module path was excluded. Keep
            # the original multi-source traversal for every other test.
            alternate = walk([sid for sid in ordinary if sid not in filtered_seeds], calls_only)
            for sid in excluded:
                result.pop(sid)
                if sid in alternate:
                    result[sid] = alternate[sid]
            for seed in sorted(filtered_seeds):
                candidates = walk([seed], calls_only)
                for sid in sorted(excluded & candidates.keys()):
                    candidate, current = candidates[sid], result.get(sid)
                    if module_allows(sid, seed) and (
                        current is None or (len(candidate), candidate) < (len(current), current)
                    ):
                        result[sid] = candidate
        for source_path in call_arguments.changes:
            group = [sid for sid in seeds if nodes[sid].path == source_path]
            for sid, candidate in walk(group, calls_only, body_path=source_path).items():
                current = result.get(sid)
                if current is None or (len(candidate), candidate) < (len(current), current):
                    result[sid] = candidate
        for source_path in module_data.changes:
            group = [sid for sid in seeds if nodes[sid].path == source_path]
            for sid, candidate in walk(group, calls_only).items():
                if nodes[sid].kind == "test" and not module_data.allows(sid, source_path):
                    continue
                current = result.get(sid)
                if current is None or (len(candidate), candidate) < (len(current), current):
                    result[sid] = candidate
        for source_path in exports.changes:
            seed = f"{source_path}::<module>"
            if seed not in seeds:
                continue
            for sid, candidate in walk([seed], calls_only).items():
                if nodes[sid].kind == "test" and not exports.allows(sid, source_path):
                    continue
                current = result.get(sid)
                if current is None or (len(candidate), candidate) < (len(current), current):
                    result[sid] = candidate
        for source_path in arguments.changes:
            group = [sid for sid in seeds if nodes[sid].path == source_path]
            for sid, candidate in walk(group, calls_only, initialization_path=source_path).items():
                current = result.get(sid)
                if current is None or (len(candidate), candidate) < (len(current), current):
                    result[sid] = candidate
        return result

    paths = active_paths(False)
    for module in aggregate:
        for sid, candidate in walk(
            [module], False, nodes[module].path, body_path=nodes[module].path
        ).items():
            if nodes[sid].kind == "test" and (
                not descriptors.allows(sid, nodes[module].path)
                or not dispatch.allows(sid, nodes[module].path)
                or not guarded.allows(sid, nodes[module].path)
            ):
                continue
            current = paths.get(sid)
            if current is None or (len(candidate), candidate) < (len(current), current):
                paths[sid] = candidate
    call_paths = active_paths(True)
    fixture_paths: dict[str, list[str]] = {}
    old_fixtures = add_fixture_edges(before) if fixtures else set()
    new_fixtures = add_fixture_edges(after) if fixtures else set()
    # A new path must exist in one revision from injection through the call trail.
    # Keep the existing selection and ranking for paths that already have call evidence.
    fixture_seeds = [sid for sid in active if nodes[sid].kind != "module"]
    revision_injections: tuple[
        tuple[Literal["before", "after"], set[tuple[str, str, str]]], ...
    ] = (("before", old_fixtures), ("after", new_fixtures))
    for revision, injections in revision_injections:
        if not injections:
            continue
        revision_calls = walk(fixture_seeds, True, revision=revision)
        for source, target, _ in sorted(injections):
            tail = revision_calls.get(target)
            if tail is None or source in call_paths or source in tail:
                continue
            candidate = [source, *tail]
            current = fixture_paths.get(source)
            if current is None or (len(candidate), candidate) < (len(current), current):
                fixture_paths[source] = candidate
    added_calls: dict[str, str] = {}
    added_incoming: dict[str, set[str]] = defaultdict(set)
    active_targets = set(active)
    if reexports:
        # The existing graph selects tests. New edges can explain those tests
        # without expanding, pruning or rerouting the selection walk.
        additions = add_reexport_edges(before) | add_reexport_edges(after)
        if additions:
            for source, target, _ in sorted(additions):
                added_incoming[target].add(source)
                if (
                    source in paths
                    and nodes[source].kind == "test"
                    and source not in call_paths
                    and target in active_targets
                    and call_arguments.allows(source, target, nodes[target].path)
                ):
                    added_calls.setdefault(source, target)
    comparisons = set()
    if equality:
        # A comparison site directly calls the proved binding. Keep the original
        # walks and scores for all other paths, including direct test edits.
        comparisons = add_comparison_edges(before, mode=equality) | add_comparison_edges(
            after, mode=equality
        )
        for source, target in sorted(comparisons):
            if (
                target in active_targets
                and source not in call_paths
                and source not in fixture_paths
            ):
                added_calls.setdefault(source, target)
                added_incoming[target].add(source)
                paths.setdefault(source, [source, target])
    for source, path in fixture_paths.items():
        paths.setdefault(source, path)
    extrema_paths: dict[str, list[str]] = {}
    extrema_incoming: dict[str, set[str]] = defaultdict(set)
    if equality is True:
        before_extrema = add_keyed_extrema_edges(before)
        after_extrema = add_keyed_extrema_edges(after)
        for trail in sorted(before_extrema | after_extrema):
            source, helper, target = trail
            extrema_incoming[target].add(helper)
            if (
                target in active_targets
                and source not in call_paths
                and source not in fixture_paths
                and source not in added_calls
            ):
                # An ordinary caller edge and a helper edge proved for another
                # test can appear together in a revision without this proof.
                hops = ((source, helper, "call"), (helper, target, "call"))
                if any(
                    trail not in proved and all(hop in index.edges for hop in hops)
                    for index, proved in ((before, before_extrema), (after, after_extrema))
                ):
                    continue
                candidate = [source, helper, target]
                extrema_paths.setdefault(source, candidate)
                paths.setdefault(source, candidate)
    if old_fixtures or new_fixtures or comparisons or added_incoming or extrema_incoming:
        edges = merge_edges(before, after)
    recommendations = []
    for sid in sorted(paths):
        if nodes[sid].kind != "test" or sid not in after.nodes:
            continue
        proof = added_calls.get(sid)
        injection = fixture_paths.get(sid)
        extremum = extrema_paths.get(sid)
        resolved = call_paths.get(sid) or injection or extremum
        precise = proof is not None or resolved is not None
        path = [sid, proof] if proof else resolved or paths[sid]
        distance = len(path) - 1
        incoming = reverse[path[-1]]
        if proof:
            incoming = incoming | added_incoming[proof]
        elif extremum:
            incoming = incoming | extrema_incoming[path[-1]]
        fan_in = len(incoming)
        score = min(100, max(1, (90 if precise else 50) - 10 * distance + min(10, fan_in)))
        reason = "Resolved call path" if precise else "Conservative module/import dependency"
        if distance == 0:
            reason = "Test itself changed"
        # Edges are sorted by (source, target, kind), preferring call on a tied pair.
        # Retain scoring and typed-edge preference while identifying each exact hop.
        if proof:
            used_edges = [edges[(sid, proof, "call")]]
        elif injection:
            reason = "Resolved fixture dependency"
            used_edges = [edges[(sid, injection[1], "fixture")]]
            used_edges.extend(
                edges[(a, b, "call")] for a, b in zip(path[1:], path[2:], strict=False)
            )
        elif extremum:
            used_edges = [edges[(a, b, "call")] for a, b in zip(path, path[1:], strict=False)]
        else:
            original = [typed_pairs[(a, b)][0] for a, b in zip(path, path[1:], strict=False)]
            used_edges = [edges[(e.source, e.target, e.kind)] for e in original]
        in_before = sid in before.nodes and all(e.before for e in used_edges)
        in_after = sid in after.nodes and all(e.after for e in used_edges)
        recommendations.append(
            Recommendation(
                symbol=sid,
                score=score,
                distance=distance,
                reason=reason,
                evidence_path=path,
                evidence_edges=[e.id for e in used_edges],
                path_revision="both"
                if in_before and in_after
                else "before"
                if in_before
                else "after"
                if in_after
                else "mixed",
            )
        )
    recommendations.sort(key=lambda item: (-item.score, item.symbol))
    return Report(
        schema_version="2.1" if old_fixtures or new_fixtures else "2.0",
        label=request.label,
        nodes=[nodes[sid] for sid in sorted(nodes)],
        edges=[edges[key] for key in sorted(edges)],
        changed=changed,
        changes=[
            SymbolChange(
                symbol=sid,
                path=nodes[sid].path,
                status="added"
                if sid not in before.nodes
                else "removed"
                if sid not in after.nodes
                else "modified",
                before=before.ranges.get(sid),
                after=after.ranges.get(sid),
            )
            for sid in changed
        ],
        source_files=[
            SourceFile(path=path, before=before.sources.get(path), after=after.sources.get(path))
            for path in sorted({nodes[sid].path for sid in changed})
        ],
        removed=sorted(before.nodes.keys() - after.nodes.keys()),
        impacted=sorted(set(paths) - set(changed)),
        recommendations=recommendations,
        warnings=sorted(
            set(
                before.warnings
                + after.warnings
                + [
                    "Static analysis is incomplete: dynamic dispatch, fixtures, "
                    "reflection, re-exports, "
                    "inheritance and runtime imports may hide dependencies. "
                    "Keep the full test suite as a gate.",
                    "Risk scores prioritize review; they are not calibrated failure probabilities.",
                ]
            )
        ),
        stats={
            "files_base": len(request.base.files),
            "files_head": len(request.head.files),
            "symbols": len(nodes),
            "edges": len(edges),
            "changed": len(changed),
            "impacted": len(set(paths) - set(changed)),
            "recommended_tests": len(recommendations),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
