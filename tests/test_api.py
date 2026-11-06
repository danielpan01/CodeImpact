import pytest
from fastapi.testclient import TestClient

from codeimpact.api import app
from codeimpact.demo import demo_request

client = TestClient(app)


def test_health_and_demo_schema():
    assert client.get("/health").json()["status"] == "ok"
    response = client.get("/api/demo")
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert len(body["recommendations"]) == 3
    assert "fingerprint" not in body["nodes"][0]


def test_snapshot_round_trip():
    request = client.get("/api/demo/snapshots").json()
    response = client.post("/api/analyze", json=request)
    assert response.status_code == 200
    assert response.json()["changed"] == ["shop/pricing.py::<module>", "shop/pricing.py::discount"]


@pytest.mark.parametrize(
    "path", ["../a.py", "/a.py", "a.txt", "a\\b.py", "a/../b.py", "./a.py", "C:/a.py"]
)
def test_unsafe_paths_rejected(path):
    payload = demo_request().model_dump()
    payload["head"]["files"] = {path: ""}
    assert client.post("/api/analyze", json=payload).status_code == 422


def test_limits_and_unknown_fields():
    payload = demo_request().model_dump()
    payload["head"]["files"] = {"a.py": "x" * 200_001}
    assert client.post("/api/analyze", json=payload).status_code == 422
    assert client.post("/api/analyze", json={"bogus": True}).status_code == 422
    assert client.post("/api/analyze", content=b"x" * 6_000_001).status_code == 413


def test_duplicate_module_error_is_user_facing():
    payload = {"base": {"files": {}}, "head": {"files": {"a.py": "", "src/a.py": ""}}}
    assert client.post("/api/analyze", json=payload).status_code == 422
