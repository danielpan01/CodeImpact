"""Source-only file and unittest method discovery policies."""

import ast
from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import Literal

from codeimpact.partial_bindings import audit, before

DiscoveryPolicy = Literal["test-files-v1", "test-files-v2", "test-files-v3"]
LEGACY_POLICY: DiscoveryPolicy = "test-files-v1"
V2_POLICY: DiscoveryPolicy = "test-files-v2"
CURRENT_POLICY: DiscoveryPolicy = "test-files-v3"


def is_test_file(path: str, *, policy: DiscoveryPolicy = CURRENT_POLICY) -> bool:
    if policy not in (LEGACY_POLICY, V2_POLICY, CURRENT_POLICY):
        raise ValueError(f"Unknown discovery policy: {policy}")
    name = PurePosixPath(path).name
    return name.endswith(".py") and (
        name.startswith("test_")
        or name.endswith("_test.py")
        or (policy != LEGACY_POLICY and name == "test.py")
    )


def shadows_unittest(paths: Iterable[str]) -> bool:
    """A captured module or package can shadow the standard-library import."""
    return any(
        p.name == "unittest.py" or "unittest" in p.parts[:-1] for p in map(PurePosixPath, paths)
    )


def is_mixed_case_name(name: str) -> bool:
    return len(name) >= 5 and name.startswith("test") and "A" <= name[4] <= "Z"


def unittest_base(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "TestCase"
        and isinstance(node.value, ast.Name)
        and node.value.id == "unittest"
    )


def mixed_case_methods(tree: ast.Module) -> set[ast.FunctionDef]:
    """Prove a direct qualified TestCase base in the captured module namespace."""
    imports = [
        stmt
        for stmt in tree.body
        if isinstance(stmt, ast.Import)
        and any(alias.name == "unittest" and alias.asname is None for alias in stmt.names)
    ]
    if len(imports) != 1:
        return set()
    scope = audit(tree.body)
    if scope.wildcard or scope.counts["unittest"] != 1 or "unittest" in scope.blocked:
        return set()

    # Decline escapes of the module object. Also decline direct access to the
    # import cache/search path, which can replace an otherwise ordinary import.
    bases = {
        base.value
        for cls in ast.walk(tree)
        if isinstance(cls, ast.ClassDef)
        for base in cls.bases
        if isinstance(base, ast.Attribute) and unittest_base(base)
    }
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id == "unittest"
            and node not in bases
        ) or (
            isinstance(node, ast.Attribute)
            and node.attr in {"modules", "path", "meta_path", "path_hooks"}
            and isinstance(node.value, ast.Name)
            and node.value.id == "sys"
        ):
            return set()

    methods: set[ast.FunctionDef] = set()
    for cls in tree.body:
        if (
            not isinstance(cls, ast.ClassDef)
            or len(cls.bases) != 1
            or not unittest_base(cls.bases[0])
            or cls.decorator_list
            or cls.keywords
            or cls.type_params
            or scope.counts[cls.name] != 1
            or cls.name in scope.blocked
            or not before(imports[0], cls)
        ):
            continue
        bindings = audit(cls.body)
        if bindings.wildcard:
            continue
        methods.update(
            stmt
            for stmt in cls.body
            if isinstance(stmt, ast.FunctionDef)
            and is_mixed_case_name(stmt.name)
            and not stmt.decorator_list
            and bindings.counts[stmt.name] == 1
            and stmt.name not in bindings.blocked
        )
    return methods
