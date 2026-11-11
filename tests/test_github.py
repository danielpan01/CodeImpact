import asyncio
import base64
import copy
import hashlib
from collections import Counter
from itertools import pairwise

import httpx
import pytest
from fastapi.testclient import TestClient

from codeimpact.analyzer import analyze
from codeimpact.api import app, github_reader
from codeimpact.github import GitHubReader
from codeimpact.models import AnalysisRequest, Snapshot

URL = "https://github.com/acme/widget/pull/7"
BASE, HEAD, MERGE, OLD_TREE, NEW_TREE = (letter * 40 for letter in "bcade")
BASE_FILES = {
    "core.py": "def price(): return 10\n",
    "cart.py": "from core import price\ndef checkout(): return price()\n",
    "test_cart.py": "from cart import checkout\ndef test_cart(): assert checkout() == 10\n",
    "health.py": "def health(): return True\n",
    "test_health.py": "from health import health\ndef test_health(): assert health()\n",
}


def oid(raw):
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw, usedforsecurity=False).hexdigest()


class FakeGitHub:
    def __init__(self, before=None, after=None, fork=False):
        self.before = BASE_FILES.copy() if before is None else before
        self.after = (
            self.before | {"core.py": "def price(): return 20\n"} if after is None else after
        )
        self.repo = "acme/widget"
        self.head_repo = "contributor/widget-fork" if fork else self.repo
        self.calls = []
        self.overrides = {}
        self.routes = {}
        self.metadata = {
            "number": 7,
            "title": "Adjust price",
            "base": {"sha": BASE, "repo": {"full_name": self.repo, "private": False}},
            "head": {"sha": HEAD, "repo": {"full_name": self.head_repo, "private": False}},
        }
        self.routes[f"/repos/{self.repo}/pulls/7"] = self.metadata
        self.compare_path = (
            f"/repos/{self.repo}/compare/{BASE}...{self.head_repo.split('/')[0]}:{HEAD}"
        )
        # A paginated comparison's changed-file/commit arrays are NOT the snapshot input.
        self.routes[self.compare_path] = {
            "base_commit": {"sha": BASE},
            "merge_base_commit": {"sha": MERGE},
            "total_commits": 99,
            "commits": [],
            "files": [],
        }
        for repo, sha, tree_sha, files in [
            (self.repo, MERGE, OLD_TREE, self.before),
            (self.head_repo, HEAD, NEW_TREE, self.after),
        ]:
            self.routes[f"/repos/{repo}/git/commits/{sha}"] = {
                "sha": sha,
                "tree": {"sha": tree_sha},
            }
            entries = []
            for path, source in files.items():
                raw = source.encode() if isinstance(source, str) else source
                sha_blob = oid(raw)
                entries.append(
                    {
                        "path": path,
                        "sha": sha_blob,
                        "size": len(raw),
                        "mode": "100644",
                        "type": "blob",
                    }
                )
                self.routes[f"/repos/{repo}/git/blobs/{sha_blob}"] = {
                    "sha": sha_blob,
                    "size": len(raw),
                    "encoding": "base64",
                    "content": base64.b64encode(raw).decode(),
                }
            self.routes[f"/repos/{repo}/git/trees/{tree_sha}"] = {
                "sha": tree_sha,
                "truncated": False,
                "tree": entries,
            }

    def __call__(self, request):
        assert request.url.scheme == "https" and request.url.host == "api.github.com"
        assert request.method == "GET"
        self.calls.append(request)
        path = request.url.path
        if path in self.overrides:
            value = self.overrides[path]
            if isinstance(value, Exception):
                raise value
            return value
        assert path in self.routes, f"Unexpected GitHub request: {path}"
        response = httpx.Response(200, json=copy.deepcopy(self.routes[path]))
        if path.endswith("/pulls/7"):
            # Branch moves immediately after metadata retrieval; the pinned HEAD must win.
            self.metadata["head"]["sha"] = "f" * 40
        return response


@pytest.fixture
def serve():
    def make_client(server):
        async def reader():
            async with httpx.AsyncClient(transport=httpx.MockTransport(server)) as client:
                yield GitHubReader(client)

        app.dependency_overrides[github_reader] = reader
        return TestClient(app)

    yield make_client
    app.dependency_overrides.clear()


def assert_paths(report):
    edges = {(e["source"], e["target"]) for e in report["edges"]}
    for item in report["recommendations"]:
        assert item["evidence_path"][0] == item["symbol"]
        assert item["evidence_path"][-1] in report["changed"]
        assert all(edge in edges for edge in pairwise(item["evidence_path"]))
        assert item["symbol"] not in report["removed"]


@pytest.mark.parametrize("fork", [False, True])
def test_real_route_uses_complete_pinned_snapshots_and_matches_local_analysis(serve, fork):
    server = FakeGitHub(fork=fork)
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 200, response.text
    body = response.json()
    local = analyze(
        AnalysisRequest(
            base=Snapshot(files=server.before),
            head=Snapshot(files=server.after),
            label=body["label"],
        )
    )
    assert {k: v for k, v in body.items() if k not in {"stats", "source"}} == local.model_dump(
        exclude={"stats"}
    )
    assert body["source"] == {
        "kind": "github_pr",
        "repository": "acme/widget",
        "head_repository": server.head_repo,
        "pr_number": 7,
        "pr_url": URL,
        "title": "Adjust price",
        "base_sha": BASE,
        "head_sha": HEAD,
        "merge_base_sha": MERGE,
        "analyzer_version": "0.1.0",
    }
    assert [r["symbol"] for r in body["recommendations"]] == ["test_cart.py::test_cart"]
    assert body["recommendations"][0]["reason"] == "Resolved call path"
    assert "test_health.py::test_health" not in body["impacted"]
    assert_paths(body)
    paths = [r.url.path for r in server.calls]
    assert paths.count("/repos/acme/widget/pulls/7") == 1
    assert all("f" * 40 not in path for path in paths)
    assert f"/repos/acme/widget/git/commits/{BASE}" not in paths
    compare = next(r for r in server.calls if "/compare/" in r.url.path)
    assert compare.url.params["per_page"] == "1"
    blobs = [r.url.path.rsplit("/", 1)[-1] for r in server.calls if "/blobs/" in r.url.path]
    assert max(Counter(blobs).values()) == 1


def test_deleted_function_and_test_keep_old_edges_but_exclude_removed_tests(serve):
    before = BASE_FILES | {
        "test_removed.py": "from core import price\ndef test_removed(): return price()\n"
    }
    server = FakeGitHub(before, BASE_FILES | {"core.py": ""})
    body = serve(server).post("/api/github/pr", json={"url": URL}).json()
    assert "core.py::price" in body["removed"]
    assert "test_removed.py::test_removed" in body["removed"]
    assert [r["symbol"] for r in body["recommendations"]] == ["test_cart.py::test_cart"]
    assert body["recommendations"][0]["evidence_path"][-1] == "core.py::price"
    assert_paths(body)


def test_empty_module_comment_change_stays_semantically_unchanged(serve):
    files = {"a.py": "", "test_a.py": "import a\ndef test_a(): assert a is not None\n"}
    body = (
        serve(FakeGitHub(files, files | {"a.py": "# only comments\n\n"}))
        .post("/api/github/pr", json={"url": URL})
        .json()
    )
    assert body["changed"] == [] and body["recommendations"] == []


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/acme/widget/pull/7",
        "https://evil.example/acme/widget/pull/7",
        "https://github.com.evil.example/acme/widget/pull/7",
        "https://user:secret@github.com/acme/widget/pull/7",
        "https://github.com:443/acme/widget/pull/7",
        "https://github.com/acme/widget/issues/7",
        URL + "?token=secret",
        URL + "#diff",
        URL + "/files",
        URL + "/",
        URL + "\n",
        "https://github.com/acme/../pull/7",
        "https://github.com/acme/%2e%2e/pull/7",
        "https://github.com/acme/widget/pull/0",
        "file:///etc/passwd",
    ],
)
def test_invalid_url_never_contacts_github(serve, url):
    server = FakeGitHub()
    response = serve(server).post("/api/github/pr", json={"url": url})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_url"
    assert server.calls == []


@pytest.mark.parametrize("payload", [{}, {"url": URL, "token": "secret"}, {"url": "x" * 301}])
def test_invalid_request_has_safe_friendly_error(serve, payload):
    server = FakeGitHub()
    response = serve(server).post("/api/github/pr", json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_request"
    assert "secret" not in response.text and not server.calls


@pytest.mark.parametrize("which", ["base", "head"])
def test_private_repository_is_refused_even_with_access(serve, which):
    server = FakeGitHub(fork=True)
    server.metadata[which]["repo"]["private"] = True
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "private_repository"
    assert len(server.calls) == 1


@pytest.mark.parametrize(
    "status,headers,code,expected",
    [
        (404, {}, "not_found", 404),
        (401, {}, "github_auth", 503),
        (403, {"x-ratelimit-remaining": "0"}, "rate_limited", 429),
        (403, {"retry-after": "30"}, "rate_limited", 429),
        (429, {}, "rate_limited", 429),
        (403, {}, "github_forbidden", 503),
        (500, {}, "github_unavailable", 502),
        (302, {"location": "https://evil.example/steal"}, "redirect", 422),
    ],
)
def test_github_errors_are_actionable_and_never_leak_upstream_body(
    serve, status, headers, code, expected
):
    server = FakeGitHub()
    server.overrides["/repos/acme/widget/pulls/7"] = httpx.Response(
        status, headers=headers, text="secret-upstream-body"
    )
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == expected
    assert response.json()["detail"]["code"] == code
    assert "secret" not in response.text and len(server.calls) == 1


@pytest.mark.parametrize(
    "failure,code,status",
    [
        (httpx.ReadTimeout("secret"), "timeout", 504),
        (httpx.ConnectError("secret"), "network", 502),
    ],
)
def test_network_errors_are_recoverable(serve, failure, code, status):
    server = FakeGitHub()
    server.overrides["/repos/acme/widget/pulls/7"] = failure
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == status
    assert response.json()["detail"]["code"] == code
    assert response.json()["detail"]["retryable"] is True
    assert "secret" not in response.text


def test_truncated_tree_fails_without_partial_report(serve):
    server = FakeGitHub()
    server.routes[f"/repos/acme/widget/git/trees/{OLD_TREE}"]["truncated"] = True
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "incomplete_tree"
    assert not any("/blobs/" in r.url.path for r in server.calls)


@pytest.mark.parametrize(
    "files",
    [
        {"huge.py": "#" * 200_001},
        {f"a{i}.py": "#" * 100_001 for i in range(20)},
        {f"a{i}.py": "" for i in range(301)},
    ],
)
def test_snapshot_limits_checked_before_fetching_blobs(serve, files):
    server = FakeGitHub(files, files)
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "too_large"
    assert not any("/blobs/" in r.url.path for r in server.calls)


def test_skipped_inputs_are_explained_and_not_fetched(serve):
    server = FakeGitHub()
    entries = server.routes[f"/repos/acme/widget/git/trees/{OLD_TREE}"]["tree"]
    for path, mode, kind in [
        ("link.py", "120000", "blob"),
        ("external", "160000", "commit"),
        ("vendor/lib.py", "100644", "blob"),
    ]:
        entries.append({"path": path, "sha": "f" * 40, "size": 12, "mode": mode, "type": kind})
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 200
    warnings = response.json()["warnings"]
    for kind in ["symlinks", "submodules", "excluded Python files"]:
        assert any(kind in w for w in warnings)
    assert not any("f" * 40 in r.url.path for r in server.calls)


def test_non_utf8_and_corrupt_blob_fail_explicitly(serve):
    server = FakeGitHub({"a.py": b"\xff"}, {})
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unsupported_encoding"
    server = FakeGitHub()
    blob = next(value for key, value in server.routes.items() if "/blobs/" in key)
    blob["content"] = base64.b64encode(b"different bytes").decode()
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "invalid_response"


@pytest.mark.parametrize(
    "budget,value", [("MAX_RESPONSE_BYTES", 1), ("MAX_NETWORK_BYTES", 1), ("MAX_REQUESTS", 1)]
)
def test_download_budgets_fail_closed(serve, monkeypatch, budget, value):
    # Response size uses the call's bound default; network and request limits are runtime constants.
    import codeimpact.github as github

    if budget == "MAX_RESPONSE_BYTES":
        server = FakeGitHub()
        server.overrides["/repos/acme/widget/pulls/7"] = httpx.Response(
            200, content=b"x" * (github.MAX_RESPONSE_BYTES + 1)
        )
    else:
        monkeypatch.setattr(github, budget, value)
        server = FakeGitHub()
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "too_large"


def test_whole_import_deadline(serve, monkeypatch):
    monkeypatch.setattr("codeimpact.github.MAX_SECONDS", 0.01)

    async def slow(request):
        await asyncio.sleep(0.1)
        return httpx.Response(200, json={})

    response = serve(slow).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 504
    assert response.json()["detail"]["code"] == "timeout"


def test_fetched_source_is_never_executed(serve, tmp_path):
    sentinel = tmp_path / "never-created"
    files = {
        "danger.py": f"from pathlib import Path\nPath({str(sentinel)!r}).write_text('executed')"
    }
    response = serve(FakeGitHub({}, files)).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 200
    assert not sentinel.exists()


@pytest.mark.parametrize("field", ["base", "head"])
def test_deleted_repository_metadata_is_explicit(serve, field):
    server = FakeGitHub()
    server.metadata[field]["repo"] = None
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "unavailable_repository"
    assert len(server.calls) == 1


@pytest.mark.parametrize("mismatch", ["repository", "number", "base", "commit", "tree"])
def test_inconsistent_provider_identity_fails_closed(serve, mismatch):
    server = FakeGitHub()
    if mismatch == "repository":
        server.metadata["base"]["repo"]["full_name"] = "different/repo"
    elif mismatch == "number":
        server.metadata["number"] = 8
    elif mismatch == "base":
        server.routes[server.compare_path]["base_commit"]["sha"] = "f" * 40
    elif mismatch == "commit":
        server.routes[f"/repos/acme/widget/git/commits/{MERGE}"]["sha"] = "f" * 40
    else:
        server.routes[f"/repos/acme/widget/git/trees/{OLD_TREE}"]["sha"] = "f" * 40
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code in {422, 502}
    assert "nodes" not in response.json()
    assert not any("/blobs/" in r.url.path for r in server.calls)


@pytest.mark.parametrize("path", ["../unsafe.py", "/unsafe.py", "a//b.py", "core.py"])
def test_unsafe_or_duplicate_tree_paths_rejected(serve, path):
    server = FakeGitHub()
    entries = server.routes[f"/repos/acme/widget/git/trees/{OLD_TREE}"]["tree"]
    entries.append(entries[0] | {"path": path})
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_path"
    assert not any("/blobs/" in r.url.path for r in server.calls)


def test_large_non_python_tree_is_bounded(serve, monkeypatch):
    monkeypatch.setattr("codeimpact.github.MAX_TREE_ENTRIES", 2)
    server = FakeGitHub()
    response = serve(server).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "too_large"
    assert not any("/blobs/" in r.url.path for r in server.calls)


def test_no_python_files_produces_visible_scope_warning(serve):
    response = serve(FakeGitHub({}, {})).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 200
    assert response.json()["nodes"] == []
    assert any("No Python files" in w for w in response.json()["warnings"])


def test_rename_is_removal_and_addition(serve):
    before = {"old.py": "def f(): return 1\n", "test_f.py": "import old\ndef test_f(): old.f()\n"}
    after = {"new.py": before["old.py"], "test_f.py": before["test_f.py"].replace("old", "new")}
    response = serve(FakeGitHub(before, after)).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 200
    body = response.json()
    assert "old.py::f" in body["removed"] and "new.py::f" in body["changed"]
    assert body["recommendations"]
    assert_paths(body)


@pytest.mark.parametrize("fail", [False, True])
def test_blob_download_concurrency_and_failure_cleanup(fail):
    files = {f"a{i}.py": f"value = {i}\n" for i in range(12)}
    server = FakeGitHub(files, files)
    active = peak = cancelled = 0

    async def transport(request):
        nonlocal active, peak, cancelled
        if "/blobs/" not in request.url.path:
            return server(request)
        active += 1
        peak = max(peak, active)
        try:
            if fail and request.url.path.endswith(oid(files["a0.py"].encode())):
                await asyncio.sleep(0.01)
                return httpx.Response(503)
            await asyncio.sleep(0.1 if fail else 0.01)
            return server(request)
        except asyncio.CancelledError:
            cancelled += 1
            raise
        finally:
            active -= 1

    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as client:
            reader = GitHubReader(client)
            if fail:
                from codeimpact.github import GitHubError

                with pytest.raises(GitHubError, match="Try again later"):
                    await reader.read(URL)
            else:
                imported = await reader.read(URL)
                assert imported.request.base.files == files
                assert imported.request.head.files == files
            # Check before closing the event loop, so its shutdown cannot mask leaked tasks.
            assert active == 0
            assert not [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    asyncio.run(run())
    assert peak == 4
    assert bool(cancelled) is fail


@pytest.mark.parametrize("token", [None, "server-only-test-secret"])
def test_optional_token_is_server_only(monkeypatch, caplog, token):
    server = FakeGitHub()
    original_client = httpx.AsyncClient
    if token:
        monkeypatch.setenv("CODEIMPACT_GITHUB_TOKEN", token)
    else:
        monkeypatch.delenv("CODEIMPACT_GITHUB_TOKEN", raising=False)

    def mock_client(**kwargs):
        return original_client(transport=httpx.MockTransport(server), **kwargs)

    monkeypatch.setattr("codeimpact.api.httpx.AsyncClient", mock_client)
    response = TestClient(app).post("/api/github/pr", json={"url": URL})
    assert response.status_code == 200
    for request in server.calls:
        assert request.headers.get("authorization") == (f"Bearer {token}" if token else None)
    assert "server-only-test-secret" not in response.text + caplog.text
