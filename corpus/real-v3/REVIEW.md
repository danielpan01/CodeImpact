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

## inflection_rules

[jpvanhal/inflection](https://github.com/jpvanhal/inflection/commit/1969b3a06a9ff06d023863e388cf8af01978d297) — Add passerby/passersby plural and singular rules with parameter examples.

Before: `2d2d37951f6c8871d27a1c74a2c0c1fe6a9354fb`; after: `1969b3a06a9ff06d023863e388cf8af01978d297`.

Label status: **draft**; author: Codex (agent draft, November 14, 2026); reviewer: none.
Frozen label SHA-256: `06a2d53a2397dc754219ac7538efdec41fdb5ebc1c264b835c1e9062a8d4f0e1`.

### Complete Python change

````diff
--- base/inflection.py
+++ head/inflection.py
@@ -20,6 +20,7 @@
     (r"(?i)^(ox)$", r'\1en'),
     (r"(?i)(m|l)ice$", r'\1ice'),
     (r"(?i)(m|l)ouse$", r'\1ice'),
+    (r"(?i)(passer)s?by$", r'\1sby'),
     (r"(?i)(matr|vert|ind)(?:ix|ex)$", r'\1ices'),
     (r"(?i)(x|ch|ss|sh)$", r'\1es'),
     (r"(?i)([^aeiouy]|qu)y$", r'\1ies'),
@@ -44,6 +45,7 @@
     (r"(?i)(quiz)zes$", r'\1'),
     (r"(?i)(matr)ices$", r'\1ix'),
     (r"(?i)(vert|ind)ices$", r'\1ex'),
+    (r"(?i)(passer)sby$", r'\1by'),
     (r"(?i)^(ox)en", r'\1'),
     (r"(?i)(alias|status)(es)?$", r'\1'),
     (r"(?i)(octop|vir)(us|i)$", r'\1us'),
--- base/test_inflection.py
+++ head/test_inflection.py
@@ -70,6 +70,7 @@
     ("perspective", "perspectives"),
 
     ("ox", "oxen"),
+    ("passerby", "passersby"),
     ("photo", "photos"),
     ("buffalo", "buffaloes"),
     ("tomato", "tomatoes"),
````

### Draft labels and source

#### expected_affected (6)

- [ ] [`test_inflection.py::test_pluralize_plural`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L330-L332) — Calls pluralize on countable plural inputs from the changed parameter table and consults PLURALS.
- [ ] [`test_inflection.py::test_pluralize_plurals`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L275-L277) — Calls pluralize with nonempty countable words, consulting the edited PLURALS rules.
- [ ] [`test_inflection.py::test_pluralize_singular`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L318-L320) — Calls pluralize over SINGULAR_TO_PLURAL, including the added passerby variant; reaches edited PLURALS.
- [ ] [`test_inflection.py::test_singularize_plural`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L324-L326) — Calls singularize over SINGULAR_TO_PLURAL, including added passersby; reaches edited SINGULARS.
- [ ] [`test_inflection.py::test_tableize`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L428-L429) — Calls tableize, which calls pluralize(underscore(word)); countable inputs reach the edited PLURALS table.
- [ ] [`test_inflection.py::test_uncountable_word_is_not_greedy`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L294-L314) — The sponsor/sponsors assertions reach pluralize/singularize rule loops; the edited PLURALS/SINGULARS data are dependencies despite the uncountable controls.

#### expected_unaffected (16)

- [ ] [`test_inflection.py::test_camelize`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L341-L342) — Calls camelize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_camelize_with_lower_downcases_the_first_letter`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L345-L346) — Calls camelize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_camelize_with_underscores`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L349-L350) — Calls camelize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_dasherize`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L423-L424) — Calls dasherize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_humanize`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L408-L409) — Calls humanize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_ordinal`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L413-L414) — Calls ordinal with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_ordinalize`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L418-L419) — Calls ordinalize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_parameterize`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L365-L366) — Calls parameterize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_parameterize_and_normalize`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L373-L374) — Calls parameterize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_parameterize_with_custom_separator`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L381-L382) — Calls parameterize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_parameterize_with_multi_character_separator`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L389-L396) — Calls parameterize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_parameterize_with_no_separator`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L403-L404) — Calls parameterize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_pluralize_empty_string`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L280-L281) — The literal empty input returns before pluralize reads PLURALS; no rule-table dependency on this path.
- [ ] [`test_inflection.py::test_titleize`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L336-L337) — Calls titleize with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_uncountability`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L288-L291) — Parameters come from unchanged UNCOUNTABLES. Both pluralize and singularize return on these entries before consulting the edited rule tables.
- [ ] [`test_inflection.py::test_underscore`](https://github.com/jpvanhal/inflection/blob/1969b3a06a9ff06d023863e388cf8af01978d297/test_inflection.py#L357-L358) — Calls underscore with unchanged test data. These paths do not depend on the edited PLURALS/SINGULARS tables or changed singular/plural parameter data; shared module import alone does not establish this dependency.

#### unclassified (0)


## inflection_title

[jpvanhal/inflection](https://github.com/jpvanhal/inflection/commit/e32443bb7dc1ba91a15336b5baab908d25f4b93a) — Preserve Unicode capitalization in titleize and extend its parameter data.

Before: `1969b3a06a9ff06d023863e388cf8af01978d297`; after: `e32443bb7dc1ba91a15336b5baab908d25f4b93a`.

Label status: **draft**; author: Codex (agent draft, November 14, 2026); reviewer: none.
Frozen label SHA-256: `4f521b67239bc737ddf718fd76d093f45767f6c4210e8832bac061e68f47e698`.

### Complete Python change

````diff
--- base/inflection.py
+++ head/inflection.py
@@ -370,9 +370,9 @@
 
     """
     return re.sub(
-        r"\b('?[a-z])",
+        r"\b('?\w)",
         lambda match: match.group(1).capitalize(),
-        humanize(underscore(word))
+        humanize(underscore(word)).title()
     )
 
 
--- base/test_inflection.py
+++ head/test_inflection.py
@@ -191,6 +191,8 @@
     ("david's code",          "David's Code"),
     ("David's code",          "David's Code"),
     ("david's Code",          "David's Code"),
+    ("ana índia",             "Ana Índia"),
+    ("Ana Índia",             "Ana Índia"),
 )
 
 
````

### Draft labels and source

#### expected_affected (1)

- [ ] [`test_inflection.py::test_titleize`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L338-L339) — Directly calls edited titleize; its MIXTURE_TO_TITLEIZED parameter data also change.

#### expected_unaffected (21)

- [ ] [`test_inflection.py::test_camelize`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L343-L344) — Calls camelize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_camelize_with_lower_downcases_the_first_letter`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L347-L348) — Calls camelize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_camelize_with_underscores`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L351-L352) — Calls camelize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_dasherize`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L425-L426) — Calls dasherize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_humanize`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L410-L411) — Calls humanize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_ordinal`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L415-L416) — Calls ordinal with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_ordinalize`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L420-L421) — Calls ordinalize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_parameterize`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L367-L368) — Calls parameterize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_parameterize_and_normalize`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L375-L376) — Calls parameterize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_parameterize_with_custom_separator`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L383-L384) — Calls parameterize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_parameterize_with_multi_character_separator`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L391-L398) — Calls parameterize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_parameterize_with_no_separator`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L405-L406) — Calls parameterize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_pluralize_empty_string`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L282-L283) — Calls pluralize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_pluralize_plural`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L332-L334) — Calls pluralize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_pluralize_plurals`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L277-L279) — Calls pluralize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_pluralize_singular`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L320-L322) — Calls pluralize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_singularize_plural`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L326-L328) — Calls singularize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_tableize`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L430-L431) — Calls tableize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_uncountability`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L290-L293) — Calls pluralize, singularize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_uncountable_word_is_not_greedy`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L296-L316) — Calls pluralize, singularize with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.
- [ ] [`test_inflection.py::test_underscore`](https://github.com/jpvanhal/inflection/blob/e32443bb7dc1ba91a15336b5baab908d25f4b93a/test_inflection.py#L359-L360) — Calls underscore with unchanged test data. These paths do not depend on titleize or its changed parameter table; shared module import alone does not establish this dependency.

#### unclassified (0)


## iso8601_errors

[micktwomey/pyiso8601](https://github.com/micktwomey/pyiso8601/commit/fde429d40d82057d2507c657b9a7bbd30e369aa8) — Make is_iso8601 raise ParseError for invalid input instead of returning False.

Before: `21f536815328987631d374421d928aab2255e3da`; after: `fde429d40d82057d2507c657b9a7bbd30e369aa8`.

Label status: **draft**; author: Codex (agent draft, November 14, 2026); reviewer: none.
Frozen label SHA-256: `1a8505dca9133aeb4312f6133ebc9942e65a62f3ea8fb92267bbadc5f5381604`.

### Complete Python change

````diff
--- base/iso8601/iso8601.py
+++ head/iso8601/iso8601.py
@@ -158,5 +158,5 @@
     try:
         m = ISO8601_REGEX.match(datestring)
         return bool(m)
-    except Exception:
-        return False
+    except Exception as e:
+        raise ParseError(e)
````

### Draft labels and source

#### expected_affected (2)

- [ ] [`iso8601/test_iso8601.py::test_parse_invalid_date`](https://github.com/micktwomey/pyiso8601/blob/fde429d40d82057d2507c657b9a7bbd30e369aa8/iso8601/test_iso8601.py#L62-L67) — Directly calls the edited/added is_iso8601 validator. The validator-addition revision also changes this test body; dependency does not assert every parameter reaches an exception branch.
- [ ] [`iso8601/test_iso8601.py::test_parse_valid_date`](https://github.com/micktwomey/pyiso8601/blob/fde429d40d82057d2507c657b9a7bbd30e369aa8/iso8601/test_iso8601.py#L244-L263) — Directly calls the edited/added is_iso8601 validator. The validator-addition revision also changes this test body; dependency does not assert every parameter reaches an exception branch.

#### expected_unaffected (6)

- [ ] [`iso8601/test_iso8601.py::test_fixedoffset_eq`](https://github.com/micktwomey/pyiso8601/blob/fde429d40d82057d2507c657b9a7bbd30e369aa8/iso8601/test_iso8601.py#L20-L22) — Compares unchanged FixedOffset objects; does not use the validator.
- [ ] [`iso8601/test_iso8601.py::test_hypothesis_valid_datetimes_with_timezone`](https://github.com/micktwomey/pyiso8601/blob/fde429d40d82057d2507c657b9a7bbd30e369aa8/iso8601/test_iso8601.py#L277-L281) — Timezone-aware generated strings go to unchanged parse_date; no dependency on is_iso8601.
- [ ] [`iso8601/test_iso8601.py::test_hypothesis_valid_naive_datetimes`](https://github.com/micktwomey/pyiso8601/blob/fde429d40d82057d2507c657b9a7bbd30e369aa8/iso8601/test_iso8601.py#L267-L271) — Generated datetime strings go to unchanged parse_date; no validator call in this test or parse_date.
- [ ] [`iso8601/test_iso8601.py::test_iso8601_regex`](https://github.com/micktwomey/pyiso8601/blob/fde429d40d82057d2507c657b9a7bbd30e369aa8/iso8601/test_iso8601.py#L16-L17) — Calls unchanged ISO8601_REGEX.match directly; does not call is_iso8601.
- [ ] [`iso8601/test_iso8601.py::test_parse_no_timezone_different_default`](https://github.com/micktwomey/pyiso8601/blob/fde429d40d82057d2507c657b9a7bbd30e369aa8/iso8601/test_iso8601.py#L25-L29) — Calls unchanged parse_date with a FixedOffset default; parse_date does not call is_iso8601.
- [ ] [`iso8601/test_iso8601.py::test_parse_utc_different_default`](https://github.com/micktwomey/pyiso8601/blob/fde429d40d82057d2507c657b9a7bbd30e369aa8/iso8601/test_iso8601.py#L32-L36) — Calls unchanged parse_date with an explicit offset; it has no dependency on is_iso8601.

#### unclassified (0)


## iso8601_validator

[micktwomey/pyiso8601](https://github.com/micktwomey/pyiso8601/commit/21f536815328987631d374421d928aab2255e3da) — Introduce and export is_iso8601; use it in valid/invalid date tests.

Before: `406db6f23ffbf6815a320c30be070b89d28e2974`; after: `21f536815328987631d374421d928aab2255e3da`.

Label status: **draft**; author: Codex (agent draft, November 14, 2026); reviewer: none.
Frozen label SHA-256: `1a8505dca9133aeb4312f6133ebc9942e65a62f3ea8fb92267bbadc5f5381604`.

### Complete Python change

````diff
--- base/iso8601/__init__.py
+++ head/iso8601/__init__.py
@@ -1,3 +1,3 @@
-from .iso8601 import UTC, FixedOffset, ParseError, parse_date
+from .iso8601 import UTC, FixedOffset, ParseError, is_iso8601, parse_date
 
-__all__ = ["parse_date", "ParseError", "UTC", "FixedOffset"]
+__all__ = ["parse_date", "is_iso8601" "ParseError", "UTC", "FixedOffset"]
--- base/iso8601/iso8601.py
+++ head/iso8601/iso8601.py
@@ -147,3 +147,16 @@
         )
     except Exception as e:
         raise ParseError(e)
+
+
+def is_iso8601(datestring: str) -> bool:
+    """Check if a string matches an ISO 8601 format.
+
+    :param datestring: The string to check for validity
+    :returns: True if the string matches an ISO 8601 format, False otherwise
+    """
+    try:
+        m = ISO8601_REGEX.match(datestring)
+        return bool(m)
+    except Exception:
+        return False
--- base/iso8601/test_iso8601.py
+++ head/iso8601/test_iso8601.py
@@ -60,6 +60,7 @@
     ],
 )
 def test_parse_invalid_date(invalid_date: str, error_string: str) -> None:
+    assert iso8601.is_iso8601(invalid_date) is False
     with pytest.raises(iso8601.ParseError) as exc:
         iso8601.parse_date(invalid_date)
     assert exc.errisinstance(iso8601.ParseError)
@@ -243,6 +244,7 @@
 def test_parse_valid_date(
     valid_date: str, expected_datetime: datetime.datetime, isoformat: str
 ) -> None:
+    assert iso8601.is_iso8601(valid_date) is True
     parsed = iso8601.parse_date(valid_date)
     assert parsed.year == expected_datetime.year
     assert parsed.month == expected_datetime.month
````

### Draft labels and source

#### expected_affected (2)

- [ ] [`iso8601/test_iso8601.py::test_parse_invalid_date`](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/iso8601/test_iso8601.py#L62-L67) — Directly calls the edited/added is_iso8601 validator. The validator-addition revision also changes this test body; dependency does not assert every parameter reaches an exception branch.
- [ ] [`iso8601/test_iso8601.py::test_parse_valid_date`](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/iso8601/test_iso8601.py#L244-L263) — Directly calls the edited/added is_iso8601 validator. The validator-addition revision also changes this test body; dependency does not assert every parameter reaches an exception branch.

#### expected_unaffected (6)

- [ ] [`iso8601/test_iso8601.py::test_fixedoffset_eq`](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/iso8601/test_iso8601.py#L20-L22) — Compares unchanged FixedOffset objects; does not use the validator.
- [ ] [`iso8601/test_iso8601.py::test_hypothesis_valid_datetimes_with_timezone`](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/iso8601/test_iso8601.py#L277-L281) — Timezone-aware generated strings go to unchanged parse_date; no dependency on is_iso8601.
- [ ] [`iso8601/test_iso8601.py::test_hypothesis_valid_naive_datetimes`](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/iso8601/test_iso8601.py#L267-L271) — Generated datetime strings go to unchanged parse_date; no validator call in this test or parse_date.
- [ ] [`iso8601/test_iso8601.py::test_iso8601_regex`](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/iso8601/test_iso8601.py#L16-L17) — Calls unchanged ISO8601_REGEX.match directly; does not call is_iso8601.
- [ ] [`iso8601/test_iso8601.py::test_parse_no_timezone_different_default`](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/iso8601/test_iso8601.py#L25-L29) — Calls unchanged parse_date with a FixedOffset default; parse_date does not call is_iso8601.
- [ ] [`iso8601/test_iso8601.py::test_parse_utc_different_default`](https://github.com/micktwomey/pyiso8601/blob/21f536815328987631d374421d928aab2255e3da/iso8601/test_iso8601.py#L32-L36) — Calls unchanged parse_date with an explicit offset; it has no dependency on is_iso8601.

#### unclassified (0)


## ordered_set_pop

[rspeer/ordered-set](https://github.com/rspeer/ordered-set/commit/1f93c9d7376dec495e1573c9c02837bce96e1c9f) — Add an index argument to OrderedSet.pop; tests in test.py are outside discovery.

Before: `34f08cef01e5a555c8441ac0bfd9d950ed823164`; after: `1f93c9d7376dec495e1573c9c02837bce96e1c9f`.

Label status: **draft**; author: Codex (agent draft, November 14, 2026); reviewer: none.
Frozen label SHA-256: `c1b7b469b5b27e9284c6f6b8acdf2caffa968023960f8ccc27d284499df1d972`.

### Complete Python change

````diff
--- base/ordered_set.py
+++ head/ordered_set.py
@@ -230,11 +230,12 @@
     get_loc = index
     get_indexer = index
 
-    def pop(self) -> T:
-        """
-        Remove and return the last element from the set.
+    def pop(self, index=-1) -> T:
+        """
+        Remove and return item at index (default last).
 
         Raises KeyError if the set is empty.
+        Raises IndexError if index is out of range.
 
         Example:
             >>> oset = OrderedSet([1, 2, 3])
@@ -244,8 +245,8 @@
         if not self.items:
             raise KeyError("Set is empty")
 
-        elem = self.items[-1]
-        del self.items[-1]
+        elem = self.items[index]
+        del self.items[index]
         del self.map[elem]
         return elem
 
````

### Draft labels and source

#### expected_affected (0)


#### expected_unaffected (0)


#### unclassified (0)


## ordered_set_syntax

[rspeer/ordered-set](https://github.com/rspeer/ordered-set/commit/b6bb881ea69c8ddde087691c1bfd5e37952ca928) — Repair an invalid f-string in OrderedSet.update, restoring module parsing.

Before: `8c837171201e3d089630e8b67645cb813b57c8dd`; after: `b6bb881ea69c8ddde087691c1bfd5e37952ca928`.

Label status: **draft**; author: Codex (agent draft, November 14, 2026); reviewer: none.
Frozen label SHA-256: `bfee4b6be5ef0e239fe30ac5478abd02c7e9d3dd8c9d65a057a2d1b8a1b9de39`.

### Complete Python change

````diff
--- base/ordered_set/__init__.py
+++ head/ordered_set/__init__.py
@@ -215,7 +215,7 @@
             for item in sequence:
                 item_index = self.add(item)
         except TypeError:
-            raise ValueError(f"Argument needs to be an iterable, got {type(sequence}")
+            raise ValueError(f"Argument needs to be an iterable, got {type(sequence)}")
         return item_index
 
     @overload
````

### Draft labels and source

#### expected_affected (30)

- [ ] [`test/test_ordered_set.py::test_binary_operations`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L32-L39) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_bitwise_and_consistency`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L378-L387) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_clear`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L130-L135) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_comparisons`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L212-L219) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_empty_pickle`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L19-L22) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_empty_repr`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L178-L180) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_eq_wrong_type`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L183-L185) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_fancy_index_class`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L78-L81) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_getitem_type_error`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L165-L168) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_indexing`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L42-L55) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_operator_consistency_difference`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L324-L332) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_operator_consistency_disjoint`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L371-L375) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_operator_consistency_isect`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L315-L321) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_operator_consistency_subset`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L353-L358) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_operator_consistency_superset`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L361-L368) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_operator_consistency_union`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L344-L350) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_operator_consistency_xor`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L335-L341) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_order`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L25-L29) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_ordered_equality`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L188-L193) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_ordered_inequality`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L196-L209) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_pandas_compat`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L84-L87) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_pickle`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L13-L16) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_pop`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L153-L162) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_remove`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L98-L120) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_remove_error`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L123-L127) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_tuples`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L90-L95) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_unordered_equality`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L222-L239) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_unordered_inequality`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L242-L252) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_update`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L138-L150) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.
- [ ] [`test/test_ordered_set.py::test_update_value_error`](https://github.com/rspeer/ordered-set/blob/b6bb881ea69c8ddde087691c1bfd5e37952ca928/test/test_ordered_set.py#L171-L175) — This test uses OrderedSet directly or through _operator_consistency_testdata. The top-level import requires ordered_set/__init__.py to parse; the repaired f-string restores that shared import dependency. No claim that every test calls update or its error branch.

#### expected_unaffected (0)


#### unclassified (0)


## Selection exclusions

Pre-analysis purposive sample: two bounded functional changes each across three previously unused MIT repositories. Source-only selection, complete supported trees, explicit metadata exclusions and no analyzer-informed replacement. HTTMock excluded for unsupported license; historical changes and repeated test definitions are not independent or representative samples. See PROTOCOL.md.

- [micktwomey/pyiso8601@00c9262b9ad1](https://github.com/micktwomey/pyiso8601/commit/00c9262b9ad141f287b3263be7f2244fa01988c2): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #39 from micktwomey/update-build-env
- [micktwomey/pyiso8601@c9b45e09dadf](https://github.com/micktwomey/pyiso8601/commit/c9b45e09dadfd8da5098d2dbd1f4e4533d929ca9): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Update development environment
- [micktwomey/pyiso8601@c147acc8952b](https://github.com/micktwomey/pyiso8601/commit/c147acc8952bf279a38d5cab1f80be71735a10cf): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Release 2.1.0
- [micktwomey/pyiso8601@2a4a78d85159](https://github.com/micktwomey/pyiso8601/commit/2a4a78d85159ab6dc38461fc8499941720b643a5): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #33 from micktwomey/python-3.12
- [micktwomey/pyiso8601@15104f3a5b2a](https://github.com/micktwomey/pyiso8601/commit/15104f3a5b2a4c2ac90ed1199a3a0cc38da37c44): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Add readthedocs configuration
- [micktwomey/pyiso8601@55cc57057c7d](https://github.com/micktwomey/pyiso8601/commit/55cc57057c7ddb253f51f50fccc40ffdb6238f11): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Bump dependencies and use official python 3.12 release in github actions
- [micktwomey/pyiso8601@c28cb09cd129](https://github.com/micktwomey/pyiso8601/commit/c28cb09cd1291c880bd46365b4eed0cc825f77c8): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #31 from micktwomey/bump-poetry-lock
- [micktwomey/pyiso8601@55e229dbdfbf](https://github.com/micktwomey/pyiso8601/commit/55e229dbdfbfcd8e35a530b7961a77faedca6a23): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Update poetry lock
- [micktwomey/pyiso8601@2f3b230359ff](https://github.com/micktwomey/pyiso8601/commit/2f3b230359ffe75fe8cbdba99824e8d6a8f71b8c): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Fixup CHANGELOG release links
- [micktwomey/pyiso8601@c4020e136764](https://github.com/micktwomey/pyiso8601/commit/c4020e136764444ca72403ce1a3249a9f645c26a): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Add version links to CHANGELOG.md
- [micktwomey/pyiso8601@dd2268b0941e](https://github.com/micktwomey/pyiso8601/commit/dd2268b0941e2f4cd31b6ce1a3d7365731656cce): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Switch to ruff for linting
- [micktwomey/pyiso8601@0c56e9b3122e](https://github.com/micktwomey/pyiso8601/commit/0c56e9b3122e2e86db481283d26d43b67e6db00e): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Release 2.0.0
- [micktwomey/pyiso8601@3ebb054ae884](https://github.com/micktwomey/pyiso8601/commit/3ebb054ae8848fb1b4c08767292c90c783ac624a): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Re-lock poetry lock file
- [micktwomey/pyiso8601@7af51f6272d8](https://github.com/micktwomey/pyiso8601/commit/7af51f6272d87b5d4efe1f5f2198a050331ef726): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Switch to CHANGELOG.md for changelogs
- [micktwomey/pyiso8601@23d7949727dc](https://github.com/micktwomey/pyiso8601/commit/23d7949727dc41ad55c73a2581a8c479bec51c7b): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Update pre-commit dependencies
- [micktwomey/pyiso8601@4a79a97b48f5](https://github.com/micktwomey/pyiso8601/commit/4a79a97b48f56aa581742ebb007e654a12b552de): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Add devenv for development
- [micktwomey/pyiso8601@95f06e32fc86](https://github.com/micktwomey/pyiso8601/commit/95f06e32fc8669d8baffb97667043ed1327f1d5e): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Bump dependencies
- [micktwomey/pyiso8601@96765716a4bc](https://github.com/micktwomey/pyiso8601/commit/96765716a4bc7762ad5433586534b834ceba886c): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Test Python 3.12-dev
- [micktwomey/pyiso8601@9911ae2d83e5](https://github.com/micktwomey/pyiso8601/commit/9911ae2d83e5f6374697bce2d961302e4cf53483): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Add assertion to test_fixedoffset_eq and bump test dependencies
- [micktwomey/pyiso8601@7b343b27611b](https://github.com/micktwomey/pyiso8601/commit/7b343b27611b60bd6d4d7be368bedd038e4a2aa6): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Bump certifi from 2022.9.24 to 2022.12.7
- [micktwomey/pyiso8601@bac0dd9363a3](https://github.com/micktwomey/pyiso8601/commit/bac0dd9363a3c95eba5b033aa93c2c274915c1a7): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Freshen up the README and docs
- [micktwomey/pyiso8601@3b883c3ec9cf](https://github.com/micktwomey/pyiso8601/commit/3b883c3ec9cf7e4aeea6486cdd0012dafb2da5df): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Drop Python 3.6 support
- [micktwomey/pyiso8601@e3b4ed3deb40](https://github.com/micktwomey/pyiso8601/commit/e3b4ed3deb40bdff78339281590a841d14811ee0): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Release 1.1.0
- [micktwomey/pyiso8601@56da11c09b10](https://github.com/micktwomey/pyiso8601/commit/56da11c09b1026e65a248c12a53c6ada94766751): Additional candidate outside the two-change sample; only commit metadata inspected, not rejected based on analyzer behavior. Title: missed a comma
- [micktwomey/pyiso8601@406db6f23ffb](https://github.com/micktwomey/pyiso8601/commit/406db6f23ffbf6815a320c30be070b89d28e2974): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Update license years
- [micktwomey/pyiso8601@46baabb7c6b3](https://github.com/micktwomey/pyiso8601/commit/46baabb7c6b3619d9ac8efd90aebaeb32d25b97d): Additional candidate outside the two-change sample; only commit metadata inspected, not rejected based on analyzer behavior. Title: Add an `__all__` to `__init.py__`
- [micktwomey/pyiso8601@4ddd936799b4](https://github.com/micktwomey/pyiso8601/commit/4ddd936799b42548afffe62f7daefa9ee75d2c27): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Remove branch filter from pull requests
- [micktwomey/pyiso8601@c8ac7857bcd2](https://github.com/micktwomey/pyiso8601/commit/c8ac7857bcd2a95f09199b8fdd0834d598234ab6): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Add missing py.typed file
- [patrys/httmock@98269075d0c3](https://github.com/patrys/httmock/commit/98269075d0c36a0e87e2b6b7ad9c6a16622aba58): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Fix version
- [patrys/httmock@d41ef1b134b9](https://github.com/patrys/httmock/commit/d41ef1b134b95f6d0809771fd0ba30418d099048): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Fix setup classifiers
- [patrys/httmock@ce2aa78ad928](https://github.com/patrys/httmock/commit/ce2aa78ad928a6c4632c7fb29b114a881acedf08): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Merge pull request #63 from jpmelos/fix-http-version-missing
- [patrys/httmock@8d73512142db](https://github.com/patrys/httmock/commit/8d73512142db8af99b047f65ab5b4b779a23b2a2): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Add tests
- [patrys/httmock@66e79a2ddd43](https://github.com/patrys/httmock/commit/66e79a2ddd4371cb8fc71a1218bec96a081e7fee): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Add res.raw.version for responses
- [patrys/httmock@d75f32af901e](https://github.com/patrys/httmock/commit/d75f32af901ed50b9778723ec20e839ea1c01cca): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Merge pull request #62 from ddeka2910/master
- [patrys/httmock@bb32d35ea64e](https://github.com/patrys/httmock/commit/bb32d35ea64eb5005bacc77579e396166c1c8e7e): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Add architecture ppc64le to travis build
- [patrys/httmock@977b87cac2ea](https://github.com/patrys/httmock/commit/977b87cac2ea128e33c6c113b715d19a4c5e97a1): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Merge pull request #61 from derekschrock/tests
- [patrys/httmock@e09c7ec692b1](https://github.com/patrys/httmock/commit/e09c7ec692b15e2c7f0fae0d7fbe4983f9f156f3): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: tests: fix pytest DeprecationWarning messages
- [patrys/httmock@55089eef09d1](https://github.com/patrys/httmock/commit/55089eef09d15315747b8ee5484588393ee119fb): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Merge pull request #60 from koobs/patch-2
- [patrys/httmock@9effcff9772b](https://github.com/patrys/httmock/commit/9effcff9772b659626c2c054560d0f9b0639acc3): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Enable (actually) Python 3.8
- [patrys/httmock@03755bd562d8](https://github.com/patrys/httmock/commit/03755bd562d858c8bfe4971678c79f470625d2d6): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Enable testing on Python 3.7 and 3.8
- [patrys/httmock@a35a35d46d2c](https://github.com/patrys/httmock/commit/a35a35d46d2c0d11b97afb74b9aa8b9eacdc8a48): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Merge pull request #58 from dplyakin/persistent-cookies
- [patrys/httmock@2f037b7d192a](https://github.com/patrys/httmock/commit/2f037b7d192ad213704f4f5eaca2403d258551ca): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Prevent session cookies from overwriting
- [patrys/httmock@4b8e0654f07e](https://github.com/patrys/httmock/commit/4b8e0654f07e61bb44ca62e813a2ee05e7e0acae): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: 1.3.0 maintenance release
- [patrys/httmock@90899beeb862](https://github.com/patrys/httmock/commit/90899beeb86253ac18de58ed05539b4e691dbbc0): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Merge pull request #54 from jsenin/master
- [patrys/httmock@9aa14f4ae372](https://github.com/patrys/httmock/commit/9aa14f4ae372b09865ff8ca2d29670219114b86e): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Added request history to remember_call decorator
- [patrys/httmock@b18bdce6d5d3](https://github.com/patrys/httmock/commit/b18bdce6d5d39fffcb27e678c77c49ae4774c0d9): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Merge pull request #52 from cclauss/patch-1
- [patrys/httmock@de76be4bd8f4](https://github.com/patrys/httmock/commit/de76be4bd8f449f1970dedc0b9b85ae6364e9cbe): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Make explicit support for both Python 2 and 3
- [patrys/httmock@7e40518f5b47](https://github.com/patrys/httmock/commit/7e40518f5b471f7f8df95fdafc33303bfd604441): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Update .travis.yml
- [patrys/httmock@4ea9419300b1](https://github.com/patrys/httmock/commit/4ea9419300b1d7fddcacbd13d69757bca3b020c1): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Update README.md
- [patrys/httmock@e86724582ea0](https://github.com/patrys/httmock/commit/e86724582ea0c50b43af22514e754117633bfb67): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Merge pull request #50 from wieslander/master
- [patrys/httmock@24877bafbd2f](https://github.com/patrys/httmock/commit/24877bafbd2f7e146c4484c320e9393c5f86c77b): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Set response.encoding to the charset from the Content-Type header.
- [patrys/httmock@67dffa231e0f](https://github.com/patrys/httmock/commit/67dffa231e0fb24a47b931f1054b8b9f39061b8d): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: 1.2.6
- [patrys/httmock@d738fa5a5963](https://github.com/patrys/httmock/commit/d738fa5a5963d8c8c7613f7679d44a03486ca545): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Merge pull request #44 from garetht/session-cookie-fix
- [patrys/httmock@99253dae95ee](https://github.com/patrys/httmock/commit/99253dae95eecfadcbd3e98cd6aec0a6bde0660a): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Merge pull request #42 from gmmephisto/pr-master-remember-calls
- [patrys/httmock@6a342f03e42f](https://github.com/patrys/httmock/commit/6a342f03e42f7e3970aae5f942353f268b6c2489): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Drop python3.2 support & enable python3.5
- [patrys/httmock@d58a2e913c8e](https://github.com/patrys/httmock/commit/d58a2e913c8eff0c694db3155dfcda943e756fd4): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Use IDNA-compatible hostnames in tests
- [patrys/httmock@ec5b4f7510d5](https://github.com/patrys/httmock/commit/ec5b4f7510d53e30d73ebed01796029ed68d5f68): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Remove deprecated '--use-mirrors' option for pip
- [patrys/httmock@988d4557d611](https://github.com/patrys/httmock/commit/988d4557d611a98ff4f529ffcb1c316c8e1546c4): Repository excluded before capture: pinned LICENSE declares Apache-2.0, outside current MIT/BSD-3-Clause corpus scope. Tests in tests.py also fall outside current discovery naming. Title: Added decorator for remembering call count
- [rspeer/ordered-set@9dfc91c27c0c](https://github.com/rspeer/ordered-set/commit/9dfc91c27c0c56df2536036bec4a5b3f717ef2ba): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #93 from MarcinKonowalczyk/patch-1
- [rspeer/ordered-set@9669ecf8bed7](https://github.com/rspeer/ordered-set/commit/9669ecf8bed7c04ce0edaa91f083616eb9bf4346): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #90 from hvox/master
- [rspeer/ordered-set@c9a5a363cad0](https://github.com/rspeer/ordered-set/commit/c9a5a363cad0c6f9f365492debb5d13781638696): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: covariant type
- [rspeer/ordered-set@8c837171201e](https://github.com/rspeer/ordered-set/commit/8c837171201e3d089630e8b67645cb813b57c8dd): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #87 from kkirsche/patch-2
- [rspeer/ordered-set@fe878ca074ee](https://github.com/rspeer/ordered-set/commit/fe878ca074eee070c8c2ab985449e0c0610074b8): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #88 from kkirsche/patch-3
- [rspeer/ordered-set@2250b23ba1fa](https://github.com/rspeer/ordered-set/commit/2250b23ba1fa5c49def0c60dc088fa060aff15b0): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #86 from kkirsche/patch-1
- [rspeer/ordered-set@614633e92732](https://github.com/rspeer/ordered-set/commit/614633e92732569684bbc3fafeaab7c40aa436e3): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Use f-strings instead of legacy formatting style
- [rspeer/ordered-set@7051265bf82e](https://github.com/rspeer/ordered-set/commit/7051265bf82e7230020328fb7e83636ee692e44a): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Simplify `_is_atomic` to use single isinstance call
- [rspeer/ordered-set@88f99835fd8a](https://github.com/rspeer/ordered-set/commit/88f99835fd8a74bb1ff61e6eb9bc2505ed81a644): Additional candidate outside the two-change sample; only commit metadata inspected, not rejected based on analyzer behavior. Title: Fix incorrect use of `Any`
- [rspeer/ordered-set@457a1ec89660](https://github.com/rspeer/ordered-set/commit/457a1ec89660f6491ea36b05b44e55dc42f6a873): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Added a changelog
- [rspeer/ordered-set@d921651b2737](https://github.com/rspeer/ordered-set/commit/d921651b2737f5cfe711868fab558a8ef79e26ca): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: use personal email in setup.py
- [rspeer/ordered-set@29e3a82e64e2](https://github.com/rspeer/ordered-set/commit/29e3a82e64e296ec6af0bd5b1b511a014f441867): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: update classifiers in pyproject.toml
- [rspeer/ordered-set@7822e4bbed97](https://github.com/rspeer/ordered-set/commit/7822e4bbed970747bf9193749c81e4dcc05a1a05): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: update authors section
- [rspeer/ordered-set@d25e130401ab](https://github.com/rspeer/ordered-set/commit/d25e130401abdbdd0eec3e0ecbcb96db0b39750b): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: update the README
- [rspeer/ordered-set@557c429e29d7](https://github.com/rspeer/ordered-set/commit/557c429e29d716fd69ff385a54d11e595264211f): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: update some metadata
- [rspeer/ordered-set@2a49243c77d5](https://github.com/rspeer/ordered-set/commit/2a49243c77d526c935341749a366762edc17aecd): Additional candidate outside the two-change sample; only commit metadata inspected, not rejected based on analyzer behavior. Title: try using Flit instead
- [rspeer/ordered-set@3289508e1b69](https://github.com/rspeer/ordered-set/commit/3289508e1b69f37f0edf3753fd2a4ef109cfd443): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: include additional files in sdist
- [rspeer/ordered-set@34f2cba9f950](https://github.com/rspeer/ordered-set/commit/34f2cba9f9509909506adeff51ddebac6060bf1b): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: update python versions, fix some types
- [rspeer/ordered-set@b66acd85e80e](https://github.com/rspeer/ordered-set/commit/b66acd85e80e1efe0262083c36f45ce5ff344506): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: convert to poetry
- [rspeer/ordered-set@4d74bee9bdfd](https://github.com/rspeer/ordered-set/commit/4d74bee9bdfdc28df2564596398656f98cbe767b): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #64 from kairi003/feature/pop_with_index
- [rspeer/ordered-set@e68b99a21ddf](https://github.com/rspeer/ordered-set/commit/e68b99a21ddfdf391bb890ff46f14a65ef96fd94): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #68 from LuminosoInsight/fix-py3.5-types
- [rspeer/ordered-set@a7908a10d95b](https://github.com/rspeer/ordered-set/commit/a7908a10d95ba02b814ec698b8c15adcd0bedc4c): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: update version to 4.0.2
- [rspeer/ordered-set@aab63e3313b8](https://github.com/rspeer/ordered-set/commit/aab63e3313b801435986910a9656282a1a72c26b): Additional candidate outside the two-change sample; only commit metadata inspected, not rejected based on analyzer behavior. Title: fix
- [rspeer/ordered-set@bf1a873b4559](https://github.com/rspeer/ordered-set/commit/bf1a873b455908abc07083e054b83e3b86df4658): Additional candidate outside the two-change sample; only commit metadata inspected, not rejected based on analyzer behavior. Title: restore compatibility with Python 3.5
- [rspeer/ordered-set@f46a8eea1959](https://github.com/rspeer/ordered-set/commit/f46a8eea1959e8974ad78ed04985019f567286fb): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #65 from LuminosoInsight/remove-type-stubs
- [rspeer/ordered-set@9c2ae63129ad](https://github.com/rspeer/ordered-set/commit/9c2ae63129ade135ccb26bd2b2fc45e85019dae9): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: update __version__ to 4.0.1
- [rspeer/ordered-set@c948b6a106ea](https://github.com/rspeer/ordered-set/commit/c948b6a106eaa0e98399f9f2d926c063dffee44a): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: fix packaging, remove vestiges of type stubs
- [rspeer/ordered-set@34f08cef01e5](https://github.com/rspeer/ordered-set/commit/34f08cef01e5a555c8441ac0bfd9d950ed823164): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #61 from LuminosoInsight/py3-inline-types
- [jpvanhal/inflection@88eefaacf7d0](https://github.com/jpvanhal/inflection/commit/88eefaacf7d0caaa701af7c8ab2d0ab3f17086f1): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Fix typing errors
- [jpvanhal/inflection@04e4591a891f](https://github.com/jpvanhal/inflection/commit/04e4591a891f382fdbfa0e1bee1f09289b5cbf58): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Remove universal wheel, python 2 is unsupported (#66)
- [jpvanhal/inflection@80d8405cacf0](https://github.com/jpvanhal/inflection/commit/80d8405cacf058eb0cb582b8b8a2236cd3043f55): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Moved the metadata into setup.cfg and started extraction of a version from git tags.
- [jpvanhal/inflection@b396149e2bc5](https://github.com/jpvanhal/inflection/commit/b396149e2bc59873f76d1f5fb7f512d95b9a354d): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Added all required type hints for strict typing
- [jpvanhal/inflection@b00d4d348b32](https://github.com/jpvanhal/inflection/commit/b00d4d348b32ef5823221b20ee4cbd1d2d924462): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Bump version to 0.5.1
- [jpvanhal/inflection@ae8b5da12115](https://github.com/jpvanhal/inflection/commit/ae8b5da12115225521cefa7bde537cd1c937126a): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Added editorconfig
- [jpvanhal/inflection@5f22a6fd3b3c](https://github.com/jpvanhal/inflection/commit/5f22a6fd3b3c65ed2e7035402fe3d7c50cfc00a2): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: fix: type hint config so they are available to mypy
- [jpvanhal/inflection@66624651e486](https://github.com/jpvanhal/inflection/commit/66624651e4866b103bc12b9e8f4756936b11939f): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Bump version to 0.5.0
- [jpvanhal/inflection@83a5b16920ce](https://github.com/jpvanhal/inflection/commit/83a5b16920ce66982c42b07379eca3948870d991): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Add type hints (#45)
- [jpvanhal/inflection@c750ea013689](https://github.com/jpvanhal/inflection/commit/c750ea0136899bd8c5af5b73989554d84749a624): Additional candidate outside the two-change sample; only commit metadata inspected, not rejected based on analyzer behavior. Title: Comment out unused html_static_path from doc
- [jpvanhal/inflection@8fb7669820ca](https://github.com/jpvanhal/inflection/commit/8fb7669820caafbd4e6e31a2fa6171ed886b1506): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Bump version to 0.4.0
- [jpvanhal/inflection@3a049f152d0f](https://github.com/jpvanhal/inflection/commit/3a049f152d0f80ad957eaec43ef076a777ede5e9): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Bump copyright year
- [jpvanhal/inflection@769cf7b47fde](https://github.com/jpvanhal/inflection/commit/769cf7b47fde883e4b44cec3adf8944bd62f7363): Additional candidate outside the two-change sample; only commit metadata inspected, not rejected based on analyzer behavior. Title: Use HTTPS for the project url
- [jpvanhal/inflection@518119231fc8](https://github.com/jpvanhal/inflection/commit/518119231fc8beabf21f8c24c66379443b35063c): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Move Changelog to GitHub releases
- [jpvanhal/inflection@2d2d37951f6c](https://github.com/jpvanhal/inflection/commit/2d2d37951f6c8871d27a1c74a2c0c1fe6a9354fb): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Add PyPy 3 support
- [jpvanhal/inflection@88a0a5fe0abf](https://github.com/jpvanhal/inflection/commit/88a0a5fe0abffc37b11ee6d45eef7d8f48102250): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Drop PyPy support
- [jpvanhal/inflection@1d6c78f96a44](https://github.com/jpvanhal/inflection/commit/1d6c78f96a4497252eb2e4fb794c1347317dcd62): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: Fix doctest blocks in docstrings
- [jpvanhal/inflection@e5fd209d7b08](https://github.com/jpvanhal/inflection/commit/e5fd209d7b08735937f64591e8cca507dd2112c8): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Allow to pass arguments to pytest command in tox
- [jpvanhal/inflection@351a0f5a8d66](https://github.com/jpvanhal/inflection/commit/351a0f5a8d6637f594c3b31eb7a4d104e20c0541): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Drop Python 3.4 support
- [jpvanhal/inflection@a826dac7a562](https://github.com/jpvanhal/inflection/commit/a826dac7a562e67881ab704adbef45440566836e): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Drop support for Python 2.7
- [jpvanhal/inflection@f7458f0a60e9](https://github.com/jpvanhal/inflection/commit/f7458f0a60e9b16bfc95ba44a769101bf76177eb): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #42 from rciorba/test_on_37_and_38
- [jpvanhal/inflection@09efb13343ad](https://github.com/jpvanhal/inflection/commit/09efb13343ad07f4013d31f95b3a07da83b7ad81): Packaging, documentation, release or development-environment change outside functional source focus; commit metadata inspected. Title: add 3.7 and 3.8 as supported versions
- [jpvanhal/inflection@ad195ab72b19](https://github.com/jpvanhal/inflection/commit/ad195ab72b193b57bb4cf68396c4cd8a62f1fe6c): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge pull request #34 from hugovk/patch-1
- [jpvanhal/inflection@fe684577b1c3](https://github.com/jpvanhal/inflection/commit/fe684577b1c393cf4d2dc5b5029fe40ecaf7f641): Additional candidate outside the two-change sample; only commit metadata inspected, not rejected based on analyzer behavior. Title: Use SVG badge
- [jpvanhal/inflection@62158bb716c0](https://github.com/jpvanhal/inflection/commit/62158bb716c09474c2c0ddd0557ad2cdc3683af0): Merge copy or combined change; prefer bounded original first-parent changes. Commit metadata inspected. Title: Merge branch 'hugovk-update-versions'
- [jpvanhal/inflection@bc7323e51911](https://github.com/jpvanhal/inflection/commit/bc7323e51911687ef30caf67d47934b43b6f6508): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Upgrade Python syntax with pyupgrade
- [jpvanhal/inflection@5427ff038d91](https://github.com/jpvanhal/inflection/commit/5427ff038d91827077ae0f511368de2ba682d3bf): Typing, compatibility, testing or representation cleanup outside the selected bounded behavior changes; commit metadata inspected. Title: Replace function call with set literal
- [jpvanhal/inflection@2dfa5f645a8a](https://github.com/jpvanhal/inflection/commit/2dfa5f645a8a213eb899e254185c0f0fb10f818c): Additional candidate outside the two-change sample; only commit metadata inspected, not rejected based on analyzer behavior. Title: Add Python 3.6, drop EOL 2.6 and 3.3

## Outside-discovery review (30 definitions)

These test.py definitions are outside the discovery rule and metric denominator.
Check discovery scope separately; no affected/unaffected labels or runtime collection are claimed.
The direct test_pop calls on lines 155 and 158 are a concrete coverage gap.

- [ ] [`test.py::test_pickle`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L13-L16) — unsupported test filename.
- [ ] [`test.py::test_empty_pickle`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L19-L22) — unsupported test filename.
- [ ] [`test.py::test_order`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L25-L29) — unsupported test filename.
- [ ] [`test.py::test_binary_operations`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L32-L39) — unsupported test filename.
- [ ] [`test.py::test_indexing`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L42-L55) — unsupported test filename.
- [ ] [`test.py::test_fancy_index_class`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L78-L81) — unsupported test filename.
- [ ] [`test.py::test_pandas_compat`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L84-L87) — unsupported test filename.
- [ ] [`test.py::test_tuples`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L90-L95) — unsupported test filename.
- [ ] [`test.py::test_remove`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L98-L120) — unsupported test filename.
- [ ] [`test.py::test_remove_error`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L123-L127) — unsupported test filename.
- [ ] [`test.py::test_clear`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L130-L135) — unsupported test filename.
- [ ] [`test.py::test_update`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L138-L150) — unsupported test filename.
- [ ] [`test.py::test_pop`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L153-L162) — unsupported test filename.
- [ ] [`test.py::test_getitem_type_error`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L165-L168) — unsupported test filename.
- [ ] [`test.py::test_update_value_error`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L171-L175) — unsupported test filename.
- [ ] [`test.py::test_empty_repr`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L178-L180) — unsupported test filename.
- [ ] [`test.py::test_eq_wrong_type`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L183-L185) — unsupported test filename.
- [ ] [`test.py::test_ordered_equality`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L188-L193) — unsupported test filename.
- [ ] [`test.py::test_ordered_inequality`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L196-L209) — unsupported test filename.
- [ ] [`test.py::test_comparisons`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L212-L219) — unsupported test filename.
- [ ] [`test.py::test_unordered_equality`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L222-L239) — unsupported test filename.
- [ ] [`test.py::test_unordered_inequality`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L242-L252) — unsupported test filename.
- [ ] [`test.py::test_operator_consistency_isect`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L315-L321) — unsupported test filename.
- [ ] [`test.py::test_operator_consistency_difference`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L324-L332) — unsupported test filename.
- [ ] [`test.py::test_operator_consistency_xor`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L335-L341) — unsupported test filename.
- [ ] [`test.py::test_operator_consistency_union`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L344-L350) — unsupported test filename.
- [ ] [`test.py::test_operator_consistency_subset`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L353-L358) — unsupported test filename.
- [ ] [`test.py::test_operator_consistency_superset`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L361-L368) — unsupported test filename.
- [ ] [`test.py::test_operator_consistency_disjoint`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L371-L375) — unsupported test filename.
- [ ] [`test.py::test_bitwise_and_consistency`](https://github.com/rspeer/ordered-set/blob/1f93c9d7376dec495e1573c9c02837bce96e1c9f/test.py#L378-L387) — unsupported test filename.
