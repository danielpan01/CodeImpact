"""Constructor/default queries inspect source strings, never execute fixtures."""

import json
from pathlib import Path

import pytest

from codeimpact.analyzer import analyze
from codeimpact.evaluate import validate_report
from codeimpact.models import AnalysisRequest, Snapshot

CORE = """
class Engine:
    default_mode = "old"
    def __init__(self, key="key", mode=None, sep="."):
        if sep in "-_":
            raise ValueError("invalid")
        if mode is None:
            mode = self.default_mode
        self.mode = mode
    def run(self):
        return self.mode
class Abstract:
    def run(self):
        raise NotImplementedError()
"""


def compare(tests, source=CORE, extra=None):
    files = {"engine.py": source, "test_engine.py": tests, **(extra or {})}
    request = AnalysisRequest(
        base=Snapshot(files=files),
        head=Snapshot(files=files | {"engine.py": source.replace('"old"', '"new"')}),
    )
    report = analyze(request)
    validate_report(request, report)
    return report


def selected(report):
    return {r.symbol.split("::")[1] for r in report.recommendations}


@pytest.mark.parametrize(
    "call",
    [
        'Engine(mode="explicit")',
        'Engine("key", "explicit")',
        'Engine(**{"mode": "explicit"})',
        'Engine(sep="-")',
        "Abstract()",
    ],
)
def test_explicit_override_early_exit_and_unrelated_class_are_excluded(call):
    tests = (
        f"from engine import Engine, Abstract\n"
        f"def test_control(): return {call}.run()\n"
        f"def test_default(): return Engine().run()\n"
        f""
    )
    assert selected(compare(tests)) == {"test_default"}


@pytest.mark.parametrize(
    "argument", ["mode=None", "mode=unknown", "**options", "*values", "sep=unknown"]
)
def test_missing_none_and_unknown_arguments_keep_dependency(argument):
    tests = (
        f"from engine import Engine\n"
        f"def test_unknown(unknown, options, values): return Engine({argument}).run()\n"
        f""
    )
    assert selected(compare(tests)) == {"test_unknown"}


def test_partial_and_source_wrapper_forward_keyword_overrides():
    tests = """from engine import Engine
from functools import partial
def factory(**options): return Engine(**options)
def test_override():
    make = partial(factory, mode=None)
    return make(mode="explicit").run()
def test_default(): return factory().run()
"""
    assert selected(compare(tests)) == {"test_default"}


def test_local_fixture_factory_with_parameter_variants():
    tests = """import pytest
from engine import Engine
from functools import partial
class TestEngine:
    @pytest.fixture(params=(Engine, partial(Engine, key="other")))
    def make(self, request):
        return partial(request.param, key="key")
    def test_explicit(self, make): return make(mode="explicit").run()
    def test_default(self, make): return make().run()
    def test_invalid(self, make):
        with pytest.raises(ValueError): make(sep="-")
"""
    assert selected(compare(tests)) == {"TestEngine.test_default"}


def test_stored_factory_and_mapping_forwarding():
    source = (
        CORE
        + """
class Envelope:
    def __init__(self, engine=None, options=None, fallbacks=None):
        if engine is None: engine = Engine
        self.engine = engine
        self.options = options or {}
        self.fallbacks = fallbacks or []
    def engines(self):
        yield self.engine(**self.options)
        for options in self.fallbacks:
            yield self.engine(**options)
    def run(self):
        for engine in self.engines():
            engine.run()
"""
    )
    tests = """from engine import Envelope
def test_override():
    return Envelope(options={"mode":"explicit"}, fallbacks=[{"mode":"fallback"}]).run()
def test_missing_fallback(): return Envelope(options={"mode":"explicit"}, fallbacks=[{}]).run()
def test_unknown(options): return Envelope(options=options).run()
"""
    assert selected(compare(tests, source)) == {"test_missing_fallback", "test_unknown"}


def test_early_exception_must_precede_default_access():
    source = CORE.replace('        if sep in "-_":\n            raise ValueError("invalid")\n', "")
    source = source.replace(
        "        self.mode = mode",
        '        self.mode = mode\n        if sep in "-_": raise ValueError("invalid")',
    )
    assert selected(
        compare('from engine import Engine\ndef test_invalid(): return Engine(sep="-")\n', source)
    ) == {"test_invalid"}


def test_rebinding_argument_and_default_read_after_constructor_are_retained():
    source = CORE.replace(
        "        if mode is None:", "        mode = None\n        if mode is None:"
    )
    tests = 'from engine import Engine\ndef test_override(): return Engine(mode="explicit").run()\n'
    assert selected(compare(tests, source)) == {"test_override"}
    source = CORE.replace("return self.mode", "return self.default_mode")
    assert selected(compare(tests, source)) == {"test_override"}


def test_unknown_fixture_provider_and_dynamic_factory_keep_fallback():
    tests = """from engine import Engine
def test_unknown(make): return make(mode="explicit").run()
"""
    assert selected(compare(tests)) == {"test_unknown"}


def test_ambiguous_branch_and_mutated_mapping_keep_fallback():
    tests = """from engine import Engine
def test_branch(flag):
    mode = "explicit"
    if flag: mode = None
    return Engine(mode=mode).run()
def test_mutation(options):
    options["mode"] = unknown()
    return Engine(**options).run()
"""
    assert selected(compare(tests)) == {"test_branch", "test_mutation"}


def test_before_only_default_dependency_survives_head_override():
    tests = "from engine import Engine\ndef test_use(): return Engine().run()\n"
    request = AnalysisRequest(
        base=Snapshot(files={"engine.py": CORE, "test_engine.py": tests}),
        head=Snapshot(
            files={
                "engine.py": CORE.replace('"old"', '"new"'),
                "test_engine.py": tests.replace("Engine()", 'Engine(mode="explicit")'),
            }
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    assert selected(report) == {"test_use"}


def test_unrelated_module_effect_still_retains_broad_fallback():
    source = CORE + '\nregister("old")\n'
    assert selected(
        compare(
            'from engine import Engine\ndef test_override(): return Engine(mode="explicit")\n',
            source,
        )
    ) == {"test_override"}


def test_deleted_and_added_default_fields_keep_dependents():
    tests = "from engine import Engine\ndef test_default(): return Engine()\n"
    for before, after in [
        (CORE, CORE.replace('    default_mode = "old"\n', "")),
        (CORE.replace('    default_mode = "old"\n', ""), CORE),
    ]:
        request = AnalysisRequest(
            base=Snapshot(files={"engine.py": before, "test_engine.py": tests}),
            head=Snapshot(files={"engine.py": after, "test_engine.py": tests}),
        )
        report = analyze(request)
        validate_report(request, report)
        assert selected(report) == {"test_default"}


def test_four_real_false_positives_removed_without_changing_labels():
    case = json.loads(Path("corpus/real/cases/itsdangerous_fips.json").read_text())
    request = AnalysisRequest.model_validate(case["request"])
    report = analyze(request)
    validate_report(request, report)
    ids = {r.symbol for r in report.recommendations}
    assert set(case["expected_affected"]) <= ids
    assert not ids.intersection(case["expected_unaffected"])


def test_added_default_helper_import_does_not_reintroduce_module_fallback():
    before = "import hashlib\n" + CORE.replace(
        'default_mode = "old"', "default_mode = staticmethod(hashlib.sha1)"
    )
    after = (
        before.replace("staticmethod(hashlib.sha1)", "staticmethod(lazy)")
        + "\ndef lazy(): return external.new()\n"
    )
    tests = (
        "from engine import Engine\n"
        'def test_override(): return Engine(mode="explicit").run()\n'
        "def test_default(): return Engine().run()\n"
        ""
    )
    request = AnalysisRequest(
        base=Snapshot(files={"engine.py": before, "test_engine.py": tests}),
        head=Snapshot(
            files={
                "engine.py": after,
                "test_engine.py": tests.replace("import Engine", "import Engine, lazy"),
            }
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    assert selected(report) == {"test_default"}


@pytest.mark.parametrize("limit", ["MAX_STEPS", "MAX_DEPTH", "MAX_STATES"])
def test_exhausted_query_budgets_retain_recommendations(monkeypatch, limit):
    from codeimpact import arguments

    monkeypatch.setattr(arguments, limit, 0)
    report = compare(
        'from engine import Engine\ndef test_override(): return Engine(mode="explicit")\n'
    )
    assert selected(report) == {"test_override"}


def test_imported_unknown_option_may_be_none():
    tests = (
        "from engine import Engine\n"
        "from external import option\n"
        "def test_option(): return Engine(mode=option).run()\n"
        ""
    )
    assert selected(compare(tests)) == {"test_option"}


@pytest.mark.parametrize("use", ["obj + 1", "obj == other", 'f"{obj}"'])
def test_implicit_instance_protocols_cannot_prove_default_independence(use):
    source = CORE + "\n"
    source = source.replace(
        "    def run(self):\n        return self.mode",
        "    def __add__(self, other): return self.default_mode\n"
        "    def __eq__(self, other): return self.default_mode\n"
        "    def __str__(self): return self.default_mode\n"
        "    def run(self): return self.mode",
    )
    tests = (
        f"from engine import Engine\n"
        f"def test_protocol(other):\n"
        f'    obj=Engine(mode="explicit")\n'
        f"    return {use}\n"
        f""
    )
    assert selected(compare(tests, source)) == {"test_protocol"}


def test_custom_staticmethod_binding_cannot_hide_initialization_effects():
    before = CORE.replace('default_mode = "old"', 'default_mode = staticmethod("old")')
    source = "def staticmethod(value): return register(value)\n" + before
    tests = "from engine import Abstract\ndef test_other(): return Abstract()\n"
    assert selected(compare(tests, source)) == {"test_other"}


def test_factory_mapping_branch_mutation_cannot_be_dropped():
    tests = """from engine import Engine
def mutate(options, flag):
    if flag: options["mode"] = None
def test_mutation(flag):
    options={"mode":"explicit"}
    mutate(options, flag)
    return Engine(**options)
"""
    assert selected(compare(tests)) == {"test_mutation"}


def test_fixture_with_setup_or_ambiguous_params_is_not_inferred():
    tests = """from engine import Engine
from functools import partial
import pytest
class TestEngine:
    @pytest.fixture(params=dynamic_options)
    def make(self, request): return partial(request.param)
    def test_unknown(self, make): return make(mode="explicit")
"""
    assert selected(compare(tests)) == {"TestEngine.test_unknown"}


def test_source_is_never_executed_and_reports_repeat(tmp_path):
    marker = tmp_path / "not-created"
    source = CORE + f"\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n"
    tests = 'from engine import Engine\ndef test_override(): return Engine(mode="explicit")\n'
    first = compare(tests, source).model_dump()
    first["stats"].pop("elapsed_ms")
    second = compare(tests, source).model_dump()
    second["stats"].pop("elapsed_ms")
    assert first == second
    assert not marker.exists()


def test_custom_staticmethod_factory_with_named_value_retains_module_effects():
    before = (
        "def staticmethod(value): return register(value)\n"
        "old=1\n"
        "new=2\n"
        "class Engine:\n"
        "    default_mode=staticmethod(old)\n"
        "class Abstract: pass\n"
        ""
    )
    after = before.replace("staticmethod(old)", "staticmethod(new)")
    tests = "from engine import Abstract\ndef test_control(): return Abstract()\n"
    report = analyze(
        AnalysisRequest(
            base=Snapshot(files={"engine.py": before, "test_engine.py": tests}),
            head=Snapshot(files={"engine.py": after, "test_engine.py": tests}),
        )
    )
    assert selected(report) == {"test_control"}


def test_changed_descriptor_binding_keeps_initialization_fallback():
    before = (
        "class Descriptor:\n"
        "    def __set_name__(self,owner,name): register(name)\n"
        "one=Descriptor()\n"
        "two=Descriptor()\n"
        "class Engine:\n"
        "    default_mode=one\n"
        "class Abstract: pass\n"
        ""
    )
    after = before.replace("default_mode=one", "default_mode=two")
    tests = "from engine import Abstract\ndef test_control(): return Abstract()\n"
    report = analyze(
        AnalysisRequest(
            base=Snapshot(files={"engine.py": before, "test_engine.py": tests}),
            head=Snapshot(files={"engine.py": after, "test_engine.py": tests}),
        )
    )
    assert selected(report) == {"test_control"}


def test_local_constructor_alias_is_available_only_after_import():
    tests = """def test_after():
    from engine import Engine as Build
    return Build(mode="explicit")
def test_before():
    value = Build(mode="explicit")
    from engine import Engine as Build
    return value
"""
    assert selected(compare(tests)) == {"test_before"}


def test_keyword_only_constructor_and_alias_forwarding():
    source = CORE.replace('key="key", mode=None, sep="."', 'key="key", *, mode=None, sep="."')
    tests = (
        "from engine import Engine as Build\n"
        'def test_override(): return Build(mode="explicit")\n'
        "def test_default(): return Build()\n"
        ""
    )
    assert selected(compare(tests, source)) == {"test_default"}


def test_unknown_iteration_does_not_assume_one_pass():
    tests = """from engine import Engine
from external import items
def test_loop():
    mode="explicit"
    for item in items():
        Engine(mode=mode)
        mode=None
"""
    assert selected(compare(tests)) == {"test_loop"}


def test_unknown_comparison_receiver_retains_possible_protocol_dependency():
    tests = "from engine import Engine\ndef test_compare(value): return value == 1\n"
    assert selected(compare(tests)) == {"test_compare"}


def test_deep_default_aliases_retain_fallback_without_recursion_failure():
    aliases = "\n".join(f"a{i}=a{i + 1}" for i in range(40)) + "\na40=1\n"
    before = aliases + "class Engine:\n    default_mode=a0\nclass Abstract: pass\n"
    after = before.replace("default_mode=a0", "default_mode=a1")
    tests = "from engine import Abstract\ndef test_control(): return Abstract()\n"
    report = analyze(
        AnalysisRequest(
            base=Snapshot(files={"engine.py": before, "test_engine.py": tests}),
            head=Snapshot(files={"engine.py": after, "test_engine.py": tests}),
        )
    )
    validate_report(
        AnalysisRequest(
            base=Snapshot(files={"engine.py": before, "test_engine.py": tests}),
            head=Snapshot(files={"engine.py": after, "test_engine.py": tests}),
        ),
        report,
    )
    assert selected(report) == {"test_control"}


def test_helper_import_moving_initialization_earlier_keeps_fallback():
    before = "import hashlib\n" + CORE.replace(
        'default_mode = "old"', "default_mode = staticmethod(hashlib.sha1)"
    )
    after = (
        before.replace("staticmethod(hashlib.sha1)", "staticmethod(lazy)")
        + "\ndef lazy(): return hashlib.sha1()\n"
    )
    tests = (
        "register()\n"
        "from engine import Engine\n"
        'def test_override(): return Engine(mode="explicit")\n'
        ""
    )
    request = AnalysisRequest(
        base=Snapshot(files={"engine.py": before, "test_engine.py": tests}),
        head=Snapshot(
            files={"engine.py": after, "test_engine.py": "from engine import lazy\n" + tests}
        ),
    )
    report = analyze(request)
    validate_report(request, report)
    assert selected(report) == {"test_override"}


def test_captured_constructor_default_keeps_omitted_argument_dependency():
    source = (
        "class Engine:\n"
        '    default_mode="old"\n'
        "    def __init__(self, mode=default_mode): self.mode=mode\n"
        ""
    )
    tests = (
        "from engine import Engine\n"
        "def test_default(): return Engine()\n"
        'def test_override(): return Engine(mode="explicit")\n'
        ""
    )
    assert selected(compare(tests, source)) == {"test_default"}


def test_shared_mutable_function_default_is_not_recreated_for_each_call():
    tests = """from engine import Engine
def factory(options={"mode":"explicit"}):
    result=Engine(**options)
    options["mode"]=None
    return result
def test_shared():
    factory()
    return factory()
"""
    assert selected(compare(tests)) == {"test_shared"}


def test_effectful_definition_default_keeps_initialization_fallback():
    source = (
        "class Engine:\n"
        '    default_mode="old"\n'
        "    def __init__(self, mode=register(default_mode)): self.mode=mode\n"
        "class Abstract: pass\n"
        ""
    )
    tests = "from engine import Abstract\ndef test_control(): return Abstract()\n"
    assert selected(compare(tests, source)) == {"test_control"}


def test_method_decorator_effect_keeps_initialization_fallback():
    source = (
        "class Engine:\n"
        '    default_mode="old"\n'
        "    @register(default_mode)\n"
        "    def run(self): return 1\n"
        "class Abstract: pass\n"
        ""
    )
    tests = "from engine import Abstract\ndef test_control(): return Abstract()\n"
    assert selected(compare(tests, source)) == {"test_control"}


@pytest.mark.parametrize("scope", ["module", "class"])
def test_existing_initialization_effects_are_not_hidden_by_default_filter(scope):
    source = (
        CORE + "\nregister(Engine.default_mode)\n"
        if scope == "module"
        else CORE.replace(
            '    default_mode = "old"', '    default_mode = "old"\n    register(default_mode)'
        )
    )
    tests = "from engine import Abstract\ndef test_control(): return Abstract()\n"
    assert selected(compare(tests, source)) == {"test_control"}
