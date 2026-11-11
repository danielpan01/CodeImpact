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


@dataclass
class IndexedEdge:
    source: str
    target: str
    kind: EdgeKind
    evidence: list[DependencyEvidence] = field(default_factory=list)
    evidence_keys: set[tuple[int, int, str]] = field(default_factory=set)


@dataclass
class Index:
    nodes: dict[str, Symbol] = field(default_factory=dict)
    edges: dict[tuple[str, str, str], IndexedEdge] = field(default_factory=dict)
    ranges: dict[str, SourceRange] = field(default_factory=dict)
    sources: dict[str, SourceRevision] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

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


def build_index(snapshot: Snapshot) -> Index:
    index = Index()
    trees: dict[str, ast.Module] = {}
    modules: dict[str, str] = {}
    names: dict[str, str] = {}
    definitions: dict[str, list[tuple[str, ast.AST, str]]] = defaultdict(list)
    source_lines: dict[str, list[str]] = {}

    def collect(path: str, nodes: list[ast.stmt], prefix: str = "") -> None:
        for node in nodes:
            if isinstance(node, DEFINITIONS):
                name = f"{prefix}.{node.name}" if prefix else node.name
                sid = f"{path}::{name}"
                is_test = (
                    (PurePosixPath(path).name.startswith("test_") or path.endswith("_test.py"))
                    and node.name.startswith("test_")
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
                collect(path, node.body, name)

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
        collect(path, tree.body)

    for path, tree in trees.items():
        mod = module_name(path)
        module_id = f"{path}::<module>"
        aliases: dict[str, str] = {}
        imports: list[tuple[str, ast.Import | ast.ImportFrom]] = []
        # Only module-level imports are treated as bindings. Function-local imports
        # and reassignments are reported as limitations rather than guessed globally.
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    aliases[alias.asname or alias.name.split(".")[0]] = (
                        alias.name if alias.asname else alias.name.split(".")[0]
                    )
                    imports.append((alias.name, node))
            elif isinstance(node, ast.ImportFrom):
                parent = mod.split(".") if path.endswith("__init__.py") else mod.split(".")[:-1]
                base = node.module or ""
                if node.level:
                    base = ".".join(
                        parent[: len(parent) - node.level + 1] + ([base] if base else [])
                    )
                imports.append((base, node))
                for alias in node.names:
                    if alias.name == "*":
                        index.warnings.append(
                            f"Wildcard import is unresolved: {path}:{node.lineno}"
                        )
                    else:
                        aliases[alias.asname or alias.name] = f"{base}.{alias.name}".lstrip(".")
                        if f"{base}.{alias.name}" in modules:
                            imports.append((f"{base}.{alias.name}", node))
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

        for sid, definition, name in definitions[path]:
            index.add_edge(
                sid,
                module_id,
                "module",
                "Conservative dependency on module initialization",
                SourceLocation(path=path, **index.ranges[sid].model_dump()),
            )
            connect_calls(index, definition, sid, name, path, mod, aliases, names)
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
) -> None:
    args = getattr(node, "args", None)
    shadowed = {a.arg for a in (args.posonlyargs + args.args + args.kwonlyargs)} if args else set()
    if args:
        shadowed.update(a.arg for a in (args.vararg, args.kwarg) if a)

    def visit(current: ast.AST) -> None:
        if current is not node and isinstance(current, DEFINITIONS):
            return
        if isinstance(current, ast.Call):
            call = dotted(current.func)
            target: str | None = None
            if call:
                root, _, tail = call.partition(".")
                if root in shadowed:
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
                    index.add_edge(
                        sid,
                        target,
                        "call",
                        f"{path}:{current.lineno} calls {call}",
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
            visit(child)

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


def analyze(request: AnalysisRequest) -> Report:
    started = time.perf_counter()
    before, after = build_index(request.base), build_index(request.head)
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
    def walk(seeds: list[str], calls_only: bool) -> dict[str, list[str]]:
        adjacency: dict[str, set[str]] = defaultdict(set)
        for edge in edges.values():
            if not calls_only or edge.kind == "call":
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

    paths = walk(changed, False)
    call_paths = walk([sid for sid in changed if nodes[sid].kind != "module"], True)
    recommendations = []
    for sid in sorted(paths):
        if nodes[sid].kind != "test" or sid not in after.nodes:
            continue
        precise = sid in call_paths
        path = call_paths.get(sid, paths[sid])
        distance = len(path) - 1
        fan_in = len(reverse[path[-1]])
        score = min(100, max(1, (90 if precise else 50) - 10 * distance + min(10, fan_in)))
        reason = "Resolved call path" if precise else "Conservative module/import dependency"
        if distance == 0:
            reason = "Test itself changed"
        # Edges are sorted by (source, target, kind), preferring call on a tied pair.
        # Keep the historical BFS/ranking unchanged, but identify each exact typed hop.
        used_edges = [typed_pairs[(a, b)][0] for a, b in zip(path, path[1:], strict=False)]
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
