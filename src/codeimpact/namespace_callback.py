"""Trace literal pytest callback rows through a guarded comparison."""

import ast
import re
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from codeimpact.comparison_helper import (
    HelperProof,
    Operand,
    ParsedOperand,
    Scalar,
    assigned,
    attribute,
    call_to,
    literal,
    literal_keywords,
    positional,
)
from codeimpact.equality import (
    STDLIB,
    UNBOUND,
    Class,
    Function,
    Unproved,
    Value,
    body,
    has_yield,
    identifier,
    instance_method,
    literal_table,
    namespace_writes,
    parameters,
)
from codeimpact.models import SourceLocation
from codeimpact.parameter_rows import inline_decorator
from codeimpact.partial_bindings import dotted

if TYPE_CHECKING:
    from codeimpact.analyzer import Index


# Match the *syntax* of the captured pattern with analyzer-owned regexes.
# No captured regex is compiled or matched against an input.
_NAME = r"([A-Za-z_][A-Za-z0-9_]*)"
_DECIMAL = re.escape("(?P<") + _NAME + re.escape(r">0|[1-9]\d*)")
_DOT = re.escape(r"\.")
_PRERELEASE = r"(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
_TAG = "[0-9a-zA-Z-]+"
_OPEN = re.escape("(?:")
_CLOSE = re.escape(")")
_START, _END = re.escape("^"), re.escape("$")
_CORE_TOKENS = (
    (_START, _DECIMAL, _DOT, _DECIMAL, _DOT, _DECIMAL, _END),
    (
        _START,
        _DECIMAL,
        _OPEN,
        _DOT,
        _DECIMAL,
        _OPEN,
        _DOT,
        _DECIMAL,
        _CLOSE,
        _CLOSE,
        re.escape("(?:-(?P<") + _NAME + re.escape(">"),
        re.escape(_PRERELEASE),
        re.escape(f"(?:\\.{_PRERELEASE})*"),
        re.escape("))?"),
        re.escape(r"(?:\+(?P<") + _NAME + re.escape(">"),
        re.escape(_TAG),
        re.escape(f"(?:\\.{_TAG})*"),
        re.escape("))?"),
        _END,
    ),
)
_VERBOSE_GAP = r"[ \t\n\r\v\f]*"
_CORE_PATTERNS = {
    False: tuple(re.compile("".join(tokens)) for tokens in _CORE_TOKENS),
    True: tuple(re.compile(_VERBOSE_GAP.join(("", *tokens, ""))) for tokens in _CORE_TOKENS),
}
_CORE_TEXT = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
_TEMPLATE_KEY = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def callback_site(fn: ast.FunctionDef) -> tuple[ast.Call, str, str, str] | None:
    match body(fn):
        case [
            ast.With(
                items=[
                    ast.withitem(
                        context_expr=ast.Name(id=context), optional_vars=ast.Name(id=expected)
                    )
                ],
                body=[
                    ast.Assign(
                        targets=[ast.Name(id=result)],
                        value=ast.Call(
                            func=ast.Name(id=callback), args=[ast.Name(id=args)], keywords=[]
                        ) as call,
                    ),
                    ast.Assert(
                        test=ast.Compare(
                            left=ast.Name(id=read),
                            ops=[ast.Eq()],
                            comparators=[ast.Name(id=want)],
                        ),
                        msg=None,
                    ),
                ],
            )
        ] if (read, want) == (result, expected) and len(
            {callback, args, context, result, expected}
        ) == 5:
            if {callback, args, context} == {arg.arg for arg in parameters(fn)}:
                return call, callback, args, context
    return None


class CallbackProof(HelperProof):
    def source_shadows(self, name: str) -> bool:
        return any(m == name or m.startswith(name + ".") for m in self.resolver.modules)

    def forwarding(self, fn: Function, depth: int, *, strict: bool = False) -> None:
        if (
            strict
            and fn.wrapper
            and any(
                isinstance(node, ast.Return | ast.Raise)
                for stmt in body(fn.wrapper.node)[:-1]
                for node in ast.walk(stmt)
            )
        ):
            raise Unproved
        super().forwarding(fn, depth, strict=strict)

    def imported(self, qualified: str) -> Value:
        root, _, member = qualified.partition(".")
        if root in STDLIB | {"contextlib", "pytest"}:
            if self.source_shadows(root) or member in self.writes:
                raise Unproved
        if qualified == "contextlib.contextmanager":
            return qualified
        return super().imported(qualified)

    def initialize(
        self,
        stmts: list[ast.stmt],
        path: str,
        env: dict[str, Value],
        *,
        prefix: str,
        outer: dict[str, Value] | None = None,
    ) -> None:
        # Audit eager declarations in import order. Production classes and
        # forwarding wrappers still use the existing module initializer.
        if outer is not None:
            super().initialize(stmts, path, env, prefix=prefix, outer=outer)
            return
        for stmt in stmts:
            self.tick()
            if self.extra_declaration(stmt, path, env, prefix):
                continue
            super().initialize([stmt], path, env, prefix=prefix, outer=outer)

    def extra_declaration(
        self, stmt: ast.stmt, path: str, env: dict[str, Value], prefix: str
    ) -> bool:
        match stmt:
            # The package imports a guarded CLI entry module by its module name.
            case ast.If(
                test=ast.Compare(
                    left=ast.Name(id="__name__"),
                    ops=[ast.Eq()],
                    comparators=[ast.Constant(value="__main__")],
                ),
                orelse=[],
            ):
                if self.paths[path] != "__main__" and "__name__" not in env:
                    return True
            case ast.Import(names=[ast.alias(name="os.path", asname=None)]):
                if not self.source_shadows("os"):
                    self.define(env, "os", "module:os")
                    return True
            case ast.ImportFrom(
                module="unittest.mock", names=[ast.alias(name="patch", asname=alias)], level=0
            ) if not self.source_shadows("unittest"):
                # The import is safe. Leave mock operations opaque to this proof.
                name = alias or "patch"
                if name not in env:
                    env[name] = UNBOUND
                    return True
            case ast.FunctionDef() as fn if not fn.name.startswith("__"):
                if len(fn.decorator_list) != 1 or not self.literal_parameters:
                    return False
                decorator = fn.decorator_list[0]
                if (
                    isinstance(decorator, ast.Name)
                    and env.get(decorator.id) == "contextlib.contextmanager"
                ):
                    self.header(fn, env)
                    args = fn.args
                    params = parameters(fn)
                    if (
                        len(params) != 1
                        or args.defaults
                        or args.kwonlyargs
                        or args.vararg
                        or args.kwarg
                    ):
                        raise Unproved
                    arg = params[0].arg
                    match body(fn):
                        case [ast.Expr(value=ast.Yield(value=ast.Name(id=value)))] if (
                            arg == value
                            and not self.writes & {"__enter__", "__exit__", "contextmanager"}
                        ):
                            self.define(
                                env, fn.name, Function(prefix + fn.name, fn, mode="contextmanager")
                            )
                            return True
                    raise Unproved
                shape = inline_decorator(fn)
                if (
                    shape is not None
                    and env.get("pytest") == "pytest"
                    and not self.source_shadows("pytest")
                ):
                    self.header(fn, env)
                    for expr in shape[0].args:
                        self.table_value(expr, env)
                    self.define(env, fn.name, Function(prefix + fn.name, fn, mode="pytest"))
                    return True
        return False

    def table_value(self, expr: ast.expr, env: dict[str, Value], depth: int = 0) -> None:
        """Audit eager setup even for rows that supply no comparison proof."""
        self.tick()
        if depth >= 12:
            raise Unproved
        match expr:
            case ast.Constant():
                literal(expr)
            case ast.List(elts=items) | ast.Tuple(elts=items):
                for item in items:
                    self.table_value(item, env, depth + 1)
            case ast.Name(id=name) if isinstance(env.get(name), Function):
                return
            case ast.Call(args=[], keywords=keywords) if keywords:
                self.namespace_fields(expr, env)
            case ast.Call(func=func, args=[argument], keywords=[]):
                if dotted(func) == "pytest.raises":
                    if (
                        env.get("pytest") != "pytest"
                        or self.writes & {"raises", "ValueError"}
                        or self.expression(argument, env) != "builtin:ValueError"
                    ):
                        raise Unproved
                else:
                    self.context_entry(expr, env)
            case _:
                raise Unproved

    def namespace_fields(self, expr: ast.expr, env: dict[str, Value]) -> dict[str, Scalar]:
        if (
            not isinstance(expr, ast.Call)
            or expr.args
            or "Namespace" in self.writes
            or self.expression(expr.func, env) != "argparse.Namespace"
        ):
            raise Unproved
        fields = literal_keywords(expr)
        if any(key.startswith("__") for key in fields):
            raise Unproved
        return fields

    def context_entry(self, expr: ast.expr, env: dict[str, Value]) -> Function:
        match expr:
            case ast.Call(func=ast.Name(id=name), args=[argument], keywords=[]):
                fn = env.get(name)
                if isinstance(fn, Function) and fn.mode == "contextmanager":
                    literal(argument)
                    return fn
        raise Unproved

    def captured_pattern(self, owner: Class, member: str) -> tuple[str, bool]:
        path, name = owner.sid.split("::")
        cls = self.resolver.binding(path, name)
        if not isinstance(cls, ast.ClassDef):
            raise Unproved
        # Only declarations preceding compilation can supply the template.
        declarations: dict[str, ast.expr | None] = {}
        compiled = None
        for stmt in cls.body:
            value: ast.expr | None
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target, value = stmt.targets[0], stmt.value
            elif isinstance(stmt, ast.AnnAssign):
                target, value = stmt.target, stmt.value
            else:
                continue
            if isinstance(target, ast.Name):
                if target.id == member:
                    compiled = value
                    break
                declarations[target.id] = value
        env = self.module(path)
        if (
            not isinstance(compiled, ast.Call)
            or compiled.keywords
            or not 1 <= len(compiled.args) <= 2
            or (dotted(compiled.func) or "").split(".")[0] in owner.members
            or self.expression(compiled.func, env) != "re.compile"
            or member in self.writes
        ):
            raise Unproved
        value = compiled.args[0]
        if isinstance(value, ast.Call):
            match value.func:
                case ast.Attribute(value=ast.Name(id=template), attr="format") if not value.args:
                    constant = declarations.get(template)
                    if not isinstance(constant, ast.Constant) or not isinstance(
                        text := constant.value, str
                    ):
                        raise Unproved
                    if len(text) > 2048 or template in self.writes:
                        raise Unproved
                    keys = literal_keywords(value)
                    if keys.keys() != set(_TEMPLATE_KEY.findall(text)) or any(
                        fill != "" for fill in keys.values()
                    ):
                        raise Unproved
                    value = ast.Constant(value=_TEMPLATE_KEY.sub("", text))
                case _:
                    raise Unproved
        text = literal(value)
        if not isinstance(text, str) or len(text) > 2048:
            raise Unproved
        if len(compiled.args) == 2:
            flags = compiled.args[1]
            if (dotted(flags) or "").split(".")[0] in owner.members or self.expression(
                flags, env
            ) != "re.VERBOSE":
                raise Unproved
        return text, len(compiled.args) == 2

    def parse_fields(self, owner: Class, factory: Function, text: str) -> Operand:
        if factory.mode != "builtin:classmethod" or factory.wrapper or has_yield(factory.node):
            raise Unproved
        args = factory.node.args
        names = [arg.arg for arg in parameters(factory.node)]
        if (
            len(names) not in (2, 3)
            or len(set(names)) != len(names)
            or args.kwonlyargs
            or args.vararg
            or args.kwarg
        ):
            raise Unproved
        cls, source, *option = names
        stmts = body(factory.node)
        env = self.function_env(factory)
        if stmts and isinstance(stmts[0], ast.If):
            check = stmts[0]
            if not isinstance(check.test, ast.UnaryOp):
                alias = check.orelse
                if len(alias) != 1 or not isinstance(alias[0], ast.If):
                    raise Unproved
                reject = alias[0]
                # The first arm decodes bytes. It is unreachable for an exact str.
                if self.isinstance_accepts(check.test, source, "builtin:str", factory, env):
                    raise Unproved
                if not self.isinstance_accepts(check.test, source, "builtin:bytes", factory, env):
                    raise Unproved
            else:
                reject = check
            if not (
                isinstance(reject.test, ast.UnaryOp)
                and isinstance(reject.test.op, ast.Not)
                and not reject.orelse
                and len(reject.body) == 1
                and isinstance(reject.body[0], ast.Raise)
                and self.isinstance_accepts(
                    reject.test.operand, source, "builtin:str", factory, env
                )
            ):
                raise Unproved
            stmts = stmts[1:]
        if option:
            if (
                len(args.defaults) != 1
                or not isinstance(args.defaults[0], ast.Constant)
                or args.defaults[0].value is not False
                or not stmts
                or not isinstance(choice := stmts[0], ast.If)
                or not identifier(choice.test, option[0])
                or len(choice.orelse) != 1
            ):
                raise Unproved
            stmts = choice.orelse + stmts[1:]
        elif args.defaults:
            raise Unproved
        if len(stmts) < 3:
            raise Unproved
        match_name, call = assigned(stmts[0])
        match call:
            case ast.Call(
                func=ast.Attribute(value=pattern, attr="match"),
                args=[ast.Name(id=actual)],
                keywords=[],
            ) if actual == source and match_name not in names:
                member = attribute(pattern, cls)
            case _:
                raise Unproved
        match stmts[1]:
            case ast.If(
                test=ast.Compare(
                    left=ast.Name(id=checked),
                    ops=[ast.Is()],
                    comparators=[ast.Constant(value=None)],
                ),
                body=[ast.Raise()],
                orelse=[],
            ) if checked == match_name:
                pass
            case _:
                raise Unproved
        ast_pattern, verbose = self.captured_pattern(owner, member)
        values = _CORE_TEXT.fullmatch(text) if len(text) <= 64 else None
        if values is None:
            raise Unproved
        for grammar in _CORE_PATTERNS[verbose]:
            if found := grammar.fullmatch(ast_pattern):
                break
        else:
            raise Unproved
        keys = found.groups()
        if len(keys) != len(set(keys)):
            raise Unproved
        captures = dict(zip(keys, [*values.groups(), *([None] * (len(keys) - 3))], strict=True))
        unpack = self.group_dictionary(stmts[2:], cls, match_name, captures, names)
        return self.construct_operand(owner, [], unpack)

    @staticmethod
    def group_dictionary(
        stmts: list[ast.stmt],
        cls: str,
        match_name: str,
        captures: dict[str, Scalar],
        parameters: list[str],
    ) -> dict[str, Scalar]:
        if not stmts:
            raise Unproved
        if isinstance(stmts[0], ast.Return) and len(stmts) == 1:
            call_to(return_expansion(stmts[0], cls), match_name + ".groupdict", 0)
            return captures
        group_value: ast.expr | None
        if isinstance(stmts[0], ast.AnnAssign) and isinstance(stmts[0].target, ast.Name):
            group = stmts[0].target.id
            group_value = stmts[0].value
        else:
            group, group_value = assigned(stmts[0])
        if group_value is None or group in [match_name, *parameters]:
            raise Unproved
        call_to(group_value, match_name + ".groupdict", 0)
        if not isinstance(stmts[-1], ast.Return) or not identifier(
            return_expansion(stmts[-1], cls), group
        ):
            raise Unproved
        for statement in stmts[1:-1]:
            match statement:
                case ast.If(
                    test=ast.UnaryOp(
                        op=ast.Not(),
                        operand=ast.Subscript(
                            value=ast.Name(id=read), slice=ast.Constant(value=key)
                        ),
                    ),
                    body=[
                        ast.Assign(
                            targets=[
                                ast.Subscript(
                                    value=ast.Name(id=write), slice=ast.Constant(value=destination)
                                )
                            ],
                            value=ast.Constant(value=value),
                        )
                    ],
                    orelse=[],
                ) if read == write == group and key == destination and key in list(captures)[:3]:
                    # Core groups always capture a nonempty string on supported inputs.
                    literal(ast.Constant(value=value))
                case _:
                    raise Unproved
        return captures

    def run_callback(
        self, callback: Function, fields: dict[str, Scalar]
    ) -> tuple[Function, Function, ast.Call, ast.Call, ast.Call]:
        if callback.mode:
            raise Unproved
        if callback.wrapper:
            self.forwarding(callback, 0, strict=True)
        (arg,) = positional(callback.node, 1)
        match body(callback.node):
            case [
                ast.Assign(targets=[ast.Name(id=left)], value=ast.Call() as parse),
                ast.Return(
                    value=ast.Call(
                        func=ast.Name(id="str"), args=[ast.Call() as compare], keywords=[]
                    )
                ),
            ] if left != arg:
                pass
            case _:
                raise Unproved
        env = self.function_env(callback)
        if "str" in env or "str" in self.writes or not isinstance(parse.func, ast.Attribute):
            raise Unproved
        owner = self.expression(parse.func.value, env)
        method = parse.func.attr
        if not isinstance(owner, Class) or not isinstance(
            factory := owner.members.get(method), Function
        ):
            raise Unproved
        (lhs_arg,) = call_to(parse, dotted(parse.func) or "", 1)
        method = attribute(compare.func, left)
        (rhs_arg,) = call_to(compare, f"{left}.{method}", 1)
        lhs = fields.get(attribute(lhs_arg, arg))
        rhs = fields.get(attribute(rhs_arg, arg))
        if not isinstance(lhs, str) or not isinstance(rhs, str):
            raise Unproved
        left_instance = self.parse_fields(owner, factory, lhs)
        right_instance = self.parse_fields(owner, factory, rhs)
        compare_method = instance_method(owner, method)
        target, invocation, conversion = self.helper_call(
            compare_method, left_instance, ParsedOperand(right_instance, factory)
        )
        if conversion is None:
            raise Unproved
        return target, compare_method, compare, conversion, invocation


def return_expansion(stmt: ast.Return, cls: str) -> ast.expr:
    match stmt.value:
        case ast.Call(
            func=ast.Name(id=target), args=[], keywords=[ast.keyword(arg=None, value=value)]
        ) if target == cls:
            return value
    raise Unproved


def pytest_setup_is_supported(proof: CallbackProof, path: str) -> bool:
    setup_paths = [path, *(str(parent / "conftest.py") for parent in PurePosixPath(path).parents)]
    for source in setup_paths:
        if source in proof.unparseable:
            return False
        scope = proof.resolver.scopes.get(source)
        if scope and (
            scope.wildcard
            or any(
                name.startswith(("pytest_", "setup_", "teardown_")) or name == "pytestmark"
                for name in scope.counts.keys() | scope.blocked
            )
        ):
            return False
    return True


def add_namespace_callback_edges(index: "Index") -> set[tuple[str, str]]:
    resolver = index.partials
    if resolver is None:
        return set()
    candidates = [
        (sid, fn, candidate, table)
        for sid, fn in index.syntax.items()
        if index.nodes[sid].kind == "test"
        and "." not in index.nodes[sid].name
        and isinstance(fn, ast.FunctionDef)
        and (candidate := callback_site(fn)) is not None
        and (table := literal_table(fn)) is not None
    ]
    if not candidates:
        return set()
    try:
        writes = namespace_writes(resolver)
    except Unproved:
        return set()
    proof = CallbackProof(
        resolver,
        {path for path, source in index.sources.items() if source.parse_status == "unparseable"},
        scalar_factories=True,
        literal_parameters=True,
        strict_callable_values=True,
        literal_keyword_dicts=True,
    )
    proof.writes = writes
    edges = set()
    for sid, fn, (site, callback, arguments, context), (names, rows) in candidates:
        path = index.nodes[sid].path
        if path not in proof.paths or not pytest_setup_is_supported(proof, path):
            continue
        shape = inline_decorator(fn)
        assert shape is not None
        try:
            env = proof.module(path)
            test = env.get(fn.name)
            if not isinstance(test, Function) or not proof.pytest_parameterization(test):
                continue
        except (Unproved, RecursionError):
            continue
        for row, row_node in zip(rows, shape[1].elts, strict=True):
            try:
                cells = dict(zip(names, row, strict=True))
                callee = proof.expression(cells[callback], env)
                if not isinstance(callee, Function) or callee.sid not in index.nodes:
                    continue
                fields = proof.namespace_fields(cells[arguments], env)
                manager = proof.context_entry(cells[context], env)
                target, method, compare, convert, invocation = proof.run_callback(callee, fields)
                if target.sid not in index.nodes or target.sid == sid:
                    continue
            except (Unproved, RecursionError):
                continue
            via = ""
            if callee.wrapper:
                line = body(callee.wrapper.node)[-1].lineno
                via = f" via {callee.wrapper.sid} at line {line}"
            method_name = method.sid.split("::")[1]
            index.add_edge(
                sid,
                target.sid,
                "call",
                f"{path}:{site.lineno} calls {callee.sid}{via} from the pytest row at line "
                f"{row_node.lineno} after {manager.sid} yields on entry. "
                f"The command calls {method_name} at line "
                f"{compare.lineno}, converts the second string at line {convert.lineno}, and "
                f"reaches {target.sid.split('::')[1]} through {method_name} at line "
                f"{invocation.lineno} after equal "
                "normalized core fields bypass the early return.",
                SourceLocation(
                    path=path, line=site.lineno, end_line=site.end_lineno or site.lineno
                ),
            )
            edges.add((sid, target.sid))
    return edges
