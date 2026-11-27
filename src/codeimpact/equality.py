"""Resolve initial comparison calls for bounded, source-proved operand types."""

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from codeimpact.discovery import is_test_file
from codeimpact.models import SourceLocation
from codeimpact.parameter_rows import inline_decorator
from codeimpact.partial_bindings import audit, dotted
from codeimpact.pytest_fixtures import direct_pytest_import

if TYPE_CHECKING:
    from codeimpact.analyzer import Index
    from codeimpact.partial_bindings import PartialBindings


EqualityMode = (
    bool
    | Literal[
        "exact-class",
        "factories",
        "first-assertion",
        "less-than",
        "inequality",
        "dictionary",
        "parameterized",
        "string-parameter",
        "raises-less-than",
    ]
)
LiteralParameter = tuple[str, Literal["tuple", "list", "str"]]
MAX_PROOF_STEPS = 16_000
MAX_PARAMETER_ROWS = 64
MAX_PARAMETER_CELLS = 256
COMPARISON_METHODS: dict[type[ast.cmpop], tuple[str, str]] = {
    ast.Eq: ("==", "__eq__"),
    ast.Lt: ("<", "__lt__"),
    ast.Gt: (">", "__gt__"),
    ast.NotEq: ("!=", "__ne__"),
}
PREVIOUS_MODES: dict[EqualityMode, EqualityMode] = {
    True: "raises-less-than",
    "raises-less-than": "string-parameter",
    "string-parameter": "parameterized",
    "parameterized": "dictionary",
    "dictionary": "inequality",
    "inequality": "less-than",
    "less-than": "first-assertion",
    "first-assertion": "factories",
    "factories": "exact-class",
}


class Unproved(Exception):
    """The snapshot cannot establish the binding within this slice."""


@dataclass(frozen=True)
class Function:
    sid: str
    node: ast.FunctionDef
    wrapper: "Function | None" = None
    mode: str = ""


@dataclass
class Class:
    sid: str
    members: dict[str, "Value"] = field(default_factory=dict)


@dataclass(frozen=True)
class Instance:
    owner: Class
    fields: frozenset[str] = frozenset()


Value = str | Function | Class | Instance
UNBOUND = "unbound"
DATA = "data"
TYPE = "type"
REGEX = "regex"
MATCH = "match"
FRAME = "frame"
CODE = "code"
LIST = "list"
DICT = "dict"
EXACT_DICT = "exact-builtin-dict"
PROPERTY = "property"
STDLIB = {
    "__future__",
    "argparse",
    "functools",
    "inspect",
    "re",
    "sys",
    "types",
    "typing",
    "warnings",
}
BUILTINS = {
    "bool",
    "bytes",
    "classmethod",
    "dict",
    "float",
    "int",
    "isinstance",
    "list",
    "object",
    "property",
    "staticmethod",
    "str",
    "slice",
    "tuple",
    "type",
    "ValueError",
    "Warning",
    "TypeError",
    "DeprecationWarning",
    "PendingDeprecationWarning",
    "NotImplemented",
}
DATA_TYPES = {
    "argparse.Namespace",
    "argparse.ArgumentParser",
    "types.FrameType",
    "re.Pattern",
    "typing.Any",
    "typing.Callable",
    "typing.ClassVar",
    "typing.Collection",
    "typing.Dict",
    "typing.Iterable",
    "typing.Iterator",
    "typing.List",
    "typing.Optional",
    "typing.Pattern",
    "typing.SupportsInt",
    "typing.Tuple",
    "typing.Type",
    "typing.Union",
}
EXTERNAL = DATA_TYPES | {
    "inspect.currentframe",
    "inspect.getfile",
    "re.compile",
    "re.VERBOSE",
    "typing.TypeVar",
    "typing.cast",
    "functools.partial",
    "functools.wraps",
    "warnings.warn_explicit",
}
MAGIC = {
    "__init__",
    "__eq__",
    "__ne__",
    "__lt__",
    "__le__",
    "__gt__",
    "__ge__",
    "__iter__",
    "__getitem__",
    "__repr__",
    "__str__",
    "__hash__",
}
RISKY = {
    "__class__",
    "__bases__",
    "__getattribute__",
    "__getattr__",
    "__dict__",
    "__builtins__",
    "__globals__",
    "__wrapped__",
    "__code__",
}


def body(node: ast.FunctionDef) -> list[ast.stmt]:
    return node.body[1:] if ast.get_docstring(node, clean=False) is not None else node.body


def identifier(node: ast.AST | None, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def parameters(fn: ast.FunctionDef) -> list[ast.arg]:
    return [*fn.args.posonlyargs, *fn.args.args]


class Proof:
    def __init__(
        self,
        resolver: "PartialBindings",
        unparseable: set[str],
        *,
        scalar_factories: bool,
        literal_parameters: bool = False,
    ):
        self.scalar_factories = scalar_factories
        self.literal_parameters = literal_parameters
        self.resolver = resolver
        self.unparseable = unparseable
        self.paths = {path: module for module, path in resolver.modules.items()}
        self.modules: dict[str, dict[str, Value]] = {}
        self.loading: set[str] = set()
        self.steps = 0
        self.writes: set[str] = set()
        self.initializing: dict[str, dict[str, Value]] = {}

    def tick(self) -> None:
        self.steps += 1
        if self.steps > MAX_PROOF_STEPS:
            raise Unproved

    def module(self, path: str) -> dict[str, Value]:
        self.tick()
        if path in self.modules:
            return self.modules[path]
        if path in self.unparseable or path in self.loading or len(self.loading) >= 12:
            raise Unproved
        parent = self.resolver.modules.get(self.paths[path].rpartition(".")[0])
        if parent and parent not in self.loading:
            self.module(parent)
            # The package may have already imported this child.
            if path in self.modules:
                return self.modules[path]
        self.loading.add(path)
        try:
            env: dict[str, Value] = {}
            self.initializing[path] = env
            self.initialize(self.resolver.trees[path].body, path, env, prefix=f"{path}::")
            self.modules[path] = env
            return env
        finally:
            self.loading.remove(path)
            self.initializing.pop(path, None)

    def imported(self, qualified: str) -> Value:
        module, _, name = qualified.rpartition(".")
        if module in self.resolver.modules:
            parent = self.resolver.modules[module]
            if parent in self.loading:
                # Importing a child from its package is expected. Reading a
                # partially initialized package binding is outside this proof.
                if name in self.initializing[parent] or qualified not in self.resolver.modules:
                    raise Unproved
            elif name in (env := self.module(parent)):
                return env[name]
        if qualified in self.resolver.modules:
            self.module(self.resolver.modules[qualified])
            return f"module:{qualified}"
        if qualified in STDLIB and not any(
            key.startswith(qualified + ".") for key in self.resolver.modules
        ):
            return f"module:{qualified}"
        if module in STDLIB and qualified in EXTERNAL:
            return qualified
        raise Unproved

    def define(self, env: dict[str, Value], name: str, value: Value) -> None:
        if (
            name in env
            or name in self.writes
            or name in RISKY | {"__name__", "__package__", "__path__"}
        ):
            raise Unproved
        env[name] = value

    def initialize(
        self,
        stmts: list[ast.stmt],
        path: str,
        env: dict[str, Value],
        *,
        prefix: str,
        outer: dict[str, Value] | None = None,
    ) -> None:
        test_path = path.startswith("tests/") or (self.literal_parameters and is_test_file(path))
        for stmt in stmts:
            self.tick()
            scope = env if outer is None else outer | env
            if isinstance(stmt, (ast.Import, ast.ImportFrom)) and outer is None:
                if isinstance(stmt, ast.ImportFrom):
                    nesting = len(self.paths[path].split(".")) - (not path.endswith("/__init__.py"))
                    if stmt.level > nesting or any(a.name == "*" for a in stmt.names):
                        raise Unproved
                elif any("." in alias.name for alias in stmt.names):
                    raise Unproved
                bindings, _ = self.resolver.decode(stmt, path, self.resolver.modules)
                for name, qualified in bindings:
                    if (
                        test_path
                        and qualified == "pytest"
                        and qualified not in self.resolver.modules
                    ):
                        self.define(env, name, "pytest")
                    else:
                        self.define(env, name, self.imported(qualified))
            elif isinstance(stmt, ast.ClassDef) and outer is None:
                if stmt.bases or stmt.keywords or stmt.decorator_list or stmt.type_params:
                    raise Unproved
                owner = Class(prefix + stmt.name)
                self.initialize(stmt.body, path, owner.members, prefix=owner.sid + ".", outer=env)
                self.define(env, stmt.name, owner)
            elif isinstance(stmt, ast.FunctionDef):
                if stmt.name.startswith("__") and (outer is None or stmt.name not in MAGIC):
                    raise Unproved
                self.header(stmt, scope)
                fn = Function(prefix + stmt.name, stmt)
                if len(stmt.decorator_list) > 1:
                    raise Unproved
                if stmt.decorator_list:
                    decorator = stmt.decorator_list[0]
                    if (
                        test_path
                        and outer is None
                        and isinstance(decorator, ast.Call)
                        and dotted(decorator.func) == "pytest.mark.parametrize"
                        and env.get("pytest") == "pytest"
                        and not decorator.keywords
                        and all(self.inert(self.expression(arg, scope)) for arg in decorator.args)
                    ):
                        self.define(env, stmt.name, Function(fn.sid, stmt, mode="pytest"))
                        continue
                    decoration = self.expression(decorator, scope)
                    if decoration == "builtin:property" and outer is not None:
                        if stmt.name in env:
                            raise Unproved
                        env[stmt.name] = PROPERTY
                        continue
                    if decoration == "property:setter" and outer is not None:
                        if isinstance(decorator, ast.Attribute) and identifier(
                            decorator.value, stmt.name
                        ):
                            continue
                        raise Unproved
                    if (
                        decoration in ("builtin:classmethod", "builtin:staticmethod")
                        and outer is not None
                    ):
                        assert isinstance(decoration, str)
                        fn = Function(fn.sid, stmt, mode=decoration)
                    elif isinstance(decoration, Function):
                        wrapper = (
                            decoration.wrapper
                            if decoration.mode == "decorator"
                            else self.wrapper(decoration)
                        )
                        fn = Function(fn.sid, stmt, wrapper=wrapper)
                    else:
                        raise Unproved
                self.define(env, stmt.name, fn)
            elif isinstance(stmt, (ast.Assign, ast.AnnAssign)):
                targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
                if (
                    len(targets) != 1
                    or not isinstance(target := targets[0], ast.Name)
                    or stmt.value is None
                ):
                    raise Unproved
                if isinstance(stmt, ast.AnnAssign):
                    self.annotation(stmt.annotation, scope)
                if outer is not None and target.id.startswith("__") and target.id != "__slots__":
                    raise Unproved
                if target.id == "__slots__" and not (
                    isinstance(stmt.value, (ast.Tuple, ast.List))
                    and all(
                        isinstance(x, ast.Constant)
                        and isinstance(x.value, str)
                        and x.value.isidentifier()
                        and not x.value.startswith("__")
                        for x in stmt.value.elts
                    )
                ):
                    raise Unproved
                self.define(env, target.id, self.expression(stmt.value, scope))
            elif not isinstance(stmt, ast.Pass) and not (
                isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
            ):
                raise Unproved

    def annotation(self, expr: ast.expr | None, env: dict[str, Value]) -> None:
        if expr is None:
            return
        value = self.expression(expr, env)
        if not (
            isinstance(value, Class)
            or value in (DATA, LIST, TYPE, "functools.partial")
            or isinstance(value, str)
            and value in DATA_TYPES
            or isinstance(value, str)
            and value.startswith("builtin:")
        ):
            raise Unproved

    def header(self, fn: ast.FunctionDef, env: dict[str, Value]) -> None:
        if fn.type_params:
            raise Unproved
        for arg in ast.walk(fn.args):
            if isinstance(arg, ast.arg):
                self.annotation(arg.annotation, env)
        self.annotation(fn.returns, env)
        for default in [*fn.args.defaults, *fn.args.kw_defaults]:
            if default is not None and not self.inert(self.expression(default, env)):
                raise Unproved

    def wrapper(self, factory: Function) -> Function:
        path = factory.sid.split("::")[0]
        params = parameters(factory.node)
        stmts = body(factory.node)
        if factory.wrapper or factory.mode or len(params) != 1:
            raise Unproved
        argument = params[0].arg
        env = self.module(path) if path not in self.loading else self.initializing[path]
        if len(stmts) == 3:
            first, *stmts = stmts
            match first:
                case ast.If(
                    test=ast.Compare(
                        left=ast.Name(id=name),
                        ops=[ast.Is()],
                        comparators=[ast.Constant(value=None)],
                    ),
                    body=[
                        ast.Return(
                            value=ast.Call(
                                func=partial, args=[ast.Name(id=target)], keywords=keywords
                            )
                        )
                    ],
                    orelse=[],
                ):
                    if (
                        name != argument
                        or target != factory.node.name
                        or self.expression(partial, env) != "functools.partial"
                    ):
                        raise Unproved
                    if any(
                        kw.arg is None
                        or not identifier(kw.value, kw.arg)
                        or kw.arg not in {p.arg for p in factory.node.args.kwonlyargs}
                        for kw in keywords
                    ):
                        raise Unproved
                case _:
                    raise Unproved
        match stmts:
            case [ast.FunctionDef() as fn, ast.Return(value=ast.Name(id=name))] if fn.name == name:
                self.header(fn, env)
                match fn.decorator_list:
                    case [ast.Call(func=wraps, args=[ast.Name(id=wrapped)], keywords=[])]:
                        if wrapped == argument and self.expression(wraps, env) == "functools.wraps":
                            return Function(f"{factory.sid}.{name}", fn)
        raise Unproved

    @staticmethod
    def inert(value: Value) -> bool:
        return isinstance(value, str) and (
            value
            in {
                DATA,
                LIST,
                DICT,
                EXACT_DICT,
                MATCH,
                FRAME,
                CODE,
                REGEX,
                TYPE,
                "re.VERBOSE",
                "builtin:DeprecationWarning",
                "builtin:PendingDeprecationWarning",
            }
            or isinstance(value, str)
            and value in DATA_TYPES
        )

    def expression(self, expr: ast.expr, env: dict[str, Value], *, depth: int = 0) -> Value:
        self.tick()
        if depth >= 24:
            raise Unproved

        def read(child: ast.expr) -> Value:
            return self.expression(child, env, depth=depth + 1)

        def data(child: ast.expr) -> None:
            if not self.inert(read(child)):
                raise Unproved

        match expr:
            case ast.Constant():
                return DATA
            case ast.JoinedStr(values=parts):
                for part in parts:
                    data(part)
                return DATA
            case ast.FormattedValue(value=formatted, format_spec=None):
                data(formatted)
                return DATA
            case ast.IfExp(test=test, body=yes, orelse=no):
                for part in (test, yes, no):
                    data(part)
                return DATA
            case ast.Name(id=name):
                if name in env:
                    if env[name] == UNBOUND:
                        raise Unproved
                    return env[name]
                if name in BUILTINS:
                    return f"builtin:{name}"
            case ast.Attribute(value=receiver, attr=name):
                value = read(receiver)
                if isinstance(value, str) and value.startswith("module:"):
                    return self.imported(f"{value.removeprefix('module:')}.{name}")
                if isinstance(value, Instance) and name not in RISKY:
                    member = value.owner.members.get(name)
                    if isinstance(member, Function) and not member.mode:
                        return member
                    if member is None and name in value.fields:
                        return DATA
                if isinstance(value, Class) and name in value.members:
                    return value.members[name]
                if value == PROPERTY and name == "setter":
                    return "property:setter"
                if (
                    value == TYPE or isinstance(value, str) and value in DATA_TYPES
                ) and name == "__args__":
                    return DATA
                if value == FRAME and name in ("f_back", "f_code", "f_lineno"):
                    return {"f_back": FRAME, "f_code": CODE, "f_lineno": DATA}[name]
                if isinstance(value, Function) and name == "__qualname__":
                    return DATA
            case ast.Tuple(elts=elts) | ast.List(elts=elts):
                for child in elts:
                    data(child)
                return LIST if isinstance(expr, ast.List) else DATA
            case ast.Dict(keys=keys, values=values):
                for key, entry in zip(keys, values, strict=True):
                    if key is None:
                        raise Unproved
                    data(key)
                    data(entry)
                return DICT
            case ast.Subscript(value=base, slice=subscript):
                value = read(base)
                if isinstance(value, str) and (value in DATA_TYPES or value == TYPE):
                    parts = subscript.elts if isinstance(subscript, ast.Tuple) else [subscript]
                    for item in parts:
                        self.annotation(item, env)
                    return TYPE
                if value in (DATA, LIST, DICT, EXACT_DICT):
                    data(subscript)
                    return DATA
            case ast.Slice(lower=start, upper=end, step=step):
                for bound in (start, end, step):
                    if bound is not None:
                        data(bound)
                return DATA
            case ast.BinOp(left=left, op=ast.Add() | ast.Mod(), right=right):
                data(left)
                data(right)
                return DATA
            case ast.BoolOp(values=values):
                for child in values:
                    data(child)
                return DATA
            case ast.UnaryOp(op=ast.Not() | ast.UAdd() | ast.USub(), operand=operand):
                data(operand)
                return DATA
            case ast.Compare(left=left, comparators=right):
                for child in [left, *right]:
                    data(child)
                return DATA
            case ast.ListComp(
                elt=elt,
                generators=[
                    ast.comprehension(target=ast.Name(id=name), iter=items, ifs=[], is_async=0)
                ],
            ):
                data(items)
                data_env = env | {name: DATA}
                if self.inert(self.expression(elt, data_env, depth=depth + 1)):
                    return LIST
            case ast.Call():
                return self.call(expr, env, depth=depth + 1)
        raise Unproved

    def call(self, call: ast.Call, env: dict[str, Value], *, depth: int) -> Value:
        args = [self.expression(arg, env, depth=depth) for arg in call.args]
        kwargs = {key.arg: self.expression(key.value, env, depth=depth) for key in call.keywords}
        if isinstance(attr := call.func, ast.Attribute):
            receiver = self.expression(attr.value, env, depth=depth)
            if isinstance(receiver, Instance):
                method = receiver.owner.members.get(attr.attr)
                if isinstance(method, Function) and not method.mode and not method.wrapper:
                    return self.constructed(method, receiver, args, kwargs, depth=depth)
                raise Unproved
            if isinstance(receiver, Class):
                method = receiver.members.get(attr.attr)
                if isinstance(method, Function) and method.mode == "builtin:classmethod":
                    return self.constructed(method, receiver, args, kwargs, depth=depth)
                if (
                    self.scalar_factories
                    and not kwargs
                    and isinstance(method, Function)
                    and method.mode == "builtin:staticmethod"
                    and not method.wrapper
                ):
                    return self.scalar_transform(receiver, method, args)
                raise Unproved
            if all(map(self.inert, [*args, *kwargs.values()])) and None not in kwargs:
                methods = {
                    (DATA, "decode"): DATA,
                    (DATA, "format"): DATA,
                    (DATA, "join"): DATA,
                    (REGEX, "match"): MATCH,
                    (MATCH, "groupdict"): DICT,
                    (DICT, "items"): DATA,
                    (EXACT_DICT, "items"): DATA,
                    (LIST, "append"): DATA,
                }
                if isinstance(receiver, str) and (receiver, attr.attr) in methods:
                    return methods[receiver, attr.attr]
        func = self.expression(call.func, env, depth=depth)
        if isinstance(func, Class):
            if all(map(self.inert, [*args, *kwargs.values()])):
                if None in kwargs and kwargs[None] not in (DICT, EXACT_DICT):
                    raise Unproved
                return self.constructor(func, depth)
            raise Unproved
        if isinstance(func, Function):
            if not func.wrapper and not func.mode:
                # A source decorator factory is recognized by its complete eager body.
                if self.loading:
                    return self.bind_decorator(func, args, kwargs)
            return self.constructed(func, None, args, kwargs, depth=depth)
        if func == "builtin:type" and len(args) == 1 and not kwargs:
            if isinstance(args[0], Instance):
                return args[0].owner
            if self.inert(args[0]):
                return DATA
        if func in ("builtin:isinstance", "typing.cast") and len(args) == 2 and not kwargs:
            if (
                func == "builtin:isinstance"
                and self.inert(args[0])
                and (
                    self.inert(args[1])
                    or isinstance(args[1], str)
                    and args[1].startswith("builtin:")
                )
            ):
                return DATA
            if func == "typing.cast" and (self.inert(args[1]) or isinstance(args[1], Function)):
                return args[1]
        observations = {
            "re.compile": REGEX,
            "typing.TypeVar": TYPE,
            "inspect.currentframe": FRAME,
            "inspect.getfile": DATA,
            "warnings.warn_explicit": DATA,
            "builtin:int": DATA,
            "builtin:str": DATA,
            "builtin:tuple": DATA,
            "builtin:ValueError": DATA,
            "builtin:TypeError": DATA,
        }
        if (
            isinstance(func, str)
            and func in observations
            and None not in kwargs
            and all(
                self.inert(v) or isinstance(v, str) and v.startswith("builtin:")
                for v in [*args, *kwargs.values()]
            )
        ):
            return observations[func]
        raise Unproved

    def scalar_transform(self, owner: Class, fn: Function, args: list[Value]) -> Value:
        """Audit a static one-input regex rewrite on normal return, without running the regex."""
        params = parameters(fn.node)
        sig = fn.node.args
        if (
            self.loading
            or args != [DATA]
            or len(params) != 1
            or sig.vararg
            or sig.kwarg
            or sig.kwonlyargs
            or sig.defaults
            or "re" in self.resolver.modules
            or self.writes
            & {"compile", "search", "group", "span", "staticmethod", "int", "str", "max", "len"}
        ):
            raise Unproved
        param = params[0].arg
        stmts = body(fn.node)
        match stmts:
            case [
                ast.Assign(
                    targets=[ast.Name(id=match_name)],
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Attribute(value=ast.Name(id=class_name), attr=pattern),
                            attr="search",
                        ),
                        args=[ast.Name(id=subject)],
                        keywords=[],
                    ),
                ),
                ast.If(test=ast.Name(id=guard), body=updates, orelse=[]),
                ast.Return(value=ast.Name(id=result)),
            ] if subject == result == param and guard == match_name and match_name != param:
                pass
            case _:
                raise Unproved
        namespace = self.module(fn.sid.split("::")[0])
        locals_ = set(audit(stmts, local=True).counts) | {param}
        if (
            class_name in locals_
            or namespace.get(class_name) is not owner
            or owner.members.get(pattern) != REGEX
        ):
            raise Unproved

        # Only plain scalar temporaries, a successful match's capture/span, and
        # unshadowed builtins can feed the returned argument. No callback/descriptor
        # on arbitrary data is assumed pure. The no-match branch returns the input.
        scalars = {param}

        def capture(call: ast.expr, operation: str) -> bool:
            match call:
                case ast.Call(
                    func=ast.Attribute(value=ast.Name(id=name), attr=method),
                    args=[ast.Constant(value=index)],
                    keywords=[],
                ):
                    return (
                        name == match_name
                        and method == operation
                        and type(index) is int
                        and index >= 0
                    )
            return False

        def scalar(expr: ast.expr) -> bool:
            self.tick()
            match expr:
                case ast.Name(id=name):
                    return name in scalars
                case ast.Constant(value=value):
                    return type(value) in (int, str)
                case ast.BinOp(left=left, op=ast.Add() | ast.Sub(), right=right):
                    return scalar(left) and scalar(right)
                case ast.Subscript(
                    value=value_expr, slice=ast.Slice(lower=lo, upper=hi, step=None)
                ):
                    return scalar(value_expr) and all(scalar(v) for v in (lo, hi) if v is not None)
                case ast.Call(func=ast.Name(id=name), args=values, keywords=[]):
                    arity = {"str": 1, "int": 1, "len": 1, "max": 2}
                    return (
                        arity.get(name) == len(values)
                        and name not in locals_
                        and name not in namespace
                        and all(scalar(v) for v in values)
                    )
            return capture(expr, "group")

        for stmt in updates:
            self.tick()
            match stmt:
                case ast.Assign(targets=[ast.Name(id=name)], value=expr) if (
                    name != match_name and scalar(expr)
                ):
                    scalars.add(name)
                case ast.Assign(
                    targets=[ast.Tuple(elts=[ast.Name(id=start), ast.Name(id=end)])], value=expr
                ) if match_name not in (start, end) and capture(expr, "span"):
                    scalars.update((start, end))
                case _:
                    raise Unproved
        return DATA

    def bind_decorator(
        self, fn: Function, args: list[Value], kwargs: dict[str | None, Value]
    ) -> Function:
        if len(args) > 1 or len(args) == 1 and not isinstance(args[0], Function):
            raise Unproved
        if set(kwargs) - {p.arg for p in fn.node.args.kwonlyargs} or not all(
            map(self.inert, kwargs.values())
        ):
            raise Unproved
        if not args and (
            len(body(fn.node)) != 3
            or not fn.node.args.defaults
            or not isinstance(fn.node.args.defaults[0], ast.Constant)
            or fn.node.args.defaults[0].value is not None
        ):
            raise Unproved
        wrapper = self.wrapper(fn)
        if not args:
            return Function(fn.sid, fn.node, wrapper=wrapper, mode="decorator")
        target = args[0]
        assert isinstance(target, Function)
        if target.mode or target.wrapper:
            raise Unproved
        return Function(target.sid, target.node, wrapper=wrapper)

    def constructor(self, owner: Class, depth: int) -> Instance:
        fn = owner.members.get("__init__")
        if fn is None:
            return Instance(owner)
        if not isinstance(fn, Function) or fn.wrapper or fn.mode or not parameters(fn.node):
            raise Unproved
        args = parameters(fn.node)
        receiver = args[0].arg
        scope = audit(body(fn.node), local=True)
        if receiver in scope.counts:
            raise Unproved
        env: dict[str, Value] = self.module(fn.sid.split("::")[0]) | {
            name: UNBOUND for name in scope.counts
        }
        env.update((arg.arg, DATA) for arg in args)
        env[receiver] = Instance(owner)
        if self.statements(body(fn.node), env, depth, receiver=receiver):
            raise Unproved
        result = env[receiver]
        assert isinstance(result, Instance)
        return result

    def constructed(
        self,
        fn: Function,
        receiver: Instance | Class | None,
        args: list[Value],
        kwargs: dict[str | None, Value],
        *,
        depth: int,
    ) -> Instance:
        self.tick()
        if (
            depth >= 16
            or self.loading
            or None in kwargs
            or not all(map(self.inert, [*args, *kwargs.values()]))
        ):
            raise Unproved
        env = self.module(fn.sid.split("::")[0]).copy()
        scoped = audit(body(fn.node), local=True)
        env.update((name, UNBOUND) for name in scoped.counts)
        fn_args = fn.node.args
        if fn_args.kwonlyargs or fn_args.vararg or fn_args.kwarg:
            raise Unproved
        params = parameters(fn.node)
        if receiver is not None:
            if not params:
                raise Unproved
            env[params[0].arg] = receiver
            params = params[1:]
        if len(args) > len(params) or set(kwargs) - {p.arg for p in params[len(args) :]}:
            raise Unproved
        if any(
            param.arg not in kwargs
            for param in params[len(args) : len(params) - len(fn_args.defaults)]
        ):
            raise Unproved
        for param in params:
            env[param.arg] = DATA
        if fn.wrapper:
            self.forwarding(fn, depth)
        stmts = body(fn.node)
        if not stmts or not isinstance(end := stmts[-1], ast.Return) or end.value is None:
            raise Unproved
        if self.statements(stmts[:-1], env, depth):
            raise Unproved
        result = self.expression(end.value, env, depth=depth)
        if isinstance(result, Instance):
            return result
        raise Unproved

    def forwarding(self, fn: Function, depth: int) -> None:
        assert fn.wrapper is not None
        factory_sid = fn.wrapper.sid.rsplit(".", 1)[0]
        factory = self.module(factory_sid.split("::")[0]).get(factory_sid.split("::")[1])
        if not isinstance(factory, Function) or not parameters(factory.node):
            raise Unproved
        func = parameters(factory.node)[0].arg
        wrapper = fn.wrapper.node
        vararg, kwarg = wrapper.args.vararg, wrapper.args.kwarg
        stmts = body(wrapper)
        if not stmts or not vararg or not kwarg or parameters(wrapper) or wrapper.args.kwonlyargs:
            raise Unproved
        match stmts[-1]:
            case ast.Return(
                value=ast.Call(
                    func=ast.Name(id=target),
                    args=[ast.Starred(value=ast.Name(id=args))],
                    keywords=[ast.keyword(arg=None, value=ast.Name(id=kwargs))],
                )
            ):
                if (target, args, kwargs) != (func, vararg.arg, kwarg.arg):
                    raise Unproved
            case _:
                raise Unproved
        env = self.module(factory_sid.split("::")[0]) | {
            p.arg: DATA for p in factory.node.args.kwonlyargs
        }
        env.update({func: fn, vararg.arg: DATA, kwarg.arg: DATA})
        effect_scope = audit(stmts[:-1], local=True)
        if {func, vararg.arg, kwarg.arg} & effect_scope.counts.keys():
            raise Unproved
        self.statements(stmts[:-1], env, depth)

    def comparison_operand(self, expr: ast.expr, env: dict[str, Value], *, depth: int = 0) -> Value:
        if isinstance(expr, ast.Dict) and all(isinstance(key, ast.Constant) for key in expr.keys):
            self.expression(expr, env, depth=depth)
            return EXACT_DICT
        if (
            isinstance(expr, ast.Call)
            and identifier(expr.func, "dict")
            and "dict" not in env
            and "dict" not in self.writes
        ):
            self.tick()
            if expr.args or any(
                kw.arg is None or not self.inert(self.expression(kw.value, env, depth=depth + 1))
                for kw in expr.keywords
            ):
                raise Unproved
            return EXACT_DICT
        return self.expression(expr, env, depth=depth)

    def statements(
        self,
        stmts: list[ast.stmt],
        env: dict[str, Value],
        depth: int,
        *,
        receiver: str | None = None,
        dictionary_operands: bool = False,
    ) -> bool:
        # Record exact dictionaries in the test's straight-line comparison prefix.
        read = self.comparison_operand if dictionary_operands else self.expression
        for stmt in stmts:
            self.tick()
            match stmt:
                case ast.Assign(targets=[ast.Name(id=name)], value=expr):
                    env[name] = read(expr, env, depth=depth)
                case ast.AnnAssign(target=ast.Name(id=name), value=expr) if expr is not None:
                    env[name] = read(expr, env, depth=depth)
                case ast.Assign(
                    targets=[ast.Subscript(value=ast.Name(id=name), slice=key)], value=expr
                ):
                    if env.get(name) not in (DICT, EXACT_DICT) or not all(
                        self.inert(self.expression(term, env, depth=depth)) for term in (key, expr)
                    ):
                        raise Unproved
                case ast.Assign(
                    targets=[ast.Attribute(value=ast.Name(id=name), attr=attr)], value=expr
                ) if name == receiver:
                    instance = env.get(name)
                    if (
                        not isinstance(instance, Instance)
                        or attr in instance.owner.members
                        or attr.startswith("__")
                        or not self.inert(self.expression(expr, env, depth=depth))
                    ):
                        raise Unproved
                    env[name] = Instance(instance.owner, instance.fields | {attr})
                case ast.If(test=condition, body=yes, orelse=no):
                    if not self.inert(self.expression(condition, env, depth=depth)):
                        raise Unproved
                    left, right = env.copy(), env.copy()
                    stopped_left = self.statements(yes, left, depth + 1, receiver=receiver)
                    stopped_right = self.statements(no, right, depth + 1, receiver=receiver)
                    if stopped_left and stopped_right:
                        raise Unproved
                    merged = (
                        right
                        if stopped_left
                        else left
                        if stopped_right
                        else {
                            name: left[name]
                            if name in left and left[name] == right.get(name)
                            else UNBOUND
                            for name in left.keys() | right.keys()
                        }
                    )
                    env.clear()
                    env.update(merged)
                case ast.For(
                    target=target,
                    iter=items,
                    body=[ast.If(body=[ast.Raise()], orelse=[])] as loop,
                    orelse=[],
                ):
                    if receiver is None or not self.inert(self.expression(items, env, depth=depth)):
                        raise Unproved
                    names = target.elts if isinstance(target, ast.Tuple) else [target]
                    if not all(isinstance(n, ast.Name) for n in names):
                        raise Unproved
                    loop_names = {n.id: DATA for n in names if isinstance(n, ast.Name)}
                    self.statements(loop, env | loop_names, depth + 1, receiver=receiver)
                    env.update((name, UNBOUND) for name in loop_names)
                case ast.Raise(exc=expr, cause=None) if expr is not None:
                    if not self.inert(self.expression(expr, env, depth=depth)):
                        raise Unproved
                    return True
                case ast.Expr(value=ast.Call() as expr):
                    if not self.inert(self.expression(expr, env, depth=depth)):
                        raise Unproved
                case ast.Delete(targets=[ast.Name(id=name)]):
                    if env.get(name) != FRAME:
                        raise Unproved
                    del env[name]
                case ast.Pass():
                    pass
                case _:
                    raise Unproved
        return False

    def comparison(
        self,
        fn: ast.FunctionDef,
        env: dict[str, Value],
        position: int,
        site: ast.Compare,
        method_name: str,
        *,
        dictionary_operands: bool,
        parameter: LiteralParameter | None,
    ) -> tuple[Function, str] | None:
        # Binding is function-wide, but only the prefix establishes operand values.
        stmts = body(fn)
        scoped = audit(stmts, local=True)
        if method_name != "__eq__" or position < len(stmts) - 1:
            # A yield anywhere can change the calling convention, even after return.
            if scoped.wildcard or any(
                isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(fn)
            ):
                return None
        local = env | {name: UNBOUND for name in scoped.counts}
        if parameter is not None:
            if parameter[0] in scoped.counts:
                return None
            # The proof uses the parameter only as the direct right operand.
            local[parameter[0]] = UNBOUND
        if self.statements(stmts[:position], local, 0, dictionary_operands=dictionary_operands):
            return None
        in_raises = isinstance(stmts[position], ast.With)
        exception = "TypeError" if method_name == "__gt__" else "ValueError"
        if in_raises and (
            local.get("pytest") != "pytest"
            or exception in local
            or self.writes & {"raises", exception}
        ):
            return None
        lhs = self.expression(site.left, local)
        if not isinstance(lhs, Instance):
            return None
        if parameter is not None:
            name, builtin_type = parameter
            detail = (
                f"with an exact builtin {builtin_type} from pytest parameter {name!r} on the right"
            )
        elif method_name == "__gt__":
            # The recognized TypeError context requires an exact int constant.
            detail = "with an exact builtin int on the right"
        else:
            read_rhs = self.comparison_operand if dictionary_operands else self.expression
            rhs = read_rhs(site.comparators[0], local)
            if isinstance(rhs, Instance) and lhs.owner is rhs.owner:
                detail = "on the same exact class"
            elif dictionary_operands and rhs == EXACT_DICT:
                detail = "with an exact builtin dict on the right"
            else:
                return None

        # The same class or an unrelated exact builtin rules out subclass priority.
        # The proof stops at the initial call even if it returns NotImplemented.
        method = lhs.owner.members.get(method_name)
        if isinstance(method, Function) and not method.mode:
            target = method.wrapper or method
            args = target.node.args
            pos = len(parameters(target.node))
            if (
                pos - len(args.defaults) <= 2
                and (pos >= 2 or args.vararg)
                and all(default is not None for default in args.kw_defaults)
            ):
                if in_raises:
                    detail += f" inside pytest.raises({exception})"
                return target, detail
        return None


def literal_parameter(fn: ast.FunctionDef, *, allow_strings: bool) -> LiteralParameter | None:
    shape = inline_decorator(fn)
    args = fn.args
    if shape is None or (
        len(args.args) != 1
        or args.posonlyargs
        or args.kwonlyargs
        or args.vararg
        or args.kwarg
        or args.defaults
    ):
        return None
    decorator, table = shape
    name = args.args[0].arg
    if not isinstance(decorator.args[0], ast.Constant) or decorator.args[0].value != name:
        return None
    if not 1 <= len(table.elts) <= MAX_PARAMETER_ROWS:
        return None
    if allow_strings and all(
        isinstance(row, ast.Constant) and type(row.value) is str for row in table.elts
    ):
        return name, "str"
    first_row = table.elts[0]
    if not isinstance(first_row, (ast.Tuple, ast.List)):
        return None
    row_type = type(first_row)
    cells = 0
    for row in table.elts:
        if not isinstance(row, row_type):
            return None
        cells += len(row.elts)
        if cells > MAX_PARAMETER_CELLS or any(
            not isinstance(cell, ast.Constant) for cell in row.elts
        ):
            return None
    return name, "tuple" if isinstance(first_row, ast.Tuple) else "list"


def raises_comparison(
    stmt: ast.With, *, exception: str, operator: type[ast.cmpop]
) -> ast.Compare | None:
    match stmt:
        case ast.With(
            items=[
                ast.withitem(
                    context_expr=ast.Call(
                        func=ast.Attribute(value=ast.Name(id="pytest"), attr="raises"),
                        args=[ast.Name(id=expected)],
                        keywords=[],
                    ),
                    optional_vars=None,
                )
            ],
            body=[ast.Expr(value=ast.Compare(ops=[op], comparators=[_]) as site)],
        ) if expected == exception and isinstance(op, operator):
            return site
    return None


def comparison_site(
    fn: ast.FunctionDef,
    *,
    first: bool,
    operators: tuple[type[ast.cmpop], ...],
    literal_parameters: bool,
    allow_strings: bool,
    allow_raises: bool,
    allow_greater_raises: bool,
) -> tuple[int, ast.Compare, LiteralParameter | None] | None:
    parameter = literal_parameter(fn, allow_strings=allow_strings) if literal_parameters else None
    if fn.type_params or fn.returns:
        return None
    if parameter is None and (
        fn.decorator_list or parameters(fn) or fn.args.kwonlyargs or fn.args.vararg or fn.args.kwarg
    ):
        return None
    stmts = body(fn)
    for position, stmt in enumerate(stmts):
        site_operators = operators
        expression: ast.expr | None
        if isinstance(stmt, ast.Assert):
            expression = stmt.test
        elif allow_raises and isinstance(stmt, ast.With):
            if parameter is not None and parameter[1] == "str":
                expression = raises_comparison(stmt, exception="ValueError", operator=ast.Lt)
            elif allow_greater_raises and parameter is None:
                expression = raises_comparison(stmt, exception="TypeError", operator=ast.Gt)
                if expression is not None:
                    right_int = expression.comparators[0]
                    if not isinstance(right_int, ast.Constant) or type(right_int.value) is not int:
                        continue
                site_operators = (ast.Gt,)
            else:
                continue
            if expression is None:
                continue
        else:
            continue
        match expression:
            case ast.Compare(ops=[ast.Eq()], comparators=[_]) as site if (
                parameter is None and position == len(stmts) - 1
            ):
                return position, site, None
            case ast.Compare(ops=[op], comparators=[right]) as site if (
                first
                and isinstance(op, site_operators)
                and (
                    parameter is None or isinstance(op, ast.Lt) and identifier(right, parameter[0])
                )
                and all(
                    isinstance(prefix, (ast.Assign, ast.AnnAssign, ast.Pass))
                    for prefix in stmts[:position]
                )
            ):
                return position, site, parameter
        if first:
            break
    return None


def namespace_writes(resolver: "PartialBindings") -> set[str]:
    writes = set()
    steps = 0
    dynamic = {
        "setattr",
        "delattr",
        "__setattr__",
        "__delattr__",
        "eval",
        "exec",
        "vars",
        "globals",
        "locals",
        "__import__",
        "reload",
        "__builtins__",
        "__dict__",
        "__globals__",
        "__closure__",
        "__defaults__",
        "__kwdefaults__",
        "__code__",
    }
    for tree in resolver.trees.values():
        for node in ast.walk(tree):
            steps += 1
            if steps > 20_000 or isinstance(node, (ast.Global, ast.Nonlocal)):
                raise Unproved
            match node:
                case ast.Attribute(attr=name, ctx=ast.Store() | ast.Del()):
                    writes.add(name)
                case ast.Name(id=name) | ast.Attribute(attr=name):
                    if name in dynamic or dotted(node) == "sys.modules":
                        raise Unproved
                case ast.alias(name=name) if name.rsplit(".", 1)[-1] in dynamic:
                    raise Unproved
    if RISKY & writes:
        raise Unproved
    return writes


def add_comparison_edges(index: "Index", *, mode: EqualityMode) -> set[tuple[str, str]]:
    resolver = index.partials
    if resolver is None:
        return set()
    literal_parameters = mode in (True, "parameterized", "string-parameter", "raises-less-than")
    first = literal_parameters or mode in (
        "first-assertion",
        "less-than",
        "inequality",
        "dictionary",
    )
    operators: tuple[type[ast.cmpop], ...] = (ast.Eq,)
    if literal_parameters or mode in ("inequality", "dictionary"):
        operators += (ast.Lt, ast.NotEq)
    elif mode == "less-than":
        operators += (ast.Lt,)
    candidates = [
        (sid, node, candidate)
        for sid, node in index.syntax.items()
        if index.nodes[sid].kind == "test"
        and isinstance(node, ast.FunctionDef)
        and "." not in index.nodes[sid].name
        and (
            candidate := comparison_site(
                node,
                first=first,
                operators=operators,
                literal_parameters=literal_parameters,
                allow_strings=mode in (True, "string-parameter", "raises-less-than"),
                allow_raises=mode in (True, "raises-less-than"),
                allow_greater_raises=mode is True,
            )
        )
        is not None
    ]
    if not candidates:
        return set()
    try:
        writes = namespace_writes(resolver)
    except Unproved:
        return set()
    proof = Proof(
        resolver,
        {path for path, source in index.sources.items() if source.parse_status == "unparseable"},
        scalar_factories=mode != "exact-class",
        literal_parameters=literal_parameters,
    )
    proof.writes = writes
    edges = set()
    for sid, fn, (position, site, parameter) in candidates:
        path = index.nodes[sid].path
        try:
            env = proof.module(path)
            test = env.get(fn.name)
            if not isinstance(test, Function):
                continue
            if parameter is not None and (
                test.mode != "pytest"
                or writes & {"mark", "parametrize"}
                or not direct_pytest_import(resolver.binding(path, "pytest", fn.decorator_list[0]))
            ):
                continue
            op, method_name = COMPARISON_METHODS[type(site.ops[0])]
            if method_name == "__gt__" and not direct_pytest_import(
                resolver.binding(path, "pytest", site)
            ):
                continue
            binding = proof.comparison(
                fn,
                env,
                position,
                site,
                method_name,
                dictionary_operands=(literal_parameters or mode == "dictionary")
                and method_name == "__ne__",
                parameter=parameter,
            )
            if binding is None:
                continue
            target, detail = binding
            if target.sid not in index.nodes:
                continue
            index.add_edge(
                sid,
                target.sid,
                "call",
                f"{path}:{site.lineno} calls the bound {method_name} via {op} {detail}",
                SourceLocation(
                    path=path, line=site.lineno, end_line=site.end_lineno or site.lineno
                ),
            )
            edges.add((sid, target.sid))
        except (Unproved, RecursionError):
            continue
    if mode in PREVIOUS_MODES and proof.steps > MAX_PROOF_STEPS:
        # Additional sites or helpers may consume the budget before a previously
        # provable comparison. Preserve that edge with its bounded predecessor.
        edges.update(add_comparison_edges(index, mode=PREVIOUS_MODES[mode]))
    return edges
