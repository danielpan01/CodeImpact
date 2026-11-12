"""Bounded argument guards on existing resolved call paths.

This is a selection-only query over captured AST and call sites. It never executes
source, invents edges, removes import fallback, or treats an edited body as unchanged.
"""

import ast
import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from codeimpact.analyzer import Index

MAX_STEPS = 2000
MAX_DEPTH = 16
MAX_ITEMS = 64
UNKNOWN = object()
TYPES = {
    "bool": bool,
    "int": int,
    "float": float,
    "str": str,
    "bytes": bytes,
    "tuple": tuple,
    "list": list,
    "dict": dict,
    "type": type,
}


@dataclass(frozen=True)
class CallBinding:
    source: str
    target: str
    args: tuple[ast.expr, ...] = ()
    keywords: tuple[ast.keyword, ...] = ()
    partial_name: str | None = None


class Uncertain(Exception):
    """An incomplete proof retains the existing call path."""


def dotted(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute) and (parent := dotted(node.value)):
        return parent + "." + node.attr
    return None


def changed_bodies(before: "Index", after: "Index", path: str) -> set[str]:
    """Require the complete module difference to be existing plain function bodies."""
    trees = [copy.deepcopy(index.syntax.get(f"{path}::<module>")) for index in (before, after)]
    if not isinstance(trees[0], ast.Module) or not isinstance(trees[1], ast.Module):
        return set()
    functions = [
        {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        for tree in trees
        if isinstance(tree, ast.Module)
    ]
    changed = set()
    for name in functions[0].keys() & functions[1].keys():
        old, new = functions[0][name], functions[1][name]
        if ast.dump(old) == ast.dump(new):
            continue
        if old.decorator_list or new.decorator_list:
            return set()
        old.body = new.body = [ast.Pass()]
        if ast.dump(old) != ast.dump(new):
            return set()
        changed.add(f"{path}::{name}")
    return changed if changed and ast.dump(trees[0]) == ast.dump(trees[1]) else set()


class Query:
    def __init__(self, index: "Index", targets: set[str]):
        self.index = index
        self.targets = targets
        self.relevant = set(targets)
        for _ in range(len(index.nodes)):
            added = {b.source for b in index.call_bindings.values() if b.target in self.relevant}
            if added <= self.relevant:
                break
            self.relevant.update(added)
        self.steps = 0
        self.stack: set[str] = set()
        self.builtins: dict[tuple[str, str], bool] = {}
        self.captures: dict[tuple[str, str], bool] = {}
        self.customized_functions = any(
            isinstance(node, ast.Attribute)
            and node.attr in {"__defaults__", "__kwdefaults__", "__code__"}
            for path in index.sources
            for node in ast.walk(index.syntax[f"{path}::<module>"])
        )

    def tick(self) -> None:
        self.steps += 1
        if self.steps > MAX_STEPS or len(self.stack) > MAX_DEPTH:
            raise Uncertain("guard budget")

    def builtin(self, sid: str, name: str) -> bool:
        path = self.index.nodes[sid].path
        key = (path, name)
        if key not in self.builtins:
            self.builtins[key] = self.unshadowed(path, name)
        return self.builtins[key]

    def unshadowed(self, path: str, name: str) -> bool:
        tree = self.index.syntax[f"{path}::<module>"]
        # Even a competing binding in a nested scope prevents this type proof.
        for n in ast.walk(tree):
            if isinstance(n, ast.Name) and n.id == name and isinstance(n.ctx, (ast.Store, ast.Del)):
                return False
            if (
                isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and n.name == name
            ):
                return False
            if isinstance(n, ast.arg) and n.arg == name:
                return False
            if isinstance(n, (ast.Import, ast.ImportFrom)) and any(
                (a.asname or a.name.split(".")[0]) in {name, "*"} for a in n.names
            ):
                return False
        return True

    def immutable(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Constant) or (
            isinstance(node, ast.Tuple)
            and len(node.elts) <= MAX_ITEMS
            and all(self.immutable(child) for child in node.elts)
        )

    def known(self, value: Any) -> bool:
        self.tick()
        if isinstance(value, (list, tuple)):
            return all(self.known(v) for v in value)
        if isinstance(value, dict):
            return all(self.known(v) for v in value.values())
        return value is not UNKNOWN

    def mutable(self, value: Any) -> bool:
        self.tick()
        return isinstance(value, (list, dict)) or (
            isinstance(value, tuple) and any(self.mutable(item) for item in value)
        )

    def stable_capture(self, binding: CallBinding) -> bool:
        """Partial keywords are mutable: reject attribute access and callable escape."""
        if binding.partial_name is None:
            return True
        path = self.index.nodes[binding.source].path
        key = (path, binding.partial_name)
        if key not in self.captures:
            tree = self.index.syntax[f"{path}::<module>"]
            parents = {
                child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)
            }
            self.captures[key] = all(
                (
                    isinstance(parents.get(node), ast.Call)
                    and getattr(parents[node], "func", None) is node
                )
                or self.invocation_alias(node, parents)
                for node in ast.walk(tree)
                if isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id == binding.partial_name
            )
        return self.captures[key]

    def invocation_alias(self, node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
        """A literal loop can alias a partial solely for invocation, without exposing it."""
        value = node
        while isinstance(parents.get(value), (ast.Tuple, ast.List)):
            value = parents[value]
        loop = parents.get(value)
        if (
            not isinstance(loop, ast.For)
            or loop.iter is not value
            or not isinstance(value, (ast.Tuple, ast.List))
        ):
            return False
        aliases: set[str] = set()

        def match(target: ast.AST, item: ast.AST) -> bool:
            if item is node:
                if not isinstance(target, ast.Name):
                    return False
                aliases.add(target.id)
            elif isinstance(item, (ast.Tuple, ast.List)):
                if not isinstance(target, (ast.Tuple, ast.List)) or len(item.elts) != len(
                    target.elts
                ):
                    return False
                return all(match(a, b) for a, b in zip(target.elts, item.elts, strict=True))
            return True

        if (
            len(value.elts) > MAX_ITEMS
            or not all(match(loop.target, item) for item in value.elts)
            or not aliases
        ):
            return False
        scope: ast.AST = loop
        while scope in parents and not isinstance(
            scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)
        ):
            scope = parents[scope]
        return all(
            isinstance(parents.get(use), ast.Call) and getattr(parents[use], "func", None) is use
            for use in ast.walk(scope)
            if isinstance(use, ast.Name) and isinstance(use.ctx, ast.Load) and use.id in aliases
        )

    def value(self, node: ast.AST, env: dict[str, Any], sid: str) -> Any:
        self.tick()
        if isinstance(node, ast.Constant) and type(node.value) in {
            str,
            bytes,
            bool,
            int,
            float,
            type(None),
        }:
            return node.value
        if isinstance(node, ast.Name):
            return env.get(node.id, UNKNOWN)
        if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) <= MAX_ITEMS:
            values = tuple(self.value(n, env, sid) for n in node.elts)
            if not self.known(values):
                return UNKNOWN
            return list(values) if isinstance(node, ast.List) else values
        if isinstance(node, ast.Dict) and len(node.keys) <= MAX_ITEMS:
            result = {}
            for key, value in zip(node.keys, node.values, strict=True):
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    return UNKNOWN
                result[key.value] = self.value(value, env, sid)
            return result
        if isinstance(node, ast.UnaryOp):
            value = self.value(node.operand, env, sid)
            if isinstance(node.op, ast.Not) and value is not UNKNOWN:
                return not value
            if type(value) in {int, float} and isinstance(node.op, (ast.UAdd, ast.USub)):
                return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BoolOp):
            operand = UNKNOWN
            for child in node.values:
                operand = self.value(child, env, sid)
                if operand is UNKNOWN:
                    return UNKNOWN
                elif isinstance(node.op, ast.And) and not operand:
                    return operand
                elif isinstance(node.op, ast.Or) and operand:
                    return operand
            return operand
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = self.value(node.left, env, sid), self.value(node.comparators[0], env, sid)
            if not self.known(left) or not self.known(right):
                return UNKNOWN
            op = node.ops[0]
            if isinstance(op, (ast.Eq, ast.NotEq)):
                return (left == right) == isinstance(op, ast.Eq)
            if isinstance(op, (ast.Is, ast.IsNot)) and (left is None or right is None):
                return (left is right) == isinstance(op, ast.Is)
            if isinstance(op, (ast.In, ast.NotIn)) and isinstance(right, tuple):
                return (left in right) == isinstance(op, ast.In)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "isinstance"
            and len(node.args) == 2
            and not node.keywords
            and self.builtin(sid, "isinstance")
        ):
            value = self.value(node.args[0], env, sid)
            types = node.args[1].elts if isinstance(node.args[1], ast.Tuple) else [node.args[1]]
            if value is not UNKNOWN and all(
                isinstance(t, ast.Name) and t.id in TYPES and self.builtin(sid, t.id) for t in types
            ):
                return isinstance(
                    value, tuple(TYPES[t.id] for t in types if isinstance(t, ast.Name))
                )
        return UNKNOWN

    def supplied(
        self, call: ast.Call, binding: CallBinding, env: dict[str, Any]
    ) -> tuple[list[Any], dict[str, Any]]:
        if not self.stable_capture(binding):
            raise Uncertain("mutable or escaped partial")
        args = [self.value(a, {}, binding.source) for a in binding.args]
        for arg in call.args:
            value = self.value(
                arg.value if isinstance(arg, ast.Starred) else arg, env, binding.source
            )
            if isinstance(arg, ast.Starred):
                if not isinstance(value, (list, tuple)):
                    raise Uncertain("unknown positional expansion")
                args.extend(value)
            else:
                args.append(value)
        kwargs = {
            k.arg: self.value(k.value, {}, binding.source)
            for k in binding.keywords
            if k.arg is not None
        }
        supplied: dict[str, Any] = {}
        for keyword in call.keywords:
            value = self.value(keyword.value, env, binding.source)
            values = {keyword.arg: value} if keyword.arg is not None else value
            if not isinstance(values, dict) or supplied.keys() & values.keys():
                raise Uncertain("unknown or duplicate keyword expansion")
            supplied.update(values)
        kwargs.update(supplied)  # Partial keyword arguments are overridable.
        if len(args) + len(kwargs) > MAX_ITEMS:
            raise Uncertain("argument budget")
        return args, kwargs

    def bind(
        self, sid: str, node: ast.FunctionDef, args: list[Any], kwargs: dict[str, Any]
    ) -> dict[str, Any]:
        parameters = node.args.posonlyargs + node.args.args
        if len(args) > len(parameters) and node.args.vararg is None:
            raise Uncertain("excess arguments")
        supplied = dict(kwargs)
        env = {}
        defaults = dict(
            zip(
                [p.arg for p in parameters[len(parameters) - len(node.args.defaults) :]],
                node.args.defaults,
                strict=True,
            )
        )
        for pos, param in enumerate(parameters):
            if pos < len(args):
                if param.arg in supplied:
                    raise Uncertain("duplicate argument")
                env[param.arg] = args[pos]
            elif param.arg in supplied and param not in node.args.posonlyargs:
                env[param.arg] = supplied.pop(param.arg)
            elif param.arg in defaults:
                default = defaults[param.arg]
                env[param.arg] = (
                    self.value(default, {}, sid) if self.immutable(default) else UNKNOWN
                )
            else:
                raise Uncertain("missing required positional argument")
        for param, kw_default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True):
            if param.arg not in supplied and kw_default is None:
                raise Uncertain("missing required keyword argument")
            env[param.arg] = (
                supplied.pop(param.arg)
                if param.arg in supplied
                else (
                    self.value(kw_default, {}, sid)
                    if kw_default is not None and self.immutable(kw_default)
                    else UNKNOWN
                )
            )
        if node.args.vararg:
            env[node.args.vararg.arg] = tuple(args[len(parameters) :])
        if node.args.kwarg:
            env[node.args.kwarg.arg] = supplied
        elif supplied:
            raise Uncertain("unexpected keyword")
        return env

    def expr(self, node: ast.AST, env: dict[str, Any], sid: str, *, terminal: bool = False) -> bool:
        self.tick()
        if isinstance(node, ast.Call):
            if any(
                self.expr(arg, env, sid) for arg in [*node.args, *(k.value for k in node.keywords)]
            ):
                return True
            spelling = dotted(node.func) or ""
            if spelling.split(".")[-1] in {
                "globals",
                "locals",
                "vars",
                "eval",
                "exec",
                "getattr",
                "setattr",
                "delattr",
                "__import__",
                "import_module",
            }:
                raise Uncertain("reflective call")
            binding = self.index.call_bindings.get(node)
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "pop",
                "popitem",
                "clear",
                "update",
                "setdefault",
                "append",
                "extend",
                "insert",
                "remove",
                "sort",
                "reverse",
                "add",
                "discard",
            }:
                raise Uncertain("possible argument mutation")
            if binding:
                definition = self.index.syntax.get(binding.target)
                resolver = self.index.partials
                if (
                    not isinstance(definition, ast.FunctionDef)
                    or definition.decorator_list
                    or resolver is None
                    or resolver.binding(self.index.nodes[binding.target].path, definition.name)
                    is not definition
                ):
                    raise Uncertain("customized or ambiguous source callable")
            if binding and binding.target in self.relevant:
                args, kwargs = self.supplied(node, binding, env)
                reaches = self.function(binding.target, args, kwargs)
                if (
                    not reaches
                    and not terminal
                    and any(self.mutable(value) for value in [*args, *kwargs.values()])
                ):
                    raise Uncertain("callee may have mutated a later guard value")
                return reaches
            if (
                not (terminal and binding)
                and any(
                    self.mutable(self.value(arg, env, sid))
                    for arg in [*node.args, *(keyword.value for keyword in node.keywords)]
                )
                and not (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "isinstance"
                    and self.builtin(sid, "isinstance")
                )
            ):
                raise Uncertain("mutable argument escaped to another call")
            if isinstance(node.func, ast.Name) and node.func.id in env:
                raise Uncertain("dynamic callable")
            if (
                not binding
                and isinstance(node.func, ast.Name)
                and not (
                    node.func.id
                    in {*TYPES, "isinstance", "len", "tuple", "TypeError", "ValueError"}
                    and self.builtin(sid, node.func.id)
                )
            ):
                raise Uncertain("unresolved named callable")
            if not isinstance(node.func, (ast.Name, ast.Attribute)):
                raise Uncertain("dynamic target")
            return False
        if isinstance(node, (ast.Name, ast.Attribute)):
            spelling = dotted(node) or ""
            if spelling and spelling.split(".")[0] not in env:
                resolver = self.index.partials
                assert resolver is not None
                if resolver.resolve(self.index.nodes[sid].path, spelling) in self.relevant:
                    return True  # A relevant callable escapes as a value.
        return any(self.expr(child, env, sid) for child in ast.iter_child_nodes(node))

    def block(
        self, body: list[ast.stmt], env: dict[str, Any], sid: str, invalid: set[str]
    ) -> tuple[bool, bool]:
        """Return (reaches changed body, may continue); unknown paths remain live."""
        for node in body:
            self.tick()
            if isinstance(node, ast.If):
                if self.expr(node.test, env, sid):
                    return True, True
                condition = self.value(node.test, env, sid)
                branches = (
                    [node.body, node.orelse]
                    if condition is UNKNOWN
                    else [node.body if condition else node.orelse]
                )
                continuations = []
                for branch in branches:
                    hit, live = self.block(branch, dict(env), sid, invalid)
                    if hit:
                        return True, True
                    continuations.append(live)
                if not any(continuations):
                    return False, False
                # Do not carry branch-dependent assignments as constants.
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                        env[child.id] = UNKNOWN
            elif isinstance(node, (ast.Return, ast.Raise)):
                if any(
                    self.expr(child, env, sid, terminal=isinstance(node, ast.Return))
                    for child in ast.iter_child_nodes(node)
                ):
                    return True, True
                return False, False
            elif isinstance(node, (ast.For, ast.While)):
                # No loop cardinality, exception matching or context-manager execution.
                # Visit every syntactic alternative; never propagate their early exits.
                for field, value in ast.iter_fields(node):
                    if field in {"body", "orelse", "finalbody"} and isinstance(value, list):
                        if self.block(value, dict(env), sid, invalid)[0]:
                            return True, True
                    elif isinstance(value, ast.AST) and self.expr(value, env, sid):
                        return True, True
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
                        env[child.id] = UNKNOWN
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                if node.value is not None:
                    if self.expr(node.value, env, sid):
                        return True, True
                    if isinstance(node.value, ast.Name) and self.mutable(
                        env.get(node.value.id, UNKNOWN)
                    ):
                        raise Uncertain("mutable argument alias")
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    for target in targets:
                        if not isinstance(target, ast.Name):
                            raise Uncertain("mutation or destructuring")
                        env[target.id] = (
                            UNKNOWN if target.id in invalid else self.value(node.value, env, sid)
                        )
            elif isinstance(node, (ast.Expr, ast.Assert)):
                if self.expr(node, env, sid):
                    return True, True
            elif isinstance(node, ast.Pass):
                pass
            else:
                raise Uncertain("unsupported control flow")
        return False, True

    def function(self, sid: str, args: list[Any], kwargs: dict[str, Any]) -> bool:
        self.tick()
        if self.customized_functions:
            raise Uncertain("customized function defaults or code")
        if sid in self.targets:
            return True  # Dependency labels are function-body level, not edited-line coverage.
        if sid not in self.relevant:
            return False
        node = self.index.syntax.get(sid)
        if not isinstance(node, ast.FunctionDef) or node.decorator_list or sid in self.stack:
            raise Uncertain("unsupported callable or recursion")
        env = self.bind(sid, node, args, kwargs)
        invalid = {
            n.id
            for n in ast.walk(node)
            if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del))
        }
        invalid.update(
            name
            for n in ast.walk(node)
            if isinstance(n, (ast.Global, ast.Nonlocal))
            for name in n.names
        )
        for name in invalid & env.keys():
            env[name] = UNKNOWN
        self.stack.add(sid)
        try:
            return self.block(node.body, env, sid, invalid)[0]
        finally:
            self.stack.remove(sid)


class CallArgumentFilter:
    def __init__(self, before: "Index", after: "Index", paths: set[str]):
        self.indexes = (before, after)
        self.changes = {
            p: targets for p in sorted(paths) if (targets := changed_bodies(before, after, p))
        }
        self.cache: dict[tuple[str, str, str], bool] = {}
        self.queries = {
            path: tuple(Query(index, targets) for index in self.indexes)
            for path, targets in self.changes.items()
        }

    def allows(self, source: str, target: str, path: str) -> bool:
        if path not in self.changes:
            return True
        key = (source, target, path)
        if key not in self.cache:
            keep = False
            for index, query in zip(self.indexes, self.queries[path], strict=True):
                query.steps = 0
                # Module/class targets and paths supported only by fallback are
                # not function-call guard proofs. Preserve that evidence.
                if target not in query.relevant or not isinstance(
                    index.syntax.get(target), ast.FunctionDef
                ):
                    keep = True
                    continue
                for call, binding in index.call_bindings.items():
                    if binding.source != source or binding.target != target:
                        continue
                    try:
                        args, kwargs = query.supplied(call, binding, {})
                        keep |= query.function(target, args, kwargs)
                    except (Uncertain, RecursionError):
                        keep = True
            self.cache[key] = keep
        return self.cache[key]
