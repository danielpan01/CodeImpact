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

## humanize_intcomma_locale

[python-humanize/humanize](https://github.com/python-humanize/humanize/commit/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a) — Internationalize the thousands separator used by intcomma.

Before: `0cbd1ababec2dcdd71e57856f9b0cce8c4d21b51`; after: `cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a`.

Label status: **draft**; author: Codex source-only draft, November 17, 2026; reviewer: none.
Frozen label SHA-256: `0bbcdd229ba46c41c550e829f899a752da19fdbce22f6e64ca7b32fb7381c7d5`.

### Complete Python change

````diff
--- base/src/humanize/__init__.py
+++ head/src/humanize/__init__.py
@@ -1,7 +1,7 @@
 """Main package for humanize."""
 import pkg_resources
 from humanize.filesize import naturalsize
-from humanize.i18n import activate, deactivate
+from humanize.i18n import activate, deactivate, thousands_separator
 from humanize.number import apnumber, fractional, intcomma, intword, ordinal, scientific
 from humanize.time import (
     naturaldate,
@@ -30,5 +30,6 @@
     "ordinal",
     "precisedelta",
     "scientific",
+    "thousands_separator",
     "VERSION",
 ]
--- base/src/humanize/i18n.py
+++ head/src/humanize/i18n.py
@@ -3,10 +3,16 @@
 import os.path
 from threading import local

-__all__ = ["activate", "deactivate", "gettext", "ngettext"]
+__all__ = ["activate", "deactivate", "gettext", "ngettext", "thousands_separator"]

 _TRANSLATIONS = {None: gettext_module.NullTranslations()}
 _CURRENT = local()
+
+
+# Mapping of locale to thousands separator
+_THOUSANDS_SEPARATOR = {
+    "fr_FR": " ",
+}


 def _get_default_locale_path():
@@ -129,3 +135,16 @@
         str: Original text, unchanged.
     """
     return message
+
+
+def thousands_separator() -> str:
+    """Return the thousands separator for a locale, default to comma.
+
+    Returns:
+         str: Thousands separator.
+    """
+    try:
+        sep = _THOUSANDS_SEPARATOR[_CURRENT.locale]
+    except (AttributeError, KeyError):
+        sep = ","
+    return sep
--- base/src/humanize/number.py
+++ head/src/humanize/number.py
@@ -8,6 +8,7 @@
 from .i18n import gettext as _
 from .i18n import gettext_noop as N_
 from .i18n import pgettext as P_
+from .i18n import thousands_separator


 def ordinal(value):
@@ -97,9 +98,10 @@
     Returns:
         str: string containing commas every three digits.
     """
+    sep = thousands_separator()
     try:
         if isinstance(value, str):
-            float(value.replace(",", ""))
+            float(value.replace(sep, ""))
         else:
             float(value)
     except (TypeError, ValueError):
@@ -110,7 +112,7 @@
     else:
         orig = str(value)

-    new = re.sub(r"^(-?\d+)(\d{3})", r"\g<1>,\g<2>", orig)
+    new = re.sub(r"^(-?\d+)(\d{3})", fr"\g<1>{sep}\g<2>", orig)
     if orig == new:
         return new
     else:
--- base/tests/test_i18n.py
+++ head/tests/test_i18n.py
@@ -24,6 +24,20 @@
         assert humanize.naturaltime(three_seconds) == "3 seconds ago"
         assert humanize.ordinal(5) == "5th"
         assert humanize.precisedelta(one_min_three_seconds) == "1 minute and 7 seconds"
+
+
+def test_intcomma():
+    number = 10_000_000
+
+    assert humanize.intcomma(number) == "10,000,000"
+
+    try:
+        humanize.i18n.activate("fr_FR")
+        assert humanize.intcomma(number) == "10 000 000"
+
+    finally:
+        humanize.i18n.deactivate()
+        assert humanize.intcomma(number) == "10,000,000"


 def test_default_locale_path_defined__file__():
````

### Draft labels and source

#### expected_affected (2)

- [ ] [`tests/test_i18n.py::test_intcomma`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_i18n.py#L29-L40) — The added test activates fr_FR and calls intcomma with the same integer before, during and after activation.
- [ ] [`tests/test_number.py::test_intcomma`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_number.py#L61-L62) — The numeric cases enter intcomma, which now uses the locale separator inside the grouping substitution.

#### expected_unaffected (32)

- [ ] [`tests/test_filesize.py::test_naturalsize`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_filesize.py#L34-L39) — Exercises the naturalsize file-size formatter. The captured call chain does not reach intcomma.
- [ ] [`tests/test_i18n.py::TestActivate.test_default_locale_path_null__file__`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_i18n.py#L66-L72) — The test calls activate with absent locale location metadata and checks the error path, separate from intcomma.
- [ ] [`tests/test_i18n.py::TestActivate.test_default_locale_path_undefined__file__`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_i18n.py#L74-L80) — The test calls activate with absent locale location metadata and checks the error path, separate from intcomma.
- [ ] [`tests/test_i18n.py::test_default_locale_path_defined__file__`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_i18n.py#L43-L45) — Exercises locale path lookup with a defined module file. The captured call chain does not reach intcomma.
- [ ] [`tests/test_i18n.py::test_default_locale_path_null__file__`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_i18n.py#L48-L51) — Exercises locale path lookup with a null module file. The captured call chain does not reach intcomma.
- [ ] [`tests/test_i18n.py::test_default_locale_path_undefined__file__`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_i18n.py#L54-L57) — Exercises locale path lookup after deleting the module file attribute. The captured call chain does not reach intcomma.
- [ ] [`tests/test_i18n.py::test_i18n`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_i18n.py#L8-L26) — Exercises naturaltime, ordinal and precisedelta across locale activation. The captured call chain does not reach intcomma.
- [ ] [`tests/test_number.py::test_apnumber`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_number.py#L111-L112) — Exercises apnumber word formatting. The captured call chain does not reach intcomma.
- [ ] [`tests/test_number.py::test_fractional`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_number.py#L132-L133) — Exercises fractional rational-number formatting. The captured call chain does not reach intcomma.
- [ ] [`tests/test_number.py::test_intword`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_number.py#L93-L94) — Exercises intword formatting. The captured call chain does not reach intcomma.
- [ ] [`tests/test_number.py::test_intword_powers`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_number.py#L65-L67) — Exercises only the length of the intword powers table. The captured call chain does not reach intcomma.
- [ ] [`tests/test_number.py::test_ordinal`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_number.py#L28-L29) — Exercises ordinal formatting. The captured call chain does not reach intcomma.
- [ ] [`tests/test_number.py::test_scientific`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_number.py#L154-L155) — Exercises scientific notation, including conversion of float inputs. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_date_and_delta`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L55-L67) — Exercises date_and_delta conversion before formatting. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturaldate`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L267-L268) — Exercises the naturaldate formatter. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturalday`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L223-L224) — Exercises the naturalday formatter. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturaldelta`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L125-L126) — Exercises the naturaldelta formatter. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturaldelta_minimum_unit_default`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L285-L290) — Exercises the naturaldelta formatter for the minimum unit default cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturaldelta_minimum_unit_explicit`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L328-L333) — Exercises the naturaldelta formatter for the minimum unit explicit cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturaldelta_nomonths`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L86-L87) — Exercises the naturaldelta formatter for the nomonths cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturaldelta_when_explicit`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L343-L345) — Exercises the naturaldelta formatter for the when explicit cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturaldelta_when_missing_tzinfo`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L357-L364) — Exercises the naturaldelta formatter for the when missing tzinfo cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturaltime`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L161-L162) — Exercises the naturaltime formatter. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturaltime_minimum_unit_default`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L381-L386) — Exercises the naturaltime formatter for the minimum unit default cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturaltime_minimum_unit_explicit`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L424-L429) — Exercises the naturaltime formatter for the minimum unit explicit cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_naturaltime_nomonths`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L203-L204) — Exercises the naturaltime formatter for the nomonths cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_precisedelta_bogus_call`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L636-L643) — Exercises the precisedelta formatter for the bogus call cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_precisedelta_custom_format`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L555-L556) — Exercises the precisedelta formatter for the custom format cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_precisedelta_multiple_units`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L506-L507) — Exercises the precisedelta formatter for the multiple units cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_precisedelta_one_unit_enough`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L452-L453) — Exercises the precisedelta formatter for the one unit enough cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_precisedelta_suppress_units`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L630-L633) — Exercises the precisedelta formatter for the suppress units cases. The captured call chain does not reach intcomma.
- [ ] [`tests/test_time.py::test_time_unit`](https://github.com/python-humanize/humanize/blob/cb0ac5989cea442e5e4b2f4effc3906aad1a1d1a/tests/test_time.py#L646-L653) — Exercises Unit enum comparison and invalid comparison handling. The captured call chain does not reach intcomma.

#### unclassified (0)


### Outside discovery (0)


## humanize_small_delta

[python-humanize/humanize](https://github.com/python-humanize/humanize/commit/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742) — Return a zero minimum unit for a too-small precise delta.

Before: `9d9de69177154b41b2d6ef412d1487639e99833d`; after: `62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742`.

Label status: **draft**; author: Codex source-only draft, November 17, 2026; reviewer: none.
Frozen label SHA-256: `5efdaa2fd8e2ea4a589b0b42717ed1e3abd7b74c728bd9871a2a34ecaa64313f`.

### Complete Python change

````diff
--- base/src/humanize/time.py
+++ head/src/humanize/time.py
@@ -427,6 +427,20 @@
     '1.50 minutes'

     ```
+
+    If the delta is too small to be represented with the minimum unit,
+    a value of zero will be returned:
+
+    ```pycon
+    >>> delta = dt.timedelta(seconds=1)
+    >>> precisedelta(delta, minimum_unit="minutes")
+    '0.02 minutes'
+
+    >>> delta = dt.timedelta(seconds=0.1)
+    >>> precisedelta(delta, minimum_unit="minutes")
+    '0 minutes'
+
+    ```
     """
     date, delta = date_and_delta(value)
     if date is None:
@@ -501,7 +515,7 @@
     texts = []
     for unit, fmt in zip(reversed(Unit), fmts):
         singular_txt, plural_txt, value = fmt
-        if value > 0:
+        if value > 0 or (not texts and unit == min_unit):
             fmt_txt = ngettext(singular_txt, plural_txt, value)
             if unit == min_unit and math.modf(value)[0] > 0:
                 fmt_txt = fmt_txt.replace("%d", format)
--- base/tests/test_time.py
+++ head/tests/test_time.py
@@ -496,6 +496,11 @@
             "microseconds",
             "1 year, 5 days and 2 seconds",
         ),
+        (
+            dt.timedelta(seconds=0.01),
+            "minutes",
+            "0 minutes",
+        ),
     ],
 )
 def test_precisedelta_multiple_units(val, min_unit, expected):
````

### Draft labels and source

#### expected_affected (5)

- [ ] [`tests/test_i18n.py::test_i18n`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_i18n.py#L8-L26) — Calls precisedelta before and after locale activation. The supplied nonzero timedelta reaches the edited formatting loop.
- [ ] [`tests/test_time.py::test_precisedelta_custom_format`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L555-L556) — Calls precisedelta with a custom format, reaching the loop that builds unit text.
- [ ] [`tests/test_time.py::test_precisedelta_multiple_units`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L506-L507) — Calls precisedelta with multiple units, reaching the loop that builds unit text.
- [ ] [`tests/test_time.py::test_precisedelta_one_unit_enough`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L452-L453) — The changed parameter list adds a fraction of a second with minutes as the minimum unit and calls precisedelta.
- [ ] [`tests/test_time.py::test_precisedelta_suppress_units`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L630-L633) — Calls precisedelta with suppressed units, reaching the loop that builds unit text.

#### expected_unaffected (28)

- [ ] [`tests/test_filesize.py::test_naturalsize`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_filesize.py#L34-L39) — Exercises the naturalsize file-size formatter. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_i18n.py::TestActivate.test_default_locale_path_null__file__`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_i18n.py#L52-L58) — The test calls activate with absent locale location metadata and checks the error path, separate from precisedelta.
- [ ] [`tests/test_i18n.py::TestActivate.test_default_locale_path_undefined__file__`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_i18n.py#L60-L66) — The test calls activate with absent locale location metadata and checks the error path, separate from precisedelta.
- [ ] [`tests/test_i18n.py::test_default_locale_path_defined__file__`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_i18n.py#L29-L31) — Exercises locale path lookup with a defined module file. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_i18n.py::test_default_locale_path_null__file__`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_i18n.py#L34-L37) — Exercises locale path lookup with a null module file. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_i18n.py::test_default_locale_path_undefined__file__`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_i18n.py#L40-L43) — Exercises locale path lookup after deleting the module file attribute. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_number.py::test_apnumber`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_number.py#L111-L112) — Exercises apnumber word formatting. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_number.py::test_fractional`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_number.py#L132-L133) — Exercises fractional rational-number formatting. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_number.py::test_intcomma`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_number.py#L61-L62) — Exercises integer thousands formatting. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_number.py::test_intword`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_number.py#L93-L94) — Exercises intword formatting. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_number.py::test_intword_powers`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_number.py#L65-L67) — Exercises only the length of the intword powers table. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_number.py::test_ordinal`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_number.py#L28-L29) — Exercises ordinal formatting. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_number.py::test_scientific`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_number.py#L154-L155) — Exercises scientific notation, including conversion of float inputs. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_date_and_delta`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L55-L67) — Exercises date_and_delta conversion before formatting. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturaldate`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L267-L268) — Exercises the naturaldate formatter. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturalday`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L223-L224) — Exercises the naturalday formatter. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturaldelta`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L125-L126) — Exercises the naturaldelta formatter. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturaldelta_minimum_unit_default`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L285-L290) — Exercises the naturaldelta formatter for the minimum unit default cases. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturaldelta_minimum_unit_explicit`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L328-L333) — Exercises the naturaldelta formatter for the minimum unit explicit cases. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturaldelta_nomonths`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L86-L87) — Exercises the naturaldelta formatter for the nomonths cases. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturaldelta_when_explicit`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L343-L345) — Exercises the naturaldelta formatter for the when explicit cases. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturaldelta_when_missing_tzinfo`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L357-L364) — Exercises the naturaldelta formatter for the when missing tzinfo cases. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturaltime`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L161-L162) — Exercises the naturaltime formatter. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturaltime_minimum_unit_default`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L381-L386) — Exercises the naturaltime formatter for the minimum unit default cases. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturaltime_minimum_unit_explicit`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L424-L429) — Exercises the naturaltime formatter for the minimum unit explicit cases. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_naturaltime_nomonths`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L203-L204) — Exercises the naturaltime formatter for the nomonths cases. The captured call chain does not reach precisedelta.
- [ ] [`tests/test_time.py::test_precisedelta_bogus_call`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L636-L643) — None returns early and the suppressed-years options raise before the edited loop. The remaining call uses naturaldelta.
- [ ] [`tests/test_time.py::test_time_unit`](https://github.com/python-humanize/humanize/blob/62706fd4cb90ebeb9bf85685bad8ab1fa9d0c742/tests/test_time.py#L646-L653) — Exercises Unit enum comparison and invalid comparison handling. The captured call chain does not reach precisedelta.

#### unclassified (0)


### Outside discovery (0)


## icecream_local_time

[gruns/icecream](https://github.com/gruns/icecream/commit/792cfdec01fccbe069fe485bad0846940251efa6) — Format source-free call timestamps in local rather than UTC time.

Before: `b85b8dc668ad17ddf86742913aaa49b073204567`; after: `792cfdec01fccbe069fe485bad0846940251efa6`.

Label status: **draft**; author: Codex source-only draft, November 17, 2026; reviewer: none.
Frozen label SHA-256: `c1b7b469b5b27e9284c6f6b8acdf2caffa968023960f8ccc27d284499df1d972`.

### Complete Python change

````diff
--- base/icecream/icecream.py
+++ head/icecream/icecream.py
@@ -17,8 +17,8 @@
 import inspect
 import pprint
 import sys
+from datetime import datetime
 from contextlib import contextmanager
-from datetime import datetime
 from os.path import basename
 from textwrap import dedent

@@ -296,7 +296,7 @@
         return context

     def _formatTime(self):
-        now = datetime.utcnow()
+        now = datetime.now()
         formatted = now.strftime('%H:%M:%S.%f')[:-3]
         return ' at %s' % formatted

````

### Draft labels and source

#### expected_affected (0)


#### expected_unaffected (0)


#### unclassified (0)


### Outside discovery (32)

- [`tests/test_icecream.py::TestIceCream.testArgToStringFunction`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testAsArgument`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testCallSurroundedByExpressions`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testColoring`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testComments`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testComplicated`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testDifferentName`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testEnableDisable`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testExpressionArguments`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testFormat`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testIncludeContextMultiLine`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testIncludeContextSingleLine`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMethodArguments`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultilineContainerArgs`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultilineInvocationWithComments`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultilineValueWrapped`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultipleArguments`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultipleArgumentsLongLineWrapped`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultipleCallsOnSameLine`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultipleTupleArguments`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testNestedMultiline`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testNoSourceAvailable`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testOutputFunction`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testPrefixConfiguration`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testReturnValue`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testSingleArgument`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testSingleArgumentLongLineNotWrapped`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testSingleTupleArgument`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testValues`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testWithoutArgs`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_install.py::TestIceCreamInstall.testInstall`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_install.py) — `unsupported_function_name`
- [`tests/test_install.py::TestIceCreamInstall.testUninstall`](https://github.com/gruns/icecream/blob/792cfdec01fccbe069fe485bad0846940251efa6/tests/test_install.py) — `unsupported_function_name`

## icecream_source_error

[gruns/icecream](https://github.com/gruns/icecream/commit/2d0144ef5f4529564b5fe7f64fc1a86e0a682074) — Change the public message raised when source is unavailable.

Before: `daa30a0672e4588ca75a7072352114fe4232869a`; after: `2d0144ef5f4529564b5fe7f64fc1a86e0a682074`.

Label status: **draft**; author: Codex source-only draft, November 17, 2026; reviewer: none.
Frozen label SHA-256: `c1b7b469b5b27e9284c6f6b8acdf2caffa968023960f8ccc27d284499df1d972`.

### Complete Python change

````diff
--- base/icecream/icecream.py
+++ head/icecream/icecream.py
@@ -94,7 +94,8 @@
     Raised when icecream fails to find or access source code that's
     required to parse and analyze. This can happen, for example, when

-      - ic() is invoked inside an interactive shell, e.g. python -i.
+      - ic() is invoked inside a REPL or interactive shell, e.g. from the
+        command line (CLI) or with python -i.

       - The source code is mangled and/or packaged, e.g. with a project
         freezer like PyInstaller.
@@ -104,7 +105,7 @@
     """
     infoMessage = (
         'Failed to access the underlying source code for analysis. Was ic() '
-        'invoked in an interpreter (e.g. python -i), a frozen application '
+        'invoked in a REPL (e.g. from the command line), a frozen application '
         '(e.g. packaged with PyInstaller), or did the underlying source code '
         'change during execution?')

````

### Draft labels and source

#### expected_affected (0)


#### expected_unaffected (0)


#### unclassified (0)


### Outside discovery (32)

- [`tests/test_icecream.py::TestIceCream.testArgToStringFunction`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testAsArgument`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testCallSurroundedByExpressions`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testColoring`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testComments`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testComplicated`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testDifferentName`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testEnableDisable`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testExpressionArguments`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testFormat`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testIncludeContextMultiLine`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testIncludeContextSingleLine`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMethodArguments`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultilineContainerArgs`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultilineInvocationWithComments`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultilineValueWrapped`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultipleArguments`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultipleArgumentsLongLineWrapped`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultipleCallsOnSameLine`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testMultipleTupleArguments`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testNestedMultiline`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testNoSourceAvailable`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testOutputFunction`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testPrefixConfiguration`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testReturnValue`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testSingleArgument`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testSingleArgumentLongLineNotWrapped`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testSingleTupleArgument`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testValues`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_icecream.py::TestIceCream.testWithoutArgs`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_icecream.py) — `unsupported_function_name`
- [`tests/test_install.py::TestIceCreamInstall.testInstall`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_install.py) — `unsupported_function_name`
- [`tests/test_install.py::TestIceCreamInstall.testUninstall`](https://github.com/gruns/icecream/blob/2d0144ef5f4529564b5fe7f64fc1a86e0a682074/tests/test_install.py) — `unsupported_function_name`

## oyaml_error_context

[wimglenn/oyaml](https://github.com/wimglenn/oyaml/commit/6350d9de586f40014296b55427ccbc1d7f47269a) — Preserve contextual errors when constructing mappings with unhashable keys.

Before: `425fd975c063aed8770826b98376a19b83a6c3de`; after: `6350d9de586f40014296b55427ccbc1d7f47269a`.

Label status: **draft**; author: Codex source-only draft, November 17, 2026; reviewer: none.
Frozen label SHA-256: `7a4bf3ca72a1a1875ae61f031a3a76a6defba9f9fae0070ab7e26475c104fdde`.

### Complete Python change

````diff
--- base/oyaml.py
+++ head/oyaml.py
@@ -17,7 +17,12 @@

 def map_constructor(loader, node):
     loader.flatten_mapping(node)
-    return OrderedDict(loader.construct_pairs(node))
+    pairs = loader.construct_pairs(node)
+    try:
+        return OrderedDict(pairs)
+    except TypeError:
+        loader.construct_mapping(node)  # trigger any contextual error
+        raise


 if pyyaml.safe_dump is pyyaml.dump:
--- base/setup.py
+++ head/setup.py
@@ -2,7 +2,7 @@

 setup(
     name="oyaml",
-    version="0.8",
+    version="0.9",
     description="Ordered YAML: drop-in replacement for PyYAML which preserves dict ordering",
     long_description=open("README.rst").read(),
     author="Wim Glenn",
--- base/test_oyaml.py
+++ head/test_oyaml.py
@@ -2,6 +2,7 @@
 from types import GeneratorType

 import pytest
+from yaml.constructor import ConstructorError
 from yaml.representer import RepresenterError

 import oyaml as yaml
@@ -186,3 +187,8 @@
     assert map2 == expected
     assert map3 == expected
     assert map4 == expected
+
+
+def test_unhashable_error_context():
+    with pytest.raises(ConstructorError, match=r".*line.*column.*"):
+        yaml.safe_load("{foo: bar}: baz")
````

### Draft labels and source

#### expected_affected (3)

- [ ] [`test_oyaml.py::test_loads_to_ordered_dict`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L62-L64) — The skip guard requires the old dict implementation, where oyaml registers map_constructor for the mapping load.
- [ ] [`test_oyaml.py::test_safe_loads_to_ordered_dict`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L75-L77) — The skip guard requires the old dict implementation, where oyaml registers map_constructor for the mapping load.
- [ ] [`test_oyaml.py::test_unhashable_error_context`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L192-L194) — Added test sends an unhashable mapping key to safe_load and asserts the contextual constructor message.

#### expected_unaffected (8)

- [ ] [`test_oyaml.py::test_dump`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L15-L16) — Exercises dump of a root ordered mapping, using representers rather than the edited mapping constructor.
- [ ] [`test_oyaml.py::test_dump_all`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L23-L27) — Exercises dump_all of ordered and plain mapping documents, using representers rather than the edited mapping constructor.
- [ ] [`test_oyaml.py::test_dump_and_safe_dump_match`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L30-L33) — Exercises dump and safe_dump of the same plain mapping, using representers rather than the edited mapping constructor.
- [ ] [`test_oyaml.py::test_loads_to_std_dict`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L68-L71) — The skip guard requires a runtime with ordered standard dicts, where oyaml skips the loader registration.
- [ ] [`test_oyaml.py::test_safe_dump`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L19-L20) — Exercises safe_dump of a root ordered mapping, using representers rather than the edited mapping constructor.
- [ ] [`test_oyaml.py::test_safe_dump_all`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L36-L40) — Exercises safe_dump_all of ordered and plain mapping documents, using representers rather than the edited mapping constructor.
- [ ] [`test_oyaml.py::test_safe_loads_to_std_dict`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L81-L84) — The skip guard requires a runtime with ordered standard dicts, where oyaml skips the loader registration.
- [ ] [`test_oyaml.py::test_subclass_dump`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L91-L95) — This checks safe and unsafe representation of an OrderedDict subclass, without loading through the edited constructor.

#### unclassified (7)

- [ ] [`test_oyaml.py::test_anchors_and_references`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L98-L121) — Exercises load of nested mappings with anchors and merged defaults. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_load`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L43-L45) — Exercises load of a root plain mapping. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_load_all`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L53-L58) — Exercises load_all of a root mapping and an empty mapping. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_merge`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L149-L189) — Exercises load of a sequence of mapping merges and overrides. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_omap`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L124-L140) — Exercises load of a mapping containing an explicit omap value. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_omap_flow_style`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L143-L146) — Exercises load of a mapping containing a flow-style omap value. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_safe_load`](https://github.com/wimglenn/oyaml/blob/6350d9de586f40014296b55427ccbc1d7f47269a/test_oyaml.py#L48-L50) — Exercises safe_load of a root plain mapping. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.

### Outside discovery (0)


## oyaml_registrations

[wimglenn/oyaml](https://github.com/wimglenn/oyaml/commit/5152325dcdb68b3684c7ba745a8710df6ea40b9a) — Register ordered mappings on Python and optional C loaders and dumpers.

Before: `6350d9de586f40014296b55427ccbc1d7f47269a`; after: `5152325dcdb68b3684c7ba745a8710df6ea40b9a`.

Label status: **draft**; author: Codex source-only draft, November 17, 2026; reviewer: none.
Frozen label SHA-256: `686a34c83107ef60542a08a6ccaea0db7a0c7eb6e5dee71f78d04f731a176b85`.

### Complete Python change

````diff
--- base/oyaml.py
+++ head/oyaml.py
@@ -25,29 +25,29 @@
         raise


-if pyyaml.safe_dump is pyyaml.dump:
-    # PyYAML v4.x
-    SafeDumper = pyyaml.dumper.Dumper
-    DangerDumper = pyyaml.dumper.DangerDumper
+_loaders = [getattr(pyyaml.loader, x) for x in pyyaml.loader.__all__]
+_dumpers = [getattr(pyyaml.dumper, x) for x in pyyaml.dumper.__all__]
+try:
+    _cyaml = pyyaml.cyaml.__all__
+except AttributeError:
+    pass
 else:
-    SafeDumper = pyyaml.dumper.SafeDumper
-    DangerDumper = pyyaml.dumper.Dumper
+    _loaders += [getattr(pyyaml.cyaml, x) for x in _cyaml if x.endswith("Loader")]
+    _dumpers += [getattr(pyyaml.cyaml, x) for x in _cyaml if x.endswith("Dumper")]

-pyyaml.add_representer(dict, map_representer, Dumper=SafeDumper)
-pyyaml.add_representer(OrderedDict, map_representer, Dumper=SafeDumper)
-pyyaml.add_representer(dict, map_representer, Dumper=DangerDumper)
-pyyaml.add_representer(OrderedDict, map_representer, Dumper=DangerDumper)
-
+Dumper = None
+for Dumper in _dumpers:
+    pyyaml.add_representer(dict, map_representer, Dumper=Dumper)
+    pyyaml.add_representer(OrderedDict, map_representer, Dumper=Dumper)

 Loader = None
 if not _std_dict_is_order_preserving:
-    for loader_name in pyyaml.loader.__all__:
-        Loader = getattr(pyyaml.loader, loader_name)
+    for Loader in _loaders:
         pyyaml.add_constructor("tag:yaml.org,2002:map", map_constructor, Loader=Loader)


 # Merge PyYAML namespace into ours.
 # This allows users a drop-in replacement:
 #   import oyaml as yaml
-del map_constructor, map_representer, SafeDumper, DangerDumper, Loader
+del map_constructor, map_representer, Loader, Dumper
 from yaml import *
--- base/setup.py
+++ head/setup.py
@@ -2,7 +2,7 @@

 setup(
     name="oyaml",
-    version="0.9",
+    version="1.0",
     description="Ordered YAML: drop-in replacement for PyYAML which preserves dict ordering",
     long_description=open("README.rst").read(),
     author="Wim Glenn",
--- base/test_oyaml.py
+++ head/test_oyaml.py
@@ -192,3 +192,17 @@
 def test_unhashable_error_context():
     with pytest.raises(ConstructorError, match=r".*line.*column.*"):
         yaml.safe_load("{foo: bar}: baz")
+
+
+@pytest.mark.skipif(not hasattr(yaml, "CSafeLoader"), reason="requires cyaml loaders")
+def test_explicit_loader():
+    data = yaml.load("{x: 1, z: 3, y: 2}", Loader=yaml.CSafeLoader)
+    assert data == {"x": 1, "z": 3, "y": 2}
+    assert list(data) == ["x", "z", "y"]
+
+
+@pytest.mark.skipif(not hasattr(yaml, "CSafeDumper"), reason="requires cyaml dumpers")
+def test_explicit_dumper():
+    data = OrderedDict([("x", 1), ("z", 3), ("y", 2)])
+    text = yaml.dump(data, Dumper=yaml.CSafeDumper, default_flow_style=None)
+    assert text == "{x: 1, z: 3, y: 2}\n"
````

### Draft labels and source

#### expected_affected (9)

- [ ] [`test_oyaml.py::test_dump`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L15-L16) — Exercises dump of a root ordered mapping. The changed initialization iterates the dumper registry for these mapping representers.
- [ ] [`test_oyaml.py::test_dump_all`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L23-L27) — Exercises dump_all of ordered and plain mapping documents. The changed initialization iterates the dumper registry for these mapping representers.
- [ ] [`test_oyaml.py::test_dump_and_safe_dump_match`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L30-L33) — Exercises dump and safe_dump of the same plain mapping. The changed initialization iterates the dumper registry for these mapping representers.
- [ ] [`test_oyaml.py::test_explicit_dumper`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L205-L208) — Added test explicitly requests CSafeDumper and dumps an ordered mapping via the added registration.
- [ ] [`test_oyaml.py::test_explicit_loader`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L198-L201) — Added test explicitly requests CSafeLoader, whose mapping registration is added when available.
- [ ] [`test_oyaml.py::test_loads_to_ordered_dict`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L62-L64) — The skip guard requires the old dict implementation, where oyaml registers map_constructor for the mapping load.
- [ ] [`test_oyaml.py::test_safe_dump`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L19-L20) — Exercises safe_dump of a root ordered mapping. The changed initialization iterates the dumper registry for these mapping representers.
- [ ] [`test_oyaml.py::test_safe_dump_all`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L36-L40) — Exercises safe_dump_all of ordered and plain mapping documents. The changed initialization iterates the dumper registry for these mapping representers.
- [ ] [`test_oyaml.py::test_safe_loads_to_ordered_dict`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L75-L77) — The skip guard requires the old dict implementation, where oyaml registers map_constructor for the mapping load.

#### expected_unaffected (2)

- [ ] [`test_oyaml.py::test_loads_to_std_dict`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L68-L71) — The skip guard requires a runtime with ordered standard dicts, where oyaml skips the loader registration.
- [ ] [`test_oyaml.py::test_safe_loads_to_std_dict`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L81-L84) — The skip guard requires a runtime with ordered standard dicts, where oyaml skips the loader registration.

#### unclassified (9)

- [ ] [`test_oyaml.py::test_anchors_and_references`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L98-L121) — Exercises load of nested mappings with anchors and merged defaults. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_load`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L43-L45) — Exercises load of a root plain mapping. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_load_all`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L53-L58) — Exercises load_all of a root mapping and an empty mapping. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_merge`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L149-L189) — Exercises load of a sequence of mapping merges and overrides. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_omap`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L124-L140) — Exercises load of a mapping containing an explicit omap value. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_omap_flow_style`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L143-L146) — Exercises load of a mapping containing a flow-style omap value. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_safe_load`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L48-L50) — Exercises safe_load of a root plain mapping. Whether the edited loader registration or callback governs this call depends on the external implementation and interpreter guard.
- [ ] [`test_oyaml.py::test_subclass_dump`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L91-L95) — Dumps an OrderedDict subclass under safe and unsafe modes. External PyYAML dispatch chooses the applicable representer.
- [ ] [`test_oyaml.py::test_unhashable_error_context`](https://github.com/wimglenn/oyaml/blob/5152325dcdb68b3684c7ba745a8710df6ea40b9a/test_oyaml.py#L192-L194) — Loads an unhashable mapping key with safe_load. The selected external loader and registration are runtime dependent.

### Outside discovery (0)


## Selection exclusions

The pre-analysis protocol fixes repository/window ordering and selects two eligible functional first-parent changes per repository. See PROTOCOL.md and CANDIDATES.md.

- [madzak/python-json-logger@6d43bde05ed8](https://github.com/madzak/python-json-logger/commit/6d43bde05ed8d6ce6b8740aa1d7ac9eaf4a6af18): Documentation, release, packaging or CI/maintenance metadata only.
- [madzak/python-json-logger@a335e6177998](https://github.com/madzak/python-json-logger/commit/a335e61779984ae283f424b4e21483cc6e1800ab): Documentation, release, packaging or CI/maintenance metadata only.
- [madzak/python-json-logger@c0b4ba1efee3](https://github.com/madzak/python-json-logger/commit/c0b4ba1efee39b1acd0ff898aad93a1cf447192b): Test-only change.
- [madzak/python-json-logger@bd9e54f5274b](https://github.com/madzak/python-json-logger/commit/bd9e54f5274be970300fdd13940cc1a6eac603f3): Test-only change.
- [madzak/python-json-logger@6083af56e5b0](https://github.com/madzak/python-json-logger/commit/6083af56e5b001d90896ca70dc841ce80576b068): Documentation, release, packaging or CI/maintenance metadata only.
- [madzak/python-json-logger@9d5bb1f2de4f](https://github.com/madzak/python-json-logger/commit/9d5bb1f2de4fbf40ffc8591b470d70bdc667a990): Documentation, release, packaging or CI/maintenance metadata only.
- [madzak/python-json-logger@83b847aef3c6](https://github.com/madzak/python-json-logger/commit/83b847aef3c68bc98d1c72af6e3f3272b63e1727): Test-only change.
- [madzak/python-json-logger@41a763dde0bd](https://github.com/madzak/python-json-logger/commit/41a763dde0bd1967f3cb31df26c1071953b82039): Documentation, release, packaging or CI/maintenance metadata only.
- [madzak/python-json-logger@e756b9bb8d5e](https://github.com/madzak/python-json-logger/commit/e756b9bb8d5edd1cbfa1f975f0b0e560cf5df30a): Documentation, release, packaging or CI/maintenance metadata only.
- [madzak/python-json-logger@9876d0411377](https://github.com/madzak/python-json-logger/commit/9876d0411377a9a8cbab72b4207d557f9dc42526): Merge copy, excluded by protocol.
- [madzak/python-json-logger@d7fe3fec5f76](https://github.com/madzak/python-json-logger/commit/d7fe3fec5f761a0223f2624bc951fa600fad2b6b): Merge copy, excluded by protocol.
- [madzak/python-json-logger@4006b5cd1268](https://github.com/madzak/python-json-logger/commit/4006b5cd12684bd3dc4e71054b09c173278a481a): Documentation, release, packaging or CI/maintenance metadata only.
- [madzak/python-json-logger@cf6a8ff14e02](https://github.com/madzak/python-json-logger/commit/cf6a8ff14e0214c031918d2e8390e2d74f04178a): Documentation, release, packaging or CI/maintenance metadata only.
- [madzak/python-json-logger@687cc5226087](https://github.com/madzak/python-json-logger/commit/687cc52260876fd2189cbb7c5856e3fbaff65279): Documentation, release, packaging or CI/maintenance metadata only.
- [madzak/python-json-logger@46826c4921a2](https://github.com/madzak/python-json-logger/commit/46826c4921a2eff492e4f9fe9044fe4ec6c38187): Production candidate in BSD-2-Clause repository, outside the allowlist.
- [madzak/python-json-logger@32aa5120b2b0](https://github.com/madzak/python-json-logger/commit/32aa5120b2b0c32dcf61e528bbba88a0f38d5f36): Merge copy, excluded by protocol.
- [madzak/python-json-logger@3a9a93692658](https://github.com/madzak/python-json-logger/commit/3a9a9369265822f7db8845a7a9f1b1d0f3b29be1): Merge copy, excluded by protocol.
- [madzak/python-json-logger@88838bd9627e](https://github.com/madzak/python-json-logger/commit/88838bd9627ee0eed1e8d9429b42890f7f484c06): Production candidate in BSD-2-Clause repository, outside the allowlist.
- [madzak/python-json-logger@c15337a3d748](https://github.com/madzak/python-json-logger/commit/c15337a3d748e5b564f668ef728c61d6f919a74e): Production candidate in BSD-2-Clause repository, outside the allowlist.
- [madzak/python-json-logger@12ab1c30c248](https://github.com/madzak/python-json-logger/commit/12ab1c30c24846cadfba214fa9cd2c00d899ab2a): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@218147363a40](https://github.com/pydanny/cached-property/commit/218147363a4085c0826a80a83984f3d20e718aa0): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@fe3aae9fd892](https://github.com/pydanny/cached-property/commit/fe3aae9fd892e87ca24e33086b45bc2ff9f33108): Merge copy, excluded by protocol.
- [pydanny/cached-property@c97cf414254e](https://github.com/pydanny/cached-property/commit/c97cf414254e2aed83417785b3890a4f2602ba81): Docstring-only production change.
- [pydanny/cached-property@b4cc28f4f08e](https://github.com/pydanny/cached-property/commit/b4cc28f4f08e9c4bd06b35f92ab0f5a1aa2ae9b7): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@51c2086859cd](https://github.com/pydanny/cached-property/commit/51c2086859cd97f75e38e86c8e472cb7abdb4999): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@1ff7f45d298c](https://github.com/pydanny/cached-property/commit/1ff7f45d298cd38263133cd8cc2f35516cf4cf0f): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@53dcadfedb92](https://github.com/pydanny/cached-property/commit/53dcadfedb92374eec890d58d824c7437c68f05c): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@cb8d53fd100e](https://github.com/pydanny/cached-property/commit/cb8d53fd100e14dbb564f22bff8ec94868371e1a): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@cdea716046a8](https://github.com/pydanny/cached-property/commit/cdea716046a82de3bc971e0f32a41412f9d657e8): Merge copy, excluded by protocol.
- [pydanny/cached-property@537a5ca047aa](https://github.com/pydanny/cached-property/commit/537a5ca047aa5240476332a26f39f949c9a15458): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@93949e7cb4a3](https://github.com/pydanny/cached-property/commit/93949e7cb4a3cc562d452d379acb86b253454cf7): Formatting across the project.
- [pydanny/cached-property@945d81d40fae](https://github.com/pydanny/cached-property/commit/945d81d40fae050efff30e14e6c09da8ddaa40c3): Merge copy, excluded by protocol.
- [pydanny/cached-property@20ad6d3e1741](https://github.com/pydanny/cached-property/commit/20ad6d3e174193b1a4df1802ec64e0c2d6052841): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@863223bab17a](https://github.com/pydanny/cached-property/commit/863223bab17abf6ede84a34804554c01a95f9ba0): Merge copy, excluded by protocol.
- [pydanny/cached-property@55be8e79d2e1](https://github.com/pydanny/cached-property/commit/55be8e79d2e1cc1eed6d1507feea7a17c4d1700e): Merge copy, excluded by protocol.
- [pydanny/cached-property@3ee256b035cd](https://github.com/pydanny/cached-property/commit/3ee256b035cd1c9fe491da22f051213e466a2495): Merge copy, excluded by protocol.
- [pydanny/cached-property@82ebde2a7aae](https://github.com/pydanny/cached-property/commit/82ebde2a7aae75b6fa388225ee7d58222d232b0a): Merge copy, excluded by protocol.
- [pydanny/cached-property@99f1a6eac837](https://github.com/pydanny/cached-property/commit/99f1a6eac837e8b3850d70cf9f5e8faa522c6b3f): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@8b45f2cb3990](https://github.com/pydanny/cached-property/commit/8b45f2cb39900600a10106b416e62f467389a98c): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@cd13b5f0f3de](https://github.com/pydanny/cached-property/commit/cd13b5f0f3de0c8f80af2715bdced5a884b6e23d): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@9fe089a2ae88](https://github.com/python-humanize/humanize/commit/9fe089a2ae88dabd17d74e24e2af42725f5b91c4): Changes test-only mock imports and packaging.
- [python-humanize/humanize@a43c266c3056](https://github.com/python-humanize/humanize/commit/a43c266c30565e025a26abc77e747d88923dac6b): Translation data only, no production Python behavior change.
- [python-humanize/humanize@05cc05da3f34](https://github.com/python-humanize/humanize/commit/05cc05da3f34d55dc3feb3decaaa9f4e98491a45): Translation data only, no production Python behavior change.
- [python-humanize/humanize@b0afc5f214bb](https://github.com/python-humanize/humanize/commit/b0afc5f214bbeccac3751dc8407642e9c9a8f613): Translation data only, no production Python behavior change.
- [python-humanize/humanize@526baa71a654](https://github.com/python-humanize/humanize/commit/526baa71a654ac939c246837bbe1bc75bfd662c0): Translation data only, no production Python behavior change.
- [python-humanize/humanize@56459415de8a](https://github.com/python-humanize/humanize/commit/56459415de8ad3da0820c2de36823f0e86271620): Translation data only, no production Python behavior change.
- [python-humanize/humanize@429a7c5f6306](https://github.com/python-humanize/humanize/commit/429a7c5f63068b656ff03be42da9f30e5398387f): Translation data only, no production Python behavior change.
- [python-humanize/humanize@54502fcb5635](https://github.com/python-humanize/humanize/commit/54502fcb5635ce96ae5d6409bbc715fa0a207e50): Translation data only, no production Python behavior change.
- [python-humanize/humanize@53a9a085df88](https://github.com/python-humanize/humanize/commit/53a9a085df88e2c5d5ab5e9f0f5b6941d543b407): Translation data only, no production Python behavior change.
- [python-humanize/humanize@9fed723dea69](https://github.com/python-humanize/humanize/commit/9fed723dea69bf8b837bbd97fef6e0efd5c9f3a4): Example-only change.
- [python-humanize/humanize@3299e2e51704](https://github.com/python-humanize/humanize/commit/3299e2e5170475882a8b8e2421931a926df5c10f): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@d4f7f998a485](https://github.com/python-humanize/humanize/commit/d4f7f998a48581843fbbb597565d225c4a37c446): Raw strings retain regex and replacement values, addressing invalid escape warnings.
- [python-humanize/humanize@86e6f226fe04](https://github.com/python-humanize/humanize/commit/86e6f226fe04626f80e6b4727ca578c469ad4a60): Merge copy, excluded by protocol.
- [python-humanize/humanize@2783e8903885](https://github.com/python-humanize/humanize/commit/2783e8903885f7b7cdc6fa189ecb63ef160a63d0): Translation data only, no production Python behavior change.
- [python-humanize/humanize@8e5580f2b563](https://github.com/python-humanize/humanize/commit/8e5580f2b56350129450a12dda9ea00e57b9be5e): Translation data only, no production Python behavior change.
- [python-humanize/humanize@bec33540362a](https://github.com/python-humanize/humanize/commit/bec33540362a04b01a13ae9a639bfeae002c9c96): Translation entry and test whitespace only.
- [python-humanize/humanize@019fdcd961e5](https://github.com/python-humanize/humanize/commit/019fdcd961e5f4274279d2b3eea7ecc777db256a): Translation data only, no production Python behavior change.
- [python-humanize/humanize@32c469bc378d](https://github.com/python-humanize/humanize/commit/32c469bc378de22e8eabd5f9565bd7cffe7c7ae0): Merge copy, excluded by protocol.
- [python-humanize/humanize@fc4a2303cf8d](https://github.com/python-humanize/humanize/commit/fc4a2303cf8dd31052a51f5c2c4ba3348aa74ce7): Merge copy, excluded by protocol.
- [python-humanize/humanize@292a38ad3f2b](https://github.com/python-humanize/humanize/commit/292a38ad3f2b2bfa61f1c8bef74af4a838be899e): Merge copy, excluded by protocol.
- [wimglenn/oyaml@d0195070d26b](https://github.com/wimglenn/oyaml/commit/d0195070d26bd982f1e4e604bded5510dd035cd7): Merge copy, excluded by protocol.
- [wimglenn/oyaml@7381373cec37](https://github.com/wimglenn/oyaml/commit/7381373cec378a464e1cf4ca8b03c6cb8493469b): CI, metadata, documentation and tests only.
- [wimglenn/oyaml@45bef7ee676e](https://github.com/wimglenn/oyaml/commit/45bef7ee676e30a68a122fbac9801727e0064aab): Merge copy, excluded by protocol.
- [gruns/icecream@7bf20d4c6cbc](https://github.com/gruns/icecream/commit/7bf20d4c6cbc855d3c64d6369a4e0bae753599d8): Merge copy, excluded by protocol.
- [gruns/icecream@987a00151870](https://github.com/gruns/icecream/commit/987a00151870a0d99c484e63aff70af658dbf2d2): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@69f203c719d0](https://github.com/gruns/icecream/commit/69f203c719d00af230a7bfea5a6ddd783c9ecf2d): Merge copy, excluded by protocol.
- [gruns/icecream@d5bcaa250ef9](https://github.com/gruns/icecream/commit/d5bcaa250ef9e0f59eb70ffcefd892d0ad9de39b): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@fb919b77069f](https://github.com/gruns/icecream/commit/fb919b77069f52ef6597b0ac74ea0939873d8298): Release version and changelog only.
- [gruns/icecream@b6a4421e1760](https://github.com/gruns/icecream/commit/b6a4421e1760ae1972659c404200967af827321e): Merge copy, excluded by protocol.
- [gruns/icecream@ae9f728be4ad](https://github.com/gruns/icecream/commit/ae9f728be4adcf14f07a0e77cf76af6d99507f48): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@e952dc5b36af](https://github.com/gruns/icecream/commit/e952dc5b36af4671867b052225863299e396d30c): Merge copy, excluded by protocol.
- [gruns/icecream@a361a2a9ed97](https://github.com/gruns/icecream/commit/a361a2a9ed97bbec292452f73d170663d217cb8a): Merge copy, excluded by protocol.
- [gruns/icecream@8f92940de9dc](https://github.com/gruns/icecream/commit/8f92940de9dcb6f2133ff03c004e1d9896847bcf): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@db8156570713](https://github.com/gruns/icecream/commit/db81565707137d177fa1fcdabe5d9b1cb22b2c4e): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@daa30a0672e4](https://github.com/gruns/icecream/commit/daa30a0672e4588ca75a7072352114fe4232869a): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@9bd62f3c3ae4](https://github.com/gruns/icecream/commit/9bd62f3c3ae4e0502b8dc7a4ccf25de45ef0bd19): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@52d37e51e8a0](https://github.com/gruns/icecream/commit/52d37e51e8a0808b1d23ada9f46511a76d88a0bd): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@ffefe1b9ceb0](https://github.com/gruns/icecream/commit/ffefe1b9ceb04a476a4f5ab8dbe56d93d553c3fb): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@90e639ac1bdd](https://github.com/gruns/icecream/commit/90e639ac1bdd26100f2672a05a9c338cd615ce23): Merge copy, excluded by protocol.
- [gruns/icecream@b0a5a94993ef](https://github.com/gruns/icecream/commit/b0a5a94993efe3eac93e18d36c8aea351bbd57e6): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@792c59009219](https://github.com/gruns/icecream/commit/792c59009219e8d8b1f4054acbcecf02ce884034): Merge copy, excluded by protocol.
- [gruns/icecream@0280d0df84e6](https://github.com/gruns/icecream/commit/0280d0df84e66f3016cb05c0f4b98c10cd9c0432): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@1925fc694beb](https://github.com/gruns/icecream/commit/1925fc694bebff81bc37e29997ac3a0e5fcffd24): Documentation, release, packaging or CI/maintenance metadata only.
- [gruns/icecream@cb60412d2881](https://github.com/gruns/icecream/commit/cb60412d2881e405c23fe693382345bd828f4471): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@a0f03c137ab3](https://github.com/python-humanize/humanize/commit/a0f03c137ab33a9b4896789b94edb95ab635f9df): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@97fc008f5b3a](https://github.com/python-humanize/humanize/commit/97fc008f5b3af03d09e41cfd0afc8ddbeae8f195): Merge copy, excluded by protocol.
- [python-humanize/humanize@89b73e009964](https://github.com/python-humanize/humanize/commit/89b73e0099646ed6d3a7826e8c276a25f4e32d93): Merge copy, excluded by protocol.
- [python-humanize/humanize@9b5fa9d1e384](https://github.com/python-humanize/humanize/commit/9b5fa9d1e38429f7a954605ed0c420c242cb5107): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@6ca44f7d14a5](https://github.com/python-humanize/humanize/commit/6ca44f7d14a5bac0d8af2358e97eafe105174c09): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@5195e30c3bad](https://github.com/python-humanize/humanize/commit/5195e30c3bad6eb1992300c4920df5fdb5d150cd): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@0cbd1ababec2](https://github.com/python-humanize/humanize/commit/0cbd1ababec2dcdd71e57856f9b0cce8c4d21b51): Merge copy, excluded by protocol.
- [python-humanize/humanize@794a1eb43079](https://github.com/python-humanize/humanize/commit/794a1eb43079bbd21c3898ae930813cb55b81fcc): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@36bc853e3824](https://github.com/python-humanize/humanize/commit/36bc853e382460adb0d56c8237f9813f2c2d2750): Merge copy, excluded by protocol.
- [python-humanize/humanize@55b5c18b003e](https://github.com/python-humanize/humanize/commit/55b5c18b003efd27a82e330619c3774adf306ebb): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@3b8505d5bfd8](https://github.com/python-humanize/humanize/commit/3b8505d5bfd805462303afb53252f75a2d2069a0): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@c24f3e3b3041](https://github.com/python-humanize/humanize/commit/c24f3e3b304129fbb779f88cb8eaa64a8e802772): Merge copy, excluded by protocol.
- [python-humanize/humanize@93119f292072](https://github.com/python-humanize/humanize/commit/93119f292072ea44aa83f705b0c9bdc869cec2b7): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@6d1e98966a47](https://github.com/python-humanize/humanize/commit/6d1e98966a47978572c6ce6606f19414499784fe): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@b2785e9671bb](https://github.com/python-humanize/humanize/commit/b2785e9671bbbe260a82bc7689a3db0308866592): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@d97c61c00375](https://github.com/python-humanize/humanize/commit/d97c61c00375f7c70654d5901cc39e2e22d63854): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@128717639723](https://github.com/python-humanize/humanize/commit/128717639723f035cca1acc8f9c1e1a427247c34): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@184269e4b8f9](https://github.com/python-humanize/humanize/commit/184269e4b8f9415927e19d841891c9021235f6ce): Merge copy, excluded by protocol.
- [python-humanize/humanize@2bf7f5bb4812](https://github.com/python-humanize/humanize/commit/2bf7f5bb481238c544a0557a3319659fda6d6fc3): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@aec9dc22412a](https://github.com/python-humanize/humanize/commit/aec9dc22412a70c26286f3a9a116164dc7163d2c): Merge copy, excluded by protocol.
- [python-humanize/humanize@eaaa1e2ca6d0](https://github.com/python-humanize/humanize/commit/eaaa1e2ca6d00847973df09cba65ef4a79cf5ae0): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@2d4143e0aecb](https://github.com/python-humanize/humanize/commit/2d4143e0aecb719a376dc757b439fc7e41b0d773): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@c3152b6d6fe6](https://github.com/python-humanize/humanize/commit/c3152b6d6fe6caa050ca448fa544ec757b7809ef): Merge copy, excluded by protocol.
- [python-humanize/humanize@518bae32535a](https://github.com/python-humanize/humanize/commit/518bae32535ad7f78b8788c9581d947fe67e69de): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@b0fe8eb00d4d](https://github.com/python-humanize/humanize/commit/b0fe8eb00d4d6f9699c4def5a2c57ee8d31a93a6): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@b03cd63ccccf](https://github.com/python-humanize/humanize/commit/b03cd63ccccf9d712cf710641e091fadd073e758): Documentation, release, packaging or CI/maintenance metadata only.
- [python-humanize/humanize@809e66b7231b](https://github.com/python-humanize/humanize/commit/809e66b7231b7f1ad4ba5db11b2728b95655d68c): Merge copy, excluded by protocol.
- [pydanny/cached-property@409f24286e16](https://github.com/pydanny/cached-property/commit/409f24286e16ea3086af463edea6b80cdd62deed): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@4adb33246294](https://github.com/pydanny/cached-property/commit/4adb33246294a6e7370c62212028b9fb152f6157): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@0be6adca6f17](https://github.com/pydanny/cached-property/commit/0be6adca6f173ee7d2d0d5ec31d6b01650bac97e): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@f075b4f71741](https://github.com/pydanny/cached-property/commit/f075b4f71741f84b687327948fc3a65e4d858b2c): Merge copy, excluded by protocol.
- [pydanny/cached-property@ab48d01ec5b7](https://github.com/pydanny/cached-property/commit/ab48d01ec5b716b7078fa1da06cbf538da9e8ff7): Merge copy, excluded by protocol.
- [pydanny/cached-property@6b4e990aca40](https://github.com/pydanny/cached-property/commit/6b4e990aca401ef47f7517c914b6b6cda360f9e5): Merge copy, excluded by protocol.
- [pydanny/cached-property@4056dca17cfc](https://github.com/pydanny/cached-property/commit/4056dca17cfc1bbe18f43819ece998cedb994a28): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@426aa51d08d4](https://github.com/pydanny/cached-property/commit/426aa51d08d4c43cd318872c97e8d086abe013b8): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@a5ecd1df8edf](https://github.com/pydanny/cached-property/commit/a5ecd1df8edf1379581f4da37defa7ff1b1d1172): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@deb84ce9c9a5](https://github.com/pydanny/cached-property/commit/deb84ce9c9a53e2ca4969b8aa47dc80795fdf43a): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@bad6d273bded](https://github.com/pydanny/cached-property/commit/bad6d273bdedb28e4dc237fa2f4b06b60da1f33a): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@d10a9661ae3a](https://github.com/pydanny/cached-property/commit/d10a9661ae3ae59c60e9edbaa70a639b0dd76ce5): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@831c889ecf17](https://github.com/pydanny/cached-property/commit/831c889ecf17ec2933513d45bbff6eeb1513a6dd): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@46b84eb8ccf7](https://github.com/pydanny/cached-property/commit/46b84eb8ccf7f42598e04aab0b61eb21f0c4a290): Merge copy, excluded by protocol.
- [pydanny/cached-property@f7b6d211c6d1](https://github.com/pydanny/cached-property/commit/f7b6d211c6d1439253ee0ac01898731219bc27e6): CI, history and tox support metadata only.
- [pydanny/cached-property@0990bfdb9694](https://github.com/pydanny/cached-property/commit/0990bfdb9694def81227c87879b180153ffb86ea): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@63c1f67a492d](https://github.com/pydanny/cached-property/commit/63c1f67a492d6fc37ea3b72ae6f88e7b87d0bd8a): Merge copy, excluded by protocol.
- [pydanny/cached-property@9a1b19a8247c](https://github.com/pydanny/cached-property/commit/9a1b19a8247c3f8ea7adcdfc2e1404f9937a91e0): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@9cb55ecb394a](https://github.com/pydanny/cached-property/commit/9cb55ecb394a7e82ebb97a9099b7e87766eadddf): Documentation, release, packaging or CI/maintenance metadata only.
- [pydanny/cached-property@08a02298bdfd](https://github.com/pydanny/cached-property/commit/08a02298bdfd6e8203df7c8620a651be7d03a89f): Documentation, release, packaging or CI/maintenance metadata only.
