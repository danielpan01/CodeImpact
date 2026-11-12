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

## itsdangerous_fips

[pallets/itsdangerous](https://github.com/pallets/itsdangerous/commit/2f69e841d2a979c616a55b226e444694f5d9c962) — Deferred default digest lookup crosses class defaults, signer construction and serializer fixtures; no FIPS runtime claim.

Before: `93ae366874bbd4f69d90495c45b2cd336387496c`; after: `2f69e841d2a979c616a55b226e444694f5d9c962`.

Label status: **draft**; author: Codex; reviewer: none.
Frozen label SHA-256: `b1a43f766b79cf26a38155c0b771aa07dd7eb1c72b5297e7b66345ac54695125`.

### Complete Python change

````diff
--- base/src/itsdangerous/signer.py
+++ head/src/itsdangerous/signer.py
@@ -37,13 +37,21 @@
         return b""
 
 
+def _lazy_sha1(string: bytes = b"") -> t.Any:
+    """Don't access ``hashlib.sha1`` until runtime. FIPS builds may not include
+    SHA-1, in which case the import and use as a default would fail before the
+    developer can configure something else.
+    """
+    return hashlib.sha1(string)
+
+
 class HMACAlgorithm(SigningAlgorithm):
     """Provides signature generation using HMACs."""
 
     #: The digest method to use with the MAC algorithm. This defaults to
     #: SHA1, but can be changed to any other function in the hashlib
     #: module.
-    default_digest_method: t.Any = staticmethod(hashlib.sha1)
+    default_digest_method: t.Any = staticmethod(_lazy_sha1)
 
     def __init__(self, digest_method: t.Any = None):
         if digest_method is None:
@@ -109,7 +117,7 @@
     #: doesn't apply when used intermediately in HMAC.
     #:
     #: .. versionadded:: 0.14
-    default_digest_method: t.Any = staticmethod(hashlib.sha1)
+    default_digest_method: t.Any = staticmethod(_lazy_sha1)
 
     #: The default scheme to use to derive the signing key from the
     #: secret key and salt. The default is ``django-concat``. Possible
--- base/tests/test_itsdangerous/test_serializer.py
+++ head/tests/test_itsdangerous/test_serializer.py
@@ -14,6 +14,7 @@
 from itsdangerous.exc import BadPayload
 from itsdangerous.exc import BadSignature
 from itsdangerous.serializer import Serializer
+from itsdangerous.signer import _lazy_sha1
 from itsdangerous.signer import Signer
 
 
@@ -177,7 +178,7 @@
         )
 
         unsigners = serializer.iter_unsigners()
-        assert next(unsigners).digest_method == hashlib.sha1
+        assert next(unsigners).digest_method == _lazy_sha1
 
         for signer in unsigners:
             assert signer.digest_method == hashlib.sha256
````

### Draft labels and source

#### expected_affected (29)

- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_alt_salt`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L123-L129) — test_alt_salt constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_bad_payload_exception`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L81-L89) — test_bad_payload_exception constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_bad_signature_exception`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L72-L79) — test_bad_signature_exception constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_changed_value`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L64-L70) — test_changed_value constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_file`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L113-L121) — test_file constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_iter_unsigners`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L167-L184) — test_iter_unsigners constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_loads_unsafe`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L91-L111) — test_loads_unsafe constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_serializer`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L52-L53) — test_serializer constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_serializer_kwargs`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L146-L154) — test_serializer_kwargs constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_signer_cls`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L131-L137) — test_signer_cls constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_signer_kwargs`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L139-L144) — test_signer_kwargs constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_serializer.py::test_digests`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L187-L197) — test_digests constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_algorithm`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_signer.py#L87-L92) — test_algorithm constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_broken_signature`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_signer.py#L42-L51) — test_broken_signature constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_changed_value`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_signer.py#L53-L59) — test_changed_value constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_invalid_key_derivation`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_signer.py#L74-L78) — test_invalid_key_derivation constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_key_derivation`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_signer.py#L70-L72) — test_key_derivation constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_no_separator`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_signer.py#L34-L40) — test_no_separator constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_secret_keys`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_signer.py#L94-L102) — test_secret_keys constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_signer`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_signer.py#L27-L32) — test_signer constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimedSerializer.test_max_age`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_timed.py#L101-L111) — test_max_age constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimedSerializer.test_return_payload`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_timed.py#L113-L115) — test_return_payload constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_future_age`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_timed.py#L78-L85) — test_future_age constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_malformed_future_timestamp`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_timed.py#L69-L76) — test_malformed_future_timestamp constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_malformed_timestamp`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_timed.py#L59-L67) — test_malformed_timestamp constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_max_age`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_timed.py#L34-L43) — test_max_age constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_return_timestamp`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_timed.py#L45-L47) — test_return_timestamp constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_sig_error_date_signed`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_timed.py#L87-L93) — test_sig_error_date_signed constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_timestamp_missing`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_timed.py#L49-L57) — test_timestamp_missing constructs/uses a default-digest signer (directly or via the visible signer/serializer fixtures and make_signer), or checks that default. Signer.__init__ reads default_digest_method; HMACAlgorithm receives it. No SHA-1 availability or runtime failure is asserted.

#### expected_unaffected (8)

- [ ] [`tests/test_itsdangerous/test_encoding.py::test_base64`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_encoding.py#L18-L22) — test_base64 tests standalone byte/base64/integer conversions in encoding.py, which do not use the signer digest defaults.
- [ ] [`tests/test_itsdangerous/test_encoding.py::test_base64_bad`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_encoding.py#L25-L27) — test_base64_bad tests standalone byte/base64/integer conversions in encoding.py, which do not use the signer digest defaults.
- [ ] [`tests/test_itsdangerous/test_encoding.py::test_int_bytes`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_encoding.py#L33-L37) — test_int_bytes tests standalone byte/base64/integer conversions in encoding.py, which do not use the signer digest defaults.
- [ ] [`tests/test_itsdangerous/test_encoding.py::test_want_bytes`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_encoding.py#L12-L14) — test_want_bytes tests standalone byte/base64/integer conversions in encoding.py, which do not use the signer digest defaults.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_fallback_signers`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_serializer.py#L156-L165) — Both serializer factories pass explicit hashlib.sha256/sha1 digest methods, including the fallback. They bypass the changed defaults.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_digest_method`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_signer.py#L80-L82) — The signer_factory is passed hashlib.md5 explicitly; Signer.__init__ forwards that digest to HMACAlgorithm, bypassing both changed defaults.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_invalid_separator`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_signer.py#L61-L65) — Signer.__init__ rejects sep="-" before reading default_digest_method; the invalid separator error has no dependency on the changed digest default.
- [ ] [`tests/test_itsdangerous/test_signer.py::test_abstract_algorithm`](https://github.com/pallets/itsdangerous/blob/2f69e841d2a979c616a55b226e444694f5d9c962/tests/test_itsdangerous/test_signer.py#L105-L109) — Constructs SigningAlgorithm and checks its abstract get_signature error; it does not construct HMACAlgorithm or Signer.

#### unclassified (0)


## itsdangerous_future

[pallets/itsdangerous](https://github.com/pallets/itsdangerous/commit/c30678d19e37011890e2374cca04f7789e101793) — Negative signature-age rejection in timestamp verification, including inherited and fixture-driven tests.

Before: `1a9b8d1f9968eb248bda69f39d373a6330b692ba`; after: `c30678d19e37011890e2374cca04f7789e101793`.

Label status: **draft**; author: Codex; reviewer: none.
Frozen label SHA-256: `5e52f3701c5333d253e66b392b0a7aff2c47367d78bcc3ee199161b65ec681d8`.

### Complete Python change

````diff
--- base/src/itsdangerous/timed.py
+++ head/src/itsdangerous/timed.py
@@ -104,6 +104,13 @@
                     date_signed=self.timestamp_to_datetime(timestamp),
                 )
 
+            if age < 0:
+                raise SignatureExpired(
+                    f"Signature age {age} < 0 seconds",
+                    payload=value,
+                    date_signed=self.timestamp_to_datetime(timestamp),
+                )
+
         if return_timestamp:
             return value, self.timestamp_to_datetime(timestamp)
 
--- base/tests/test_itsdangerous/test_timed.py
+++ head/tests/test_itsdangerous/test_timed.py
@@ -64,6 +64,13 @@
 
         assert "Malformed" in str(exc_info.value)
 
+    def test_future_age(self, signer):
+        signed = signer.sign("value")
+
+        with freeze_time("1971-05-31"):
+            with pytest.raises(SignatureExpired):
+                signer.unsign(signed, max_age=10)
+
 
 class TestTimedSerializer(FreezeMixin, TestSerializer):
     @pytest.fixture()
````

### Draft labels and source

#### expected_affected (7)

- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimedSerializer.test_max_age`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_timed.py#L80-L90) — test_max_age calls TimestampSigner.unsign directly through signer_factory, or through TimedSerializer.loads and its default_signer. This is a dependency on the edited callable, even when max_age is omitted; it is not a prediction of assertion failure.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimedSerializer.test_return_payload`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_timed.py#L92-L94) — test_return_payload calls TimestampSigner.unsign directly through signer_factory, or through TimedSerializer.loads and its default_signer. This is a dependency on the edited callable, even when max_age is omitted; it is not a prediction of assertion failure.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_future_age`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_timed.py#L67-L72) — test_future_age calls TimestampSigner.unsign directly through signer_factory, or through TimedSerializer.loads and its default_signer. This is a dependency on the edited callable, even when max_age is omitted; it is not a prediction of assertion failure.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_malformed_timestamp`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_timed.py#L58-L65) — test_malformed_timestamp calls TimestampSigner.unsign directly through signer_factory, or through TimedSerializer.loads and its default_signer. This is a dependency on the edited callable, even when max_age is omitted; it is not a prediction of assertion failure.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_max_age`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_timed.py#L34-L43) — test_max_age calls TimestampSigner.unsign directly through signer_factory, or through TimedSerializer.loads and its default_signer. This is a dependency on the edited callable, even when max_age is omitted; it is not a prediction of assertion failure.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_return_timestamp`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_timed.py#L45-L47) — test_return_timestamp calls TimestampSigner.unsign directly through signer_factory, or through TimedSerializer.loads and its default_signer. This is a dependency on the edited callable, even when max_age is omitted; it is not a prediction of assertion failure.
- [ ] [`tests/test_itsdangerous/test_timed.py::TestTimestampSigner.test_timestamp_missing`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_timed.py#L49-L56) — test_timestamp_missing calls TimestampSigner.unsign directly through signer_factory, or through TimedSerializer.loads and its default_signer. This is a dependency on the edited callable, even when max_age is omitted; it is not a prediction of assertion failure.

#### expected_unaffected (19)

- [ ] [`tests/test_itsdangerous/test_encoding.py::test_base64`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_encoding.py#L18-L22) — test_base64 exercises encoding helpers, not TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_encoding.py::test_base64_bad`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_encoding.py#L25-L27) — test_base64_bad exercises encoding helpers, not TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_encoding.py::test_int_bytes`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_encoding.py#L33-L37) — test_int_bytes exercises encoding helpers, not TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_encoding.py::test_want_bytes`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_encoding.py#L12-L14) — test_want_bytes exercises encoding helpers, not TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_jws.py::TestJWSSerializer.test_algorithm`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_jws.py#L28-L30) — test_algorithm uses JSONWebSignatureSerializer/TimedJSONWebSignatureSerializer. jws.py implements header expiration separately using the ordinary Signer; it does not use TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_jws.py::TestJWSSerializer.test_algorithm_mismatch`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_jws.py#L38-L46) — test_algorithm_mismatch uses JSONWebSignatureSerializer/TimedJSONWebSignatureSerializer. jws.py implements header expiration separately using the ordinary Signer; it does not use TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_jws.py::TestJWSSerializer.test_invalid_algorithm`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_jws.py#L32-L36) — test_invalid_algorithm uses JSONWebSignatureSerializer/TimedJSONWebSignatureSerializer. jws.py implements header expiration separately using the ordinary Signer; it does not use TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_jws.py::TestJWSSerializer.test_load_payload_exceptions`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_jws.py#L58-L65) — test_load_payload_exceptions uses JSONWebSignatureSerializer/TimedJSONWebSignatureSerializer. jws.py implements header expiration separately using the ordinary Signer; it does not use TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_jws.py::TestTimedJWSSerializer.test_default_expires_in`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_jws.py#L75-L77) — test_default_expires_in uses JSONWebSignatureSerializer/TimedJSONWebSignatureSerializer. jws.py implements header expiration separately using the ordinary Signer; it does not use TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_jws.py::TestTimedJWSSerializer.test_exp`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_jws.py#L81-L91) — test_exp uses JSONWebSignatureSerializer/TimedJSONWebSignatureSerializer. jws.py implements header expiration separately using the ordinary Signer; it does not use TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_jws.py::TestTimedJWSSerializer.test_invalid_exp`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_jws.py#L111-L120) — test_invalid_exp uses JSONWebSignatureSerializer/TimedJSONWebSignatureSerializer. jws.py implements header expiration separately using the ordinary Signer; it does not use TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_jws.py::TestTimedJWSSerializer.test_invalid_iat`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_jws.py#L122-L125) — test_invalid_iat uses JSONWebSignatureSerializer/TimedJSONWebSignatureSerializer. jws.py implements header expiration separately using the ordinary Signer; it does not use TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_jws.py::TestTimedJWSSerializer.test_missing_exp`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_jws.py#L101-L108) — test_missing_exp uses JSONWebSignatureSerializer/TimedJSONWebSignatureSerializer. jws.py implements header expiration separately using the ordinary Signer; it does not use TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_jws.py::TestTimedJWSSerializer.test_return_header`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_jws.py#L95-L99) — test_return_header uses JSONWebSignatureSerializer/TimedJSONWebSignatureSerializer. jws.py implements header expiration separately using the ordinary Signer; it does not use TimestampSigner.unsign.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_iter_unsigners`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L148-L165) — test_iter_unsigners only exercises ordinary Serializer digest output, the abstract algorithm, constructor/key-derivation errors, or iteration over signer objects. No call to TimestampSigner.unsign is made in that body.
- [ ] [`tests/test_itsdangerous/test_serializer.py::test_digests`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L168-L178) — test_digests only exercises ordinary Serializer digest output, the abstract algorithm, constructor/key-derivation errors, or iteration over signer objects. No call to TimestampSigner.unsign is made in that body.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_invalid_key_derivation`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_signer.py#L74-L78) — test_invalid_key_derivation only exercises ordinary Serializer digest output, the abstract algorithm, constructor/key-derivation errors, or iteration over signer objects. No call to TimestampSigner.unsign is made in that body.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_invalid_separator`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_signer.py#L61-L65) — test_invalid_separator only exercises ordinary Serializer digest output, the abstract algorithm, constructor/key-derivation errors, or iteration over signer objects. No call to TimestampSigner.unsign is made in that body.
- [ ] [`tests/test_itsdangerous/test_signer.py::test_abstract_algorithm`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_signer.py#L95-L99) — test_abstract_algorithm only exercises ordinary Serializer digest output, the abstract algorithm, constructor/key-derivation errors, or iteration over signer objects. No call to TimestampSigner.unsign is made in that body.

#### unclassified (18)

- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_alt_salt`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L106-L112) — TestSerializer.test_alt_salt is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_bad_payload_exception`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L66-L74) — TestSerializer.test_bad_payload_exception is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_bad_signature_exception`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L58-L64) — TestSerializer.test_bad_signature_exception is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_changed_value`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L50-L56) — TestSerializer.test_changed_value is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_fallback_signers`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L137-L146) — TestSerializer.test_fallback_signers is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_file`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L98-L104) — TestSerializer.test_file is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_loads_unsafe`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L76-L96) — TestSerializer.test_loads_unsafe is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_serializer`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L38-L39) — TestSerializer.test_serializer is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_serializer_kwargs`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L127-L135) — TestSerializer.test_serializer_kwargs is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_signer_cls`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L114-L120) — TestSerializer.test_signer_cls is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_serializer.py::TestSerializer.test_signer_kwargs`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_serializer.py#L122-L125) — TestSerializer.test_signer_kwargs is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_algorithm`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_signer.py#L87-L92) — TestSigner.test_algorithm is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_broken_signature`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_signer.py#L42-L51) — TestSigner.test_broken_signature is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_changed_value`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_signer.py#L53-L59) — TestSigner.test_changed_value is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_digest_method`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_signer.py#L80-L82) — TestSigner.test_digest_method is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_key_derivation`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_signer.py#L70-L72) — TestSigner.test_key_derivation is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_no_separator`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_signer.py#L34-L40) — TestSigner.test_no_separator is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.
- [ ] [`tests/test_itsdangerous/test_signer.py::TestSigner.test_signer`](https://github.com/pallets/itsdangerous/blob/c30678d19e37011890e2374cca04f7789e101793/tests/test_itsdangerous/test_signer.py#L27-L32) — TestSigner.test_signer is an inherited base test reused with ordinary, timestamp, URL-safe and/or JWS fixtures. The one definition ID collapses multiple collection contexts. Some subclass executions can reach TimestampSigner.unsign while others cannot; retain uncertainty until a reviewer agrees how to label that shared ID.

## markupsafe_format_map

[pallets/markupsafe](https://github.com/pallets/markupsafe/commit/391aa07d3c68d4d0888b31fdea62516df9e19cb8) — New escaping-aware mapping-format method, contrasting API addition with the whitespace fix.

Before: `60e7eb97e65947a83fa290010f3dde71be8fed84`; after: `391aa07d3c68d4d0888b31fdea62516df9e19cb8`.

Label status: **draft**; author: Codex; reviewer: none.
Frozen label SHA-256: `526d229e291a62c10de2d568198da2a92acdf39c7b48dc1ad2e3330da49174bd`.

### Complete Python change

````diff
--- base/src/markupsafe/__init__.py
+++ head/src/markupsafe/__init__.py
@@ -208,6 +208,10 @@
         formatter = EscapeFormatter(self.escape)
         return self.__class__(formatter.vformat(self, args, kwargs))
 
+    def format_map(self, map: t.Mapping[str, t.Any]) -> str:  # type: ignore[override]
+        formatter = EscapeFormatter(self.escape)
+        return self.__class__(formatter.vformat(self, (), map))
+
     def __html_format__(self, format_spec: str) -> "Markup":
         if format_spec:
             raise ValueError("Unsupported format specification for Markup.")
--- base/tests/test_markupsafe.py
+++ head/tests/test_markupsafe.py
@@ -108,6 +108,11 @@
     assert result == "<bar/>"
 
 
+def test_format_map():
+    result = Markup("<em>{value}</em>").format_map({"value": "<value>"})
+    assert result == "<em>&lt;value&gt;</em>"
+
+
 def test_formatting_empty():
     formatted = Markup("{}").format(0)
     assert formatted == Markup("0")
````

### Draft labels and source

#### expected_affected (1)

- [ ] [`tests/test_markupsafe.py::test_format_map`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L111-L113) — Directly calls Markup.format_map, the changed method; the real change also edits/adds this test.

#### expected_unaffected (14)

- [ ] [`tests/test_markupsafe.py::test_complex_custom_formatting`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L137-L159) — test_complex_custom_formatting exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_custom_formatting`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L121-L134) — test_custom_formatting exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_dict_interpol`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L60-L67) — test_dict_interpol exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_format`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L100-L108) — test_format exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_formatting_empty`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L116-L118) — test_formatting_empty exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_formatting_with_objects`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L162-L167) — test_formatting_with_objects exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_html_interop`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L35-L45) — test_html_interop exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_missing_interpol`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L49-L51) — test_missing_interpol exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_mul`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L183-L184) — test_mul exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_splitting`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L176-L180) — test_splitting exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_string_interpolation`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L25-L26) — test_string_interpolation exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_tuple_interpol`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L54-L57) — test_tuple_interpol exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_type_behavior`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L29-L32) — test_type_behavior exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_unescape`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L85-L97) — test_unescape exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.format_map; constructing Markup alone does not exercise every method.

#### unclassified (8)

- [ ] [`tests/test_escape.py::test_escape`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_escape.py#L28-L29) — test_escape uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.format_map call is visible.
- [ ] [`tests/test_exception_custom_html.py::test_exception_custom_html`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_exception_custom_html.py#L9-L18) — test_exception_custom_html uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.format_map call is visible.
- [ ] [`tests/test_leak.py::test_markup_leaks`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_leak.py#L13-L28) — test_markup_leaks uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.format_map call is visible.
- [ ] [`tests/test_markupsafe.py::test_adding`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L6-L9) — test_adding uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.format_map call is visible.
- [ ] [`tests/test_markupsafe.py::test_escape_return_type`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L187-L195) — test_escape_return_type uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.format_map call is visible.
- [ ] [`tests/test_markupsafe.py::test_escape_silent`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L170-L173) — test_escape_silent uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.format_map call is visible.
- [ ] [`tests/test_markupsafe.py::test_escaping`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L70-L82) — test_escaping uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.format_map call is visible.
- [ ] [`tests/test_markupsafe.py::test_soft_str`](https://github.com/pallets/markupsafe/blob/391aa07d3c68d4d0888b31fdea62516df9e19cb8/tests/test_markupsafe.py#L198-L201) — test_soft_str uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.format_map call is visible.

## markupsafe_striptags

[pallets/markupsafe](https://github.com/pallets/markupsafe/commit/60a6512315d0ce05e6788808f80be526f2084b3f) — Whitespace handling bug in an HTML/string method; includes its real test edit and the unchanged tests.

Before: `73e6a4886564a554c4a19983d29c97f9fc95457d`; after: `60a6512315d0ce05e6788808f80be526f2084b3f`.

Label status: **draft**; author: Codex; reviewer: none.
Frozen label SHA-256: `c68bc7795fb811cddb1249d3e1e068ce7a285e9424394103196a6a42fe54ff21`.

### Complete Python change

````diff
--- base/src/markupsafe/__init__.py
+++ head/src/markupsafe/__init__.py
@@ -158,8 +158,7 @@
         >>> Markup("Main &raquo;\t<em>About</em>").striptags()
         'Main » About'
         """
-        # collapse spaces
-        value = " ".join(self.split())
+        value = str(self)
 
         # Look for comments then tags separately. Otherwise, a comment that
         # contains a tag would end early, leaving some of the comment behind.
@@ -193,6 +192,8 @@
 
             value = f"{value[:start]}{value[end + 1:]}"
 
+        # collapse spaces
+        value = " ".join(value.split())
         return self.__class__(value).unescape()
 
     @classmethod
--- base/tests/test_markupsafe.py
+++ head/tests/test_markupsafe.py
@@ -73,7 +73,7 @@
         Markup(
             "<!-- outer comment -->"
             "<em>Foo &amp; Bar"
-            "<!-- inner comment about <em> -->"
+            " <!-- inner comment about <em> -->\n "
             "</em>"
             "<!-- comment\nwith\nnewlines\n-->"
             "<meta content='tag\nwith\nnewlines'>"
````

### Draft labels and source

#### expected_affected (1)

- [ ] [`tests/test_markupsafe.py::test_escaping`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L70-L82) — Directly calls Markup.striptags, the changed method; the real change also edits/adds this test.

#### expected_unaffected (15)

- [ ] [`tests/test_markupsafe.py::test_complex_custom_formatting`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L137-L159) — test_complex_custom_formatting exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_custom_formatting`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L121-L134) — test_custom_formatting exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_dict_interpol`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L60-L67) — test_dict_interpol exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_format`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L100-L108) — test_format exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_format_map`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L111-L113) — test_format_map exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_formatting_empty`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L116-L118) — test_formatting_empty exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_formatting_with_objects`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L162-L167) — test_formatting_with_objects exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_html_interop`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L35-L45) — test_html_interop exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_missing_interpol`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L49-L51) — test_missing_interpol exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_mul`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L183-L184) — test_mul exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_splitting`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L176-L180) — test_splitting exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_string_interpolation`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L25-L26) — test_string_interpolation exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_tuple_interpol`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L54-L57) — test_tuple_interpol exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_type_behavior`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L29-L32) — test_type_behavior exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.
- [ ] [`tests/test_markupsafe.py::test_unescape`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L85-L97) — test_unescape exercises other Markup operators, unescape, split or format methods. Those bodies do not call Markup.striptags; constructing Markup alone does not exercise every method.

#### unclassified (7)

- [ ] [`tests/test_escape.py::test_escape`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_escape.py#L28-L29) — test_escape uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.striptags call is visible.
- [ ] [`tests/test_exception_custom_html.py::test_exception_custom_html`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_exception_custom_html.py#L9-L18) — test_exception_custom_html uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.striptags call is visible.
- [ ] [`tests/test_leak.py::test_markup_leaks`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_leak.py#L13-L28) — test_markup_leaks uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.striptags call is visible.
- [ ] [`tests/test_markupsafe.py::test_adding`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L6-L9) — test_adding uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.striptags call is visible.
- [ ] [`tests/test_markupsafe.py::test_escape_return_type`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L187-L195) — test_escape_return_type uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.striptags call is visible.
- [ ] [`tests/test_markupsafe.py::test_escape_silent`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L170-L173) — test_escape_silent uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.striptags call is visible.
- [ ] [`tests/test_markupsafe.py::test_soft_str`](https://github.com/pallets/markupsafe/blob/60a6512315d0ce05e6788808f80be526f2084b3f/tests/test_markupsafe.py#L198-L201) — test_soft_str uses an escape/soft-string fixture or conditional speedups export. tests/conftest.py includes the C extension, outside these Python snapshots; cross-implementation behavior is left for review. No direct Markup.striptags call is visible.

## schedule_repr

[dbader/schedule](https://github.com/dbader/schedule/commit/3863effe15ec8239ba88c65a4231a67e43b116df) — Partially configured job representation fix exercises special-method dispatch and unrelated scheduling controls.

Before: `a3ecd3548aff70bef15a61baee0d2d7f22f57992`; after: `3863effe15ec8239ba88c65a4231a67e43b116df`.

Label status: **draft**; author: Codex; reviewer: none.
Frozen label SHA-256: `9b3901e0a71dc0ff9d0967d87730781e87f0d03958e1d3e88c7e4c37aafffd3b`.

### Complete Python change

````diff
--- base/schedule/__init__.py
+++ head/schedule/__init__.py
@@ -292,9 +292,13 @@
             job_func_name = self.job_func.__name__
         else:
             job_func_name = repr(self.job_func)
-        args = [repr(x) if is_repr(x) else str(x) for x in self.job_func.args]
-        kwargs = ["%s=%s" % (k, repr(v)) for k, v in self.job_func.keywords.items()]
-        call_repr = job_func_name + "(" + ", ".join(args + kwargs) + ")"
+
+        if self.job_func is not None:
+            args = [repr(x) if is_repr(x) else str(x) for x in self.job_func.args]
+            kwargs = ["%s=%s" % (k, repr(v)) for k, v in self.job_func.keywords.items()]
+            call_repr = job_func_name + "(" + ", ".join(args + kwargs) + ")"
+        else:
+            call_repr = "[None]"
 
         if self.at_time is not None:
             return "Every %s %s at %s do %s %s" % (
--- base/test_schedule.py
+++ head/test_schedule.py
@@ -661,6 +661,10 @@
             )
         )
 
+        # Ensure Job.__repr__ does not throw exception on a partially-composed Job
+        s3 = repr(schedule.every(10))
+        assert s3 == "Every 10 None do [None] (last run: [never], next run: [never])"
+
     def test_to_string_lambda_job_func(self):
         assert len(str(every().minute.do(lambda: 1))) > 1
         assert len(str(every().day.at("10:30").do(lambda: 1))) > 1
````

### Draft labels and source

#### expected_affected (3)

- [ ] [`test_schedule.py::SchedulerTests.test_repr_functools_partial_job_func`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L672-L680) — test_repr_functools_partial_job_func explicitly applies repr() to a Job, invoking the changed Job.__repr__. test_to_repr also covers the newly supported incomplete Job.
- [ ] [`test_schedule.py::SchedulerTests.test_time_range_repr`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L237-L243) — test_time_range_repr explicitly applies repr() to a Job, invoking the changed Job.__repr__. test_to_repr also covers the newly supported incomplete Job.
- [ ] [`test_schedule.py::SchedulerTests.test_to_repr`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L643-L666) — test_to_repr explicitly applies repr() to a Job, invoking the changed Job.__repr__. test_to_repr also covers the newly supported incomplete Job.

#### expected_unaffected (35)

- [ ] [`test_schedule.py::SchedulerTests.test_at_time`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L245-L287) — test_at_time exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_at_time_hour`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L388-L420) — test_at_time_hour exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_at_time_minute`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L422-L438) — test_at_time_minute exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_at_timezone`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L526-L566) — test_at_timezone exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_cancel_job`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L808-L828) — test_cancel_job exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_cancel_jobs`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L830-L840) — test_cancel_jobs exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_clear_by_tag`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L877-L894) — test_clear_by_tag exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_daylight_saving_time`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L568-L576) — test_daylight_saving_time exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_get_by_tag`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L849-L875) — test_get_by_tag exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_idle_seconds`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L796-L806) — test_idle_seconds exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_job_func_args_are_passed_on`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L624-L628) — test_job_func_args_are_passed_on exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_misconfigured_job_wont_break_scheduler`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L896-L904) — test_misconfigured_job_wont_break_scheduler exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_property`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L785-L794) — test_next_run_property exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_time`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L440-L461) — test_next_run_time exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_time_day_end`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L463-L485) — test_next_run_time_day_end exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_time_hour_end`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L487-L502) — test_next_run_time_hour_end exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_time_minute_end`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L504-L524) — test_next_run_time_minute_end exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_with_tag`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L199-L211) — test_next_run_with_tag exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_run_all`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L578-L584) — test_run_all exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_run_all_with_decorator`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L586-L602) — test_run_all_with_decorator exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_run_all_with_decorator_args`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L604-L612) — test_run_all_with_decorator_args exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_run_all_with_decorator_defaultargs`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L614-L622) — test_run_all_with_decorator_defaultargs exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_run_every_n_days_at_specific_time`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L758-L783) — test_run_every_n_days_at_specific_time exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_run_every_weekday_at_specific_time_past_today`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L743-L756) — test_run_every_weekday_at_specific_time_past_today exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_run_every_weekday_at_specific_time_today`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L732-L741) — test_run_every_weekday_at_specific_time_today exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_run_pending`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L692-L730) — test_run_pending exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_singular_time_units_match_plural_units`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L213-L218) — test_singular_time_units_match_plural_units exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_tag_type_enforcement`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L842-L847) — test_tag_type_enforcement exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_time_range`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L220-L235) — test_time_range exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_time_units`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L79-L197) — test_time_units exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_to_string`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L630-L641) — test_to_string exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_to_string_functools_partial_job_func`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L682-L690) — test_to_string_functools_partial_job_func exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_to_string_lambda_job_func`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L668-L670) — test_to_string_lambda_job_func exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_until_time`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L289-L365) — test_until_time exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.
- [ ] [`test_schedule.py::SchedulerTests.test_weekday_at_todady`](https://github.com/dbader/schedule/blob/3863effe15ec8239ba88c65a4231a67e43b116df/test_schedule.py#L367-L386) — test_weekday_at_todady exercises scheduling, tags, timing or str(Job), without a Job repr() call. Job has a separate unchanged __str__; Job.run and cancel_job use string formatting, not the edited __repr__.

#### unclassified (0)


## schedule_tags

[dbader/schedule](https://github.com/dbader/schedule/commit/c883af0229143285cf38e1c7733aaf36656c8744) — Tagged next-run API adds a method and changes a property/wrapper while preserving unrelated job operations.

Before: `64f83981b2a55136ea3737b8c35cf3da7b270055`; after: `c883af0229143285cf38e1c7733aaf36656c8744`.

Label status: **draft**; author: Codex; reviewer: none.
Frozen label SHA-256: `1d3592d7f5d91000973a6f6097419b3f8e28fa607b17947052ff508b5ff008c5`.

### Complete Python change

````diff
--- base/schedule/__init__.py
+++ head/schedule/__init__.py
@@ -173,17 +173,25 @@
         if isinstance(ret, CancelJob) or ret is CancelJob:
             self.cancel_job(job)
 
-    @property
-    def next_run(self) -> Optional[datetime.datetime]:
+    def get_next_run(
+        self, tag: Optional[Hashable] = None
+    ) -> Optional[datetime.datetime]:
         """
         Datetime when the next job should run.
+
+        :param tag: Filter the next run for the given tag parameter
 
         :return: A :class:`~datetime.datetime` object
                  or None if no jobs scheduled
         """
         if not self.jobs:
             return None
-        return min(self.jobs).next_run
+        jobs_filtered = self.get_jobs(tag)
+        if not jobs_filtered:
+            return None
+        return min(jobs_filtered).next_run
+
+    next_run = property(get_next_run)
 
     @property
     def idle_seconds(self) -> Optional[float]:
@@ -808,11 +816,11 @@
     default_scheduler.cancel_job(job)
 
 
-def next_run() -> Optional[datetime.datetime]:
+def next_run(tag: Optional[Hashable] = None) -> Optional[datetime.datetime]:
     """Calls :meth:`next_run <Scheduler.next_run>` on the
     :data:`default scheduler instance <default_scheduler>`.
     """
-    return default_scheduler.next_run
+    return default_scheduler.get_next_run(tag)
 
 
 def idle_seconds() -> Optional[float]:
--- base/test_schedule.py
+++ head/test_schedule.py
@@ -190,6 +190,20 @@
         job_instance.latest = 3
         self.assertRaises(ScheduleError, job_instance._schedule_next_run)
 
+    def test_next_run_with_tag(self):
+        with mock_datetime(2014, 6, 28, 12, 0):
+            job1 = every(5).seconds.do(make_mock_job(name="job1")).tag("tag1")
+            job2 = every(2).hours.do(make_mock_job(name="job2")).tag("tag1", "tag2")
+            job3 = (
+                every(1)
+                .minutes.do(make_mock_job(name="job3"))
+                .tag("tag1", "tag3", "tag2")
+            )
+            assert schedule.next_run("tag1") == job1.next_run
+            assert schedule.default_scheduler.get_next_run("tag2") == job3.next_run
+            assert schedule.next_run("tag3") == job3.next_run
+            assert schedule.next_run("tag4") is None
+
     def test_singular_time_units_match_plural_units(self):
         assert every().second.unit == every().seconds.unit
         assert every().minute.unit == every().minutes.unit
@@ -717,7 +731,7 @@
             assert schedule.next_run() == original_datetime(2010, 1, 6, 14, 16)
 
     def test_idle_seconds(self):
-        assert schedule.next_run() is None
+        assert schedule.default_scheduler.next_run is None
         assert schedule.idle_seconds() is None
 
         mock_job = make_mock_job()
````

### Draft labels and source

#### expected_affected (4)

- [ ] [`test_schedule.py::SchedulerTests.test_idle_seconds`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L733-L743) — test_idle_seconds calls schedule.next_run/get_next_run or reads Scheduler.next_run via idle_seconds. These reach the changed scheduler-level lookup/property. The new tagged test and edited idle test are included.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_property`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L722-L731) — test_next_run_property calls schedule.next_run/get_next_run or reads Scheduler.next_run via idle_seconds. These reach the changed scheduler-level lookup/property. The new tagged test and edited idle test are included.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_time`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L433-L454) — test_next_run_time calls schedule.next_run/get_next_run or reads Scheduler.next_run via idle_seconds. These reach the changed scheduler-level lookup/property. The new tagged test and edited idle test are included.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_with_tag`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L193-L205) — test_next_run_with_tag calls schedule.next_run/get_next_run or reads Scheduler.next_run via idle_seconds. These reach the changed scheduler-level lookup/property. The new tagged test and edited idle test are included.

#### expected_unaffected (32)

- [ ] [`test_schedule.py::SchedulerTests.test_at_time`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L239-L281) — test_at_time exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_at_time_hour`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L381-L413) — test_at_time_hour exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_at_time_minute`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L415-L431) — test_at_time_minute exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_cancel_job`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L745-L765) — test_cancel_job exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_cancel_jobs`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L767-L777) — test_cancel_jobs exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_clear_by_tag`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L814-L831) — test_clear_by_tag exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_get_by_tag`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L786-L812) — test_get_by_tag exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_job_func_args_are_passed_on`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L565-L569) — test_job_func_args_are_passed_on exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_misconfigured_job_wont_break_scheduler`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L833-L841) — test_misconfigured_job_wont_break_scheduler exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_time_day_end`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L456-L478) — test_next_run_time_day_end exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_time_hour_end`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L480-L495) — test_next_run_time_hour_end exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_next_run_time_minute_end`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L497-L517) — test_next_run_time_minute_end exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_repr_functools_partial_job_func`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L609-L617) — test_repr_functools_partial_job_func exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_run_all`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L519-L525) — test_run_all exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_run_all_with_decorator`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L527-L543) — test_run_all_with_decorator exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_run_all_with_decorator_args`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L545-L553) — test_run_all_with_decorator_args exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_run_all_with_decorator_defaultargs`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L555-L563) — test_run_all_with_decorator_defaultargs exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_run_every_n_days_at_specific_time`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L695-L720) — test_run_every_n_days_at_specific_time exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_run_every_weekday_at_specific_time_past_today`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L680-L693) — test_run_every_weekday_at_specific_time_past_today exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_run_every_weekday_at_specific_time_today`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L669-L678) — test_run_every_weekday_at_specific_time_today exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_run_pending`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L629-L667) — test_run_pending exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_singular_time_units_match_plural_units`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L207-L212) — test_singular_time_units_match_plural_units exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_tag_type_enforcement`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L779-L784) — test_tag_type_enforcement exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_time_range`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L214-L229) — test_time_range exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_time_range_repr`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L231-L237) — test_time_range_repr exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_time_units`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L73-L191) — test_time_units exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_to_repr`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L584-L603) — test_to_repr exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_to_string`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L571-L582) — test_to_string exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_to_string_functools_partial_job_func`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L619-L627) — test_to_string_functools_partial_job_func exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_to_string_lambda_job_func`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L605-L607) — test_to_string_lambda_job_func exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_until_time`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L283-L358) — test_until_time exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.
- [ ] [`test_schedule.py::SchedulerTests.test_weekday_at_todady`](https://github.com/dbader/schedule/blob/c883af0229143285cf38e1c7733aaf36656c8744/test_schedule.py#L360-L379) — test_weekday_at_todady exercises Job configuration/execution, representation or job-list filtering, without calling scheduler-level next_run/get_next_run/idle_seconds. Job.next_run is a separate stored timestamp; get_jobs is unchanged and does not call get_next_run.

#### unclassified (0)


## Selection exclusions

Purposive pilot chosen from source-change descriptions before analyzer execution, not a random or representative accuracy sample. Three small public libraries provide string/HTML processing, signed serialization, and scheduling. Two commits per repository vary bug fixes and API/default behavior. Take each selected commit against its exact first parent (including two merge commits); retain the entire supported Python tree. Exclude changes outside Python runtime behavior, duplicate merge copies, unsupported licenses, or snapshots exceeding existing limits. No analyzer result is a selection criterion.

- [pallets/markupsafe@4e111271b149](https://github.com/pallets/markupsafe/commit/4e111271b1494995708a9e878a10829b5e10c7ba): Dependency update; not a Python runtime behavior case.
- [pallets/markupsafe@b3b0f02baddd](https://github.com/pallets/markupsafe/commit/b3b0f02baddd025191b789f5a4b0ecd3896bbf98): Lint/format migration; excluded in favor of functional source changes, before examining analyzer output.
- [pallets/markupsafe@ff06d77e1ee8](https://github.com/pallets/markupsafe/commit/ff06d77e1ee8cfe62d9e289ccc5bf1f49e4a0873): Another striptags implementation change; the whitespace fix plus a separate API addition gives broader source-level variety in a two-case quota.
- [pallets/itsdangerous@b0410878b9e4](https://github.com/pallets/itsdangerous/commit/b0410878b9e46bd4c008eeac8cf4ed3d345e69b4): Build provenance workflow change, outside Python runtime scope.
- [pallets/itsdangerous@64cd581d83c0](https://github.com/pallets/itsdangerous/commit/64cd581d83c0770ec5683d312cedbed06395b9ed): Merge copy of the timestamp work; use the single-parent functional commit instead.
- [dbader/schedule@82a43db1b938](https://github.com/dbader/schedule/commit/82a43db1b938d8fdf60103bd41f329e06c8d3651): Release metadata; not a functional source-change case.
- [dbader/schedule@073dbc6e5f82](https://github.com/dbader/schedule/commit/073dbc6e5f8254d27c656f88a5062cca2cdfc4a2): Tests-only addition, outside the runtime-source-change selection rule.
- [dbader/schedule@2dcb5833cdf2](https://github.com/dbader/schedule/commit/2dcb5833cdf2b7d7a1bda90c19e2fb7e373e66df): Timezone work was considered; representation and tagged lookup were selected for distinct source mechanisms and a bounded manual label review. This is a purposive historical sample, not the newest-two-commits sample.
