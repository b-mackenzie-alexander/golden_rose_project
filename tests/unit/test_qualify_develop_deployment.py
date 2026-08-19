import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "scripts" / "qualify_develop_deployment.py"
EVIDENCE_TEMPLATE_PATH = ROOT / "deploy" / "gcp" / "evidence-template.md"
MANIFEST_PATH = ROOT / "infra" / "policy" / "predeployment-authority-manifest.json"
EXPECTED_IMAGE_DIGEST = "sha256:" + "a" * 64


class FakeResponse:
    def __init__(
        self, status_code: int, payload: dict[str, Any], headers: dict[str, str] | None = None
    ) -> None:
        self.status_code = status_code
        self.payload = payload
        self.headers = headers or {}


class FakeRequester:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.employer_id = "11111111-1111-4111-8111-111111111111"
        self.contact_id = "22222222-2222-4222-8222-222222222222"
        self.create_version = 1
        self.revision_version = 2

    def __call__(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> FakeResponse:
        self.calls.append({"method": method, "path": path, "headers": headers, "body": body})
        if path == "/health":
            return FakeResponse(200, {"status": "ok"})
        if path == "/readiness":
            return FakeResponse(
                200,
                {
                    "status": "ready",
                    "schema_revision": "0005_database_authority",
                    "deployment_target": "gcp-develop-private-synthetic",
                    "deployed_image_digest": EXPECTED_IMAGE_DIGEST,
                },
            )
        if path == "/api/staff/v1/employers" and method == "POST":
            assert body is not None
            if len([call for call in self.calls if call["path"] == path]) == 1:
                return FakeResponse(
                    201,
                    {
                        "employer_id": self.employer_id,
                        "employer_type": "business",
                        "display_name": body["display_name"],
                        "version": self.create_version,
                    },
                    {"Idempotency-Result-Version": "1"},
                )
            return FakeResponse(
                201,
                {
                    "employer_id": self.employer_id,
                    "employer_type": "business",
                    "display_name": body["display_name"],
                    "version": self.create_version,
                },
                {"Idempotency-Result-Version": "1", "Idempotency-Replayed": "true"},
            )
        if path == f"/api/staff/v1/employers/{self.employer_id}" and method == "GET":
            return FakeResponse(
                200,
                {
                    "employer_id": self.employer_id,
                    "employer_type": "business",
                    "display_name": "redacted-in-output-only",
                    "version": self.create_version,
                },
            )
        if path == "/api/staff/v1/employers/search":
            return FakeResponse(
                200,
                {
                    "items": [{"employer_id": self.employer_id, "version": self.create_version}],
                    "next_cursor": "cursor-should-not-leak",
                },
            )
        if path == f"/api/staff/v1/employers/{self.employer_id}/revisions":
            assert body is not None
            if len([call for call in self.calls if call["path"] == path]) == 1:
                return FakeResponse(
                    200,
                    {
                        "employer_id": self.employer_id,
                        "employer_type": "business",
                        "display_name": body["display_name"],
                        "version": self.revision_version,
                    },
                    {"Idempotency-Result-Version": "2"},
                )
            return FakeResponse(
                200,
                {
                    "employer_id": self.employer_id,
                    "employer_type": "business",
                    "display_name": body["display_name"],
                    "version": self.revision_version,
                },
                {"Idempotency-Result-Version": "2", "Idempotency-Replayed": "true"},
            )
        if path == f"/api/staff/v1/employers/{self.employer_id}/contacts" and method == "POST":
            assert body is not None
            return FakeResponse(
                201,
                {
                    "employer_contact_id": self.contact_id,
                    "employer_id": self.employer_id,
                    "full_name": body["full_name"],
                    "version": 1,
                },
                {"Idempotency-Result-Version": "1"},
            )
        if path == f"/api/staff/v1/employers/{self.employer_id}/contacts/query":
            return FakeResponse(
                200,
                {
                    "items": [
                        {"employer_contact_id": self.contact_id, "employer_id": self.employer_id}
                    ],
                    "next_cursor": None,
                },
            )
        if path == f"/api/staff/v1/employers/{self.employer_id}/contacts/{self.contact_id}":
            return FakeResponse(
                200,
                {
                    "employer_contact_id": self.contact_id,
                    "employer_id": self.employer_id,
                    "full_name": "redacted-in-output-only",
                    "version": 1,
                },
            )
        raise AssertionError(f"unexpected request {method} {path}")


def load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("qualify_develop_deployment", MODULE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_qualify_develop_deployment_script_exists_and_template_mentions_qualification() -> None:
    assert MODULE_PATH.exists()
    assert EVIDENCE_TEMPLATE_PATH.exists()
    template = EVIDENCE_TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "qualification" in template.lower()
    assert "cleanup" in template.lower()


def test_manifest_lists_qualification_script_entrypoint() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert "scripts/qualify_develop_deployment.py" in manifest["scripts"]["entrypoints"]


def test_qualify_develop_deployment_accepts_reviewed_private_synthetic_flow() -> None:
    module = load_module()
    requester = FakeRequester()

    result = module.qualify_develop_deployment(
        base_url="https://staff-tracer-abc123.a.run.app",
        expected_service_url="https://staff-tracer-abc123.a.run.app",
        access_token="top-secret-token",
        expected_schema_revision="0005_database_authority",
        expected_image_digest=EXPECTED_IMAGE_DIGEST,
        allow_synthetic_writes=True,
        requester=requester,
    )

    assert result["qualification_status"] == "passed"
    assert result["health_status"] == "ok"
    assert result["readiness_status"] == "ready"
    assert result["readiness_posture"]["deployment_target"] == "gcp-develop-private-synthetic"
    assert result["readiness_posture"]["deployed_image_digest"] == EXPECTED_IMAGE_DIGEST
    assert result["employer_flow"]["create"] == "fresh"
    assert result["employer_flow"]["replay"] == "confirmed"
    assert result["employer_flow"]["revision_replay"] == "confirmed"
    assert result["employer_contact_flow"]["query"] == "passed"
    assert (
        result["cleanup_disposition"]
        == "no delete semantics exercised; use teardown/rebuild runbook"
    )

    health_call = requester.calls[0]
    readiness_call = requester.calls[1]
    assert health_call["method"] == "GET"
    assert readiness_call["method"] == "GET"
    assert "Idempotency-Key" not in health_call["headers"]
    assert "Idempotency-Key" not in readiness_call["headers"]
    assert all(
        call["headers"]["Authorization"] == "Bearer top-secret-token" for call in requester.calls
    )


@pytest.mark.parametrize(
    "bad_url, expected_message",
    [
        ("http://staff-tracer-abc123.a.run.app", "https"),
        ("file:///tmp/not-allowed", "https"),
        ("ssh://staff-tracer-abc123.a.run.app", "https"),
        ("https://user:pass@staff-tracer-abc123.a.run.app", "userinfo"),
        ("https://evil.example.com", "approved private Cloud Run authority"),
        ("https://staff-tracer-abc123.a.run.app?token=leak", "query string"),
        ("https://staff-tracer-abc123.a.run.app/#frag", "fragment"),
        ("https://staff-tracer-abc123.a.run.app/path", "must not include a path"),
        ("https://staff-tracer-abc123.a.run.app:8443", "approved https authority"),
    ],
)
def test_qualify_develop_deployment_rejects_unapproved_base_urls(
    bad_url: str, expected_message: str
) -> None:
    module = load_module()

    with pytest.raises(ValueError, match=expected_message):
        module._validate_base_url(bad_url, "https://staff-tracer-abc123.a.run.app")


def test_qualify_develop_deployment_rejects_other_valid_cloud_run_service() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="reviewed service authority"):
        module._validate_base_url(
            "https://staff-tracer-other.a.run.app",
            "https://staff-tracer-abc123.a.run.app",
        )


def test_qualify_develop_deployment_fails_closed_on_non_private_auth_gap() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="private authenticated access token is required"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            access_token="",
            expected_schema_revision="0005_database_authority",
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=True,
            requester=FakeRequester(),
        )


def test_qualify_develop_deployment_requires_explicit_live_write_acknowledgement() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="live-write acknowledgement"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            access_token="top-secret-token",
            expected_schema_revision="0005_database_authority",
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=False,
            requester=FakeRequester(),
        )


def test_qualify_develop_deployment_fails_closed_on_readiness_posture_mismatch() -> None:
    module = load_module()

    def failing_requester(
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> FakeResponse:
        if path == "/health":
            return FakeResponse(200, {"status": "ok"})
        if path == "/readiness":
            return FakeResponse(
                200,
                {
                    "status": "ready",
                    "schema_revision": "0004_employer_contact_authority",
                    "deployment_target": "gcp-develop-private-synthetic",
                    "deployed_image_digest": EXPECTED_IMAGE_DIGEST,
                },
            )
        raise AssertionError("later requests must not run after readiness failure")

    with pytest.raises(ValueError, match="schema revision"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            access_token="top-secret-token",
            expected_schema_revision="0005_database_authority",
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=True,
            requester=failing_requester,
        )


def test_render_qualification_evidence_redacts_sensitive_values() -> None:
    module = load_module()
    evidence = module.render_qualification_evidence(
        {
            "qualification_status": "passed",
            "health_status": "ok",
            "readiness_status": "ready",
            "readiness_posture": {
                "deployment_target": "gcp-develop-private-synthetic",
                "schema_revision": "0005_database_authority",
                "deployed_image_digest": EXPECTED_IMAGE_DIGEST,
            },
            "employer_flow": {
                "create": "fresh",
                "replay": "confirmed",
                "read": "passed",
                "search": "passed",
                "revision": "fresh",
                "revision_replay": "confirmed",
            },
            "employer_contact_flow": {"create": "fresh", "query": "passed", "read": "passed"},
            "cleanup_disposition": "no delete semantics exercised; use teardown/rebuild runbook",
            "internal_debug": {
                "display_name": "Synthetic Qual Employer 7f06",
                "employer_id": "11111111-1111-4111-8111-111111111111",
                "contact_id": "22222222-2222-4222-8222-222222222222",
                "cursor": "cursor-should-not-leak",
                "token": "top-secret-token",
                "dsn": "postgresql+psycopg://user:pass@db/service",
            },
        }
    )

    assert "Synthetic Qual Employer" not in evidence
    assert "11111111-1111-4111-8111-111111111111" not in evidence
    assert "22222222-2222-4222-8222-222222222222" not in evidence
    assert "cursor-should-not-leak" not in evidence
    assert "top-secret-token" not in evidence
    assert "postgresql+psycopg" not in evidence
    assert "qualification_status: passed" in evidence


def test_parse_args_preserves_token_free_argv_surface() -> None:
    module = load_module()
    args = module._parse_args(
        [
            "--base-url",
            "https://staff-tracer-abc123.a.run.app",
            "--expected-service-url",
            "https://staff-tracer-abc123.a.run.app",
            "--expected-image-digest",
            EXPECTED_IMAGE_DIGEST,
            "--access-token-env",
            "QUAL_TOKEN",
        ]
    )

    assert not hasattr(args, "access_token")
    assert args.access_token_env == "QUAL_TOKEN"


def test_main_reads_token_from_environment_and_writes_bounded_evidence(tmp_path: Path) -> None:
    module = load_module()
    requester = FakeRequester()
    os.environ["QUAL_TOKEN"] = "top-secret-token"
    qualification_function_name = "qualify_develop_deployment"
    original = getattr(module, qualification_function_name)

    try:
        setattr(
            module,
            qualification_function_name,
            lambda **kwargs: original(
                requester=requester,
                **kwargs,
            ),
        )
        exit_code = module.main(
            [
                "--base-url",
                "https://staff-tracer-abc123.a.run.app",
                "--expected-service-url",
                "https://staff-tracer-abc123.a.run.app",
                "--expected-image-digest",
                EXPECTED_IMAGE_DIGEST,
                "--access-token-env",
                "QUAL_TOKEN",
                "--allow-synthetic-writes",
                "--artifact-root",
                str(tmp_path),
                "--evidence-name",
                "qualification-evidence.md",
            ]
        )
    finally:
        setattr(module, qualification_function_name, original)
        os.environ.pop("QUAL_TOKEN", None)

    assert exit_code == 0
    evidence_path = tmp_path / "qualification-evidence.md"
    assert evidence_path.exists()
    assert "top-secret-token" not in evidence_path.read_text(encoding="utf-8")


def test_atomic_write_text_rejects_renamed_parent_replaced_with_symlink(tmp_path: Path) -> None:
    module = load_module()
    destination = tmp_path / "qualification" / "evidence.md"
    destination.parent.mkdir(parents=True)
    escaped = tmp_path / "escaped"
    escaped.mkdir()
    displaced_parent = tmp_path / "displaced-qualification"

    def swap_parent_to_symlink() -> None:
        destination.parent.rename(displaced_parent)
        destination.parent.symlink_to(escaped, target_is_directory=True)

    with pytest.raises(module.QualificationError, match="reviewed directory"):
        module._atomic_write_text(
            destination, "new evidence", before_replace=swap_parent_to_symlink
        )

    assert not (escaped / "evidence.md").exists()
    assert not (displaced_parent / "evidence.md").exists()
