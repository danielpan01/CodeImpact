"""Verify literal runtime import resolution using source strings only."""

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest

CALLER = "loader.py::read"
READER = "tests/test_loader.py::test_read"
DIRECT = "tests/test_service.py::test_direct"
CONTROL = "tests/test_control.py::test_control"
LOADER = (
    "import importlib\n\n"
    "def read():\n"
    '    module = importlib.import_module("service")\n'
    '    return getattr(module, "value")()\n'
)
SERVICE = "def value():\n    return 1\n"


def request_for(loader=LOADER, service=SERVICE, *, extra=None, target="service.py"):
    base = {
        "loader.py": loader,
        target: service,
        "tests/test_loader.py": "from loader import read\n\ndef test_read():\n    assert read()\n",
        "tests/test_service.py": (
            "from service import value\n\ndef test_direct():\n    assert value()\n"
        ),
        "tests/test_control.py": "def test_control():\n    assert True\n",
        **(extra or {}),
    }
    head = {**base, target: service.replace("return 1", "return 2")}
    return AnalysisRequest.model_validate({"base": {"files": base}, "head": {"files": head}})


@pytest.mark.parametrize("target", ["service.py", "src/service.py"])
def test_literal_runtime_call_uses_existing_call_evidence(target):
    request = request_for(target=target)
    report = analyze(request)
    validate_report(request, report)
    assert report.schema_version == "2.0"
    recommendations = {rec.symbol: rec for rec in report.recommendations}
    assert recommendations.keys() == {READER, DIRECT}
    destination = f"{target}::value"
    reader = recommendations[READER]
    assert reader.evidence_path == [READER, CALLER, destination]
    assert reader.reason == "Resolved call path"
    assert reader.path_revision == "both"
    assert recommendations[DIRECT].evidence_path == [DIRECT, destination]
    by_id = {edge.id: edge for edge in report.edges}
    edge = by_id[reader.evidence_edges[1]]
    assert (edge.kind, edge.source, edge.target, edge.revision) == (
        "call",
        CALLER,
        destination,
        "both",
    )
    assert edge.before == edge.after
    (item,) = edge.after
    assert item.location.model_dump() == {"path": "loader.py", "line": 5, "end_line": 5}
    assert item.target_location.model_dump() == {"path": target, "line": 1, "end_line": 2}
    assert "import_module" in item.text and "getattr" in item.text


def test_removed_direct_target_has_before_only_runtime_call():
    request = request_for()
    request.head.files["service.py"] = "def replacement():\n    return 2\n"
    report = analyze(request)
    validate_report(request, report)
    rec = next(rec for rec in report.recommendations if rec.symbol == READER)
    assert rec.evidence_path == [READER, CALLER, "service.py::value"]
    assert rec.path_revision == "before"
    assert "service.py::value" in report.removed
    edge = next(edge for edge in report.edges if edge.id == rec.evidence_edges[1])
    assert edge.kind == "call" and edge.revision == "before" and not edge.after
    assert edge.before[0].target_location.path == "service.py"


@pytest.mark.parametrize(
    "loader",
    [
        LOADER.replace("import importlib", "import another as importlib"),
        LOADER.replace("def read()", "def read(importlib)"),
        LOADER.replace("def read()", "def read(*, getattr)"),
        LOADER.replace("def read()", "def read(**getattr)"),
        LOADER.replace("module =", "getattr =").replace("getattr(module,", "getattr(getattr,"),
        LOADER.replace("import importlib", "import importlib\nimportlib = other"),
        LOADER.replace("import importlib", "import importlib\nimportlib.import_module = other"),
        LOADER.replace("import importlib", "import importlib\ngetattr = other"),
        LOADER.replace("import importlib", "import importlib\n__builtins__ = {}"),
        LOADER.replace("import importlib", "import importlib\nfrom extra import *"),
        LOADER.replace("import importlib", "if flag:\n    import importlib"),
        LOADER.replace('"service"', '"serv" + "ice"'),
        LOADER.replace('"service"', '".service", "example"'),
        LOADER.replace('"value"', "KEY"),
        LOADER.replace('"value"', '"value", default'),
        LOADER.replace("return getattr", "module = other\n    return getattr"),
        LOADER.replace("return getattr", "inspect(module)\n    return getattr"),
        LOADER.replace("def read():", "@decorate\ndef read():"),
        LOADER.replace('return getattr(module, "value")()', 'return getattr(module, "value")(arg)'),
        LOADER + "\ndef patch():\n    setattr(importlib, 'import_module', other)\n",
    ],
)
def test_unproven_source_binding_does_not_add_a_call(loader):
    request = request_for(loader)
    report = analyze(request)
    validate_report(request, report)
    assert not any(e.source == CALLER and e.target == "service.py::value" for e in report.edges)


@pytest.mark.parametrize(
    ("target", "service", "extra"),
    [
        ("service.py", "initialize()\n" + SERVICE, {}),
        ("service.py", "import unknown\n" + SERVICE, {}),
        ("service.py", "import broken\n" + SERVICE, {"broken.py": "def unparseable("}),
        ("service.py", SERVICE + "\nvalue = 2\n", {}),
        ("service.py", SERVICE + "\n" + SERVICE, {}),
        ("service.py", SERVICE + "\ndef __getattr__(name): return value\n", {}),
        ("service.py", "@decorate\n" + SERVICE, {}),
        ("service.py", "from helper import value\n", {"helper.py": SERVICE}),
        ("service.py", SERVICE, {"src/importlib/__init__.py": ""}),
        ("service/__init__.py", SERVICE, {}),
        ("sys.py", SERVICE, {}),
    ],
)
def test_unproven_module_or_member_does_not_add_a_call(target, service, extra):
    loader = LOADER.replace('"service"', '"sys"') if target == "sys.py" else LOADER
    request = request_for(loader, service, extra=extra, target=target)
    report = analyze(request)
    validate_report(request, report)
    assert not any(e.source == CALLER and e.kind == "call" for e in report.edges)


def test_ambiguous_module_inventory_is_rejected_before_resolution():
    request = request_for(extra={"src/service.py": SERVICE})
    with pytest.raises(ValueError, match="Ambiguous module layout"):
        analyze(request)


@pytest.mark.parametrize(
    "patch",
    [
        "import sys\nsys.path.insert(0, somewhere)\n",
        "import builtins as b\nb.getattr = replacement\n",
        "__builtins__['getattr'] = replacement\n",
        "import importlib as lib\nchange_loader(lib)\n",
        "import service\nservice.value = replacement\n",
        "import loader\nloader.getattr = replacement\n",
        "import loader\nloader.importlib = replacement\n",
    ],
)
def test_captured_import_and_namespace_mutations_keep_the_lookup_unresolved(patch):
    request = request_for(extra={"setup.py": patch})
    report = analyze(request)
    validate_report(request, report)
    assert not any(e.source == CALLER and e.target == "service.py::value" for e in report.edges)
    assert any(rec.symbol == DIRECT for rec in report.recommendations)


def test_fixture_and_runtime_paths_coexist_in_schema_2_1():
    request = request_for(
        extra={
            "tests/conftest.py": (
                "import pytest\n"
                "from service import value\n"
                "@pytest.fixture\n"
                "def quoted(): return value()\n"
            ),
            "tests/test_fixture.py": "def test_quote(quoted):\n    assert quoted\n",
        }
    )
    report = analyze(request)
    validate_report(request, report)
    assert report.schema_version == "2.1"
    fixture, reader = (
        next(rec for rec in report.recommendations if rec.symbol == symbol)
        for symbol in ("tests/test_fixture.py::test_quote", READER)
    )
    edges = {edge.id: edge.kind for edge in report.edges}
    assert [edges[eid] for eid in fixture.evidence_edges] == ["fixture", "call"]
    assert [edges[eid] for eid in reader.evidence_edges] == ["call", "call"]
    assert fixture.path_revision == reader.path_revision == "both"


def test_package_caller_remains_outside_the_proven_layout():
    request = request_for(extra={"example/__init__.py": ""})
    for side in (request.base, request.head):
        side.files["example/loader.py"] = side.files.pop("loader.py")
        side.files["tests/test_loader.py"] = side.files["tests/test_loader.py"].replace(
            "from loader import", "from example.loader import"
        )
    report = analyze(request)
    validate_report(request, report)
    assert not any(
        edge.source == "example/loader.py::read" and edge.kind == "call" for edge in report.edges
    )
