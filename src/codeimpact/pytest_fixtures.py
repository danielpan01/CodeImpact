"""Same-directory pytest fixture injection proved from one snapshot's syntax."""

import ast
from functools import cache
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from codeimpact.explicit_reexports import Proof, passive_definition
from codeimpact.models import SourceLocation

if TYPE_CHECKING:
    from codeimpact.analyzer import Index


def direct_pytest_import(stmt: ast.AST | None) -> bool:
    return (
        isinstance(stmt, ast.Import)
        and len(stmt.names) == 1
        and stmt.names[0].name == "pytest"
        and stmt.names[0].asname is None
    )


def fixture_decorator(node: ast.FunctionDef) -> ast.Attribute | None:
    if len(node.decorator_list) != 1:
        return None
    decorator = node.decorator_list[0]
    if (
        isinstance(decorator, ast.Attribute)
        and decorator.attr == "fixture"
        and isinstance(decorator.value, ast.Name)
        and decorator.value.id == "pytest"
    ):
        return decorator
    return None


def add_fixture_edges(index: "Index") -> set[tuple[str, str, str]]:
    partials = index.partials
    if partials is None:
        return set()
    trees = partials.trees
    if not any(PurePosixPath(path).name == "conftest.py" for path in trees):
        return set()
    if any(
        part in {"pytest.py", "pytest"}
        for path in index.sources
        for part in PurePosixPath(path).parts
    ):
        return set()
    proof = Proof(partials)
    # The index uses empty trees for parse errors. They cannot prove initialization.
    proof.checked.update(
        (path, False)
        for path, source in index.sources.items()
        if source.parse_status == "unparseable"
    )
    edges: set[tuple[str, str, str]] = set()

    @cache
    def simple_module(path: str, *, conftest: bool) -> bool:
        scope = partials.scopes[path]
        if (
            scope.wildcard
            or scope.blocked
            or any(
                count != 1
                or name.startswith(("pytest_", "setup_", "teardown_"))
                or name == "pytestmark"
                for name, count in scope.counts.items()
            )
        ):
            return False
        if path not in proof.modules or any(
            (init := str(parent / "__init__.py")) in index.sources and not proof.initialized(init)
            for parent in PurePosixPath(path).parents
        ):
            return False
        for stmt in trees[path].body:
            if direct_pytest_import(stmt):
                continue
            if (
                conftest
                and isinstance(stmt, ast.FunctionDef)
                and (decorator := fixture_decorator(stmt))
            ):
                if (
                    not direct_pytest_import(partials.binding(path, "pytest", decorator))
                    or stmt.name == "request"
                    or stmt.name.startswith("__")
                    or stmt.returns is not None
                    or stmt.type_params
                    or any(isinstance(n, ast.arg) for n in ast.walk(stmt.args))
                    or any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(stmt))
                ):
                    return False
                continue
            if isinstance(stmt, ast.Assign) or not proof.statement(path, stmt):
                return False
        return True

    for test_path, tree in trees.items():
        directory = PurePosixPath(test_path).parent
        conftest = str(directory / "conftest.py")
        if (
            test_path == conftest
            or conftest not in trees
            or any(str(parent / "conftest.py") in index.sources for parent in directory.parents)
        ):
            continue
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            source = f"{test_path}::{node.name}"
            if index.nodes[source].kind != "test" or not passive_definition(node):
                continue
            args = node.args
            if (
                len(args.args) != 1
                or args.posonlyargs
                or args.kwonlyargs
                or args.defaults
                or args.vararg
                or args.kwarg
                or any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(node))
            ):
                continue
            parameter = args.args[0]
            target = f"{conftest}::{parameter.arg}"
            declaration = partials.binding(conftest, parameter.arg)
            if (
                isinstance(declaration, ast.FunctionDef)
                and fixture_decorator(declaration)
                and partials.binding(test_path, parameter.arg) is None
                and simple_module(conftest, conftest=True)
                and simple_module(test_path, conftest=False)
            ):
                index.add_edge(
                    source,
                    target,
                    "fixture",
                    f"Parameter {parameter.arg} receives same-directory pytest fixture",
                    SourceLocation(
                        path=test_path,
                        line=parameter.lineno,
                        end_line=parameter.end_lineno or parameter.lineno,
                    ),
                )
                edges.add((source, target, "fixture"))
    return edges
