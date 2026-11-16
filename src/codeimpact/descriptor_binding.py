"""Source-only exclusion proof for a receiver-only descriptor signature change.

The query follows a closed subset of eager bindings and a zero-argument ordinary
lookup. Unsupported operations decline the proof. It produces no graph edges.
"""

import ast
import copy
from dataclasses import dataclass, field

from codeimpact.arguments import MAX_STEPS
from codeimpact.selection import MAX_DEPTH, References

TRUSTED_IMPORTS = {
    "collections",
    "collections.abc",
    "functools",
    "heapq",
    "inspect",
    "itertools",
    "math",
    "operator",
    "random",
    "threading",
    "time",
    "typing",
    "unittest",
    "warnings",
    "weakref",
}
BUILTINS = {
    "object",
    "tuple",
    "type",
    "str",
    "BaseException",
    "LookupError",
    "property",
    "staticmethod",
    "classmethod",
    "super",
    "iter",
    "next",
    "KeyError",
    "TypeError",
    "ValueError",
    "StopIteration",
    "AttributeError",
    "NotImplementedError",
    "Exception",
}
PLAIN_BASES = {
    "object",
    "tuple",
    "collections.abc.MutableMapping",
    "typing.Protocol",
    "unittest.TestCase",
}


class Unknown(Exception):
    """An unsupported operation prevents exclusion."""


class Stops(Exception):
    def __init__(self, error: str):
        self.error = error


@dataclass(eq=False)
class External:
    name: str


@dataclass(eq=False)
class Function:
    node: ast.FunctionDef
    scope: "Scope"
    defaults: dict[str, "Value"]
    owner: "Class | None" = None


@dataclass(eq=False)
class Class:
    name: str
    bases: tuple["Class | External", ...]
    attrs: dict[str, "Value"] = field(default_factory=dict)
    custom: bool = False


@dataclass(eq=False)
class Instance:
    cls: Class
    attrs: dict[str, "Value"] = field(default_factory=dict)


@dataclass(eq=False)
class Bound:
    function: Function
    receiver: Instance


@dataclass(eq=False)
class Static:
    function: Function


@dataclass(eq=False)
class Metadata:
    attrs: dict[str, "Value"]


@dataclass(eq=False)
class Iterator:
    values: tuple["Value", ...]
    position: int = 0


type Value = (
    str
    | bytes
    | int
    | float
    | bool
    | None
    | External
    | Function
    | Class
    | Instance
    | Bound
    | Static
    | Metadata
    | Iterator
    | tuple["Value", ...]
    | dict[str, "Value"]
)


@dataclass
class Scope:
    values: dict[str, Value]
    parent: "Scope | None" = None
    owner: Class | None = None
    blocked: set[str] = field(default_factory=set)
    class_body: bool = False

    def get(self, name: str) -> Value:
        if name in self.values:
            return self.values[name]
        if name in self.blocked:
            raise Unknown("unbound local")
        if self.parent is not None:
            return self.parent.get(name)
        if name in BUILTINS:
            return External(name)
        raise Unknown("unknown name")

    def attribute(self, name: str) -> str:
        if self.owner and name.startswith("__") and not name.endswith("__"):
            return f"_{self.owner.name.lstrip('_')}{name}"
        return name


def changed_receiver(
    before: References, after: References, path: str
) -> tuple[ast.FunctionDef, ast.FunctionDef] | None:
    old = before.index.syntax.get(f"{path}::<module>")
    new = after.index.syntax.get(f"{path}::<module>")
    if not isinstance(old, ast.Module) or not isinstance(new, ast.Module):
        return None
    if len(old.body) != len(new.body):
        return None
    changed = [
        (a, b) for a, b in zip(old.body, new.body, strict=True) if ast.dump(a) != ast.dump(b)
    ]
    if len(changed) != 1:
        return None
    old_class, new_class = changed[0]
    if not isinstance(old_class, ast.ClassDef) or not isinstance(new_class, ast.ClassDef):
        return None
    if old_class.name != new_class.name:
        return None
    owner = f"{path}::{new_class.name}"
    sid = f"{owner}.__call__"
    a, b = before.index.syntax.get(sid), after.index.syntax.get(sid)
    if not isinstance(a, ast.FunctionDef) or not isinstance(b, ast.FunctionDef):
        return None
    if b.decorator_list or len(b.args.posonlyargs) != 1:
        return None
    if not all(ref.member(owner, "__get__") for ref in (before, after)):
        return None
    if a not in old_class.body or b not in new_class.body:
        return None
    normalized = copy.deepcopy(new_class)
    method = normalized.body[new_class.body.index(b)]
    assert isinstance(method, ast.FunctionDef)
    method.args.args.insert(0, method.args.posonlyargs.pop())
    return (a, b) if ast.dump(old_class) == ast.dump(normalized) else None


class Query:
    def __init__(self, refs: References, target: ast.AST):
        self.refs = refs
        self.target = target
        self.steps = 0
        self.depth = 0
        self.modules: dict[str, Scope] = {}
        self.initializing: dict[str, Scope] = {}
        self.calling: set[ast.AST] = set()
        self.following_wrapper = False
        self.symbols = {node: sid for sid, node in refs.index.syntax.items()}

    def tick(self) -> None:
        self.steps += 1
        if self.steps > MAX_STEPS or self.depth > MAX_DEPTH:
            raise Unknown("descriptor query budget")

    def module(self, name: str) -> Scope:
        self.tick()
        if name in self.initializing:
            raise Unknown("initialization cycle")
        if name in self.modules:
            return self.modules[name]
        path = self.refs.modules.get(name)
        if not path:
            raise Unknown("missing source module")
        node = self.refs.index.syntax[f"{path}::<module>"]
        if (
            not isinstance(node, ast.Module)
            or self.refs.index.sources[path].parse_status != "parsed"
        ):
            raise Unknown("module source unavailable")
        scope = Scope(
            {
                "__name__": name,
                "__package__": name if path.endswith("/__init__.py") else name.rpartition(".")[0],
            }
        )
        self.initializing[name] = scope
        self.depth += 1
        try:
            parent = name.rpartition(".")[0]
            if parent in self.refs.modules and parent not in self.initializing:
                self.module(parent)
            self.block(node.body, scope)
        finally:
            del self.initializing[name]
            self.depth -= 1
        self.modules[name] = scope
        return scope

    def imported(self, module: str, name: str = "") -> Value:
        self.tick()
        if module in self.refs.modules:
            if not name:
                return Metadata(self.module(module).values)
            scope = self.module(module)
            if name not in scope.values and f"{module}.{name}" in self.refs.modules:
                return self.imported(f"{module}.{name}")
            if name in scope.values:
                return scope.values[name]
            raise Unknown("missing module member")
        if module not in TRUSTED_IMPORTS or module.split(".")[0] in self.refs.modules:
            raise Unknown("external import")
        return External(f"{module}.{name}" if name else module)

    def imports(self, node: ast.Import | ast.ImportFrom, scope: Scope) -> None:
        if isinstance(node, ast.Import):
            for alias in node.names:
                value = self.imported(alias.name)
                root, _, suffix = alias.name.partition(".")
                scope.values[alias.asname or root] = (
                    self.imported(root) if not alias.asname and suffix else value
                )
            return
        package = scope.get("__package__")
        if not isinstance(package, str):
            raise Unknown("package")
        parts = package.split(".")
        if node.level > len(parts):
            raise Unknown("relative import")
        prefix = parts[: len(parts) + 1 - node.level] if node.level else []
        module = ".".join(prefix + ([node.module] if node.module else []))
        for alias in node.names:
            if alias.name == "*":
                raise Unknown("star import")
            child = f"{module}.{alias.name}"
            if node.level and not node.module and module in self.initializing:
                # A package may eagerly load one of its own submodules. A back
                # reference to the unfinished package still declines.
                pending = self.initializing[module].values
                if alias.name in pending:
                    value = pending[alias.name]
                elif child in self.refs.modules:
                    value = self.imported(child)
                else:
                    raise Unknown("initialization cycle")
            else:
                value = self.imported(module, alias.name)
            scope.values[alias.asname or alias.name] = value

    def member(self, cls: Class, name: str, depth: int = 0) -> Value:
        self.tick()
        if depth > MAX_DEPTH:
            raise Unknown("base depth")
        if name in cls.attrs:
            return cls.attrs[name]
        for base in cls.bases:
            if (
                isinstance(base, Class)
                and (value := self.member(base, name, depth + 1)) is not None
            ):
                return value
        return None

    def attr(self, value: Value, name: str) -> Value:
        self.tick()
        if isinstance(value, External):
            return External(f"{value.name}.{name}")
        if isinstance(value, Metadata):
            if name in value.attrs:
                return value.attrs[name]
        if isinstance(value, (Class, Instance)):
            cls = value.cls if isinstance(value, Instance) else value
            if cls.custom or len(cls.bases) > 1:
                raise Unknown("custom lookup")
            if isinstance(value, Instance) and name in value.attrs:
                return value.attrs[name]
            member = self.member(cls, name)
            if isinstance(member, Static):
                return member.function
            if isinstance(member, Function):
                return Bound(member, value) if isinstance(value, Instance) else member
            if isinstance(member, Instance):
                return self.lookup_descriptor(value, member)
            if isinstance(member, External) and member.name == "<property>":
                raise Unknown("property lookup may call a getter")
            if member is not None:
                return member
        if isinstance(value, (Function, Instance, Class)) and name == "__wrapped__":
            raise Unknown("unknown wrapper")
        if isinstance(value, dict) and name in {"pop", "values"}:
            return Metadata({"operation": name, "dict": value})
        raise Unknown("unknown attribute")

    def lookup_descriptor(self, receiver: Class | Instance, descriptor: Instance) -> Value:
        cls = receiver.cls if isinstance(receiver, Instance) else receiver
        if cls.bases or cls.custom or descriptor.cls.custom:
            raise Unknown("custom descriptor binding")
        getter = self.member(descriptor.cls, "__get__")
        if not isinstance(getter, Function):
            raise Unknown("unknown descriptor")
        obj = receiver if isinstance(receiver, Instance) else None
        return self.call(getter, [descriptor, obj, cls], {})

    def header(self, node: ast.FunctionDef, scope: Scope) -> Function:
        self.tick()
        if node.type_params:
            raise Unknown("generic function")
        parameters = node.args.posonlyargs + node.args.args
        defaults = {
            p.arg: self.expr(v, scope)
            for p, v in zip(
                parameters[len(parameters) - len(node.args.defaults) :],
                node.args.defaults,
                strict=True,
            )
        }
        defaults.update(
            {
                p.arg: self.expr(v, scope)
                for p, v in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True)
                if v is not None
            }
        )
        for annotation in [
            node.returns,
            *(p.annotation for p in parameters + node.args.kwonlyargs),
            *(p.annotation for p in (node.args.vararg, node.args.kwarg) if p),
        ]:
            self.annotation(annotation, scope)
        return Function(
            node,
            scope.parent if scope.class_body and scope.parent is not None else scope,
            defaults,
            scope.owner,
        )

    def annotation(self, node: ast.AST | None, scope: Scope) -> None:
        """Check a passive type expression without invoking annotation hooks."""
        self.tick()
        if node is None or isinstance(node, ast.Constant):
            return
        if isinstance(node, (ast.Name, ast.Attribute)):
            value = self.expr(node, scope)
            if isinstance(value, (Class, External)):
                return
        elif isinstance(node, (ast.Tuple, ast.List)):
            for item in node.elts:
                self.annotation(item, scope)
            return
        elif isinstance(node, ast.Subscript):
            base = self.expr(node.value, scope)
            if isinstance(base, External) and base.name in {
                "type",
                "collections.abc.Iterable",
                "collections.abc.Container",
                "collections.abc.Callable",
                "typing.Callable",
            }:
                self.annotation(node.slice, scope)
                return
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            # Only known standard-library aliases can implement the union here.
            if all(isinstance(x, ast.Subscript) for x in (node.left, node.right)):
                self.annotation(node.left, scope)
                self.annotation(node.right, scope)
                return
        raise Unknown("effectful or unsupported annotation")

    def definition(self, node: ast.FunctionDef, scope: Scope) -> None:
        if any(
            isinstance(dec, ast.Name) and dec.id == "classmethod" for dec in node.decorator_list
        ):
            raise Unknown("classmethod decorator")
        decorators = [self.expr(dec, scope) for dec in node.decorator_list]
        value: Value = self.header(node, scope)
        for decorator in reversed(decorators):
            value = self.invoke(decorator, [value], {})
        scope.values[scope.attribute(node.name)] = value

    def class_definition(self, node: ast.ClassDef, scope: Scope) -> None:
        if node.keywords or node.type_params or len(node.bases) > 2:
            raise Unknown("custom class creation")
        if node.decorator_list:
            decorators = [self.expr(dec, scope) for dec in node.decorator_list]
            if (
                node.bases
                or [d.name for d in decorators if isinstance(d, External)]
                != ["functools.total_ordering"]
                or len(decorators) != 1
            ):
                raise Unknown("custom class decorator")
        bases = []
        for expr in node.bases:
            base = self.expr(expr, scope)
            if not isinstance(base, Class) and not (
                isinstance(base, External) and base.name in PLAIN_BASES
            ):
                raise Unknown("unknown base")
            if isinstance(base, Class) and self.member(base, "__init_subclass__") is not None:
                raise Unknown("effectful subclass hook")
            bases.append(base)
        cls = Class(node.name, tuple(bases))
        cls.custom = any(isinstance(base, Class) and base.custom for base in bases)
        lexical = scope.parent if scope.class_body else scope
        body = Scope(cls.attrs, lexical, cls, class_body=True)
        self.block(node.body, body)
        for special in (
            "__getattribute__",
            "__getattr__",
            "__setattr__",
            "__new__",
            "__set__",
            "__delete__",
            "__del__",
        ):
            if special in cls.attrs:
                cls.custom = True
        if "__slots__" in cls.attrs or node.decorator_list:
            cls.custom = True
        for name, value in list(cls.attrs.items()):
            if isinstance(value, Instance) and (hook := self.member(value.cls, "__set_name__")):
                if not isinstance(hook, Function):
                    raise Unknown("unknown descriptor registration")
                self.call(hook, [value, cls, name], {})
        scope.values[scope.attribute(node.name)] = cls

    def truth(self, value: Value) -> bool:
        if value is None or isinstance(value, (bool, int, float, str, bytes, tuple, dict)):
            return bool(value)
        raise Unknown("nonliteral condition")

    def expr(self, node: ast.AST | None, scope: Scope) -> Value:
        self.tick()
        if node is None:
            return None
        if isinstance(node, ast.Constant) and (
            node.value is None or isinstance(node.value, (bool, int, float, str, bytes))
        ):
            return node.value
        if isinstance(node, ast.Name):
            return scope.get(scope.attribute(node.id))
        if isinstance(node, (ast.Tuple, ast.List)):
            return tuple(self.expr(v, scope) for v in node.elts)
        if isinstance(node, ast.Dict) and not node.keys:
            return {}
        if isinstance(node, ast.Attribute):
            return self.attr(self.expr(node.value, scope), scope.attribute(node.attr))
        if isinstance(node, ast.Lambda):
            # A factory may store callbacks. Calling this opaque value declines.
            if (
                node.args.defaults
                or any(node.args.kw_defaults)
                or any(isinstance(n, ast.NamedExpr) for n in ast.walk(node.body))
            ):
                raise Unknown("effectful lambda header")
            return External("<lambda>")
        if isinstance(node, ast.Compare) and len(node.ops) == len(node.comparators) == 1:
            a, b = self.expr(node.left, scope), self.expr(node.comparators[0], scope)
            if isinstance(node.ops[0], (ast.Is, ast.IsNot)):
                if a is None or b is None or a is b:
                    return (a is b) == isinstance(node.ops[0], ast.Is)
                raise Unknown("identity")
            if isinstance(node.ops[0], ast.NotEq) and isinstance(a, str) and isinstance(b, str):
                return a != b
        if isinstance(node, ast.BoolOp):
            result = self.expr(node.values[0], scope)
            for part in node.values[1:]:
                if self.truth(result) == isinstance(node.op, ast.Or):
                    break
                result = self.expr(part, scope)
            return result
        if isinstance(node, ast.IfExp):
            return self.expr(
                node.body if self.truth(self.expr(node.test, scope)) else node.orelse, scope
            )
        if isinstance(node, ast.Call):
            callee = self.expr(node.func, scope)
            args: list[Value] = []
            kwargs: dict[str, Value] = {}
            for arg in node.args:
                if isinstance(arg, ast.Starred):
                    value = self.expr(arg.value, scope)
                    if not isinstance(value, tuple):
                        raise Unknown("positional expansion")
                    args.extend(value)
                else:
                    args.append(self.expr(arg, scope))
            for kw in node.keywords:
                val = self.expr(kw.value, scope)
                if kw.arg is None:
                    if not isinstance(val, dict) or kwargs.keys() & val.keys():
                        raise Unknown("keyword expansion")
                    kwargs.update(val)
                elif kw.arg not in kwargs:
                    kwargs[kw.arg] = val
                else:
                    raise Unknown("duplicate keyword")
            if isinstance(callee, External) and callee.name == "super":
                if args or kwargs or not scope.owner or len(scope.owner.bases) != 1:
                    raise Unknown("custom super")
                base = scope.owner.bases[0]
                receiver = next(iter(scope.values.values()), None)
                if isinstance(base, Class) and isinstance(receiver, Instance):
                    return Metadata(
                        {
                            name: Bound(value, receiver)
                            for name, value in base.attrs.items()
                            if isinstance(value, Function) and name == "__init__"
                        }
                    )
                raise Unknown("unknown super receiver")
            return self.invoke(callee, args, kwargs)
        raise Unknown(type(node).__name__)

    def bind(self, target: ast.AST, value: Value, scope: Scope) -> None:
        self.tick()
        if isinstance(target, ast.Name) and target.id not in {
            "__builtins__",
            "__name__",
            "__package__",
        }:
            scope.values[scope.attribute(target.id)] = value
            return
        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
            obj = scope.get(target.value.id)
            if (
                isinstance(obj, Instance)
                and not obj.cls.custom
                and target.attr
                not in {
                    "__class__",
                    "__dict__",
                    "__wrapped__",
                    "__signature__",
                    "__call__",
                    "__get__",
                }
            ):
                name = scope.attribute(target.attr)
                if self.member(obj.cls, name) is not None:
                    raise Unknown("attribute may be a descriptor")
                obj.attrs[name] = value
                return
        raise Unknown("mutation or destructuring")

    def block(self, statements: list[ast.stmt], scope: Scope) -> tuple[bool, Value]:
        for stmt in statements:
            self.tick()
            if isinstance(stmt, ast.FunctionDef):
                self.definition(stmt, scope)
            elif isinstance(stmt, ast.ClassDef):
                self.class_definition(stmt, scope)
            elif isinstance(stmt, (ast.Import, ast.ImportFrom)):
                self.imports(stmt, scope)
            elif isinstance(stmt, ast.Assign):
                value = self.expr(stmt.value, scope)
                for target in stmt.targets:
                    self.bind(target, value, scope)
            elif (
                isinstance(stmt, ast.AnnAssign)
                and stmt.value is None
                and isinstance(stmt.target, ast.Name)
            ):
                if scope.parent is None or scope.class_body:
                    self.annotation(stmt.annotation, scope)
            elif isinstance(stmt, ast.Expr):
                self.expr(stmt.value, scope)
            elif isinstance(stmt, ast.Return):
                return True, self.expr(stmt.value, scope)
            elif isinstance(stmt, ast.Pass):
                continue
            elif isinstance(stmt, ast.If):
                done, value = self.block(
                    stmt.body if self.truth(self.expr(stmt.test, scope)) else stmt.orelse, scope
                )
                if done:
                    return done, value
            elif isinstance(stmt, ast.Try) and not stmt.finalbody:
                try:
                    done, value = self.block(stmt.body, scope)
                except Stops as error:
                    done, value = self.handle(stmt.handlers, error, scope)
                else:
                    if not done:
                        done, value = self.block(stmt.orelse, scope)
                if done:
                    return done, value
            elif isinstance(stmt, ast.Raise):
                raised = self.expr(stmt.exc, scope)
                if not isinstance(raised, External) or not raised.name.startswith("error:"):
                    raise Unknown("unknown exception")
                self.expr(stmt.cause, scope)
                raise Stops(raised.name.removeprefix("error:"))

            else:
                raise Unknown(type(stmt).__name__)
        return False, None

    def handle(
        self, handlers: list[ast.ExceptHandler], error: Stops, scope: Scope
    ) -> tuple[bool, Value]:
        for handler in handlers:
            if handler.name or handler.type is None:
                raise Unknown("exception binding")
            types = self.expr(handler.type, scope)
            if not isinstance(types, tuple):
                types = (types,)
            exceptions = {
                "BaseException",
                "Exception",
                "LookupError",
                "KeyError",
                "TypeError",
                "ValueError",
                "StopIteration",
            }
            if not all(isinstance(t, External) and t.name in exceptions for t in types):
                raise Unknown("unknown exception type")
            matching = {error.error, "Exception", "BaseException"}
            if error.error == "KeyError":
                matching.add("LookupError")
            if any(isinstance(t, External) and t.name in matching for t in types):
                return self.block(handler.body, scope)
        raise error

    def call(self, fn: Function, args: list[Value], kwargs: dict[str, Value]) -> Value:
        self.tick()
        node = fn.node
        if node is self.target or node in self.calling:
            raise Unknown("changed callable or cycle")
        a = node.args
        params = a.posonlyargs + a.args
        if len(args) > len(params) and not a.vararg:
            raise Unknown("extra args")
        values: dict[str, Value] = {}
        supplied = dict(kwargs)
        for i, p in enumerate(params + a.kwonlyargs):
            if i < min(len(args), len(params)):
                if p.arg in supplied and p not in a.posonlyargs:
                    raise Unknown("duplicate argument")
                values[p.arg] = args[i]
            elif p.arg in supplied and p not in a.posonlyargs:
                values[p.arg] = supplied.pop(p.arg)
            elif p.arg in fn.defaults:
                values[p.arg] = fn.defaults[p.arg]
            else:
                raise Unknown("missing argument")
        if a.vararg:
            values[a.vararg.arg] = tuple(args[len(params) :])
        if a.kwarg:
            values[a.kwarg.arg] = supplied
        elif supplied:
            raise Unknown("extra keywords")
        sid = self.symbols.get(node)
        if sid is None:
            raise Unknown("unindexed source function")
        local = self.refs.index.local_bindings.get(sid)
        scope = Scope(
            values, fn.scope, fn.owner, self.refs.blocked[sid] | (local.bound if local else set())
        )
        self.calling.add(node)
        self.depth += 1
        try:
            return self.block(node.body, scope)[1]
        finally:
            self.depth -= 1
            self.calling.remove(node)

    def invoke(self, fn: Value, args: list[Value], kwargs: dict[str, Value]) -> Value:
        self.tick()
        if isinstance(fn, Bound):
            return self.call(fn.function, [fn.receiver, *args], kwargs)
        if isinstance(fn, Function):
            return self.call(fn, args, kwargs)
        if isinstance(fn, Class):
            if fn.custom or len(fn.bases) > 1 or any(isinstance(b, External) for b in fn.bases):
                raise Unknown("custom construction")
            obj = Instance(fn)
            if isinstance(init := self.member(fn, "__init__"), Function):
                if self.call(init, [obj, *args], kwargs) is not None:
                    raise Unknown("non-None initializer result")
            elif init is not None or args or kwargs:
                raise Unknown("unknown initializer")
            return obj
        if isinstance(fn, Instance):
            method = self.member(fn.cls, "__call__")
            if isinstance(method, Function):
                return self.call(method, [fn, *args], kwargs)
        if isinstance(fn, Metadata):
            data = fn.attrs.get("dict")
            if isinstance(data, dict) and not kwargs:
                if (
                    fn.attrs.get("operation") == "pop"
                    and len(args) == 1
                    and isinstance(args[0], str)
                ):
                    if args[0] not in data:
                        raise Stops("KeyError")
                    return data.pop(args[0])
                if fn.attrs.get("operation") == "values" and not args:
                    return tuple(data.values())
        if isinstance(fn, External) and not kwargs:
            name = fn.name
            if name == "functools.update_wrapper" and len(args) == 2:
                wrapped = args[1]
                receiver = args[0]
                metadata = (
                    "__dict__",
                    "__wrapped__",
                    "__annotations__",
                    "__module__",
                    "__name__",
                    "__qualname__",
                    "__doc__",
                    "__type_params__",
                    "__signature__",
                )
                if (
                    isinstance(receiver, Instance)
                    and not receiver.cls.custom
                    and isinstance(wrapped, Function)
                    and wrapped.node is not self.target
                    and all(self.member(receiver.cls, name) is None for name in metadata)
                ):
                    receiver.attrs["__wrapped__"] = wrapped
                    return args[0]
            if name == "staticmethod" and len(args) == 1 and isinstance(args[0], Function):
                return Static(args[0])
            if name == "property" and len(args) == 1 and isinstance(args[0], Function):
                return External("<property>")
            if name in {"object", "weakref.WeakKeyDictionary"} and not args:
                return External(f"<{name}>")
            if (
                name == "collections.namedtuple"
                and len(args) == 2
                and isinstance(args[0], str)
                and (isinstance(args[1], tuple) and all(isinstance(v, str) for v in args[1]))
            ):
                return External("<namedtuple>")
            if (
                name == "inspect.signature"
                and self.following_wrapper
                and len(args) == 1
                and isinstance(args[0], Instance)
            ):
                wrapper = args[0]
                wrapped = wrapper.attrs.get("__wrapped__")
                if (
                    isinstance(wrapped, Function)
                    and "__signature__" not in wrapper.attrs
                    and (self.member(wrapper.cls, "__signature__") is None)
                ):
                    # Model only the first positional parameter of a plain wrapped function.
                    params = wrapped.node.args.posonlyargs + wrapped.node.args.args
                    kind = External("POSITIONAL_OR_KEYWORD")
                    values: dict[str, Value] = {}
                    if params:
                        p = params[0]
                        values[p.arg] = Metadata(
                            {
                                "kind": External("POSITIONAL_ONLY")
                                if wrapped.node.args.posonlyargs
                                else kind,
                                "POSITIONAL_OR_KEYWORD": kind,
                                "name": p.arg,
                            }
                        )
                    return Metadata({"parameters": values})
            if name == "iter" and len(args) == 1 and isinstance(args[0], tuple):
                return Iterator(args[0])
            if name == "next" and len(args) == 1 and isinstance(iterator := args[0], Iterator):
                if iterator.position == len(iterator.values):
                    raise Stops("StopIteration")
                value = iterator.values[iterator.position]
                iterator.position += 1
                return value
            if name in {"KeyError", "TypeError", "ValueError", "StopIteration"} and all(
                isinstance(v, (str, bytes, int, float, bool)) or v is None for v in args
            ):
                return External(f"error:{name}")
        raise Unknown("unresolved invocation")

    def excludes(self, sid: str) -> bool:
        node = self.refs.index.syntax[sid]
        if not isinstance(node, ast.FunctionDef) or node.decorator_list or not node.body:
            return False
        owner = self.refs.owner(sid)
        if (owner and self.refs.class_children[owner]) or (
            node.args.vararg or node.args.kwarg or node.args.kwonlyargs or node.args.posonlyargs
        ):
            return False
        # One direct descriptor invocation, optionally in the standard
        # assertRaises context and preceded by simple receiver bindings.
        stmt = node.body[-1]
        assertion = None
        if isinstance(stmt, ast.With) and owner:
            if len(stmt.items) != 1 or len(stmt.body) != 1 or stmt.items[0].optional_vars:
                return False
            assertion = stmt.items[0].context_expr
            stmt = stmt.body[0]
            if [p.arg for p in node.args.args] != ["self"]:
                return False
        elif node.args.args or owner:
            return False
        if (
            not isinstance(stmt, ast.Expr)
            or not isinstance(stmt.value, ast.Call)
            or not isinstance(stmt.value.func, ast.Attribute)
            or stmt.value.args
            or stmt.value.keywords
        ):
            return False
        access = stmt.value.func
        path = self.refs.index.nodes[sid].path
        module = self.refs.index.nodes[f"{path}::<module>"].name
        try:
            modules = [n.name for n in self.refs.index.nodes.values() if n.kind == "module"]
            if len(set(modules)) != len(modules):
                return False
            scope = self.module(module)
            if owner and not self.assertion_context(scope, owner, assertion):
                return False
            if {"setUpModule", "tearDownModule", "load_tests"} & scope.values.keys():
                return False
            local = Scope({}, scope, blocked=self.refs.blocked[sid])
            for binding in node.body[:-1]:
                if (
                    not isinstance(binding, ast.Assign)
                    or len(binding.targets) != 1
                    or not isinstance(binding.targets[0], ast.Name)
                    or binding.targets[0].id in local.values
                    or not isinstance(binding.value, (ast.Name, ast.Call))
                ):
                    return False
                value = self.expr(binding.value, local)
                if not isinstance(value, (Class, Instance)):
                    return False
                self.bind(binding.targets[0], value, local)
            receiver = self.expr(access.value, local)
            if not isinstance(receiver, (Class, Instance)):
                return False
            cls = receiver.cls if isinstance(receiver, Instance) else receiver
            if isinstance(receiver, Instance) and access.attr in receiver.attrs:
                return False
            descriptor = self.member(cls, access.attr)
            if not isinstance(descriptor, Instance):
                return False
            wrapped = self.lookup_descriptor(receiver, descriptor)
            if not isinstance(wrapped, (Function, Instance, Bound)) or wrapped is descriptor:
                return False
            self.following_wrapper = True
            try:
                result = self.invoke(wrapped, [], {})
            except Stops as error:
                return error.error == "TypeError"
            return result is None or isinstance(result, (str, int, float, bool, bytes))
        except (Stops, Unknown, RecursionError):
            return False

    @staticmethod
    def assertion_context(scope: Scope, owner: str, call: ast.expr | None) -> bool:
        cls = scope.get(owner.split("::")[1])
        if not isinstance(cls, Class) or cls.custom or len(cls.bases) != 1:
            return False
        base = cls.bases[0]
        if not isinstance(base, External) or base.name != "unittest.TestCase":
            return False
        hooks = {
            "assertRaises",
            "__init__",
            "setUp",
            "tearDown",
            "setUpClass",
            "tearDownClass",
            "run",
            "defaultTestResult",
        }
        if hooks & cls.attrs.keys():
            return False
        return (
            isinstance(call, ast.Call)
            and ast.unparse(call.func) == "self.assertRaises"
            and not call.keywords
            and len(call.args) == 1
            and isinstance(call.args[0], ast.Name)
            and call.args[0].id == "TypeError"
            and isinstance(error := scope.get("TypeError"), External)
            and error.name == "TypeError"
        )


class DescriptorFallback:
    def __init__(self, before: References, after: References, paths: set[str]):
        self.before = before
        self.after = after
        self.changes = {
            path: targets
            for path in sorted(paths)
            if (targets := changed_receiver(before, after, path)) is not None
        }

    def allows(self, sid: str, path: str) -> bool:
        targets = self.changes.get(path)
        if targets is None:
            return True
        return not all(
            sid in refs.index.syntax and Query(refs, target).excludes(sid)
            for refs, target in zip((self.before, self.after), targets, strict=True)
        )
