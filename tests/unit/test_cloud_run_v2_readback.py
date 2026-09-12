import importlib.util
import io
import json
import subprocess
from email.message import Message
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request

import pytest


def module() -> ModuleType:
    path = Path(__file__).parents[2] / "scripts/read_cloud_run_v2.py"
    spec = importlib.util.spec_from_file_location("cloud_run_v2", path)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def install(monkeypatch: pytest.MonkeyPatch, m: ModuleType, pages: list[Any]) -> list[Request]:
    calls: list[Request] = []

    def token(command: list[str], **kwargs: Any) -> SimpleNamespace:
        assert command == ["gcloud", "auth", "print-access-token"]
        return SimpleNamespace(returncode=0, stdout="private-token\n")

    def fetch(request: Request, timeout: int) -> io.BytesIO:
        calls.append(request)
        value = pages.pop(0)
        if isinstance(value, Exception):
            raise value
        return io.BytesIO(json.dumps(value).encode())

    monkeypatch.setattr(m.subprocess, "run", token)
    monkeypatch.setattr(m, "build_opener", lambda *args: SimpleNamespace(open=fetch))
    return calls


def test_reads_v2_get_with_token_only_in_header(monkeypatch):
    m = module()
    job: dict[str, Any] = {
        "name": "projects/example-project/locations/us-east4/jobs/run-migrations",
        "template": {"template": {"containers": []}},
    }
    calls = install(monkeypatch, m, [job])
    assert m.read_resource("example-project", "us-east4", "jobs", "run-migrations") == job
    assert calls[0].full_url == "https://run.googleapis.com/v2/" + job["name"]
    assert calls[0].headers["Authorization"] == "Bearer private-token"
    assert calls[0].method == "GET"


def test_lists_all_pages_and_rejects_pagination_cycles(monkeypatch):
    m = module()
    calls = install(
        monkeypatch,
        m,
        [{"jobs": [{"name": "first"}], "nextPageToken": "a&b"}, {"jobs": [{"name": "second"}]}],
    )
    assert m.read_resource("example-project", "us-east4", "jobs") == [
        {"name": "first"},
        {"name": "second"},
    ]
    assert "pageToken=a%26b" in calls[1].full_url
    install(monkeypatch, m, [{"nextPageToken": "repeat"}, {"nextPageToken": "repeat"}])
    with pytest.raises(m.ReadbackError, match="pagination"):
        m.read_resource("example-project", "us-east4", "jobs")


@pytest.mark.parametrize(
    ("status", "message"), [(404, "NOT_FOUND"), (403, "HTTP 403"), (500, "HTTP 500")]
)
def test_http_failures_are_distinct_and_do_not_reflect_payload(monkeypatch, status, message):
    m = module()
    install(
        monkeypatch,
        m,
        [
            HTTPError(
                "https://private.invalid",
                status,
                "secret-payload",
                Message(),
                io.BytesIO(b"private-token"),
            )
        ],
    )
    with pytest.raises(m.ReadbackError, match=message) as e:
        m.read_resource("example-project", "us-east4", "jobs", "run-migrations")
    assert "private" not in str(e.value) and "secret" not in str(e.value)


def test_rejects_path_injection_before_authentication(monkeypatch):
    m = module()
    monkeypatch.setattr(
        m.subprocess, "run", lambda *a, **kw: pytest.fail("authentication must not run")
    )
    with pytest.raises(m.ReadbackError):
        m.read_resource("example-project", "../other", "jobs", "run-migrations")


def test_rejects_v1_and_missing_v2_identity(monkeypatch):
    m = module()
    install(
        monkeypatch,
        m,
        [{"apiVersion": "run.googleapis.com/v1", "metadata": {"name": "run-migrations"}}],
    )
    with pytest.raises(m.ReadbackError, match="v2"):
        m.read_resource("example-project", "us-east4", "jobs", "run-migrations")


def test_token_failure_and_redirect_never_expose_or_forward_credentials(monkeypatch):
    m = module()
    monkeypatch.setattr(
        m.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=1, stdout="private-token")
    )
    with pytest.raises(m.ReadbackError, match="authentication"):
        m.read_resource("example-project", "us-east4", "jobs")
    assert (
        m.NoRedirect().redirect_request(
            None, None, 302, "redirect", {}, "https://untrusted.invalid"
        )
        is None
    )


@pytest.mark.parametrize(
    "defect", [None, "condition", "generation", "revision", "image", "containers"]
)
def test_actual_service_workflow_accepts_current_v2_revision_only(tmp_path, defect):
    import os
    import sys

    import yaml  # type: ignore[import-untyped]

    root = Path(__file__).parents[2]
    workflow = yaml.safe_load((root / ".github/workflows/deploy-develop.yml").read_text())
    step = next(
        s
        for s in workflow["jobs"]["deploy"]["steps"]
        if s.get("name") == "Verify service readiness transition"
    )
    body = step["run"].split("python - <<'PY'\n", 1)[1].rsplit("\nPY", 1)[0]
    image = "example/image@sha256:" + "1" * 64
    service: dict[str, Any] = {
        "terminalCondition": {"state": "CONDITION_SUCCEEDED"},
        "generation": "2",
        "observedGeneration": "2",
        "latestReadyRevision": "rev2",
        "latestCreatedRevision": "rev2",
        "template": {"containers": [{"image": image}]},
    }
    if defect == "condition":
        service["terminalCondition"]["state"] = "CONDITION_FAILED"
    if defect == "generation":
        service["observedGeneration"] = "1"
    if defect == "revision":
        service["latestReadyRevision"] = "rev1"
    if defect == "image":
        service["template"]["containers"][0]["image"] = "different"
    if defect == "containers":
        service["template"]["containers"].append({"image": image})
    (tmp_path / "build").mkdir()
    (tmp_path / "build/deploy-result.json").write_text("{}")
    result = subprocess.run(
        [sys.executable, "-"],
        input=body,
        cwd=tmp_path,
        env=os.environ
        | {
            "SERVICE_JSON": json.dumps(service),
            "MANAGED_IMAGE": image,
            "IMAGE_DIGEST": "sha256:" + "1" * 64,
        },
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0 if defect is None else result.returncode != 0
