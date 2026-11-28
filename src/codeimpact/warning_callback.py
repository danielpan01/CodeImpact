"""Prove keyed extrema reached from literal rows inside pytest.warns."""

import ast
import re
from functools import partial
from typing import TYPE_CHECKING

from codeimpact.comparison_helper import literal, literal_keywords
from codeimpact.equality import (
    Class,
    Function,
    Instance,
    Unproved,
    Value,
    add_keyed_helper_edge,
    body,
    has_yield,
    keyed_comparison,
    literal_table,
    namespace_writes,
)
from codeimpact.models import SourceLocation
from codeimpact.namespace_callback import CallbackProof, pytest_setup_is_supported
from codeimpact.parameter_rows import inline_decorator
from codeimpact.partial_bindings import audit, dotted

if TYPE_CHECKING:
    from codeimpact.analyzer import Index


# Check a small grammar for valid match arguments without compiling a
# captured regex or predicting whether a warning would match it.
_WARNING_PATTERN = re.compile(r"(?:[A-Za-z0-9_ .:'-]|\[(?:a-z|A-Z|0-9|_)+\]\+){1,160}")


def warning_site(fn: ast.FunctionDef) -> tuple[ast.Call, ast.Call, str, str, str] | None:
    match body(fn):
        case [
            ast.With(
                items=[
                    ast.withitem(
                        context_expr=ast.Call(
                            func=ast.Attribute(value=ast.Name(id="pytest"), attr="warns"),
                            args=[ast.Name(id="DeprecationWarning")],
                        ) as context,
                        optional_vars=(None | ast.Name()),
                    )
                ],
                body=[
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id=callback),
                            args=[ast.Starred(value=ast.Name(id=args))],
                            keywords=[ast.keyword(arg=None, value=ast.Name(id=kwargs))],
                        ) as site
                    ),
                    *_,
                ],
            ),
            *_,
        ] if len({callback, args, kwargs}) == 3:
            match context.keywords:
                case []:
                    return context, site, callback, args, kwargs
                case [ast.keyword(arg="match", value=ast.Constant(value=str() as pattern))]:
                    if len(pattern) <= 256 and _WARNING_PATTERN.fullmatch(pattern):
                        return context, site, callback, args, kwargs
    return None


class WarningCallbackProof(CallbackProof):
    def table_value(self, expr: ast.expr, env: dict[str, Value], depth: int = 0) -> None:
        # Every row is evaluated at collection, even if it supplies no call proof.
        if depth >= 12:
            raise Unproved
        match expr:
            case ast.Dict(keys=keys, values=values):
                self.tick()
                for key, value in zip(keys, values, strict=True):
                    if key is None:
                        raise Unproved
                    literal(key)
                    literal(value)
                return
            case ast.Call(func=func, args=[], keywords=keywords) if dotted(func):
                binding = self.expression(func, env)
                if binding == "builtin:dict" and "dict" not in self.writes:
                    literal_keywords(expr)
                    return
                if binding == "argparse.Namespace" and "Namespace" not in self.writes:
                    names = set()
                    for keyword in keywords:
                        name = keyword.arg
                        if name is None or name.startswith("__") or name in names:
                            raise Unproved
                        names.add(name)
                        # A source callable can be stored as a passive field.
                        if not isinstance(keyword.value, ast.Name) or not isinstance(
                            env.get(keyword.value.id), Function
                        ):
                            literal(keyword.value)
                    return
        super().table_value(expr, env, depth)

    def warning_environment(
        self, path: str, fn: ast.FunctionDef, columns: set[str]
    ) -> dict[str, Value]:
        env = self.module(path)
        test = env.get(fn.name)
        scope = audit(body(fn), local=True)
        context_names = {"pytest", "DeprecationWarning"}
        if (
            not isinstance(test, Function)
            or not self.pytest_parameterization(test)
            or env.get("pytest") != "pytest"
            or self.source_shadows("pytest")
            or "DeprecationWarning" in env
            or self.writes & {"warns", "DeprecationWarning", "__enter__", "__exit__"}
            or scope.wildcard
            or (columns | context_names) & (scope.counts.keys() | scope.blocked)
            or columns & context_names
            or has_yield(fn)
        ):
            raise Unproved
        return env

    def parsed_keys(
        self, inputs: tuple[str, str], factory: Function, owner: Class | None
    ) -> tuple[Instance, Instance]:
        if owner is None:
            raise Unproved
        first = self.parse_fields(owner, factory, inputs[0])
        second = self.parse_fields(owner, factory, inputs[1])
        # Check initialization for these bound values without projecting fields.
        self.core(first, [])
        self.core(second, [])
        return first.instance, second.instance


def add_warning_callback_edges(index: "Index") -> set[tuple[str, str, str]]:
    resolver = index.partials
    if resolver is None:
        return set()
    candidates = [
        (sid, fn, candidate, table)
        for sid, fn in index.syntax.items()
        if index.nodes[sid].kind == "test"
        and "." not in index.nodes[sid].name
        and isinstance(fn, ast.FunctionDef)
        and (candidate := warning_site(fn)) is not None
        and (table := literal_table(fn)) is not None
    ]
    if not candidates:
        return set()
    try:
        writes = namespace_writes(resolver)
    except Unproved:
        return set()
    proof = WarningCallbackProof(
        resolver,
        {path for path, source in index.sources.items() if source.parse_status == "unparseable"},
        scalar_factories=True,
        literal_parameters=True,
        strict_callable_values=True,
        literal_keyword_dicts=True,
    )
    proof.writes = writes
    trails = set()
    for sid, fn, (context, site, callback, args, kwargs), (names, rows) in candidates:
        path = index.nodes[sid].path
        columns = {callback, args, kwargs}
        if (
            columns != set(names)
            or path not in proof.paths
            or not pytest_setup_is_supported(proof, path)
        ):
            continue
        shape = inline_decorator(fn)
        assert shape is not None
        try:
            env = proof.warning_environment(path, fn, columns)
        except (Unproved, RecursionError):
            continue
        for row, row_node in zip(rows, shape[1].elts, strict=True):
            cells = dict(zip(names, row, strict=True))
            bound_callback = cells[callback]
            if not isinstance(bound_callback, ast.Name):
                continue
            helper = env.get(bound_callback.id)
            if (
                not isinstance(helper, Function)
                or helper.wrapper is None
                or helper.sid not in index.nodes
            ):
                continue
            match cells[args], cells[kwargs]:
                case (
                    ast.Tuple(
                        elts=[ast.Constant(value=str() as left), ast.Constant(value=str() as right)]
                    ),
                    ast.Dict(keys=[], values=[]),
                ):
                    inputs = (left, right)
                case _:
                    continue
            try:
                comparison, builtin, method, target = keyed_comparison(
                    proof, helper, key_results=partial(proof.parsed_keys, inputs)
                )
            except (Unproved, RecursionError):
                continue
            if target.sid in (sid, helper.sid) or target.sid not in index.nodes:
                continue
            wrapper_line = body(helper.wrapper.node)[-1].lineno
            index.add_edge(
                sid,
                helper.sid,
                "call",
                f"{path}:{site.lineno} calls {helper.sid} via {helper.wrapper.sid} at line "
                f"{wrapper_line}, expanding two literal strings and empty keyword arguments "
                f"from the pytest row at line {row_node.lineno} inside pytest.warns at line "
                f"{context.lineno}",
                SourceLocation(
                    path=path, line=site.lineno, end_line=site.end_lineno or site.lineno
                ),
            )
            add_keyed_helper_edge(index, helper.sid, target.sid, comparison, builtin, method)
            trails.add((sid, helper.sid, target.sid))
    return trails
