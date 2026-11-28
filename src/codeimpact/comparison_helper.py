"""Prove a test-scoped comparison call past an equal-core guard."""

import ast
from dataclasses import dataclass
from typing import TYPE_CHECKING

from codeimpact.equality import (
    COMPARISON_METHODS,
    TYPE,
    UNBOUND,
    Class,
    Function,
    Instance,
    Proof,
    Unproved,
    Value,
    body,
    comparison_site,
    comparison_target,
    has_yield,
    identifier,
    instance_method,
    namespace_writes,
    parameters,
)
from codeimpact.models import SourceLocation
from codeimpact.partial_bindings import audit, dotted

if TYPE_CHECKING:
    from codeimpact.analyzer import Index


Scalar = str | int | None
OPERATORS = (ast.Lt, ast.NotEq)
BUILTIN_PARAMETER_TYPES = {
    f"builtin:{name}" for name in ("dict", "tuple", "list", "str", "bytes", "int")
}


@dataclass
class Operand:
    instance: Instance
    arguments: dict[str, Scalar]


@dataclass(frozen=True)
class DictionaryOperand:
    keywords: dict[str, Scalar]


@dataclass(frozen=True)
class ParsedOperand:
    value: Operand
    factory: Function


def literal(node: ast.expr) -> Scalar:
    if isinstance(node, ast.Constant):
        value = node.value
        if value is None or isinstance(value, (str, int)) and not isinstance(value, bool):
            return value
    raise Unproved


def positional(fn: ast.FunctionDef, count: int) -> list[str]:
    args = fn.args
    names = [arg.arg for arg in parameters(fn)]
    if (
        len(names) != count
        or len(set(names)) != count
        or args.defaults
        or args.kwonlyargs
        or args.vararg
        or args.kwarg
        or has_yield(fn)
    ):
        raise Unproved
    return names


def assigned(stmt: ast.stmt) -> tuple[str, ast.expr]:
    match stmt:
        case ast.Assign(targets=[ast.Name(id=name)], value=value):
            return name, value
    raise Unproved


def one_return(fn: ast.FunctionDef) -> ast.expr:
    match body(fn):
        case [ast.Return(value=value)] if value is not None:
            return value
    raise Unproved


def call_to(node: ast.AST, name: str, arity: int) -> list[ast.expr]:
    if isinstance(node, ast.Call) and dotted(node.func) == name and not node.keywords:
        if len(node.args) == arity and not any(isinstance(arg, ast.Starred) for arg in node.args):
            return node.args
    raise Unproved


def attribute(node: ast.AST, receiver: str) -> str:
    if isinstance(node, ast.Attribute) and identifier(node.value, receiver):
        return node.attr
    raise Unproved


def literal_keywords(call: ast.Call) -> dict[str, Scalar]:
    keywords: dict[str, Scalar] = {}
    for item in call.keywords:
        if item.arg is None or item.arg in keywords:
            raise Unproved
        keywords[item.arg] = literal(item.value)
    return keywords


def bind_constructor(
    init: ast.FunctionDef, arguments: list[Scalar], keywords: dict[str, Scalar]
) -> dict[str, Scalar]:
    args = init.args
    positional_args = parameters(init)
    names = [p.arg for p in positional_args]
    if (
        not names
        or len(names) != len(set(names))
        or args.kwonlyargs
        or args.vararg
        or args.kwarg
        or len(arguments) >= len(names)
    ):
        raise Unproved
    bound = dict(zip(names[1:], arguments, strict=False))
    allowed = {p.arg for p in args.args} - {names[0]}
    if keywords.keys() - allowed or keywords.keys() & bound.keys():
        raise Unproved
    bound.update(keywords)
    first_default = len(names) - len(args.defaults)
    for i, name in enumerate(names[1:], start=1):
        if name in bound:
            continue
        if i < first_default:
            raise Unproved
        bound[name] = literal(args.defaults[i - first_default])
    return bound


def integer(value: Scalar) -> int:
    if type(value) is int:
        return value
    if (
        isinstance(value, str)
        and 0 < len(value) <= 64
        and value.isascii()
        and value.removeprefix("+").isdigit()
    ):
        return int(value)
    raise Unproved


def field_value(
    node: ast.expr,
    arguments: dict[str, Scalar],
    local_dict: tuple[str, dict[str, int]] | None,
    env: dict[str, Value],
) -> Scalar:
    match node:
        case ast.IfExp(
            test=ast.Compare(
                left=ast.Name(id=name), ops=[ast.Is()], comparators=[ast.Constant(value=None)]
            ),
            body=ast.Constant(value=None),
            orelse=ast.Call() as convert,
        ) if name in arguments:
            (argument,) = call_to(convert, "str", 1)
            if not identifier(argument, name) or "str" in env:
                raise Unproved
            return (
                None
                if arguments[name] is None
                else field_value(convert, arguments, local_dict, env)
            )
    if isinstance(node, ast.Subscript) and local_dict and identifier(node.value, local_dict[0]):
        key = literal(node.slice)
        if isinstance(key, str) and key in local_dict[1]:
            return local_dict[1][key]
        raise Unproved
    if isinstance(node, ast.Call):
        builtin = dotted(node.func)
        if builtin not in ("int", "str") or builtin in env:
            raise Unproved
        (node,) = call_to(node, builtin, 1)
        value = (
            arguments[node.id]
            if isinstance(node, ast.Name) and node.id in arguments
            else literal(node)
        )
        if builtin == "int":
            return integer(value)
        if type(value) is int and value.bit_length() > 256:
            raise Unproved
        return str(value)
    return (
        arguments[node.id] if isinstance(node, ast.Name) and node.id in arguments else literal(node)
    )


def guarded_dictionary_loop(
    stmt: ast.For, local_dict: tuple[str, dict[str, int]], env: dict[str, Value]
) -> set[str]:
    if "ValueError" in env or any(value < 0 for value in local_dict[1].values()):
        raise Unproved
    call_to(stmt.iter, f"{local_dict[0]}.items", 0)
    match stmt:
        case ast.For(
            target=ast.Tuple(elts=[ast.Name(id=key), ast.Name(id=value)]),
            body=[
                ast.If(
                    test=ast.Compare(
                        left=ast.Name(id=checked),
                        ops=[ast.Lt()],
                        comparators=[ast.Constant(value=0)],
                    ),
                    body=[ast.Raise(exc=ast.Call() as error, cause=None)],
                    orelse=[],
                )
            ],
            orelse=[],
        ) if value == checked and key != value:
            call_to(error, "ValueError", 1)
            return {key, value}
    raise Unproved


class HelperProof(Proof):
    def function_env(self, fn: Function) -> dict[str, Value]:
        scoped = audit(body(fn.node), local=True)
        if scoped.wildcard:
            raise Unproved
        names = scoped.counts.keys() | {arg.arg for arg in parameters(fn.node)}
        return self.module(fn.sid.split("::")[0]) | dict.fromkeys(names, UNBOUND)

    def operand(
        self,
        expr: ast.expr,
        env: dict[str, Value],
        operands: dict[str, Operand | DictionaryOperand],
        *,
        allow_dictionary: bool,
    ) -> Operand | DictionaryOperand:
        self.tick()
        if isinstance(expr, ast.Name) and expr.id in operands:
            return operands[expr.id]
        if not isinstance(expr, ast.Call) or not dotted(expr.func):
            raise Unproved
        if (
            allow_dictionary
            and identifier(expr.func, "dict")
            and "dict" not in env
            and "dict" not in self.writes
        ):
            if expr.args:
                raise Unproved
            return DictionaryOperand(literal_keywords(expr))
        owner = self.expression(expr.func, env)
        if not isinstance(owner, Class):
            raise Unproved
        return self.construct_operand(
            owner, [literal(arg) for arg in expr.args], literal_keywords(expr)
        )

    def construct_operand(
        self, owner: Class, arguments: list[Scalar], keywords: dict[str, Scalar]
    ) -> Operand:
        init = instance_method(owner, "__init__")
        bound = bind_constructor(init.node, arguments, keywords)
        return Operand(self.constructor(owner, 0), bound)

    def core(self, operand: Operand, fields: list[str]) -> tuple[int, ...]:
        init = instance_method(operand.instance.owner, "__init__")
        env = self.function_env(init)
        if {"int", "str", "ValueError"} & self.writes:
            raise Unproved
        statements = body(init.node)
        receiver = parameters(init.node)[0].arg
        local_dict = None
        arguments = operand.arguments
        if statements and isinstance(statements[0], ast.Assign):
            first = statements[0]
            if isinstance(first.value, ast.Dict):
                name, _ = assigned(first)
                if name in arguments or name == receiver:
                    raise Unproved
                values: dict[str, int] = {}
                for key, value in zip(first.value.keys, first.value.values, strict=True):
                    if (
                        not isinstance(key, ast.Constant)
                        or type(key.value) is not str
                        or key.value in values
                    ):
                        raise Unproved
                    normalized = field_value(value, arguments, None, env)
                    if type(normalized) is not int:
                        raise Unproved
                    values[key.value] = normalized
                local_dict = (name, values)
                statements = statements[1:]
                if statements and isinstance(statements[0], ast.For):
                    loop_names = guarded_dictionary_loop(statements[0], local_dict, env)
                    if loop_names & (arguments.keys() | {name, receiver}):
                        raise Unproved
                    statements = statements[1:]
        stored = {}
        for stmt in statements:
            match stmt:
                case ast.Assign(
                    targets=[ast.Attribute(value=ast.Name(id=base), attr=name)], value=value
                ) if base == receiver and name not in stored:
                    stored[name] = field_value(value, arguments, local_dict, env)
                case _:
                    raise Unproved
        result = []
        for field in fields:
            backing_field = self.read_field(operand.instance, field)
            normalized = stored.get(backing_field)
            if type(normalized) is not int:
                raise Unproved
            result.append(normalized)
        return tuple(result)

    def builtin_union(self, name: str, path: str, env: dict[str, Value]) -> set[str]:
        if env.get(name) != TYPE or "__args__" in self.writes:
            raise Unproved
        binding = self.resolver.binding(path, name)
        if isinstance(binding, ast.ImportFrom):
            aliases, _ = self.resolver.decode(binding, path, self.resolver.modules)
            qualified = dict(aliases).get(name, "")
            module, _, name = qualified.rpartition(".")
            if module not in self.resolver.modules:
                raise Unproved
            path = self.resolver.modules[module]
            binding = self.resolver.binding(path, name)
        if not (
            isinstance(binding, ast.Assign)
            and isinstance(binding.value, ast.Subscript)
            and isinstance(binding.value.slice, ast.Tuple)
        ):
            raise Unproved
        alias_env = self.module(path)
        if self.expression(binding.value.value, alias_env) != "typing.Union":
            raise Unproved
        if not binding.value.slice.elts:
            raise Unproved
        types = set()
        for child in binding.value.slice.elts:
            value = self.expression(child, alias_env)
            if not isinstance(value, str) or value not in BUILTIN_PARAMETER_TYPES:
                raise Unproved
            types.add(value)
        return types

    def accepts_type(
        self, expr: ast.expr, operand_type: Class | str, fn: Function, env: dict[str, Value]
    ) -> bool:
        if isinstance(expr, ast.Tuple):
            return any([self.accepts_type(item, operand_type, fn, env) for item in expr.elts])
        if isinstance(expr, ast.Starred):
            expr = expr.value
            if not isinstance(expr, ast.Attribute) or expr.attr != "__args__":
                raise Unproved
        if (
            isinstance(expr, ast.Attribute)
            and expr.attr == "__args__"
            and isinstance(expr.value, ast.Name)
        ):
            types = self.builtin_union(expr.value.id, fn.sid.split("::")[0], env)
            return isinstance(operand_type, str) and operand_type in types
        value = self.expression(expr, env)
        if isinstance(value, Class):
            return value is operand_type
        if isinstance(value, str) and value in BUILTIN_PARAMETER_TYPES:
            return value == operand_type
        raise Unproved

    def isinstance_accepts(
        self,
        check: ast.expr,
        argument: str,
        operand_type: Class | str,
        fn: Function,
        env: dict[str, Value],
    ) -> bool:
        if "isinstance" in env or "isinstance" in self.writes:
            raise Unproved
        actual, types = call_to(check, "isinstance", 2)
        if not identifier(actual, argument):
            raise Unproved
        return self.accepts_type(types, operand_type, fn, env)

    def wrapper_forwards(self, operator: Function, operand_type: Class | str) -> ast.Call:
        wrapper = operator.wrapper
        if wrapper is None:
            raise Unproved
        path, factory_name = wrapper.sid.rsplit(".", 1)[0].split("::")
        factory = self.module(path).get(factory_name)
        if not isinstance(factory, Function) or len(body(factory.node)) != 2:
            raise Unproved
        (captured,) = positional(factory.node, 1)
        receiver, rhs = positional(wrapper.node, 2)
        env = self.function_env(wrapper)
        if captured == wrapper.node.name or env.get(captured) == UNBOUND:
            raise Unproved
        env[captured] = UNBOUND
        statements = body(wrapper.node)
        if not statements or not isinstance(statements[-1], ast.Return):
            raise Unproved
        forwarding = statements[-1].value
        if not isinstance(forwarding, ast.Call):
            raise Unproved
        args = call_to(forwarding, captured, 2)
        if not identifier(args[0], receiver) or not identifier(args[1], rhs):
            raise Unproved
        if len(statements) == 1:
            return forwarding
        if len(statements) not in (2, 3):
            raise Unproved
        match statements[-2]:
            case ast.If(
                test=ast.UnaryOp(op=ast.Not(), operand=condition),
                body=[ast.Return(value=ast.Name(id="NotImplemented"))],
                orelse=[],
            ):
                pass
            case _:
                raise Unproved
        if len(statements) == 3:
            name, types = assigned(statements[0])
            if name in {captured, receiver, rhs, "isinstance", "NotImplemented"} or not isinstance(
                types, ast.Tuple
            ):
                raise Unproved
            if "isinstance" in env or "isinstance" in self.writes:
                raise Unproved
            actual, declared = call_to(condition, "isinstance", 2)
            accepted = (
                identifier(actual, rhs)
                and identifier(declared, name)
                and self.accepts_type(types, operand_type, wrapper, env)
            )
        else:
            accepted = self.isinstance_accepts(condition, rhs, operand_type, wrapper, env)
        if not accepted:
            raise Unproved
        return forwarding

    def after_conversions(
        self,
        fn: Function,
        receiver: str,
        other: str,
        owner: Class,
        right: Operand | DictionaryOperand | ParsedOperand,
        env: dict[str, Value],
    ) -> tuple[list[ast.stmt], Operand, ast.Call | None]:
        statements = body(fn.node)
        if not statements or not isinstance(statements[0], ast.Assign):
            raise Unproved
        if not isinstance(statements[0].value, ast.Call) or not identifier(
            statements[0].value.func, "type"
        ):
            if not isinstance(right, Operand):
                raise Unproved
            return statements, right, None
        name, value = assigned(statements[0])
        (argument,) = call_to(value, "type", 1)
        if (
            not identifier(argument, receiver)
            or name in {receiver, other, "type", "isinstance"}
            or "type" in env
            or "type" in self.writes
            or len(statements) < 2
            or not isinstance(statements[1], ast.If)
        ):
            raise Unproved
        env[name] = owner
        branch = statements[1]
        operand_type = (
            owner
            if isinstance(right, Operand)
            else ("builtin:dict" if isinstance(right, DictionaryOperand) else "builtin:str")
        )
        for _ in range(8):
            negated = isinstance(branch.test, ast.UnaryOp) and isinstance(branch.test.op, ast.Not)
            condition = (
                branch.test.operand
                if isinstance(branch.test, ast.UnaryOp) and negated
                else branch.test
            )
            if self.isinstance_accepts(condition, other, operand_type, fn, env) != negated:
                if isinstance(right, DictionaryOperand) and not negated:
                    match branch.body:
                        case [
                            ast.Assign(
                                targets=[ast.Name(id=target)],
                                value=ast.Call(
                                    func=ast.Name(id=constructor),
                                    args=[],
                                    keywords=[ast.keyword(arg=None, value=ast.Name(id=source))],
                                ) as conversion,
                            )
                        ] if target == source == other and constructor == name:
                            return (
                                statements[2:],
                                self.construct_operand(owner, [], right.keywords),
                                conversion,
                            )
                if isinstance(right, ParsedOperand) and not negated and len(branch.body) == 1:
                    target, expr = assigned(branch.body[0])
                    if target == other and isinstance(expr, ast.Call):
                        method = attribute(expr.func, name)
                        (argument,) = call_to(expr, f"{name}.{method}", 1)
                        if (
                            identifier(argument, other)
                            and owner.members.get(method) is right.factory
                        ):
                            return statements[2:], right.value, expr
                raise Unproved
            if not branch.orelse:
                if not isinstance(right, Operand):
                    raise Unproved
                return statements[2:], right, None
            if len(branch.orelse) != 1 or not isinstance(branch.orelse[0], ast.If):
                raise Unproved
            branch = branch.orelse[0]
        raise Unproved

    def tuple_projection(self, expr: ast.expr, arg: str, instance: Instance) -> list[str]:
        match expr:
            case ast.Subscript(
                value=ast.Call(func=func, args=[], keywords=[]),
                slice=ast.Slice(lower=None, upper=ast.Constant(value=int() as width), step=None),
            ) if type(width) is int and width > 0:
                reader = instance_method(instance.owner, attribute(func, arg))
                (receiver,) = positional(reader.node, 1)
                result = one_return(reader.node)
                if isinstance(result, ast.Tuple) and width <= len(result.elts):
                    attributes = [attribute(item, receiver) for item in result.elts]
                    for field in attributes:
                        self.read_field(instance, field)
                    return attributes[:width]
        raise Unproved

    def compare_core(
        self, expression: ast.expr, left: str, right: str, env: dict[str, Value]
    ) -> None:
        if not isinstance(expression, ast.Call):
            raise Unproved
        name = dotted(expression.func)
        if name is None:
            raise Unproved
        args = call_to(expression, name, 2)
        if not identifier(args[0], left) or not identifier(args[1], right):
            raise Unproved
        function = self.expression(expression.func, env)
        if not isinstance(function, Function) or function.mode or function.wrapper:
            raise Unproved
        a, b = positional(function.node, 2)
        match one_return(function.node):
            case ast.BinOp(
                left=ast.Compare(left=ast.Name(id=p), ops=[ast.Gt()], comparators=[ast.Name(id=q)]),
                op=ast.Sub(),
                right=ast.Compare(
                    left=ast.Name(id=r), ops=[ast.Lt()], comparators=[ast.Name(id=s)]
                ),
            ) if (p, q, r, s) == (a, b, a, b):
                return
        raise Unproved

    def helper_call(
        self, fn: Function, left: Operand, right: Operand | DictionaryOperand | ParsedOperand
    ) -> tuple[Function, ast.Call, ast.Call | None]:
        receiver, other = positional(fn.node, 2)
        env = self.function_env(fn)
        owner = left.instance.owner
        statements, right_instance, conversion = self.after_conversions(
            fn, receiver, other, owner, right, env
        )
        if len(statements) < 5:
            raise Unproved
        a, first = assigned(statements[0])
        b, second = assigned(statements[1])
        guard, comparison = assigned(statements[2])
        if len({a, b, guard, receiver, other}) != 5:
            raise Unproved
        fields = self.tuple_projection(first, receiver, left.instance)
        if fields != self.tuple_projection(second, other, right_instance.instance):
            raise Unproved
        if self.core(left, fields) != self.core(right_instance, fields):
            raise Unproved
        self.compare_core(comparison, a, b, env)
        match statements[3:]:
            case [
                ast.If(
                    test=ast.Name(id=condition),
                    body=[ast.Return(value=ast.Name(id=early))],
                    orelse=[],
                ),
                ast.Assign(
                    targets=[ast.Tuple(elts=[ast.Name(id=x), ast.Name(id=y)])],
                    value=ast.Tuple(elts=[read_left, read_right]),
                ),
                (
                    ast.Assign(targets=[ast.Name()], value=ast.Call() as call)
                    | ast.Return(value=ast.Call() as call)
                ),
                *_,
            ] if condition == early == guard and len({x, y, receiver, other}) == 4:
                self.read_field(left.instance, attribute(read_left, receiver))
                self.read_field(right_instance.instance, attribute(read_right, other))
                name = attribute(call.func, receiver)
                args = call_to(call, f"{receiver}.{name}", 2)
                if not identifier(args[0], x) or not identifier(args[1], y):
                    raise Unproved
                helper = owner.members.get(name)
                if (
                    isinstance(helper, Function)
                    and helper.sid == f"{owner.sid}.{name}"
                    and helper.mode in ("", "builtin:classmethod")
                    and not helper.wrapper
                ):
                    positional(helper.node, 3)
                    return helper, call, conversion
        raise Unproved

    def trail(
        self, fn: ast.FunctionDef, path: str, position: int, site: ast.Compare, *, dictionary: bool
    ) -> tuple[Function, str]:
        scoped = audit(body(fn), local=True)
        if scoped.wildcard or has_yield(fn):
            raise Unproved
        env = self.module(path) | dict.fromkeys(scoped.counts, UNBOUND)
        operands: dict[str, Operand | DictionaryOperand] = {}
        for stmt in body(fn)[:position]:
            if not isinstance(stmt, ast.Pass):
                name, expr = assigned(stmt)
                operands[name] = self.operand(expr, env, operands, allow_dictionary=dictionary)
        left = self.operand(site.left, env, operands, allow_dictionary=False)
        right = self.operand(site.comparators[0], env, operands, allow_dictionary=dictionary)
        if not isinstance(left, Operand) or dictionary != isinstance(right, DictionaryOperand):
            raise Unproved
        owner = left.instance.owner
        if isinstance(right, Operand) and owner is not right.instance.owner:
            raise Unproved
        op, method = COMPARISON_METHODS[type(site.ops[0])]
        operator = owner.members.get(method)
        wrapper = comparison_target(owner, method)
        if not isinstance(operator, Function) or wrapper is None or operator.wrapper is not wrapper:
            raise Unproved
        forwarding = self.wrapper_forwards(operator, "builtin:dict" if dictionary else owner)
        receiver, other = positional(operator.node, 2)
        match one_return(operator.node):
            case ast.Compare(
                left=ast.Call() as call, ops=[operator_test], comparators=[ast.Constant(value=zero)]
            ) if type(operator_test) is type(site.ops[0]) and type(zero) is int and zero == 0:
                name = attribute(call.func, receiver)
                (argument,) = call_to(call, f"{receiver}.{name}", 1)
                if not identifier(argument, other):
                    raise Unproved
            case _:
                raise Unproved
        compare = instance_method(owner, name)
        helper, invocation, conversion = self.helper_call(compare, left, right)
        wrapper_name = wrapper.sid.split("::")[1]
        compare_name = compare.sid.split("::")[1]
        target_name = helper.sid.split("::")[1]
        route = (
            f"{op} reaches {target_name} via {wrapper_name} at line {forwarding.lineno}, "
            f"{method} at line {call.lineno}, and {compare_name} at line {invocation.lineno}"
        )
        if conversion is not None:
            route += f" following {ast.unparse(conversion)} at line {conversion.lineno}"
        return helper, route + " after equal normalized core fields bypass the early return"


def add_comparison_helper_edges(
    index: "Index", *, allow_dictionary: bool = False
) -> set[tuple[str, str]]:
    resolver = index.partials
    if resolver is None:
        return set()
    # Dictionary sites have a separate budget so they cannot displace existing proofs.
    edges = add_comparison_helper_edges(index) if allow_dictionary else set()
    operators = (ast.NotEq,) if allow_dictionary else OPERATORS
    candidates = []
    for sid, node in index.syntax.items():
        if index.nodes[sid].kind != "test" or "." in index.nodes[sid].name:
            continue
        if not isinstance(node, ast.FunctionDef):
            continue
        found = comparison_site(
            node,
            first=True,
            operators=operators,
            literal_parameters=False,
            allow_strings=False,
            allow_raises=False,
            allow_greater_raises=False,
        )
        if found is not None and isinstance(found[1].ops[0], operators):
            candidates.append((sid, node, found[0], found[1]))
    if not candidates:
        return edges
    try:
        writes = namespace_writes(resolver)
    except Unproved:
        return edges
    proof = HelperProof(
        resolver,
        {path for path, source in index.sources.items() if source.parse_status == "unparseable"},
        scalar_factories=True,
        literal_parameters=True,
        strict_callable_values=True,
        literal_keyword_dicts=True,
    )
    proof.writes = writes
    for sid, node, position, site in candidates:
        path = index.nodes[sid].path
        try:
            target, detail = proof.trail(node, path, position, site, dictionary=allow_dictionary)
        except (Unproved, RecursionError):
            continue
        if target.sid in index.nodes:
            index.add_edge(
                sid,
                target.sid,
                "call",
                f"{path}:{site.lineno} {detail}",
                SourceLocation(
                    path=path, line=site.lineno, end_line=site.end_lineno or site.lineno
                ),
            )
            edges.add((sid, target.sid))
    return edges
