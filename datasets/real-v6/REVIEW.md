# Real-repository label review pack

Generated from pinned source and frozen labels; this command does not run the analyzer.
Labels were initially agent drafted; per-case review status is recorded below.
This pack alone does not establish independent review or upstream test execution.

Read [the protocol](README.md) first. Review source and uncertain labels before results.
Record your name, date and review reference only after checking every label in a case.
Discuss disagreements explicitly; do not relabel tests just to match recommendations.

Counts are static definition IDs, not parametrized cases or inherited test executions.
Affected means dependency on a changed callable/default, not expected assertion failure.
An import or class construction alone does not exercise all methods.
Uncertain cases remain in the denominator inventory.

## dotenv_disable_loading

[theskumar/python-dotenv](https://github.com/theskumar/python-dotenv/commit/c715d19fb88e81f04cf3506a3c2c2812621d1b46) — Introduces the environment flag at the public load_dotenv entry. Tests exercise recognized and unrecognized values with explicit environment setup.

Before: `666984de9a730a54438362b1adedd09bb1e9f5c7`; after: `c715d19fb88e81f04cf3506a3c2c2812621d1b46`.

Label status: **draft**; author: CodeImpact agent; reviewer: none.
Frozen label SHA-256: `086c606daaeac41975c2ef9e43fdc0f4adf3426434ccd6280e4eae53abf52eee`.

### Complete Python change

````diff
--- base/src/dotenv/main.py
+++ head/src/dotenv/main.py
@@ -350,6 +350,12 @@
     of `find_dotenv()`, you can explicitly call `find_dotenv()` and pass the result
     to this function as `dotenv_path`.
     """
+    if _load_dotenv_disabled():
+        logger.debug(
+			"python-dotenv: .env loading disabled by PYTHON_DOTENV_DISABLED environment variable"
+		)
+        return False
+
     if dotenv_path is None and stream is None:
         dotenv_path = find_dotenv()
 
@@ -398,3 +404,12 @@
         override=True,
         encoding=encoding,
     ).dict()
+
+def _load_dotenv_disabled() -> bool:
+    """
+    Determine if dotenv loading has been disabled.
+    """
+    if "PYTHON_DOTENV_DISABLED" not in os.environ:
+        return False
+    value = os.environ["PYTHON_DOTENV_DISABLED"].casefold()
+    return value in {"1", "true", "t", "yes", "y"}
--- base/tests/test_main.py
+++ head/tests/test_main.py
@@ -243,6 +243,130 @@
 
     assert result is True
     assert os.environ == {"a": "b"}
+
+
+@pytest.mark.parametrize(
+    "flag_value",
+    [
+        "true",
+        "yes",
+        "1",
+        "t",
+        "y",
+        "True",
+        "Yes",
+        "TRUE",
+        "YES",
+        "T",
+        "Y",
+    ],
+)
+def test_load_dotenv_disabled(dotenv_path, flag_value):
+    expected_environ = {"PYTHON_DOTENV_DISABLED": flag_value}
+    with mock.patch.dict(os.environ, {"PYTHON_DOTENV_DISABLED": flag_value}, clear=True):
+        dotenv_path.write_text("a=b")
+
+        result = dotenv.load_dotenv(dotenv_path)
+
+        assert result is False
+        assert os.environ == expected_environ
+
+
+@pytest.mark.parametrize(
+    "flag_value",
+    [
+        "true",
+        "yes",
+        "1",
+        "t",
+        "y",
+        "True",
+        "Yes",
+        "TRUE",
+        "YES",
+        "T",
+        "Y",
+    ],
+)
+def test_load_dotenv_disabled_notification(dotenv_path, flag_value):
+    with mock.patch.dict(os.environ, {"PYTHON_DOTENV_DISABLED": flag_value}, clear=True):
+        dotenv_path.write_text("a=b")
+
+        logger = logging.getLogger("dotenv.main")
+        with mock.patch.object(logger, "debug") as mock_debug:
+            result = dotenv.load_dotenv(dotenv_path)
+
+        assert result is False
+        mock_debug.assert_called_once_with(
+			"python-dotenv: .env loading disabled by PYTHON_DOTENV_DISABLED environment variable"
+        )
+
+
+@pytest.mark.parametrize(
+    "flag_value",
+    [
+        "",
+        "false",
+        "no",
+        "0",
+        "f",
+        "n",
+        "False",
+        "No",
+        "FALSE",
+        "NO",
+        "F",
+        "N",
+    ],
+)
+def test_load_dotenv_enabled(dotenv_path, flag_value):
+    expected_environ = {"PYTHON_DOTENV_DISABLED": flag_value, "a": "b"}
+    with mock.patch.dict(os.environ, {"PYTHON_DOTENV_DISABLED": flag_value}, clear=True):
+        dotenv_path.write_text("a=b")
+
+        result = dotenv.load_dotenv(dotenv_path)
+
+        assert result is True
+        assert os.environ == expected_environ
+
+
+@pytest.mark.parametrize(
+    "flag_value",
+    [
+        "",
+        "false",
+        "no",
+        "0",
+        "f",
+        "n",
+        "False",
+        "No",
+        "FALSE",
+        "NO",
+        "F",
+        "N",
+    ],
+)
+def test_load_dotenv_enabled_no_notification(dotenv_path, flag_value):
+    with mock.patch.dict(os.environ, {"PYTHON_DOTENV_DISABLED": flag_value}, clear=True):
+        dotenv_path.write_text("a=b")
+
+        logger = logging.getLogger("dotenv.main")
+        with mock.patch.object(logger, "debug") as mock_debug:
+            result = dotenv.load_dotenv(dotenv_path)
+
+        assert result is True
+        mock_debug.assert_not_called()
+
+
+@mock.patch.dict(os.environ, {}, clear=True)
+def test_load_dotenv_doesnt_disable_itself(dotenv_path):
+    dotenv_path.write_text("PYTHON_DOTENV_DISABLED=true")
+
+    result = dotenv.load_dotenv(dotenv_path)
+
+    assert result is True
+    assert os.environ == {"PYTHON_DOTENV_DISABLED": "true"}
 
 
 def test_load_dotenv_no_file_verbose():
````

### Draft labels and source

#### expected_affected (5)

- [ ] [`tests/test_main.py::test_load_dotenv_disabled`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L264-L272) — Added truthy-flag rows that set the environment explicitly and assert the new early return and lack of writes.
- [ ] [`tests/test_main.py::test_load_dotenv_disabled_notification`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L291-L302) — Added truthy-flag rows that assert the new logging path when the load is skipped.
- [ ] [`tests/test_main.py::test_load_dotenv_doesnt_disable_itself`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L363-L369) — Added test that clears the environment and puts the flag in the file. It checks that the guard runs before the flag can be loaded.
- [ ] [`tests/test_main.py::test_load_dotenv_enabled`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L322-L330) — Added false-flag rows that exercise the guard and confirm the ordinary file-loading path.
- [ ] [`tests/test_main.py::test_load_dotenv_enabled_no_notification`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L350-L359) — Added false-flag rows that exercise the guard and check that it emits no skip message.

#### expected_unaffected (63)

- [ ] [`tests/test_cli.py::test_get_default_path`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L176-L182) — The get default path command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_get_existing_value`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L62-L67) — The get existing value command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_get_non_existent_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L76-L80) — The get non existent file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_get_non_existent_value`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L70-L73) — The get non existent value command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_get_not_a_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L83-L87) — The get not a file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_list`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L28-L39) — The list command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_list_no_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L56-L59) — The list no file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_list_non_existent_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L42-L46) — The list non existent file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_list_not_a_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L49-L53) — The list not a file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L185-L191) — The run command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_existing_variable`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L194-L202) — The run with existing variable command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_existing_variable_not_overridden`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L205-L213) — The run with existing variable not overridden command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_invalid_cmd`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L240-L244) — The run with invalid cmd command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_none_value`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L216-L222) — The run with none value command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_other_env`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L225-L230) — The run with other env command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_version`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L247-L251) — The run with version command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_without_cmd`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L233-L237) — The run without cmd command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_set_export`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L143-L160) — The set export command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_set_no_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L169-L173) — The set no file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_set_non_existent_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L163-L166) — The set non existent file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_set_quote_options`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L116-L133) — The set quote options command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_unset_existing_value`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L90-L96) — The unset existing value command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_unset_non_existent_value`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_cli.py#L99-L103) — The unset non existent value command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_main_module_not_found`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_is_interactive.py#L100-L111) — This test calls find_dotenv directly and does not take the new load_dotenv environment guard.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_main_module_with_file_attribute_none`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_is_interactive.py#L179-L199) — This test calls find_dotenv directly and does not take the new load_dotenv environment guard.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_main_with_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_is_interactive.py#L129-L145) — This test calls find_dotenv directly and does not take the new load_dotenv environment guard.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_main_without_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_is_interactive.py#L113-L127) — This test calls find_dotenv directly and does not take the new load_dotenv environment guard.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_no_ps_attributes_and_normal_execution`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_is_interactive.py#L201-L216) — This test calls find_dotenv directly and does not take the new load_dotenv environment guard.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_precedence_ps1_over_main`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_is_interactive.py#L147-L163) — This test calls find_dotenv directly and does not take the new load_dotenv environment guard.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_ps1_and_ps2_both_exist`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_is_interactive.py#L165-L177) — This test calls find_dotenv directly and does not take the new load_dotenv environment guard.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_with_ps1`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_is_interactive.py#L74-L85) — This test calls find_dotenv directly and does not take the new load_dotenv environment guard.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_with_ps2`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_is_interactive.py#L87-L98) — This test calls find_dotenv directly and does not take the new load_dotenv environment guard.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_with_usecwd_override`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_is_interactive.py#L218-L232) — This test calls find_dotenv directly and does not take the new load_dotenv environment guard.
- [ ] [`tests/test_main.py::test_dotenv_values_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L465-L470) — The dotenv values file test calls dotenv_values with a file or stream. It bypasses both the load guard and implicit discovery.
- [ ] [`tests/test_main.py::test_dotenv_values_file_stream`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L516-L522) — The dotenv values file stream test calls dotenv_values with a file or stream. It bypasses both the load guard and implicit discovery.
- [ ] [`tests/test_main.py::test_dotenv_values_string_io`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L506-L513) — The dotenv values string io test calls dotenv_values with a file or stream. It bypasses both the load guard and implicit discovery.
- [ ] [`tests/test_main.py::test_find_dotenv_found`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L227-L235) — The test pins usecwd=True and checks the working-directory search. It neither depends on shell detection nor calls load_dotenv.
- [ ] [`tests/test_main.py::test_find_dotenv_no_file_no_raise`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L218-L224) — The test pins usecwd=True and checks the working-directory search. It neither depends on shell detection nor calls load_dotenv.
- [ ] [`tests/test_main.py::test_find_dotenv_no_file_raise`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L210-L215) — The test pins usecwd=True and checks the working-directory search. It neither depends on shell detection nor calls load_dotenv.
- [ ] [`tests/test_main.py::test_get_key_encoding`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L116-L122) — The get key encoding test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_get_key_no_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L74-L92) — The get key no file test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_get_key_none`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L125-L133) — The get key none test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_get_key_not_found`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L95-L102) — The get key not found test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_get_key_ok`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L105-L113) — The get key ok test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_load_dotenv_existing_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L239-L245) — The load dotenv existing file test replaces the process environment with an explicit mapping without the disabling flag. The added guard permits the same loading path.
- [ ] [`tests/test_main.py::test_load_dotenv_existing_variable_no_override`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L385-L391) — The load dotenv existing variable no override test replaces the process environment with an explicit mapping without the disabling flag. The added guard permits the same loading path.
- [ ] [`tests/test_main.py::test_load_dotenv_existing_variable_override`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L395-L401) — The load dotenv existing variable override test replaces the process environment with an explicit mapping without the disabling flag. The added guard permits the same loading path.
- [ ] [`tests/test_main.py::test_load_dotenv_file_stream`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L435-L442) — The load dotenv file stream test replaces the process environment with an explicit mapping without the disabling flag. The added guard permits the same loading path.
- [ ] [`tests/test_main.py::test_load_dotenv_redefine_var_used_in_file_no_override`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L405-L411) — The load dotenv redefine var used in file no override test replaces the process environment with an explicit mapping without the disabling flag. The added guard permits the same loading path.
- [ ] [`tests/test_main.py::test_load_dotenv_redefine_var_used_in_file_with_override`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L415-L421) — The load dotenv redefine var used in file with override test replaces the process environment with an explicit mapping without the disabling flag. The added guard permits the same loading path.
- [ ] [`tests/test_main.py::test_load_dotenv_string_io_utf_8`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L425-L431) — The load dotenv string io utf 8 test replaces the process environment with an explicit mapping without the disabling flag. The added guard permits the same loading path.
- [ ] [`tests/test_main.py::test_set_key`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L43-L52) — The set key test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_set_key_encoding`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L55-L61) — The set key encoding test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_set_key_no_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L14-L22) — The set key no file test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_set_key_permission_error`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L64-L71) — The set key permission error test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_set_key_unauthorized_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L170-L174) — The set key unauthorized file test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_unset_encoding`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L160-L167) — The unset encoding test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_unset_no_value`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L148-L157) — The unset no value test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_unset_non_existent_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L177-L188) — The unset non existent file test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_unset_with_value`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L136-L145) — The unset with value test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_parser.py::test_parse_stream`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_parser.py#L550-L553) — The parse stream test exercises parse_stream directly without loading a file into the environment or implicitly searching for one.
- [ ] [`tests/test_utils.py::test_to_cli_string`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_utils.py#L4-L19) — The to cli string test exercises get_cli_string directly without loading a file into the environment or implicitly searching for one.
- [ ] [`tests/test_variables.py::test_parse_variables`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_variables.py#L32-L35) — The parse variables test exercises parse_variables directly without loading a file into the environment or implicitly searching for one.

#### unclassified (7)

- [ ] [`tests/test_ipython.py::test_ipython_existing_variable_no_override`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_ipython.py#L10-L22) — The test clears the starting environment and calls IPython's extension and magic dispatch. The registered magic calls load_dotenv, but the unpinned shell can change state before the guard.
- [ ] [`tests/test_ipython.py::test_ipython_existing_variable_override`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_ipython.py#L26-L38) — The test clears the starting environment and calls IPython's extension and magic dispatch. The registered magic calls load_dotenv, but the unpinned shell can change state before the guard.
- [ ] [`tests/test_ipython.py::test_ipython_new_variable`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_ipython.py#L42-L53) — The test clears the starting environment and calls IPython's extension and magic dispatch. The registered magic calls load_dotenv, but the unpinned shell can change state before the guard.
- [ ] [`tests/test_main.py::test_load_dotenv_in_current_dir`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L445-L462) — The test invokes a generated script through sh. The script calls load_dotenv without a path, but the subprocess state that reaches the edited branch is not pinned.
- [ ] [`tests/test_main.py::test_load_dotenv_no_file_verbose`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_main.py#L372-L381) — The test patches the logger and expects the missing-file message. It does not pin the process flag read before that path.
- [ ] [`tests/test_zip_imports.py::test_load_dotenv_gracefully_handles_zip_imports_when_no_env_file`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_zip_imports.py#L43-L62) — A generated zip member calls load_dotenv with no arguments. The effective interpreter and environment state for the dynamic import or subprocess are not pinned by this test.
- [ ] [`tests/test_zip_imports.py::test_load_dotenv_outside_zip_file_when_called_in_zipfile`](https://github.com/theskumar/python-dotenv/blob/c715d19fb88e81f04cf3506a3c2c2812621d1b46/tests/test_zip_imports.py#L65-L102) — A generated zip member calls load_dotenv with no arguments. The effective interpreter and environment state for the dynamic import or subprocess are not pinned by this test.

### Outside discovery (0)


## dotenv_interactive_detection

[theskumar/python-dotenv](https://github.com/theskumar/python-dotenv/commit/8411987b9301f716245074872afa30646e9b9eb7) — Adds sys.ps1 and sys.ps2 checks inside find_dotenv. New tests model shell state using captured test setup.

Before: `01f899733de664cda0550207067eb36a1795062f`; after: `8411987b9301f716245074872afa30646e9b9eb7`.

Label status: **draft**; author: CodeImpact agent; reviewer: none.
Frozen label SHA-256: `5f337eb3d97dac6e2fd5802f99edf178eff5fe7dda7cba6ba38d026326fbd76f`.

### Complete Python change

````diff
--- base/src/dotenv/main.py
+++ head/src/dotenv/main.py
@@ -286,6 +286,8 @@
 
     def _is_interactive():
         """Decide whether this is running in a REPL or IPython notebook"""
+        if hasattr(sys, "ps1") or hasattr(sys, "ps2"):
+            return True
         try:
             main = __import__("__main__", None, None, fromlist=["__file__"])
         except ModuleNotFoundError:
--- base/tests/test_is_interactive.py
+++ head/tests/test_is_interactive.py
@@ -0,0 +1,227 @@
+import sys
+import builtins
+from unittest import mock
+from dotenv.main import find_dotenv
+
+
+class TestIsInteractive:
+    """Tests for the _is_interactive helper function within find_dotenv.
+
+    The _is_interactive function is used by find_dotenv to determine if the code
+    is running in an interactive environment (like a REPL, IPython notebook, etc.)
+    versus a normal script execution.
+
+    Interactive environments include:
+    - Python REPL (has sys.ps1 or sys.ps2)
+    - IPython notebooks (no __file__ in __main__)
+    - Interactive shells
+
+    Non-interactive environments include:
+    - Normal script execution (has __file__ in __main__)
+    - Module imports
+
+    Examples of the behavior:
+    >>> import sys
+    >>> # In a REPL:
+    >>> hasattr(sys, 'ps1')  # True
+    >>> # In a script:
+    >>> hasattr(sys, 'ps1')  # False
+    """
+
+    def _create_dotenv_file(self, tmp_path):
+        """Helper to create a test .env file."""
+        dotenv_path = tmp_path / ".env"
+        dotenv_path.write_text("TEST=value")
+        return dotenv_path
+
+    def _setup_subdir_and_chdir(self, tmp_path, monkeypatch):
+        """Helper to create subdirectory and change to it."""
+        test_dir = tmp_path / "subdir"
+        test_dir.mkdir()
+        monkeypatch.chdir(test_dir)
+        return test_dir
+
+    def _remove_ps_attributes(self, monkeypatch):
+        """Helper to remove ps1/ps2 attributes if they exist."""
+        if hasattr(sys, "ps1"):
+            monkeypatch.delattr(sys, "ps1")
+        if hasattr(sys, "ps2"):
+            monkeypatch.delattr(sys, "ps2")
+
+    def _mock_main_import(self, monkeypatch, mock_main_module):
+        """Helper to mock __main__ module import."""
+        original_import = builtins.__import__
+
+        def mock_import(name, *args, **kwargs):
+            if name == "__main__":
+                return mock_main_module
+            return original_import(name, *args, **kwargs)
+
+        monkeypatch.setattr(builtins, "__import__", mock_import)
+
+    def _mock_main_import_error(self, monkeypatch):
+        """Helper to mock __main__ module import that raises ModuleNotFoundError."""
+        original_import = builtins.__import__
+
+        def mock_import(name, *args, **kwargs):
+            if name == "__main__":
+                raise ModuleNotFoundError("No module named '__main__'")
+            return original_import(name, *args, **kwargs)
+
+        monkeypatch.setattr(builtins, "__import__", mock_import)
+
+    def test_is_interactive_with_ps1(self, tmp_path, monkeypatch):
+        """Test that _is_interactive returns True when sys.ps1 exists."""
+        dotenv_path = self._create_dotenv_file(tmp_path)
+
+        # Mock sys.ps1 to simulate interactive shell
+        monkeypatch.setattr(sys, "ps1", ">>> ", raising=False)
+
+        self._setup_subdir_and_chdir(tmp_path, monkeypatch)
+
+        # When _is_interactive() returns True, find_dotenv should search from cwd
+        result = find_dotenv()
+        assert result == str(dotenv_path)
+
+    def test_is_interactive_with_ps2(self, tmp_path, monkeypatch):
+        """Test that _is_interactive returns True when sys.ps2 exists."""
+        dotenv_path = self._create_dotenv_file(tmp_path)
+
+        # Mock sys.ps2 to simulate multi-line interactive input
+        monkeypatch.setattr(sys, "ps2", "... ", raising=False)
+
+        self._setup_subdir_and_chdir(tmp_path, monkeypatch)
+
+        # When _is_interactive() returns True, find_dotenv should search from cwd
+        result = find_dotenv()
+        assert result == str(dotenv_path)
+
+    def test_is_interactive_main_module_not_found(self, tmp_path, monkeypatch):
+        """Test that _is_interactive returns False when __main__ module import fails."""
+        self._remove_ps_attributes(monkeypatch)
+        self._mock_main_import_error(monkeypatch)
+
+        # Change to directory and test
+        monkeypatch.chdir(tmp_path)
+
+        # Since _is_interactive() returns False, find_dotenv should not find anything
+        # without usecwd=True
+        result = find_dotenv()
+        assert result == ""
+
+    def test_is_interactive_main_without_file(self, tmp_path, monkeypatch):
+        """Test that _is_interactive returns True when __main__ has no __file__ attribute."""
+        self._remove_ps_attributes(monkeypatch)
+        dotenv_path = self._create_dotenv_file(tmp_path)
+
+        # Mock __main__ module without __file__ attribute
+        mock_main = mock.MagicMock()
+        del mock_main.__file__  # Remove __file__ attribute
+
+        self._mock_main_import(monkeypatch, mock_main)
+        self._setup_subdir_and_chdir(tmp_path, monkeypatch)
+
+        # When _is_interactive() returns True, find_dotenv should search from cwd
+        result = find_dotenv()
+        assert result == str(dotenv_path)
+
+    def test_is_interactive_main_with_file(self, tmp_path, monkeypatch):
+        """Test that _is_interactive returns False when __main__ has __file__ attribute."""
+        self._remove_ps_attributes(monkeypatch)
+
+        # Mock __main__ module with __file__ attribute
+        mock_main = mock.MagicMock()
+        mock_main.__file__ = "/path/to/script.py"
+
+        self._mock_main_import(monkeypatch, mock_main)
+
+        # Change to directory and test
+        monkeypatch.chdir(tmp_path)
+
+        # Since _is_interactive() returns False, find_dotenv should not find anything
+        # without usecwd=True
+        result = find_dotenv()
+        assert result == ""
+
+    def test_is_interactive_precedence_ps1_over_main(self, tmp_path, monkeypatch):
+        """Test that ps1/ps2 attributes take precedence over __main__ module check."""
+        dotenv_path = self._create_dotenv_file(tmp_path)
+
+        # Set ps1 attribute
+        monkeypatch.setattr(sys, "ps1", ">>> ", raising=False)
+
+        # Mock __main__ module with __file__ attribute (which would normally return False)
+        mock_main = mock.MagicMock()
+        mock_main.__file__ = "/path/to/script.py"
+
+        self._mock_main_import(monkeypatch, mock_main)
+        self._setup_subdir_and_chdir(tmp_path, monkeypatch)
+
+        # ps1 should take precedence, so _is_interactive() returns True
+        result = find_dotenv()
+        assert result == str(dotenv_path)
+
+    def test_is_interactive_ps1_and_ps2_both_exist(self, tmp_path, monkeypatch):
+        """Test that _is_interactive returns True when both ps1 and ps2 exist."""
+        dotenv_path = self._create_dotenv_file(tmp_path)
+
+        # Set both ps1 and ps2 attributes
+        monkeypatch.setattr(sys, "ps1", ">>> ", raising=False)
+        monkeypatch.setattr(sys, "ps2", "... ", raising=False)
+
+        self._setup_subdir_and_chdir(tmp_path, monkeypatch)
+
+        # Should return True with either attribute present
+        result = find_dotenv()
+        assert result == str(dotenv_path)
+
+    def test_is_interactive_main_module_with_file_attribute_none(self, tmp_path, monkeypatch):
+        """Test _is_interactive when __main__ has __file__ attribute set to None."""
+        self._remove_ps_attributes(monkeypatch)
+
+        # Mock __main__ module with __file__ = None
+        mock_main = mock.MagicMock()
+        mock_main.__file__ = None
+
+        self._mock_main_import(monkeypatch, mock_main)
+
+        # Mock sys.gettrace to ensure debugger detection returns False
+        monkeypatch.setattr("sys.gettrace", lambda: None)
+
+        monkeypatch.chdir(tmp_path)
+
+        # __file__ = None should still be considered non-interactive
+        # and with no debugger, find_dotenv should not search from cwd
+        result = find_dotenv()
+        assert result == ""
+
+    def test_is_interactive_no_ps_attributes_and_normal_execution(self, tmp_path, monkeypatch):
+        """Test normal script execution scenario where _is_interactive should return False."""
+        self._remove_ps_attributes(monkeypatch)
+
+        # Don't mock anything - let it use the real __main__ module
+        # which should have a __file__ attribute in normal execution
+
+        # Change to directory and test
+        monkeypatch.chdir(tmp_path)
+
+        # In normal execution, _is_interactive() should return False
+        # so find_dotenv should not find anything without usecwd=True
+        result = find_dotenv()
+        assert result == ""
+
+    def test_is_interactive_with_usecwd_override(self, tmp_path, monkeypatch):
+        """Test that usecwd=True overrides _is_interactive behavior."""
+        self._remove_ps_attributes(monkeypatch)
+        dotenv_path = self._create_dotenv_file(tmp_path)
+
+        # Mock __main__ module with __file__ attribute (non-interactive)
+        mock_main = mock.MagicMock()
+        mock_main.__file__ = "/path/to/script.py"
+
+        self._mock_main_import(monkeypatch, mock_main)
+        self._setup_subdir_and_chdir(tmp_path, monkeypatch)
+
+        # Even though _is_interactive() returns False, usecwd=True should find the file
+        result = find_dotenv(usecwd=True)
+        assert result == str(dotenv_path)
````

### Draft labels and source

#### expected_affected (10)

- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_main_module_not_found`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_is_interactive.py#L99-L110) — Added control removing the ps attributes and mocking the __main__ import failure. It tests the fallback after the new shell check.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_main_module_with_file_attribute_none`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_is_interactive.py#L178-L196) — Added control removing the shell attributes, giving __main__ a null file and disabling debugger detection.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_main_with_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_is_interactive.py#L128-L144) — Added control removing the ps attributes and giving __main__ a script filename before checking the noninteractive path.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_main_without_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_is_interactive.py#L112-L126) — Added control removing the ps attributes and giving __main__ no file. It tests the preserved interactive fallback.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_no_ps_attributes_and_normal_execution`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_is_interactive.py#L198-L211) — Added control that removes both shell attributes and exercises a normal interpreter without mocking __main__.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_precedence_ps1_over_main`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_is_interactive.py#L146-L162) — Added test with sys.ps1 and a file-backed __main__. It checks that the new shell detection wins.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_ps1_and_ps2_both_exist`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_is_interactive.py#L164-L176) — Added test with both shell attributes and a file-backed __main__. It checks the new interactive path.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_with_ps1`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_is_interactive.py#L73-L84) — Added test installing sys.ps1 and checking that find_dotenv chooses the working-directory search.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_with_ps2`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_is_interactive.py#L86-L97) — Added test installing sys.ps2 and checking that find_dotenv chooses the working-directory search.
- [ ] [`tests/test_is_interactive.py::TestIsInteractive.test_is_interactive_with_usecwd_override`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_is_interactive.py#L213-L227) — Added control whose explicit usecwd argument short-circuits interactive detection and checks the working-directory result.

#### expected_unaffected (57)

- [ ] [`tests/test_cli.py::test_get_default_path`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L154-L160) — The get default path command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_get_existing_value`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L60-L65) — The get existing value command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_get_non_existent_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L74-L78) — The get non existent file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_get_non_existent_value`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L68-L71) — The get non existent value command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_get_not_a_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L81-L85) — The get not a file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_list`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L28-L37) — The list command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_list_no_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L54-L57) — The list no file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_list_non_existent_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L40-L44) — The list non existent file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_list_not_a_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L47-L51) — The list not a file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L163-L169) — The run command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_existing_variable`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L172-L180) — The run with existing variable command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_existing_variable_not_overridden`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L183-L191) — The run with existing variable not overridden command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_invalid_cmd`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L218-L222) — The run with invalid cmd command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_none_value`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L194-L200) — The run with none value command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_other_env`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L203-L208) — The run with other env command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_with_version`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L225-L229) — The run with version command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_run_without_cmd`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L211-L215) — The run without cmd command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_set_export`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L131-L138) — The set export command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_set_no_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L147-L151) — The set no file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_set_non_existent_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L141-L144) — The set non existent file command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_set_quote_options`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L114-L121) — The set quote options command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_unset_existing_value`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L88-L94) — The unset existing value command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_cli.py::test_unset_non_existent_value`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_cli.py#L97-L101) — The unset non existent value command goes through the CLI's explicit file option or its working-directory default. The CLI uses the key helpers or dotenv_values with a file and does not invoke the edited entry path.
- [ ] [`tests/test_ipython.py::test_ipython_existing_variable_no_override`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_ipython.py#L11-L23) — The captured dotenv magic explicitly passes usecwd=True, which short-circuits the edited interactive detection.
- [ ] [`tests/test_ipython.py::test_ipython_existing_variable_override`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_ipython.py#L27-L39) — The captured dotenv magic explicitly passes usecwd=True, which short-circuits the edited interactive detection.
- [ ] [`tests/test_ipython.py::test_ipython_new_variable`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_ipython.py#L43-L54) — The captured dotenv magic explicitly passes usecwd=True, which short-circuits the edited interactive detection.
- [ ] [`tests/test_main.py::test_dotenv_values_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L341-L346) — The dotenv values file test calls dotenv_values with a file or stream. It bypasses both the load guard and implicit discovery.
- [ ] [`tests/test_main.py::test_dotenv_values_file_stream`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L392-L398) — The dotenv values file stream test calls dotenv_values with a file or stream. It bypasses both the load guard and implicit discovery.
- [ ] [`tests/test_main.py::test_dotenv_values_string_io`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L382-L389) — The dotenv values string io test calls dotenv_values with a file or stream. It bypasses both the load guard and implicit discovery.
- [ ] [`tests/test_main.py::test_find_dotenv_found`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L227-L235) — The test pins usecwd=True and checks the working-directory search. It neither depends on shell detection nor calls load_dotenv.
- [ ] [`tests/test_main.py::test_find_dotenv_no_file_no_raise`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L218-L224) — The test pins usecwd=True and checks the working-directory search. It neither depends on shell detection nor calls load_dotenv.
- [ ] [`tests/test_main.py::test_find_dotenv_no_file_raise`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L210-L215) — The test pins usecwd=True and checks the working-directory search. It neither depends on shell detection nor calls load_dotenv.
- [ ] [`tests/test_main.py::test_get_key_encoding`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L116-L122) — The get key encoding test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_get_key_no_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L74-L92) — The get key no file test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_get_key_none`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L125-L133) — The get key none test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_get_key_not_found`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L95-L102) — The get key not found test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_get_key_ok`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L105-L113) — The get key ok test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_load_dotenv_existing_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L239-L245) — The load dotenv existing file test passes an explicit path or stream to load_dotenv and does not call find_dotenv.
- [ ] [`tests/test_main.py::test_load_dotenv_existing_variable_no_override`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L261-L267) — The load dotenv existing variable no override test passes an explicit path or stream to load_dotenv and does not call find_dotenv.
- [ ] [`tests/test_main.py::test_load_dotenv_existing_variable_override`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L271-L277) — The load dotenv existing variable override test passes an explicit path or stream to load_dotenv and does not call find_dotenv.
- [ ] [`tests/test_main.py::test_load_dotenv_file_stream`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L311-L318) — The load dotenv file stream test passes an explicit path or stream to load_dotenv and does not call find_dotenv.
- [ ] [`tests/test_main.py::test_load_dotenv_no_file_verbose`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L248-L257) — The load dotenv no file verbose test passes an explicit path or stream to load_dotenv and does not call find_dotenv.
- [ ] [`tests/test_main.py::test_load_dotenv_redefine_var_used_in_file_no_override`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L281-L287) — The load dotenv redefine var used in file no override test passes an explicit path or stream to load_dotenv and does not call find_dotenv.
- [ ] [`tests/test_main.py::test_load_dotenv_redefine_var_used_in_file_with_override`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L291-L297) — The load dotenv redefine var used in file with override test passes an explicit path or stream to load_dotenv and does not call find_dotenv.
- [ ] [`tests/test_main.py::test_load_dotenv_string_io_utf_8`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L301-L307) — The load dotenv string io utf 8 test passes an explicit path or stream to load_dotenv and does not call find_dotenv.
- [ ] [`tests/test_main.py::test_set_key`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L43-L52) — The set key test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_set_key_encoding`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L55-L61) — The set key encoding test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_set_key_no_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L14-L22) — The set key no file test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_set_key_permission_error`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L64-L71) — The set key permission error test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_set_key_unauthorized_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L170-L174) — The set key unauthorized file test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_unset_encoding`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L160-L167) — The unset encoding test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_unset_no_value`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L148-L157) — The unset no value test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_unset_non_existent_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L177-L188) — The unset non existent file test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_main.py::test_unset_with_value`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L136-L145) — The unset with value test uses the key-reading or key-writing utility with an explicit file. It bypasses the edited loader and discovery paths.
- [ ] [`tests/test_parser.py::test_parse_stream`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_parser.py#L168-L171) — The parse stream test exercises parse_stream directly without loading a file into the environment or implicitly searching for one.
- [ ] [`tests/test_utils.py::test_to_cli_string`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_utils.py#L4-L13) — The to cli string test exercises get_cli_string directly without loading a file into the environment or implicitly searching for one.
- [ ] [`tests/test_variables.py::test_parse_variables`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_variables.py#L32-L35) — The parse variables test exercises parse_variables directly without loading a file into the environment or implicitly searching for one.

#### unclassified (3)

- [ ] [`tests/test_main.py::test_load_dotenv_in_current_dir`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_main.py#L321-L338) — The test invokes a generated script through sh. The script calls load_dotenv without a path, but the subprocess state that reaches the edited branch is not pinned.
- [ ] [`tests/test_zip_imports.py::test_load_dotenv_gracefully_handles_zip_imports_when_no_env_file`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_zip_imports.py#L42-L61) — A generated zip member calls load_dotenv with no arguments. The effective interpreter and environment state for the dynamic import or subprocess are not pinned by this test.
- [ ] [`tests/test_zip_imports.py::test_load_dotenv_outside_zip_file_when_called_in_zipfile`](https://github.com/theskumar/python-dotenv/blob/8411987b9301f716245074872afa30646e9b9eb7/tests/test_zip_imports.py#L64-L101) — A generated zip member calls load_dotenv with no arguments. The effective interpreter and environment state for the dynamic import or subprocess are not pinned by this test.

### Outside discovery (0)


## tokenize_rt_tstrings

[asottile/tokenize-rt](https://github.com/asottile/tokenize-rt/commit/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0) — Applies the existing brace handling to template-string middle tokens. The new test pins the 3.14 input and result, with independent token utilities in the same suite.

Before: `ed9a32cc33e454dea90a7715663453b7070bb8cd`; after: `2cb9c40dd1b7dc3942b45f8675ebba49149afbc0`.

Label status: **draft**; author: CodeImpact agent; reviewer: none.
Frozen label SHA-256: `aa819ed232217c1a1c6b5c8d35af60657508e62060e50d2e3fee37ef329f94ff`.

### Complete Python change

````diff
--- base/tests/tokenize_rt_test.py
+++ head/tests/tokenize_rt_test.py
@@ -202,6 +202,25 @@
         ]
 
 
+@pytest.mark.skipif(sys.version_info < (3, 14), reason='3.14+')
+def test_src_to_tokens_tstring_with_escapes():  # pragma: >=3.14 cover
+    src = 't" a {{ {b} }} c"'
+    ret = src_to_tokens(src)
+    assert ret == [
+        Token(name='TSTRING_START', src='t"', line=1, utf8_byte_offset=0),
+        Token(name='TSTRING_MIDDLE', src=' a {{', line=1, utf8_byte_offset=2),  # noqa: E501
+        Token(name='TSTRING_MIDDLE', src=' ', line=1, utf8_byte_offset=7),
+        Token(name='OP', src='{', line=1, utf8_byte_offset=8),
+        Token(name='NAME', src='b', line=1, utf8_byte_offset=9),
+        Token(name='OP', src='}', line=1, utf8_byte_offset=10),
+        Token(name='TSTRING_MIDDLE', src=' }}', line=1, utf8_byte_offset=11),  # noqa: E501
+        Token(name='TSTRING_MIDDLE', src=' c', line=1, utf8_byte_offset=14),  # noqa: E501
+        Token(name='TSTRING_END', src='"', line=1, utf8_byte_offset=16),
+        Token(name='NEWLINE', src='', line=1, utf8_byte_offset=17),
+        Token(name='ENDMARKER', src='', line=2, utf8_byte_offset=0),
+    ]
+
+
 def test_src_to_tokens_fstring_with_named_escapes():
     src = r'f" \N{SNOWMAN} "'
     ret = src_to_tokens(src)
--- base/tokenize_rt.py
+++ head/tokenize_rt.py
@@ -110,7 +110,7 @@
 
         tok_name = tokenize.tok_name[tok_type]
 
-        if tok_name == 'FSTRING_MIDDLE':  # pragma: >=3.12 cover
+        if tok_name in {'FSTRING_MIDDLE', 'TSTRING_MIDDLE'}:  # pragma: >=3.12 cover  # noqa: E501
             if '{' in tok_text or '}' in tok_text:
                 new_tok_text = curly_escape(tok_text)
                 ecol += len(new_tok_text) - len(tok_text)
````

### Draft labels and source

#### expected_affected (1)

- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_tstring_with_escapes`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L206-L221) — Added Python 3.14+ test with template-string braces. It exercises the newly admitted TSTRING_MIDDLE token and checks source and byte offsets.

#### expected_unaffected (25)

- [ ] [`tests/tokenize_rt_test.py::test_curly_escape`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L397-L398) — It calls curly_escape directly and does not exercise the edited token-kind condition.
- [ ] [`tests/tokenize_rt_test.py::test_main`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L372-L385) — The main case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_offset_default_values`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L32-L33) — The offset default values test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.
- [ ] [`tests/tokenize_rt_test.py::test_parse_string_literal`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L284-L285) — The parse string literal test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.
- [ ] [`tests/tokenize_rt_test.py::test_re_partition_match`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L27-L29) — The re partition match test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.
- [ ] [`tests/tokenize_rt_test.py::test_re_partition_no_match`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L22-L24) — The re partition no match test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.
- [ ] [`tests/tokenize_rt_test.py::test_reversed_enumerate`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L259-L272) — The reversed enumerate case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_end_of_call_looks_like_string`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L349-L351) — The rfind string parts end of call looks like string case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_multiple_tokens`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L326-L328) — The rfind string parts multiple tokens case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_not_a_string`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L331-L333) — The rfind string parts not a string case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_only_literal`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L289-L291) — The rfind string parts only literal case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_parenthesized`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L367-L369) — The rfind string parts parenthesized case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_py312_plus`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L294-L300) — The input is an empty f-string. It has neither a template-string token nor a middle token containing braces.
- [ ] [`tests/tokenize_rt_test.py::test_roundtrip_tokenize`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L252-L256) — The three captured fixtures contain empty source, ordinary Unicode text, or a backslash continuation. They use neither template strings nor f-string brace escapes.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_escaped_nl`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L63-L79) — The src to tokens escaped nl case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_escaped_nl_no_left_ws`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L82-L97) — The src to tokens escaped nl no left ws case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_escaped_nl_windows`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L100-L116) — The src to tokens escaped nl windows case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_fstring_with_escapes`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L180-L202) — This f-string still takes the existing FSTRING_MIDDLE brace branch. Its input cannot generate the newly admitted TSTRING_MIDDLE token.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_fstring_with_named_escapes`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L224-L241) — The input is an f-string. FSTRING_MIDDLE still takes the same brace escape path after the template-string addition.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_implicit_continue`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L119-L145) — The src to tokens implicit continue case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_multiline_string`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L157-L177) — The src to tokens multiline string case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_no_eol_eof`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L148-L154) — The src to tokens no eol eof case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_simple`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L49-L60) — The src to tokens simple case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_token_matches`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L41-L46) — The token matches test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.
- [ ] [`tests/tokenize_rt_test.py::test_token_offset`](https://github.com/asottile/tokenize-rt/blob/2cb9c40dd1b7dc3942b45f8675ebba49149afbc0/tests/tokenize_rt_test.py#L36-L38) — The token offset test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.

#### unclassified (0)


### Outside discovery (0)


## tokenize_rt_unicode_escapes

[asottile/tokenize-rt](https://github.com/asottile/tokenize-rt/commit/32e62360acc5f0eb311ce0197ecfd57875f90066) — Introduces a named-Unicode escape aware brace transformation and exercises it directly and through f-string tokenization.

Before: `75de5c5c84e105531bd2702fae81ba973e40d830`; after: `32e62360acc5f0eb311ce0197ecfd57875f90066`.

Label status: **draft**; author: CodeImpact agent; reviewer: none.
Frozen label SHA-256: `fffd62cd49c1b49d66c53fbbc38d38a9ff6410e528885e58a3b7159e6eebec5a`.

### Complete Python change

````diff
--- base/tests/tokenize_rt_test.py
+++ head/tests/tokenize_rt_test.py
@@ -6,6 +6,7 @@
 import pytest
 
 from tokenize_rt import _re_partition
+from tokenize_rt import curly_escape
 from tokenize_rt import ESCAPED_NL
 from tokenize_rt import main
 from tokenize_rt import Offset
@@ -201,6 +202,26 @@
         ]
 
 
+def test_src_to_tokens_fstring_with_named_escapes():
+    src = r'f" \N{SNOWMAN} "'
+    ret = src_to_tokens(src)
+    if sys.version_info >= (3, 12):  # pragma: >=3.12 cover
+        assert ret == [
+            Token(name='FSTRING_START', src='f"', line=1, utf8_byte_offset=0),
+            Token(name='FSTRING_MIDDLE', src=' \\N{SNOWMAN}', line=1, utf8_byte_offset=2),  # noqa: E501
+            Token(name='FSTRING_MIDDLE', src=' ', line=1, utf8_byte_offset=14),
+            Token(name='FSTRING_END', src='"', line=1, utf8_byte_offset=15),
+            Token(name='NEWLINE', src='', line=1, utf8_byte_offset=16),
+            Token(name='ENDMARKER', src='', line=2, utf8_byte_offset=0),
+        ]
+    else:  # pragma: <3.12 cover
+        assert ret == [
+            Token(name='STRING', src='f" \\N{SNOWMAN} "', line=1, utf8_byte_offset=0),  # noqa: E501
+            Token(name='NEWLINE', src='', line=1, utf8_byte_offset=16),
+            Token(name='ENDMARKER', src='', line=2, utf8_byte_offset=0),
+        ]
+
+
 @pytest.mark.parametrize(
     'filename',
     (
@@ -343,3 +364,16 @@
         "1:5 NEWLINE '\\n'\n"
         "2:0 ENDMARKER ''\n"
     )
+
+
+@pytest.mark.parametrize(
+    ('s', 'expected'),
+    (
+        ('', ''),
+        ('{foo}', '{{foo}}'),
+        (r'\N{SNOWMAN}', r'\N{SNOWMAN}'),
+        (r'\N{SNOWMAN} {bar}', r'\N{SNOWMAN} {{bar}}'),
+    ),
+)
+def test_curly_escape(s, expected):
+    assert curly_escape(s) == expected
--- base/tokenize_rt.py
+++ head/tokenize_rt.py
@@ -46,6 +46,16 @@
 
 _string_re = re.compile('^([^\'"]*)(.*)$', re.DOTALL)
 _escaped_nl_re = re.compile(r'\\(\n|\r\n|\r)')
+
+NAMED_UNICODE_RE = re.compile(r'(?<!\\)(?:\\\\)*(\\N\{[^}]+\})')
+
+
+def curly_escape(s: str) -> str:
+    parts = NAMED_UNICODE_RE.split(s)
+    return ''.join(
+        part.replace('{', '{{').replace('}', '}}') if i % 2 == 0 else part
+        for i, part in enumerate(parts)
+    )
 
 
 def _re_partition(regex: Pattern[str], s: str) -> tuple[str, str, str]:
@@ -101,8 +111,10 @@
         tok_name = tokenize.tok_name[tok_type]
 
         if tok_name == 'FSTRING_MIDDLE':  # pragma: >=3.12 cover
-            ecol += tok_text.count('{') + tok_text.count('}')
-            tok_text = tok_text.replace('{', '{{').replace('}', '}}')
+            if '{' in tok_text or '}' in tok_text:
+                new_tok_text = curly_escape(tok_text)
+                ecol += len(new_tok_text) - len(tok_text)
+                tok_text = new_tok_text
 
         tokens.append(Token(tok_name, tok_text, sline, end_offset))
         last_line, last_col = eline, ecol
````

### Draft labels and source

#### expected_affected (3)

- [ ] [`tests/tokenize_rt_test.py::test_curly_escape`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L378-L379) — Added direct curly_escape test with ordinary braces and named Unicode escapes.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_fstring_with_escapes`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L180-L202) — On Python 3.12+ this f-string supplies doubled braces in middle tokens. It exercises the replaced escape-and-offset calculation and checks both pieces of evidence.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_fstring_with_named_escapes`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L205-L222) — Added test with a named Unicode escape in an f-string. Its Python 3.12+ expected tokens exercise the new brace logic.

#### expected_unaffected (22)

- [ ] [`tests/tokenize_rt_test.py::test_main`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L353-L366) — The main case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_offset_default_values`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L32-L33) — The offset default values test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.
- [ ] [`tests/tokenize_rt_test.py::test_parse_string_literal`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L265-L266) — The parse string literal test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.
- [ ] [`tests/tokenize_rt_test.py::test_re_partition_match`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L27-L29) — The re partition match test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.
- [ ] [`tests/tokenize_rt_test.py::test_re_partition_no_match`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L22-L24) — The re partition no match test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.
- [ ] [`tests/tokenize_rt_test.py::test_reversed_enumerate`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L240-L253) — The reversed enumerate case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_end_of_call_looks_like_string`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L330-L332) — The rfind string parts end of call looks like string case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_multiple_tokens`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L307-L309) — The rfind string parts multiple tokens case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_not_a_string`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L312-L314) — The rfind string parts not a string case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_only_literal`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L270-L272) — The rfind string parts only literal case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_parenthesized`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L348-L350) — The rfind string parts parenthesized case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_rfind_string_parts_py312_plus`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L275-L281) — The input is an empty f-string. It has neither a template-string token nor a middle token containing braces.
- [ ] [`tests/tokenize_rt_test.py::test_roundtrip_tokenize`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L233-L237) — The three captured fixtures contain empty source, ordinary Unicode text, or a backslash continuation. They use neither template strings nor f-string brace escapes.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_escaped_nl`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L63-L79) — The src to tokens escaped nl case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_escaped_nl_no_left_ws`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L82-L97) — The src to tokens escaped nl no left ws case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_escaped_nl_windows`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L100-L116) — The src to tokens escaped nl windows case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_implicit_continue`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L119-L145) — The src to tokens implicit continue case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_multiline_string`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L157-L177) — The src to tokens multiline string case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_no_eol_eof`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L148-L154) — The src to tokens no eol eof case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_src_to_tokens_simple`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L49-L60) — The src to tokens simple case tokenizes ordinary source with no template strings or brace-bearing f-string middle tokens.
- [ ] [`tests/tokenize_rt_test.py::test_token_matches`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L41-L46) — The token matches test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.
- [ ] [`tests/tokenize_rt_test.py::test_token_offset`](https://github.com/asottile/tokenize-rt/blob/32e62360acc5f0eb311ce0197ecfd57875f90066/tests/tokenize_rt_test.py#L36-L38) — The token offset test invokes an independent token, offset, string-literal, or regex utility without taking the edited tokenization path.

#### unclassified (0)


### Outside discovery (0)


## xmltodict_doctype

[martinblech/xmltodict](https://github.com/martinblech/xmltodict/commit/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f) — Permits a DOCTYPE without entities while retaining an entity declaration refusal. The tests pin both inputs and explicit disabled and enabled parsing.

Before: `a2a9ab7e0692a62f64d97ff12553d0d53368c854`; after: `25b61a41f580cfc211df07c5fbbf603bd8eb5a5f`.

Label status: **draft**; author: CodeImpact agent; reviewer: none.
Frozen label SHA-256: `927db073feec9e6ba02d9a1d14cb5def8404f7e218e55b7a01001eea17a27574`.

### Complete Python change

````diff
--- base/tests/test_xmltodict.py
+++ head/tests/test_xmltodict.py
@@ -419,7 +419,7 @@
     ]>
     <bomb>&c;</bomb>
     """
-    with pytest.raises(expat.ExpatError, match="entities are disabled"):
+    with pytest.raises(ValueError, match="entities are disabled"):
         parse(xml, disable_entities=True)
 
 
@@ -437,18 +437,19 @@
     assert parse(xml, disable_entities=False) == expectedResult
 
 
-def test_disable_entities_true_rejects_external_dtd():
+def test_external_entity():
     xml = """
     <!DOCTYPE external [
         <!ENTITY ee SYSTEM "http://www.python.org/">
     ]>
     <root>&ee;</root>
     """
-    with pytest.raises(expat.ExpatError, match="entities are disabled"):
-        parse(xml, disable_entities=True)
-
-
-def test_disable_entities_true_attempts_external_dtd():
+    with pytest.raises(ValueError, match="entities are disabled"):
+        parse(xml)
+    assert parse(xml, disable_entities=False) == {"root": None}
+
+
+def test_external_entity_with_custom_expat():
     xml = """
     <!DOCTYPE external [
         <!ENTITY ee SYSTEM "http://www.python.org/">
@@ -456,20 +457,37 @@
     <root>&ee;</root>
     """
 
-    def raising_external_ref_handler(*args, **kwargs):
-        parser = ParserCreate(*args, **kwargs)
-        parser.ExternalEntityRefHandler = lambda *x: 0
-        return parser
-    expat.ParserCreate = raising_external_ref_handler
-    # Using this try/catch because a TypeError is thrown before
-    # the ExpatError.
-    try:
-        parse(xml, disable_entities=False, expat=expat)
-    except expat.ExpatError:
-        assert True
-    else:
-        assert False
-    expat.ParserCreate = ParserCreate
+    class CustomExpat:
+        def __init__(self, external_entity_result):
+            self.external_entity_result = external_entity_result
+
+        def ParserCreate(self, *args, **kwargs):
+            parser = ParserCreate(*args, **kwargs)
+
+            def _handler(*args, **kwargs):
+                return self.external_entity_result
+
+            parser.ExternalEntityRefHandler = _handler
+            return parser
+
+        ExpatError = expat.ExpatError
+
+    with pytest.raises(expat.ExpatError):
+        parse(xml, disable_entities=False, expat=CustomExpat(0))
+    assert parse(xml, disable_entities=False, expat=CustomExpat(1)) == {"root": None}
+    with pytest.raises(ValueError):
+        assert parse(xml, disable_entities=True, expat=CustomExpat(1))
+    with pytest.raises(ValueError):
+        assert parse(xml, disable_entities=True, expat=CustomExpat(0))
+
+
+def test_disable_entities_true_allows_doctype_without_entities():
+    xml = """<?xml version='1.0' encoding='UTF-8'?>
+    <!DOCTYPE data SYSTEM "diagram.dtd">
+    <foo>bar</foo>
+    """
+    assert parse(xml, disable_entities=True) == {"foo": "bar"}
+    assert parse(xml, disable_entities=False) == {"foo": "bar"}
 
 
 def test_disable_entities_allows_comments_by_default():
--- base/xmltodict.py
+++ head/xmltodict.py
@@ -355,22 +355,9 @@
     parser.buffer_text = True
     if disable_entities:
         def _forbid_entities(*_args, **_kwargs):
-            raise expat.ExpatError("xmltodict.parse(): entities are disabled")
-
-        def _forbid_entities_default(text):
-            if not text:
-                return
-            stripped = text.lstrip()
-            if stripped.startswith('<!--'):
-                return
-            if stripped.startswith('<!') or stripped.startswith('&'):
-                _forbid_entities()
-
-        # Reject DTD/entity constructs explicitly instead of ignoring them.
-        parser.DefaultHandler = _forbid_entities_default
+            raise ValueError("entities are disabled")
+
         parser.EntityDeclHandler = _forbid_entities
-        parser.StartDoctypeDeclHandler = _forbid_entities
-        parser.ExternalEntityRefHandler = _forbid_entities
     if hasattr(xml_input, 'read'):
         parser.ParseFile(xml_input)
     elif isgenerator(xml_input):
````

### Draft labels and source

#### expected_affected (5)

- [ ] [`tests/test_xmltodict.py::test_disable_entities_allows_comments_by_default`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L493-L500) — Its default parse exercises the old declaration handler's explicit exception for comments. The head removes that handler and relies on the parser's ordinary comment behavior.
- [ ] [`tests/test_xmltodict.py::test_disable_entities_true_allows_doctype_without_entities`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L484-L490) — Added test for a DOCTYPE with no entity declaration. Its parse with the default entity guard enabled exercises removal of the unconditional DOCTYPE refusal.
- [ ] [`tests/test_xmltodict.py::test_disable_entities_true_rejects_xmlbomb`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L413-L423) — Changes the exception assertion for the enabled entity-declaration guard. The declaration exercises the revised callback and its ValueError.
- [ ] [`tests/test_xmltodict.py::test_external_entity`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L440-L449) — Replaces the former external declaration rejection test and compares the default refusal and the explicit opt-in paths.
- [ ] [`tests/test_xmltodict.py::test_external_entity_with_custom_expat`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L452-L481) — Replaces the custom parser test. Its disabled cases check the declaration callback with both explicit external-handler return values.

#### expected_unaffected (96)

- [ ] [`tests/test_dicttoxml.py::test_attr_order_roundtrip`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L130-L132) — The attr order roundtrip round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_attrib`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L31-L34) — The attrib round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_attrib_and_cdata`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L37-L40) — The attrib and cdata round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_attribute_values_with_angle_brackets_are_escaped`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L340-L344) — The attribute values with angle brackets are escaped case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_boolean_unparse`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L301-L308) — The boolean unparse case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_cdata`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L25-L28) — The cdata round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_comment_roundtrip_limited`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L215-L237) — The comment roundtrip limited case enables the dedicated CommentHandler and supplies neither a DOCTYPE nor an entity declaration.
- [ ] [`tests/test_dicttoxml.py::test_empty_dict_vs_empty_list_behavior`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L534-L557) — The empty dict vs empty list behavior case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_empty_list_filtering`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L457-L491) — The empty list filtering case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_empty_list_filtering_with_short_empty_elements_false`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L494-L510) — The empty list filtering with short empty elements false case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_encoding`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L240-L246) — The encoding round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_fulldoc`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L249-L253) — The fulldoc case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_generator`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L58-L64) — The generator round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_list`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L43-L46) — The list round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_list_expand_iter`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L49-L55) — The list expand iter case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_multiple_roots`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L72-L76) — The multiple roots case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_multiple_roots_nofulldoc`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L83-L89) — The multiple roots nofulldoc case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_namespace_support`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L271-L298) — The namespace support case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_nested`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L92-L98) — The nested round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_no_root`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L67-L69) — The no root case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_no_root_nofulldoc`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L79-L80) — The no root nofulldoc case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_non_empty_lists_are_not_filtered`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L513-L531) — The non empty lists are not filtered case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_non_string_attr`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L261-L263) — The non string attr case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_non_string_text_with_attributes`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L560-L596) — The non string text with attributes case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_non_string_value`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L256-L258) — The non string value case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_preprocessor`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L106-L116) — The preprocessor case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_preprocessor_skipkey`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L119-L127) — The preprocessor skipkey case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_pretty_print`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L135-L154) — The pretty print case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_pretty_print_and_short_empty_elements_consistency`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L433-L454) — The pretty print and short empty elements consistency case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_pretty_print_with_int_indent`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L193-L212) — The pretty print with int indent case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_attribute_name_starting_with_bang`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L362-L364) — The rejects attribute name starting with bang case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_attribute_name_starting_with_question`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L357-L359) — The rejects attribute name starting with question case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_attribute_name_with_angle_brackets`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L317-L323) — The rejects attribute name with angle brackets case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_attribute_name_with_slash`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L398-L400) — The rejects attribute name with slash case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_attribute_name_with_whitespace`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L403-L406) — The rejects attribute name with whitespace case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_malicious_xmlns_prefix`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L326-L337) — The rejects malicious xmlns prefix case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_names_with_quotes_and_equals`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L418-L430) — The rejects names with quotes and equals case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_non_string_names`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L374-L384) — The rejects non string names case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_tag_name_starting_with_bang`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L352-L354) — The rejects tag name starting with bang case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_tag_name_starting_with_question`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L347-L349) — The rejects tag name starting with question case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_tag_name_with_angle_brackets`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L311-L314) — The rejects tag name with angle brackets case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_tag_name_with_slash`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L387-L389) — The rejects tag name with slash case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_tag_name_with_whitespace`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L392-L395) — The rejects tag name with whitespace case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_xmlns_prefix_starting_with_question_or_bang`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L367-L371) — The rejects xmlns prefix starting with question or bang case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_xmlns_prefix_with_slash_or_whitespace`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L409-L415) — The rejects xmlns prefix with slash or whitespace case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_root`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L13-L16) — The root round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_semistructured`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L101-L103) — The semistructured round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_short_empty_elements`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L266-L268) — The short empty elements case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_simple_cdata`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L19-L22) — The simple cdata round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_unparse_rejects_comment_ending_with_hyphen`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L187-L190) — The unparse rejects comment ending with hyphen case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_unparse_rejects_comment_with_double_hyphen`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L181-L184) — The unparse rejects comment with double hyphen case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_unparse_with_element_comment`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L157-L160) — The unparse with element comment case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_unparse_with_multiple_element_comments`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L163-L166) — The unparse with multiple element comments case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_unparse_with_multiple_top_level_comments`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L175-L178) — The unparse with multiple top level comments case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_unparse_with_top_level_comment`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_dicttoxml.py#L169-L172) — The unparse with top level comment case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_xmltodict.py::test_attrib`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L105-L106) — The attrib parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_attrib_and_cdata`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L117-L118) — The attrib and cdata parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_comments`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L503-L529) — The comments case enables the dedicated CommentHandler and supplies neither a DOCTYPE nor an entity declaration.
- [ ] [`tests/test_xmltodict.py::test_custom_attrib`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L113-L114) — The custom attrib parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_custom_cdata`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L97-L98) — The custom cdata parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_disable_entities_false_returns_xmlbomb`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L426-L437) — The call explicitly sets disable_entities=False and skips the changed handler registrations, regardless of the test name.
- [ ] [`tests/test_xmltodict.py::test_encoded_string`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L223-L226) — The encoded string parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_force_cdata`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L24-L25) — The force cdata parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_force_list_basic`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L352-L371) — The force list basic parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_force_list_callable`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L374-L410) — The force list callable parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_keep_whitespace`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L146-L149) — The keep whitespace parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_list`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L101-L102) — The list parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_minimal`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L15-L17) — The minimal parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_namespace_collapse`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L260-L292) — The namespace collapse parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_namespace_collapse_all`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L295-L324) — The namespace collapse all parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_namespace_ignore`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L327-L349) — The namespace ignore parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_namespace_on_root_without_other_attrs`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L608-L629) — The namespace on root without other attrs parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_namespace_support`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L229-L257) — The namespace support parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_nested_semi_structured`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L126-L127) — The nested semi structured parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_postprocessor`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L190-L196) — The postprocessor parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_postprocessor_attribute`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L199-L205) — The postprocessor attribute parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_postprocessor_skip`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L208-L215) — The postprocessor skip parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_backwards_compatibility`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L84-L94) — The selective force cdata backwards compatibility parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_callable`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L54-L65) — The selective force cdata callable parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_empty_tuple`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L46-L51) — The selective force cdata empty tuple parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_nested_elements`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L68-L73) — The selective force cdata nested elements parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_single_element`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L38-L43) — The selective force cdata single element parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_tuple`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L28-L35) — The selective force cdata tuple parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_with_attributes`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L76-L81) — The selective force cdata with attributes parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_semi_structured`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L121-L123) — The semi structured parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_simple`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L20-L21) — The simple parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_skip_attrib`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L109-L110) — The skip attrib parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_skip_whitespace`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L130-L143) — The skip whitespace parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L152-L160) — The streaming parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming_attrs`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L589-L605) — The streaming attrs parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming_generator`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L170-L178) — The streaming generator parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming_interrupt`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L163-L167) — The streaming interrupt parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming_returns_none`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L181-L187) — The streaming returns none parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming_with_comments_and_attrs`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L532-L551) — The streaming with comments and attrs case enables the dedicated CommentHandler and supplies neither a DOCTYPE nor an entity declaration.
- [ ] [`tests/test_xmltodict.py::test_string_vs_file`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L10-L12) — The string vs file parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_unicode`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L218-L220) — The unicode parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.

#### unclassified (1)

- [ ] [`tests/test_xmltodict.py::test_streaming_memory_usage`](https://github.com/martinblech/xmltodict/blob/25b61a41f580cfc211df07c5fbbf603bd8eb5a5f/tests/test_xmltodict.py#L554-L586) — The generated elements have no entity or DOCTYPE declarations. The test also measures peak memory, and the effect of different Expat handler allocations on that threshold is unknown from source.

### Outside discovery (0)


## xmltodict_entity_policy

[martinblech/xmltodict](https://github.com/martinblech/xmltodict/commit/c986d2d37a93d45fcc059b09063d9d9c45a655ec) — Changes the default parser handler registrations from ignoring declarations to refusing them. The tests pin declaration inputs and a normal-comment control.

Before: `3d4d2d3a4cd0f68d1211dba549010261fa87b969`; after: `c986d2d37a93d45fcc059b09063d9d9c45a655ec`.

Label status: **draft**; author: CodeImpact agent; reviewer: none.
Frozen label SHA-256: `dea60191b78d98892a01b8c73d867185509ed3fcfdad46b908483390d970e4c0`.

### Complete Python change

````diff
--- base/tests/test_xmltodict.py
+++ head/tests/test_xmltodict.py
@@ -410,7 +410,7 @@
     assert parse(xml, force_list=force_list, dict_constructor=dict) == expectedResult
 
 
-def test_disable_entities_true_ignores_xmlbomb():
+def test_disable_entities_true_rejects_xmlbomb():
     xml = """
     <!DOCTYPE xmlbomb [
         <!ENTITY a "1234567890" >
@@ -419,13 +419,8 @@
     ]>
     <bomb>&c;</bomb>
     """
-    expectedResult = {'bomb': None}
-    try:
-        parse_attempt = parse(xml, disable_entities=True)
-    except expat.ExpatError:
-        assert True
-    else:
-        assert parse_attempt == expectedResult
+    with pytest.raises(expat.ExpatError, match="entities are disabled"):
+        parse(xml, disable_entities=True)
 
 
 def test_disable_entities_false_returns_xmlbomb():
@@ -442,20 +437,15 @@
     assert parse(xml, disable_entities=False) == expectedResult
 
 
-def test_disable_entities_true_ignores_external_dtd():
+def test_disable_entities_true_rejects_external_dtd():
     xml = """
     <!DOCTYPE external [
         <!ENTITY ee SYSTEM "http://www.python.org/">
     ]>
     <root>&ee;</root>
     """
-    expectedResult = {'root': None}
-    try:
-        parse_attempt = parse(xml, disable_entities=True)
-    except expat.ExpatError:
-        assert True
-    else:
-        assert parse_attempt == expectedResult
+    with pytest.raises(expat.ExpatError, match="entities are disabled"):
+        parse(xml, disable_entities=True)
 
 
 def test_disable_entities_true_attempts_external_dtd():
@@ -482,6 +472,16 @@
     expat.ParserCreate = ParserCreate
 
 
+def test_disable_entities_allows_comments_by_default():
+    xml = """
+    <a>
+        <!-- ignored -->
+        <b>1</b>
+    </a>
+    """
+    assert parse(xml) == {'a': {'b': '1'}}
+
+
 def test_comments():
     xml = """
     <a>
--- base/xmltodict.py
+++ head/xmltodict.py
@@ -354,10 +354,23 @@
         parser.CommentHandler = handler.comments
     parser.buffer_text = True
     if disable_entities:
-        # Anything not handled ends up here and entities aren't expanded.
-        parser.DefaultHandler = lambda x: None
-        # Expects an integer return; zero means failure -> expat.ExpatError.
-        parser.ExternalEntityRefHandler = lambda *x: 1
+        def _forbid_entities(*_args, **_kwargs):
+            raise expat.ExpatError("xmltodict.parse(): entities are disabled")
+
+        def _forbid_entities_default(text):
+            if not text:
+                return
+            stripped = text.lstrip()
+            if stripped.startswith('<!--'):
+                return
+            if stripped.startswith('<!') or stripped.startswith('&'):
+                _forbid_entities()
+
+        # Reject DTD/entity constructs explicitly instead of ignoring them.
+        parser.DefaultHandler = _forbid_entities_default
+        parser.EntityDeclHandler = _forbid_entities
+        parser.StartDoctypeDeclHandler = _forbid_entities
+        parser.ExternalEntityRefHandler = _forbid_entities
     if hasattr(xml_input, 'read'):
         parser.ParseFile(xml_input)
     elif isgenerator(xml_input):
````

### Draft labels and source

#### expected_affected (3)

- [ ] [`tests/test_xmltodict.py::test_disable_entities_allows_comments_by_default`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L475-L482) — Added control for the changed default-handler branch that permits comment data.
- [ ] [`tests/test_xmltodict.py::test_disable_entities_true_rejects_external_dtd`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L440-L448) — Renamed to assert an ExpatError for an external declaration under the new enabled rejection handlers.
- [ ] [`tests/test_xmltodict.py::test_disable_entities_true_rejects_xmlbomb`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L413-L423) — Renamed to require the new rejection behavior. It supplies entity declarations and explicitly leaves the guard enabled.

#### expected_unaffected (97)

- [ ] [`tests/test_dicttoxml.py::test_attr_order_roundtrip`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L130-L132) — The attr order roundtrip round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_attrib`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L31-L34) — The attrib round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_attrib_and_cdata`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L37-L40) — The attrib and cdata round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_attribute_values_with_angle_brackets_are_escaped`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L340-L344) — The attribute values with angle brackets are escaped case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_boolean_unparse`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L301-L308) — The boolean unparse case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_cdata`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L25-L28) — The cdata round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_comment_roundtrip_limited`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L215-L237) — The comment roundtrip limited case enables the dedicated CommentHandler and supplies neither a DOCTYPE nor an entity declaration.
- [ ] [`tests/test_dicttoxml.py::test_empty_dict_vs_empty_list_behavior`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L534-L557) — The empty dict vs empty list behavior case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_empty_list_filtering`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L457-L491) — The empty list filtering case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_empty_list_filtering_with_short_empty_elements_false`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L494-L510) — The empty list filtering with short empty elements false case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_encoding`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L240-L246) — The encoding round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_fulldoc`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L249-L253) — The fulldoc case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_generator`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L58-L64) — The generator round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_list`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L43-L46) — The list round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_list_expand_iter`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L49-L55) — The list expand iter case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_multiple_roots`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L72-L76) — The multiple roots case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_multiple_roots_nofulldoc`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L83-L89) — The multiple roots nofulldoc case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_namespace_support`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L271-L298) — The namespace support case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_nested`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L92-L98) — The nested round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_no_root`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L67-L69) — The no root case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_no_root_nofulldoc`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L79-L80) — The no root nofulldoc case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_non_empty_lists_are_not_filtered`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L513-L531) — The non empty lists are not filtered case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_non_string_attr`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L261-L263) — The non string attr case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_non_string_text_with_attributes`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L560-L596) — The non string text with attributes case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_non_string_value`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L256-L258) — The non string value case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_preprocessor`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L106-L116) — The preprocessor case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_preprocessor_skipkey`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L119-L127) — The preprocessor skipkey case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_pretty_print`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L135-L154) — The pretty print case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_pretty_print_and_short_empty_elements_consistency`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L433-L454) — The pretty print and short empty elements consistency case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_pretty_print_with_int_indent`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L193-L212) — The pretty print with int indent case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_attribute_name_starting_with_bang`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L362-L364) — The rejects attribute name starting with bang case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_attribute_name_starting_with_question`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L357-L359) — The rejects attribute name starting with question case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_attribute_name_with_angle_brackets`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L317-L323) — The rejects attribute name with angle brackets case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_attribute_name_with_slash`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L398-L400) — The rejects attribute name with slash case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_attribute_name_with_whitespace`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L403-L406) — The rejects attribute name with whitespace case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_malicious_xmlns_prefix`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L326-L337) — The rejects malicious xmlns prefix case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_names_with_quotes_and_equals`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L418-L430) — The rejects names with quotes and equals case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_non_string_names`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L374-L384) — The rejects non string names case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_tag_name_starting_with_bang`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L352-L354) — The rejects tag name starting with bang case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_tag_name_starting_with_question`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L347-L349) — The rejects tag name starting with question case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_tag_name_with_angle_brackets`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L311-L314) — The rejects tag name with angle brackets case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_tag_name_with_slash`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L387-L389) — The rejects tag name with slash case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_tag_name_with_whitespace`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L392-L395) — The rejects tag name with whitespace case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_xmlns_prefix_starting_with_question_or_bang`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L367-L371) — The rejects xmlns prefix starting with question or bang case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_rejects_xmlns_prefix_with_slash_or_whitespace`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L409-L415) — The rejects xmlns prefix with slash or whitespace case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_root`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L13-L16) — The root round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_semistructured`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L101-L103) — The semistructured round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_short_empty_elements`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L266-L268) — The short empty elements case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_simple_cdata`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L19-L22) — The simple cdata round trip uses XML without a DOCTYPE or entity declarations. The edited parser callbacks do not handle that input.
- [ ] [`tests/test_dicttoxml.py::test_unparse_rejects_comment_ending_with_hyphen`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L187-L190) — The unparse rejects comment ending with hyphen case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_unparse_rejects_comment_with_double_hyphen`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L181-L184) — The unparse rejects comment with double hyphen case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_unparse_with_element_comment`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L157-L160) — The unparse with element comment case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_unparse_with_multiple_element_comments`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L163-L166) — The unparse with multiple element comments case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_unparse_with_multiple_top_level_comments`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L175-L178) — The unparse with multiple top level comments case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_dicttoxml.py::test_unparse_with_top_level_comment`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_dicttoxml.py#L169-L172) — The unparse with top level comment case uses unparse's XML writer and does not create a parser.
- [ ] [`tests/test_xmltodict.py::test_attrib`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L105-L106) — The attrib parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_attrib_and_cdata`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L117-L118) — The attrib and cdata parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_comments`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L485-L511) — The comments case enables the dedicated CommentHandler and supplies neither a DOCTYPE nor an entity declaration.
- [ ] [`tests/test_xmltodict.py::test_custom_attrib`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L113-L114) — The custom attrib parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_custom_cdata`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L97-L98) — The custom cdata parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_disable_entities_false_returns_xmlbomb`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L426-L437) — The call explicitly sets disable_entities=False and skips the changed handler registrations, regardless of the test name.
- [ ] [`tests/test_xmltodict.py::test_disable_entities_true_attempts_external_dtd`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L451-L472) — The call explicitly sets disable_entities=False and skips the changed handler registrations, regardless of the test name.
- [ ] [`tests/test_xmltodict.py::test_encoded_string`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L223-L226) — The encoded string parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_force_cdata`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L24-L25) — The force cdata parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_force_list_basic`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L352-L371) — The force list basic parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_force_list_callable`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L374-L410) — The force list callable parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_keep_whitespace`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L146-L149) — The keep whitespace parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_list`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L101-L102) — The list parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_minimal`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L15-L17) — The minimal parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_namespace_collapse`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L260-L292) — The namespace collapse parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_namespace_collapse_all`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L295-L324) — The namespace collapse all parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_namespace_ignore`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L327-L349) — The namespace ignore parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_namespace_on_root_without_other_attrs`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L590-L611) — The namespace on root without other attrs parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_namespace_support`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L229-L257) — The namespace support parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_nested_semi_structured`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L126-L127) — The nested semi structured parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_postprocessor`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L190-L196) — The postprocessor parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_postprocessor_attribute`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L199-L205) — The postprocessor attribute parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_postprocessor_skip`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L208-L215) — The postprocessor skip parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_backwards_compatibility`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L84-L94) — The selective force cdata backwards compatibility parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_callable`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L54-L65) — The selective force cdata callable parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_empty_tuple`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L46-L51) — The selective force cdata empty tuple parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_nested_elements`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L68-L73) — The selective force cdata nested elements parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_single_element`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L38-L43) — The selective force cdata single element parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_tuple`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L28-L35) — The selective force cdata tuple parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_selective_force_cdata_with_attributes`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L76-L81) — The selective force cdata with attributes parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_semi_structured`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L121-L123) — The semi structured parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_simple`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L20-L21) — The simple parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_skip_attrib`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L109-L110) — The skip attrib parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_skip_whitespace`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L130-L143) — The skip whitespace parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L152-L160) — The streaming parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming_attrs`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L571-L587) — The streaming attrs parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming_generator`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L170-L178) — The streaming generator parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming_interrupt`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L163-L167) — The streaming interrupt parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming_returns_none`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L181-L187) — The streaming returns none parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_streaming_with_comments_and_attrs`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L514-L533) — The streaming with comments and attrs case enables the dedicated CommentHandler and supplies neither a DOCTYPE nor an entity declaration.
- [ ] [`tests/test_xmltodict.py::test_string_vs_file`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L10-L12) — The string vs file parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.
- [ ] [`tests/test_xmltodict.py::test_unicode`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L218-L220) — The unicode parse supplies element, attribute, or text content without a DOCTYPE or entity declaration. It does not exercise the changed declaration behavior.

#### unclassified (1)

- [ ] [`tests/test_xmltodict.py::test_streaming_memory_usage`](https://github.com/martinblech/xmltodict/blob/c986d2d37a93d45fcc059b09063d9d9c45a655ec/tests/test_xmltodict.py#L536-L568) — The generated elements have no entity or DOCTYPE declarations. The test also measures peak memory, and the effect of different Expat handler allocations on that threshold is unknown from source.

### Outside discovery (0)


## Selection exclusions

V6 ordering and eligibility as recorded in PROTOCOL.md

- [martinblech/xmltodict@d079849136b0](https://github.com/martinblech/xmltodict/commit/d079849136b031c471ec96a168ad7859ed5994ff): Release bookkeeping and version metadata only.
- [martinblech/xmltodict@a2a9ab7e0692](https://github.com/martinblech/xmltodict/commit/a2a9ab7e0692a62f64d97ff12553d0d53368c854): Publish workflow permission change only.
- [martinblech/xmltodict@656e6af9543e](https://github.com/martinblech/xmltodict/commit/656e6af9543e640fda7e96d6bdd6e693756687be): Release bookkeeping and version metadata only.
- [theskumar/python-dotenv@16f2bdad2ebb](https://github.com/theskumar/python-dotenv/commit/16f2bdad2ebbaae72790514cce713d2d22ab0f7c): Moves an unchanged helper and edits documentation and formatting. The flag behavior is already present in the parent.
- [theskumar/python-dotenv@666984de9a73](https://github.com/theskumar/python-dotenv/commit/666984de9a730a54438362b1adedd09bb1e9f5c7): The relevant CLI tests reach the exit replacement through external Click dispatch or a launched command.
- [theskumar/python-dotenv@02b68577f37d](https://github.com/theskumar/python-dotenv/commit/02b68577f37da2c4f4b9377d7a0ca2b58fdacf20): Ruff migration and formatting across the repository, with no focal behavior.
- [theskumar/python-dotenv@16e660d384b9](https://github.com/theskumar/python-dotenv/commit/16e660d384b942b11879b44500afbbe021650448): Package version and release metadata only.
- [theskumar/python-dotenv@667e82f18d6e](https://github.com/theskumar/python-dotenv/commit/667e82f18d6e5306894c8746c46b1da2d031bd23): Changelog only.
- [theskumar/python-dotenv@9d85edb3b865](https://github.com/theskumar/python-dotenv/commit/9d85edb3b8652de4601f9ad8a7a49ad9909f898a): The Windows behavior needs an external Click and subprocess execution path. The captured tests do not isolate the Windows branch.
- [asottile/tokenize-rt@2ea376551908](https://github.com/asottile/tokenize-rt/commit/2ea37655190845d13ae7756b066685014e398628): Merge with multiple parents.
- [asottile/tokenize-rt@59343a43b4ba](https://github.com/asottile/tokenize-rt/commit/59343a43b4ba869f7d2b711b776fe85182c5cf20): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@77f75bdadee3](https://github.com/asottile/tokenize-rt/commit/77f75bdadee3b2c57ccb3dcc6078cbd5d0331711): Merge with multiple parents.
- [asottile/tokenize-rt@23b33a0edf34](https://github.com/asottile/tokenize-rt/commit/23b33a0edf3403ca42ea3db681e4a38342a7ae1d): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@b2f4fb778686](https://github.com/asottile/tokenize-rt/commit/b2f4fb77868698b9bcdf565c88e46a7efcfd919a): Merge with multiple parents.
- [asottile/tokenize-rt@3bef5e00c8a7](https://github.com/asottile/tokenize-rt/commit/3bef5e00c8a732da10dd1549263102508a7d8029): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@d3874b787677](https://github.com/asottile/tokenize-rt/commit/d3874b787677593fc34aedf7174a2934e2caa94b): Merge with multiple parents.
- [asottile/tokenize-rt@200023563d5e](https://github.com/asottile/tokenize-rt/commit/200023563d5e38de4334f859d422595a5a3387be): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@bcc3c664874b](https://github.com/asottile/tokenize-rt/commit/bcc3c664874b810b40398065cb8c7d5c75030aa7): Merge with multiple parents.
- [asottile/tokenize-rt@0b4e506ea21f](https://github.com/asottile/tokenize-rt/commit/0b4e506ea21f46007e9e4420fcdb8bfbafadcaa6): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@94ef0f9d66d6](https://github.com/asottile/tokenize-rt/commit/94ef0f9d66d681c8cf75d60cb50f37484a6dc1bb): Merge with multiple parents.
- [asottile/tokenize-rt@d5e695e54d38](https://github.com/asottile/tokenize-rt/commit/d5e695e54d38292cbcd63f7e56c89c9025f110a9): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@ccae6e345530](https://github.com/asottile/tokenize-rt/commit/ccae6e3455302c9b88c030591c1f3ac8ba352faf): Merge with multiple parents.
- [asottile/tokenize-rt@64e37114c350](https://github.com/asottile/tokenize-rt/commit/64e37114c350aae8ba3e1b4b6dc2a203b8c0c6d5): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@606dc2211b87](https://github.com/asottile/tokenize-rt/commit/606dc2211b872f04ef49256ee560e57516e3a1b7): Merge with multiple parents.
- [asottile/tokenize-rt@4b03e57c5c62](https://github.com/asottile/tokenize-rt/commit/4b03e57c5c6247d83ff75e60277ee729cbc3e5c0): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@1582bcf0259d](https://github.com/asottile/tokenize-rt/commit/1582bcf0259d183259da1761444c6fc73fa7ad9a): Configuration or release metadata only (setup.cfg).
- [asottile/tokenize-rt@07ad77b23e3e](https://github.com/asottile/tokenize-rt/commit/07ad77b23e3e102f92ee1a97ad4d3e283d1c398e): Merge with multiple parents.
- [asottile/tokenize-rt@ed9a32cc33e4](https://github.com/asottile/tokenize-rt/commit/ed9a32cc33e454dea90a7715663453b7070bb8cd): Merge with multiple parents.
- [asottile/tokenize-rt@09148b30c80e](https://github.com/asottile/tokenize-rt/commit/09148b30c80e5e97599a141d7a0e23d01290596b): Configuration or release metadata only (setup.cfg).
- [asottile/tokenize-rt@9dd86b710108](https://github.com/asottile/tokenize-rt/commit/9dd86b710108e783094d6e63698814c008fd0250): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@82fd4e13b3b4](https://github.com/asottile/tokenize-rt/commit/82fd4e13b3b4ac8f4c344f51b1b77e7937aa61ba): Merge with multiple parents.
- [asottile/tokenize-rt@d3a79470d82e](https://github.com/asottile/tokenize-rt/commit/d3a79470d82e77d938c9e250e85c1825ae064912): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@2052c5939a8f](https://github.com/asottile/tokenize-rt/commit/2052c5939a8f1ddb9ccdc945a732e29f250355ec): Merge with multiple parents.
- [asottile/tokenize-rt@7debf602d6b5](https://github.com/asottile/tokenize-rt/commit/7debf602d6b5a5fcb4aa2ae902dbf1e6fd2af3ba): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@fce6e6745094](https://github.com/asottile/tokenize-rt/commit/fce6e674509468d22f884c6b361dbb4564d6b7d0): Merge with multiple parents.
- [asottile/tokenize-rt@c0aa27b20f98](https://github.com/asottile/tokenize-rt/commit/c0aa27b20f98753c74e86bb83e5dfef647bd649c): Configuration or release metadata only (.github/workflows/main.yml).
- [asottile/tokenize-rt@ff8337fa67e4](https://github.com/asottile/tokenize-rt/commit/ff8337fa67e49c27cbaf755a8f3e45d6e7488bb3): Merge with multiple parents.
- [asottile/tokenize-rt@34e4619397df](https://github.com/asottile/tokenize-rt/commit/34e4619397df919daed01d63aa6263e9f148d94b): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@413692b7c1ad](https://github.com/asottile/tokenize-rt/commit/413692b7c1ad8a873caec39dd4f427d55ee538ea): Merge with multiple parents.
- [asottile/tokenize-rt@123aaf54b539](https://github.com/asottile/tokenize-rt/commit/123aaf54b5390d2e97810ef125c613c4e1c4cfd1): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@956ea47ad95f](https://github.com/asottile/tokenize-rt/commit/956ea47ad95ffb642ce6c4becb2101b74dd9e345): Merge with multiple parents.
- [asottile/tokenize-rt@dfa21941abc9](https://github.com/asottile/tokenize-rt/commit/dfa21941abc9de43c763eb437d493baf995c8299): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@a661ff9e465f](https://github.com/asottile/tokenize-rt/commit/a661ff9e465ff05065b2380be2991668a0fb1d76): Merge with multiple parents.
- [asottile/tokenize-rt@23619a477011](https://github.com/asottile/tokenize-rt/commit/23619a47701177efdcaf5d53728f5991ecef0f35): Configuration or release metadata only (.pre-commit-config.yaml).
- [asottile/tokenize-rt@532687a2c2f5](https://github.com/asottile/tokenize-rt/commit/532687a2c2f5f6583ba4e60e6b62650360833dd8): Merge with multiple parents.
- [asottile/tokenize-rt@a3a7bed0a05d](https://github.com/asottile/tokenize-rt/commit/a3a7bed0a05d82af907cbfa14437715f7bb91b5d): Configuration or release metadata only (setup.cfg).
- [asottile/tokenize-rt@3686bae7ade9](https://github.com/asottile/tokenize-rt/commit/3686bae7ade95e9feb14bb9eb97a4f23e06fba8d): Merge with multiple parents.
