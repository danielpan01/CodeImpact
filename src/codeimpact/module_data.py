"""Negative dependency proof for edits confined to existing literal rule tables."""

import ast
import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from codeimpact.discovery import is_test_file
from codeimpact.selection import MAX_DEPTH

if TYPE_CHECKING:
    from codeimpact.analyzer import Index

MAX_STEPS = 12000
MAX_LITERAL_NODES = 4000
SCALAR = (str, bytes, int, float, bool, type(None))
DATA_METHODS = {
    "upper",
    "lower",
    "capitalize",
    "replace",
    "strip",
    "split",
    "join",
    "format",
    "encode",
    "decode",
    "group",
    "get",
    "items",
    "values",
    "keys",
}
MUTATORS = {"insert", "append", "add"}
BUILTINS = {"str", "bytes", "int", "bool", "float", "abs", "len", "tuple", "list", "set", "dict"}
EXTERNAL_CALLS = {"re.sub", "re.search", "re.escape", "unicodedata.normalize"}
EXTERNAL_MODULES = {"re", "unicodedata", "pytest"}
MODULE_HOOKS = {
    "__getattr__",
    "__dir__",
    "setup_module",
    "teardown_module",
    "setup_function",
    "teardown_function",
    "setUpModule",
    "tearDownModule",
    "load_tests",
}


class Unknown(Exception):
    """Incomplete source evidence retains the contribution."""


class ReadsTable(Exception):
    """The test reaches the edited binding."""


@dataclass(frozen=True)
class Data:
    table: tuple[str, str] | None = None


DATA = Data()


@dataclass
class Scope:
    path: str
    values: dict[str, "Value"] = field(default_factory=dict)
    parent: "Scope | None" = None


@dataclass
class Function:
    node: ast.FunctionDef | ast.Lambda
    scope: Scope


@dataclass(frozen=True)
class Module:
    path: str


@dataclass(frozen=True)
class External:
    name: str


type Value = Data | Function | Module | External


def literal(node: ast.AST) -> bool:
    nodes = list(ast.walk(node))
    return (
        len(nodes) <= MAX_LITERAL_NODES
        and all(
            isinstance(n, (ast.List, ast.Tuple, ast.Set, ast.Dict, ast.Load))
            or isinstance(n, ast.Constant)
            and type(n.value) in SCALAR
            for n in nodes
        )
        and not any(isinstance(n, ast.Dict) and None in n.keys for n in nodes)
    )


def table(node: ast.AST) -> bool:
    return (
        isinstance(node, (ast.List, ast.Tuple))
        and bool(node.elts)
        and all(isinstance(row, (ast.List, ast.Tuple)) and bool(row.elts) for row in node.elts)
        and literal(node)
    )


def changed_tables(before: "Index", after: "Index", path: str) -> set[str]:
    old, new = (i.syntax.get(f"{path}::<module>") for i in (before, after))
    if not isinstance(old, ast.Module) or not isinstance(new, ast.Module):
        return set()
    if len(old.body) != len(new.body):
        return set()
    names = set()
    normalized = copy.deepcopy(new)
    for a, b, replacement in zip(old.body, new.body, normalized.body, strict=True):
        if ast.dump(a) == ast.dump(b):
            continue
        if not (
            isinstance(a, ast.Assign)
            and isinstance(b, ast.Assign)
            and isinstance(replacement, ast.Assign)
            and len(a.targets) == len(b.targets) == 1
            and isinstance(a.targets[0], ast.Name)
            and isinstance(b.targets[0], ast.Name)
            and a.targets[0].id == b.targets[0].id
            and type(a.value) is type(b.value)
            and table(a.value)
            and table(b.value)
        ):
            return set()
        names.add(a.targets[0].id)
        replacement.value = a.value
    if not names or ast.dump(old) != ast.dump(normalized):
        return set()
    for name in names:
        # Existing binding, exactly once, without a global/nonlocal replacement.
        for tree in (old, new):
            if sum(
                isinstance(n, ast.Name) and n.id == name and isinstance(n.ctx, ast.Store)
                for n in ast.walk(tree)
            ) != 1 or any(
                isinstance(n, (ast.Global, ast.Nonlocal)) and name in n.names
                for n in ast.walk(tree)
            ):
                return set()
    return names


def deferred_body_edit(before: "Index", after: "Index", path: str) -> str | None:
    """Recognize one existing top-level function with an unchanged definition header."""
    if is_test_file(path):
        return None
    old, new = (i.syntax.get(f"{path}::<module>") for i in (before, after))
    if not isinstance(old, ast.Module) or not isinstance(new, ast.Module):
        return None
    if len(old.body) != len(new.body):
        return None
    edited = None
    for a, b in zip(old.body, new.body, strict=True):
        if ast.dump(a) == ast.dump(b):
            continue
        if (
            edited is not None
            or not isinstance(a, ast.FunctionDef)
            or not isinstance(b, ast.FunctionDef)
            or a.decorator_list
            or b.decorator_list
        ):
            return None
        old_header, new_header = copy.copy(a), copy.copy(b)
        old_header.body = new_header.body = []
        if ast.dump(old_header) != ast.dump(new_header):
            return None
        edited = a.name
    return edited


def qualified_mutation(stmt: ast.stmt, method: str) -> tuple[ast.Attribute, ast.expr] | None:
    match stmt:
        case ast.Expr(
            value=ast.Call(
                func=ast.Attribute(value=ast.Attribute(value=ast.Name()) as receiver, attr=name),
                args=[key],
                keywords=[],
            )
        ) if name == method:
            return receiver, key
    return None


class Query:
    def __init__(
        self,
        index: "Index",
        path: str,
        names: set[str],
        safe_modules: set[str],
        body_edits: dict[str, str],
    ):
        self.index = index
        self.safe_modules = safe_modules
        self.body_edits = body_edits
        self.used_body_edit = False
        self.auditing_set_cleanup = False
        self.empty_guard_caller: ast.FunctionDef | None = None
        self.changed = {(path, name) for name in names}
        self.modules: dict[str, Scope] = {}
        self.initializing: set[str] = set()
        self.steps = 0
        self.depth = 0
        self.stack: set[tuple[ast.AST, bool]] = set()
        self.parameter_tables: set[tuple[str, str]] = set()
        self.mutated_tables: set[tuple[str, str]] = set()
        self.parameter_references: set[ast.expr] = set()
        self.other_collection = False
        resolver = index.partials
        if resolver is None:
            raise Unknown("source resolver unavailable")
        self.resolver = resolver

    def tick(self) -> None:
        self.steps += 1
        if self.steps > MAX_STEPS or self.depth > MAX_DEPTH:
            raise Unknown("table proof budget")

    def touch(self, value: Value, eager: bool) -> Value:
        if not eager and isinstance(value, Data) and value.table in self.changed:
            raise ReadsTable()
        return value

    def lookup(self, name: str, scope: Scope, eager: bool) -> Value:
        current: Scope | None = scope
        while current is not None:
            if name in current.values:
                return self.touch(current.values[name], eager)
            current = current.parent
        if name in BUILTINS:
            return External(name)
        raise Unknown("unknown name")

    def module(self, path: str) -> Scope:
        self.tick()
        if path in self.body_edits:
            self.used_body_edit = True
        elif path not in self.safe_modules:
            raise Unknown("reachable module has another kind of change")
        if path in self.initializing:
            raise Unknown("eager cycle")
        if path in self.modules:
            return self.modules[path]
        tree = self.index.syntax.get(f"{path}::<module>")
        if not isinstance(tree, ast.Module) or self.index.sources[path].parse_status != "parsed":
            raise Unknown("unavailable source")
        scope = Scope(path)
        self.initializing.add(path)
        self.depth += 1
        try:
            name = self.index.nodes[f"{path}::<module>"].name
            parent = self.resolver.modules.get(name.rpartition(".")[0])
            if parent and parent not in self.initializing:
                self.module(parent)
            for stmt in tree.body:
                self.tick()
                if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                    self.imports(stmt, scope)
                elif isinstance(stmt, ast.FunctionDef):
                    if (
                        stmt.name in MODULE_HOOKS
                        or stmt.name.startswith("pytest_")
                        or stmt.name in scope.values
                    ):
                        raise Unknown("custom lifecycle or duplicate definition")
                    self.header(stmt, scope, True)
                    scope.values[stmt.name] = Function(stmt, scope)
                elif (
                    isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                ):
                    key = stmt.targets[0].id
                    if (
                        key in scope.values
                        or key.startswith("pytest")
                        or key.startswith("__")
                        and key != "__version__"
                    ):
                        raise Unknown("rebound or special module binding")
                    if not literal(stmt.value):
                        raise Unknown("nonliteral global data")
                    scope.values[key] = Data((path, key))
                elif isinstance(stmt, ast.Expr):
                    self.data(self.expr(stmt.value, scope, True))
                else:
                    raise Unknown("effectful module initialization")
            self.modules[path] = scope
            return scope
        finally:
            self.depth -= 1
            self.initializing.remove(path)

    def imports(self, node: ast.Import | ast.ImportFrom, scope: Scope) -> None:
        if any(a.asname or a.name == "*" for a in node.names):
            raise Unknown("alias or wildcard")
        bindings, imports = self.resolver.decode(node, scope.path, self.resolver.modules)
        for module in imports:
            if module in self.resolver.modules:
                self.module(self.resolver.modules[module])
            elif module not in EXTERNAL_MODULES or module.split(".")[0] in self.resolver.modules:
                raise Unknown("unknown import effects")
        for name, target in bindings:
            if name in scope.values:
                raise Unknown("competing import")
            if isinstance(node, ast.Import):
                path = self.resolver.modules.get(target)
                value: Value = Module(path) if path else External(target)
            else:
                module, _, member = target.rpartition(".")
                path = self.resolver.modules.get(module)
                if not path:
                    raise Unknown("unsupported external named import")
                imported = self.module(path)
                value = imported.values.get(member, External("<missing>"))
                if (
                    isinstance(value, (Module, External))
                    or isinstance(value, Function)
                    and (value.scope.path != path)
                ):
                    raise Unknown("re-exported binding")
            scope.values[name] = value

    @staticmethod
    def data(value: Value) -> Data:
        if not isinstance(value, Data):
            raise Unknown("callable or namespace escape")
        return value

    def reference(self, node: ast.AST, scope: Scope) -> Value:
        """Inspect a bare registered reference without consuming its contents.

        Only definition metadata and an audited initialization mutator receiver
        use this exception. All executable expressions still inspect data reads.
        """
        self.tick()
        if isinstance(node, ast.Name):
            return self.lookup(node.id, scope, True)
        if isinstance(node, ast.Attribute):
            obj = self.expr(node.value, scope, True)
            if isinstance(obj, Module):
                value = self.module(obj.path).values.get(node.attr)
                if value is not None:
                    return value
        return self.expr(node, scope, True)

    def header(self, fn: ast.FunctionDef, scope: Scope, eager: bool) -> None:
        args = fn.args
        if fn.type_params:
            raise Unknown("generic callable")
        for n in [fn.returns, *(p.annotation for p in ast.walk(args) if isinstance(p, ast.arg))]:
            if n is not None and not isinstance(n, ast.Constant):
                raise Unknown("active annotation")
        for default in [*args.defaults, *args.kw_defaults]:
            if default is not None:
                self.data(
                    self.reference(default, scope) if eager else self.expr(default, scope, False)
                )
        for decorator in fn.decorator_list:
            if not (
                fn.name.startswith("test_")
                and isinstance(decorator, ast.Call)
                and len(decorator.args) == 2
                and not decorator.keywords
                and isinstance(decorator.args[0], (ast.Tuple, ast.List))
                and all(
                    isinstance(x, ast.Constant) and isinstance(x.value, str)
                    for x in decorator.args[0].elts
                )
                and isinstance(value := self.expr(decorator.func, scope, eager), External)
                and value.name == "pytest.mark.parametrize"
            ):
                raise Unknown("unknown decorator")
            values = decorator.args[1]
            data = self.data(
                self.reference(values, scope) if eager else self.expr(values, scope, False)
            )
            expected = {p.arg for p in args.args}
            names = [x.value for x in decorator.args[0].elts if isinstance(x, ast.Constant)]
            if set(names) != expected or len(names) != len(expected):
                raise Unknown("unproved fixture argument")
            self.parameters(values, data, len(names))
        if fn.decorator_list and (
            len(fn.decorator_list) != 1
            or args.kwonlyargs
            or args.posonlyargs
            or args.vararg
            or args.kwarg
            or args.defaults
        ):
            self.other_collection = True

    def parameters(self, node: ast.expr, data: Data, arity: int) -> None:
        """Audit collection effects for this contribution's changed parameter data."""
        if data.table not in self.changed:
            return
        if isinstance(node, ast.Name):
            self.parameter_references.add(node)
        if data.table is not None:
            if data.table in self.mutated_tables:
                raise Unknown("mutated parameter data")
            self.parameter_tables.add(data.table)
            path, name = data.table
            tree = self.index.syntax.get(f"{path}::<module>")
            if not isinstance(tree, ast.Module):
                raise Unknown("unavailable parameter binding")
            values = [
                stmt.value
                for stmt in tree.body
                if isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
                and stmt.targets[0].id == name
            ]
            if len(values) != 1:
                raise Unknown("ambiguous parameter binding")
            node = values[0]
        if not (
            isinstance(node, (ast.List, ast.Tuple))
            and literal(node)
            and all(
                isinstance(row, (ast.List, ast.Tuple)) and len(row.elts) == arity
                for row in node.elts
            )
        ):
            raise Unknown("unproved parameter row shape")

    def function(
        self, fn: Function, args: list[Value], kwargs: dict[str, Value], eager: bool
    ) -> Data:
        self.tick()
        node = fn.node
        if (
            (eager or self.auditing_set_cleanup)
            and isinstance(node, ast.FunctionDef)
            and self.body_edits.get(fn.scope.path) == node.name
        ):
            raise Unknown("initializer or guarded assertion can invoke an edited function")
        for v in [*args, *kwargs.values()]:
            self.data(v)
        if (node, eager) in self.stack:
            if eager:
                raise Unknown("eager recursion")
            # Scan a recursive body once. All reads and calls are visited without
            # branch pruning and every incoming value has already been inspected.
            return DATA
        a = node.args
        params = a.posonlyargs + a.args
        if a.vararg or a.kwarg or len(args) > len(params):
            raise Unknown("variadic or excess arguments")
        local = Scope(fn.scope.path, parent=fn.scope)
        supplied = dict(kwargs)
        defaults = dict(
            zip([p.arg for p in params[len(params) - len(a.defaults) :]], a.defaults, strict=True)
        )
        for i, param in enumerate(params):
            if i < len(args):
                if param.arg in supplied:
                    raise Unknown("duplicate argument")
                value = args[i]
            elif param.arg in supplied and param not in a.posonlyargs:
                value = supplied.pop(param.arg)
            elif param.arg in defaults:
                value = self.expr(defaults[param.arg], fn.scope, eager)
            else:
                raise Unknown("missing argument")
            local.values[param.arg] = self.data(value)
        for param, default in zip(a.kwonlyargs, a.kw_defaults, strict=True):
            if param.arg in supplied:
                value = supplied.pop(param.arg)
            elif default is not None:
                value = self.expr(default, fn.scope, eager)
            else:
                raise Unknown("missing keyword")
            local.values[param.arg] = self.data(value)
        if supplied:
            raise Unknown("extra keywords")
        self.stack.add((node, eager))
        self.depth += 1
        try:
            if isinstance(node, ast.FunctionDef):
                self.header(node, fn.scope, eager)
                self.block(node.body, local, eager)
            else:
                self.data(self.expr(node.body, local, eager))
            return DATA
        finally:
            self.depth -= 1
            self.stack.remove((node, eager))

    def expr(self, node: ast.AST, scope: Scope, eager: bool) -> Value:
        self.tick()
        if isinstance(node, ast.Constant) and type(node.value) in SCALAR:
            return DATA
        if isinstance(node, ast.Name):
            return self.lookup(node.id, scope, False)
        if isinstance(node, ast.Attribute):
            obj = self.expr(node.value, scope, eager)
            if isinstance(obj, Module):
                module = self.module(obj.path)
                value = module.values.get(node.attr)
                if value is None:
                    raise Unknown("unknown module member")
                return self.touch(value, False)
            if isinstance(obj, External):
                return External(obj.name + "." + node.attr)
            raise Unknown("escaped bound data method")
        if isinstance(node, ast.Call):
            args = [self.expr(arg, scope, eager) for arg in node.args]
            if any(kw.arg is None for kw in node.keywords):
                raise Unknown("keyword expansion")
            kwargs = {kw.arg: self.expr(kw.value, scope, eager) for kw in node.keywords if kw.arg}
            if len(kwargs) != len(node.keywords):
                raise Unknown("duplicate keywords")
            if isinstance(node.func, ast.Attribute):
                obj = (
                    self.reference(node.func.value, scope)
                    if eager and node.func.attr in MUTATORS
                    else self.expr(node.func.value, scope, eager)
                )
                if isinstance(obj, Data):
                    if node.func.attr in MUTATORS and eager and obj.table is not None:
                        # Only source-owned literal tables may be populated at import.
                        if obj.table in self.parameter_tables:
                            raise Unknown("mutation after parameter registration")
                        self.mutated_tables.add(obj.table)
                        for v in [*args, *kwargs.values()]:
                            self.data(v)
                        return DATA
                    if node.func.attr in DATA_METHODS:
                        for v in [*args, *kwargs.values()]:
                            self.data(v)
                        return DATA
                    raise Unknown("unknown or effectful data method")
            fn = self.expr(node.func, scope, eager)
            if isinstance(fn, Function):
                if not eager and self.empty_string_return(node, fn):
                    return DATA
                return self.function(fn, args, kwargs, eager)
            if isinstance(fn, External) and fn.name in BUILTINS | EXTERNAL_CALLS:
                for v in [*args, *kwargs.values()]:
                    if (
                        isinstance(v, Function)
                        and isinstance(v.node, ast.Lambda)
                        and fn.name == "re.sub"
                    ):
                        self.function(v, [DATA] * len(v.node.args.args), {}, eager)
                    else:
                        self.data(v)
                return DATA
            raise Unknown("unknown call")
        if isinstance(node, ast.Lambda):
            if eager or node.args.defaults or node.args.kw_defaults:
                raise Unknown("eager callback")
            return Function(node, scope)
        if isinstance(node, (ast.ListComp, ast.GeneratorExp)):
            nested = Scope(scope.path, parent=scope)
            for generator in node.generators:
                if generator.is_async:
                    raise Unknown("async comprehension")
                self.data(self.expr(generator.iter, nested, eager))
                self.bind(generator.target, DATA, nested)
                for cond in generator.ifs:
                    self.data(self.expr(cond, nested, eager))
            self.data(self.expr(node.elt, nested, eager))
            return DATA
        if isinstance(
            node,
            (
                ast.Tuple,
                ast.List,
                ast.Set,
                ast.Dict,
                ast.Subscript,
                ast.BinOp,
                ast.UnaryOp,
                ast.BoolOp,
                ast.Compare,
                ast.IfExp,
                ast.JoinedStr,
                ast.FormattedValue,
                ast.Slice,
            ),
        ):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.expr):
                    self.data(self.expr(child, scope, eager))
            return DATA
        raise Unknown(type(node).__name__)

    def bind(self, target: ast.AST, value: Data, scope: Scope) -> None:
        if isinstance(target, ast.Name):
            scope.values[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self.bind(element, DATA, scope)
        else:
            raise Unknown("nonlocal mutation")

    def block(self, body: list[ast.stmt], scope: Scope, eager: bool) -> None:
        for stmt in body:
            self.tick()
            if isinstance(stmt, ast.FunctionDef):
                if stmt.name in scope.values or stmt.decorator_list:
                    raise Unknown("rebound or decorated helper")
                self.header(stmt, scope, eager)
                scope.values[stmt.name] = Function(stmt, scope)
            elif isinstance(stmt, ast.Assign):
                value = self.data(self.expr(stmt.value, scope, eager))
                for target in stmt.targets:
                    self.bind(target, value, scope)
            elif isinstance(stmt, ast.Return):
                if stmt.value is not None:
                    self.data(self.expr(stmt.value, scope, eager))
            elif isinstance(stmt, ast.If):
                self.data(self.expr(stmt.test, scope, eager))
                # Scan every alternative, without deriving a value-sensitive skip.
                self.block(stmt.body, scope, eager)
                self.block(stmt.orelse, scope, eager)
            elif isinstance(stmt, ast.For):
                self.data(self.expr(stmt.iter, scope, eager))
                self.bind(stmt.target, DATA, scope)
                self.block(stmt.body, scope, eager)
                self.block(stmt.orelse, scope, eager)
            elif isinstance(stmt, ast.Expr):
                self.data(self.expr(stmt.value, scope, eager))
            elif isinstance(stmt, ast.Assert):
                self.data(self.expr(stmt.test, scope, eager))
                if stmt.msg:
                    self.data(self.expr(stmt.msg, scope, eager))
            elif isinstance(stmt, ast.Pass):
                continue
            else:
                raise Unknown(type(stmt).__name__)

    def excludes(self, sid: str) -> bool:
        node = self.index.syntax.get(sid)
        if not isinstance(node, ast.FunctionDef):
            return False
        path, _, name = sid.partition("::")
        if "." in name:
            return False
        module = self.module(path)
        if any(p.rsplit("/", 1)[-1] == "conftest.py" for p in self.index.sources):
            raise Unknown("unproved captured pytest lifecycle")
        self.header(node, module, False)
        if node.args.args and not node.decorator_list:
            return False
        args = node.args
        if not (
            node.decorator_list
            or args.args
            or args.posonlyargs
            or args.kwonlyargs
            or args.vararg
            or args.kwarg
        ):
            self.empty_guard_caller = node
        if not (self.used_body_edit and self.restored_set_test(node, module)):
            self.function(Function(node, module), [DATA] * len(node.args.args), {}, False)
        if self.used_body_edit:
            self.only_parameter_references(path)
        return True

    def empty_string_return(self, call: ast.Call, fn: Function) -> bool:
        """Prove one direct literal call returns before reaching edited rule data."""
        if not (
            self.empty_guard_caller is not None
            and self.stack == {(self.empty_guard_caller, False)}
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and len(call.args) == 1
            and isinstance(call.args[0], ast.Constant)
            and call.args[0].value == ""
            and not call.keywords
            and not is_test_file(fn.scope.path)
            and any(path == fn.scope.path for path, _ in self.changed)
            and fn.scope is self.modules.get(fn.scope.path)
        ):
            return False
        node = fn.node
        if not isinstance(node, ast.FunctionDef) or node.decorator_list:
            return False
        args = node.args
        if (
            len(args.args) != 1
            or args.posonlyargs
            or args.kwonlyargs
            or args.vararg
            or args.kwarg
            or args.defaults
        ):
            return False
        word = args.args[0].arg
        body = node.body
        if isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
            if isinstance(body[0].value.value, str):
                body = body[1:]
        if not body or not isinstance(guard := body[0], ast.If):
            return False
        match guard.body:
            case [ast.Return(value=ast.Name(id=result))] if result == word:
                pass
            case _:
                return False

        condition = guard.test
        if isinstance(condition, ast.BoolOp) and isinstance(condition.op, ast.Or):
            if len(condition.values) != 2:
                return False
            condition, tail = condition.values
            match tail:
                case ast.Compare(
                    left=ast.Call(
                        func=ast.Attribute(value=ast.Name(id=receiver), attr="lower"),
                        args=[],
                        keywords=[],
                    ),
                    ops=[ast.In()],
                    comparators=[ast.Name(id=container)],
                ) if receiver == word and container != word:
                    if self.data(self.lookup(container, fn.scope, False)).table != (
                        fn.scope.path,
                        container,
                    ):
                        return False
                case _:
                    return False
        if not (
            isinstance(condition, ast.UnaryOp)
            and isinstance(condition.op, ast.Not)
            and isinstance(condition.operand, ast.Name)
            and condition.operand.id == word
        ):
            return False
        # Even a syntactically unreachable yield changes what calling the function does.
        for child in ast.walk(node):
            self.tick()
            if isinstance(child, (ast.Yield, ast.YieldFrom)):
                return False
        return True

    def restored_set_test(self, node: ast.FunctionDef, module: Scope) -> bool:
        """Audit one literal insertion guarded by immediate try/finally cleanup."""
        args = node.args
        if node.decorator_list or args.args or args.posonlyargs or args.kwonlyargs:
            return False
        if args.vararg or args.kwarg or len(node.body) < 2:
            return False
        insert, guard = node.body[-2:]
        if (
            not isinstance(guard, ast.Try)
            or guard.handlers
            or guard.orelse
            or len(guard.finalbody) != 1
            or not (add := qualified_mutation(insert, "add"))
            or not (remove := qualified_mutation(guard.finalbody[0], "remove"))
            or tuple(map(ast.dump, add)) != tuple(map(ast.dump, remove))
        ):
            return False

        local = Scope(module.path, parent=module)
        strings: dict[str, str] = {}
        for stmt in node.body[:-2]:
            self.tick()
            match stmt:
                case ast.Assign(
                    targets=[ast.Name(id=name)], value=ast.Constant(value=str() as text)
                ):
                    if name in strings:
                        raise Unknown("rebound set key or receiver")
                    strings[name] = text
                    local.values[name] = DATA
                case _:
                    raise Unknown("unproved setup before set insertion")

        receiver, key = add
        owner = self.expr(receiver.value, local, False)
        if not isinstance(owner, Module) or owner.path not in self.body_edits:
            raise Unknown("unproved set owner")
        binding = (owner.path, receiver.attr)
        if self.expr(receiver, local, False) != Data(binding) or binding in self.mutated_tables:
            raise Unknown("unproved set binding at initialization")
        match key:
            case ast.Constant(value=str() as text):
                inserted = text
            case ast.Name(id=name) if name in strings:
                inserted = strings[name]
            case _:
                raise Unknown("unproved set element")
        self.check_fresh_set_element(binding, inserted)

        if not all(isinstance(stmt, ast.Assert) for stmt in guard.body):
            raise Unknown("unproved statements between insertion and cleanup")
        self.auditing_set_cleanup = True
        try:
            self.block(guard.body, local, False)
        finally:
            self.auditing_set_cleanup = False
        return True

    def check_fresh_set_element(self, binding: tuple[str, str], inserted: str) -> None:
        path, name = binding
        tree = self.index.syntax[f"{path}::<module>"]
        assert isinstance(tree, ast.Module)  # Already audited by module().
        for stmt in tree.body:
            self.tick()
            match stmt:
                case ast.Assign(targets=[ast.Name(id=target)], value=ast.Set(elts=elements)) if (
                    target == name
                ):
                    for element in elements:
                        self.tick()
                        if (
                            not isinstance(element, ast.Constant)
                            or not isinstance(element.value, str)
                            or element.value == inserted
                        ):
                            raise Unknown("set contains the key or non-string data")
                    return
        raise Unknown("missing literal string set initializer")

    def only_parameter_references(self, path: str) -> None:
        """Allow mixed edits only for local tables used directly in known decorators."""
        if self.other_collection or not self.changed <= self.parameter_tables:
            raise Unknown("unproved parameter collection")
        tree = self.index.syntax[f"{path}::<module>"]
        for node in ast.walk(tree):
            self.tick()
            if (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and (path, node.id) in self.changed
                and node not in self.parameter_references
            ):
                raise Unknown("table used outside a supported parameter decorator")


class ModuleDataFallback:
    def __init__(self, before: "Index", after: "Index", paths: set[str]):
        self.indexes = before, after
        unique_modules = all(
            len(module_names := [n.name for n in index.nodes.values() if n.kind == "module"])
            == len(set(module_names))
            for index in self.indexes
        )
        self.changes = {
            p: names
            for p in sorted(paths)
            if unique_modules and (names := changed_tables(before, after, p))
        }
        self.safe_modules = set(self.changes) | {
            p
            for p in before.sources.keys() & after.sources.keys()
            if before.sources[p] == after.sources[p]
        }
        self.body_edits = (
            {
                p: name
                for p in sorted(paths - self.safe_modules)
                if (name := deferred_body_edit(before, after, p)) is not None
            }
            if self.changes
            else {}
        )
        self.cache: dict[tuple[str, str], bool] = {}

    def allows(self, sid: str, path: str) -> bool:
        if path not in self.changes:
            return True
        key = sid, path
        if key not in self.cache:
            keep = False
            for index in self.indexes:
                try:
                    # Only a test in the changed table's own module is eligible.
                    body_edits = (
                        self.body_edits
                        if index.nodes.get(sid) and (index.nodes[sid].path == path)
                        else {}
                    )
                    keep |= not Query(
                        index, path, self.changes[path], self.safe_modules, body_edits
                    ).excludes(sid)
                except (ReadsTable, Unknown, RecursionError):
                    keep = True
            self.cache[key] = keep
        return self.cache[key]
