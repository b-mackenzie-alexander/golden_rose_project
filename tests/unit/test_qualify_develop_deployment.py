import base64
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).parents[2]
MODULE_PATH = ROOT / "scripts" / "qualify_develop_deployment.py"
EVIDENCE_TEMPLATE_PATH = ROOT / "deploy" / "gcp" / "evidence-template.md"
MANIFEST_PATH = ROOT / "infra" / "policy" / "predeployment-authority-manifest.json"
EXPECTED_IMAGE_DIGEST = "sha256:" + "a" * 64
DEMO_PASSWORD = "top-secret-token"
SAFE_LOG_EXPORT = '[{"severity":"INFO","message":"request completed"}]'
DEMO_AUTHORIZATION = "Basic " + base64.b64encode(
    f"golden-rose-demo:{DEMO_PASSWORD}".encode()
).decode("ascii")
WRONG_DEMO_AUTHORIZATION = "Basic " + base64.b64encode(
    b"golden-rose-demo:intentionally-wrong-demo-password"
).decode("ascii")
DEMO_CHALLENGE = 'Basic realm="Golden Rose synthetic develop", charset="UTF-8"'


class FakeResponse:
    def __init__(
        self, status_code: int, payload: dict[str, Any], headers: dict[str, str] | None = None
    ) -> None:
        self.status_code = status_code
        self.payload = payload
        self.headers = {"Cache-Control": "no-store"}
        if headers:
            self.headers.update(headers)


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
            return FakeResponse(200, {"status": "ready"})
        if path == "/api/staff/v1/environment":
            if headers.get("Authorization") == DEMO_AUTHORIZATION:
                return FakeResponse(
                    200,
                    {
                        "environment": "develop",
                        "label": "Non-production fictional synthetic develop",
                        "data_boundary": "fictional-synthetic-only",
                    },
                )
            return FakeResponse(401, {}, {"WWW-Authenticate": DEMO_CHALLENGE})
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
        if (
            path.startswith("/api/staff/v1/employers/")
            and "/contacts/" not in path
            and method == "GET"
        ):
            if path != f"/api/staff/v1/employers/{self.employer_id}":
                return FakeResponse(404, {"status": "not_found"})
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
            if body and "cursor" in body:
                return FakeResponse(422, {"status": "invalid"})
            return FakeResponse(
                200,
                {
                    "items": [{"employer_id": self.employer_id, "version": self.create_version}],
                    "next_cursor": "cursor-should-not-leak",
                },
            )
        if path == f"/api/staff/v1/employers/{self.employer_id}/revisions":
            assert body is not None
            revision_calls = [call for call in self.calls if call["path"] == path]
            if len(revision_calls) == 1:
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
            if len(revision_calls) == 2:
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
            if len(revision_calls) == 3:
                return FakeResponse(412, {"status": "stale"})
            return FakeResponse(409, {"status": "conflict"})
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
            if body and "cursor" in body:
                return FakeResponse(422, {"status": "invalid"})
            return FakeResponse(
                200,
                {
                    "items": [
                        {"employer_contact_id": self.contact_id, "employer_id": self.employer_id}
                    ],
                    "next_cursor": None,
                },
            )
        if path.startswith(f"/api/staff/v1/employers/{self.employer_id}/contacts/"):
            if path != f"/api/staff/v1/employers/{self.employer_id}/contacts/{self.contact_id}":
                return FakeResponse(404, {"status": "not_found"})
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


@pytest.mark.parametrize(
    "log_export",
    [
        'authorization: "Basic redacted"',
        f"credential={DEMO_PASSWORD}",
        'request body contained "Generated Employer"',
    ],
)
def test_log_export_scan_rejects_authorization_credentials_and_fictional_values(
    log_export: str,
) -> None:
    module = load_module()

    with pytest.raises(module.QualificationError, match="log export contains prohibited values"):
        module._verify_log_export_is_safe(
            log_export,
            prohibited_values=[DEMO_PASSWORD, "Generated Employer"],
        )


def test_private_file_reader_rejects_permissive_or_symlinked_handoffs(
    tmp_path: Path,
) -> None:
    module = load_module()
    permissive = tmp_path / "permissive.txt"
    permissive.write_text("private", encoding="utf-8")
    permissive.chmod(0o644)
    linked = tmp_path / "linked.txt"
    linked.symlink_to(permissive)

    with pytest.raises(module.QualificationError, match="private file boundary failed"):
        module._read_private_text_file(permissive, label="log export")
    with pytest.raises(module.QualificationError, match="private file boundary failed"):
        module._read_private_text_file(linked, label="demo password")


def test_cloud_log_reader_runs_exact_post_qualification_bounded_query() -> None:
    module = load_module()
    calls: list[dict[str, Any]] = []

    def runner(command: list[str], **kwargs: Any) -> Any:
        calls.append({"command": command, "kwargs": kwargs})
        return SimpleNamespace(returncode=0, stdout=SAFE_LOG_EXPORT, stderr="")

    result = module._collect_cloud_run_logs(
        "golden-rose-develop-123",
        runner=runner,
    )

    assert result == SAFE_LOG_EXPORT
    assert calls == [
        {
            "command": [
                "gcloud",
                "logging",
                "read",
                (
                    'resource.type="cloud_run_revision" '
                    'AND resource.labels.service_name="staff-tracer"'
                ),
                "--project=golden-rose-develop-123",
                "--freshness=15m",
                "--limit=1000",
                "--format=json",
            ],
            "kwargs": {
                "capture_output": True,
                "check": False,
                "text": True,
                "timeout": 120,
            },
        }
    ]


def test_qualification_uses_public_probes_then_fixed_basic_denials_and_private_password() -> None:
    module = load_module()
    calls: list[dict[str, Any]] = []
    correct_authorization = "Basic " + base64.b64encode(
        b"golden-rose-demo:private-demo-password"
    ).decode("ascii")

    def requester(
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> FakeResponse:
        calls.append({"method": method, "path": path, "headers": headers, "body": body})
        if path == "/health":
            return FakeResponse(200, {"status": "ok"})
        if path == "/readiness":
            return FakeResponse(200, {"status": "ready"})
        if path == "/api/staff/v1/environment":
            if headers.get("Authorization") == correct_authorization:
                return FakeResponse(
                    200,
                    {
                        "environment": "develop",
                        "label": "Non-production fictional synthetic develop",
                        "data_boundary": "fictional-synthetic-only",
                    },
                )
            return FakeResponse(
                401,
                {},
                {
                    "WWW-Authenticate": (
                        'Basic realm="Golden Rose synthetic develop", charset="UTF-8"'
                    )
                },
            )
        raise module.QualificationError("explicit live-write acknowledgement is required")

    with pytest.raises(module.QualificationError, match="live-write acknowledgement"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            demo_password="private-demo-password",
            log_export_reader=lambda: SAFE_LOG_EXPORT,
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=False,
            requester=requester,
        )

    assert [call["path"] for call in calls] == [
        "/health",
        "/readiness",
        "/api/staff/v1/environment",
        "/api/staff/v1/environment",
        "/api/staff/v1/environment",
    ]
    assert "Authorization" not in calls[0]["headers"]
    assert "Authorization" not in calls[1]["headers"]
    assert "Authorization" not in calls[2]["headers"]
    assert calls[3]["headers"]["Authorization"].startswith("Basic ")
    assert calls[3]["headers"]["Authorization"] != correct_authorization
    assert calls[4]["headers"]["Authorization"] == correct_authorization


def test_qualify_develop_deployment_accepts_reviewed_private_synthetic_flow() -> None:
    module = load_module()
    requester = FakeRequester()
    log_reader_call_counts: list[int] = []

    def log_export_reader() -> str:
        log_reader_call_counts.append(len(requester.calls))
        return SAFE_LOG_EXPORT

    result = module.qualify_develop_deployment(
        base_url="https://staff-tracer-abc123.a.run.app",
        expected_service_url="https://staff-tracer-abc123.a.run.app",
        demo_password=DEMO_PASSWORD,
        log_export_reader=log_export_reader,
        expected_image_digest=EXPECTED_IMAGE_DIGEST,
        allow_synthetic_writes=True,
        requester=requester,
    )

    assert result["qualification_status"] == "passed"
    assert result["health_status"] == "ok"
    assert result["readiness_status"] == "ready"
    assert result["log_scan"] == "passed_no_prohibited_values"
    assert log_reader_call_counts == [len(requester.calls)]
    assert log_reader_call_counts[0] > 6
    assert result["platform_posture"]["immutable_image"] == (
        "verified_by_prior_foundation_readback"
    )
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
    assert health_call["headers"] == {"Accept": "application/json"}
    assert readiness_call["headers"] == {"Accept": "application/json"}
    assert "Idempotency-Key" not in health_call["headers"]
    assert "Idempotency-Key" not in readiness_call["headers"]
    assert "Authorization" not in requester.calls[2]["headers"]
    assert requester.calls[3]["headers"]["Authorization"] == WRONG_DEMO_AUTHORIZATION
    assert all(
        call["headers"]["Authorization"] == DEMO_AUTHORIZATION for call in requester.calls[4:]
    )


@pytest.mark.parametrize("call_index", [7, 9, 12, 13, 16, 17, 19])
def test_safe_live_error_probes_fail_closed_without_no_store(call_index: int) -> None:
    module = load_module()
    requester = FakeRequester()

    def missing_no_store_requester(
        method: str, path: str, headers: dict[str, str], body: dict[str, Any] | None
    ) -> FakeResponse:
        response = requester(method, path, headers, body)
        if len(requester.calls) == call_index:
            response.headers = {}
        return response

    with pytest.raises(ValueError, match="boundary failed"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            demo_password=DEMO_PASSWORD,
            log_export_reader=lambda: SAFE_LOG_EXPORT,
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=True,
            requester=missing_no_store_requester,
        )


def test_qualify_develop_deployment_result_marks_unperformed_manual_evidence_not_run() -> None:
    module = load_module()

    result = module.qualify_develop_deployment(
        base_url="https://staff-tracer-abc123.a.run.app",
        expected_service_url="https://staff-tracer-abc123.a.run.app",
        demo_password=DEMO_PASSWORD,
        log_export_reader=lambda: SAFE_LOG_EXPORT,
        expected_image_digest=EXPECTED_IMAGE_DIGEST,
        allow_synthetic_writes=True,
        requester=FakeRequester(),
    )

    assert result["automated_qualification"] == {
        "status": "passed",
        "synthetic_writes": "explicitly_allowed",
    }
    assert result["manual_browser"] == {"status": "not_run"}
    assert result["accessibility"] == {
        "automated_axe": "not_evidenced",
        "manual_review": "not_run",
    }
    assert result["fluent_language"] == {
        "english": "not_evidenced",
        "spanish": "not_evidenced",
    }
    assert result["tester_access"] == {"status": "not_evidenced"}
    assert result["monitoring"] == {"status": "not_evidenced"}
    assert result["recovery"] == {"status": "not_evidenced"}
    assert result["feedback"]["status"] == "not_run"


def test_qualify_develop_deployment_result_includes_structured_feedback_triage_fields() -> None:
    module = load_module()

    result = module.qualify_develop_deployment(
        base_url="https://staff-tracer-abc123.a.run.app",
        expected_service_url="https://staff-tracer-abc123.a.run.app",
        demo_password=DEMO_PASSWORD,
        log_export_reader=lambda: SAFE_LOG_EXPORT,
        expected_image_digest=EXPECTED_IMAGE_DIGEST,
        allow_synthetic_writes=True,
        requester=FakeRequester(),
    )

    assert result["feedback"] == {
        "status": "not_run",
        "structured_artifact": "not_evidenced",
        "severity": "not_triaged",
        "workflow_blocking": "not_triaged",
        "accessibility_impact": "not_triaged",
        "privacy_impact": "not_triaged",
        "security_impact": "not_triaged",
        "language_impact": "not_triaged",
        "owner_disposition_retest": "not_triaged",
    }


def test_qualify_develop_deployment_rejects_cache_permissive_success_response() -> None:
    module = load_module()
    requester = FakeRequester()

    def cache_permissive_requester(
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> FakeResponse:
        response = requester(method, path, headers, body)
        response.headers.setdefault("cache-control", "no-store")
        if path == f"/api/staff/v1/employers/{requester.employer_id}" and method == "GET":
            response.headers = {"Cache-Control": "public, max-age=60"}
        return response

    with pytest.raises(ValueError, match="employer read cache-control"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            demo_password=DEMO_PASSWORD,
            log_export_reader=lambda: SAFE_LOG_EXPORT,
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=True,
            requester=cache_permissive_requester,
        )


def test_qualify_develop_deployment_rejects_success_response_missing_no_store() -> None:
    module = load_module()
    requester = FakeRequester()

    def missing_no_store_requester(
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> Any:
        if path == "/health":
            requester.calls.append(
                {"method": method, "path": path, "headers": headers, "body": body}
            )
            return 200, {}, {"status": "ok"}
        return requester(method, path, headers, body)

    with pytest.raises(ValueError, match="health cache-control"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            demo_password=DEMO_PASSWORD,
            log_export_reader=lambda: SAFE_LOG_EXPORT,
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=True,
            requester=missing_no_store_requester,
        )


def test_qualify_develop_deployment_records_no_store_evidence_matrix() -> None:
    module = load_module()

    result = module.qualify_develop_deployment(
        base_url="https://staff-tracer-abc123.a.run.app",
        expected_service_url="https://staff-tracer-abc123.a.run.app",
        demo_password=DEMO_PASSWORD,
        log_export_reader=lambda: SAFE_LOG_EXPORT,
        expected_image_digest=EXPECTED_IMAGE_DIGEST,
        allow_synthetic_writes=True,
        requester=FakeRequester(),
    )

    assert result["no_store_evidence"] == {
        "health": "passed",
        "readiness": "passed",
        "employer_create": "passed",
        "employer_create_replay": "passed",
        "employer_detail": "passed",
        "employer_detail_not_found": "passed",
        "employer_search": "passed",
        "employer_search_malformed_cursor": "passed",
        "employer_revision": "passed",
        "employer_revision_replay": "passed",
        "employer_revision_stale": "passed",
        "employer_revision_idempotency_conflict": "passed",
        "employer_contact_create": "passed",
        "employer_contact_query": "passed",
        "employer_contact_query_malformed_cursor": "passed",
        "employer_contact_query_overlength_cursor": "passed",
        "employer_contact_read": "passed",
        "employer_contact_read_not_found": "passed",
        "controlled_error_outcomes": {
            "employer_create_errors": "source_controlled_static_contract_not_live_run",
            "employer_detail_errors": "source_controlled_static_contract_plus_live_not_found",
            "employer_search_errors": (
                "source_controlled_static_contract_plus_live_cursor_validation"
            ),
            "employer_revision_errors": (
                "source_controlled_static_contract_plus_live_stale_and_idempotency_conflict"
            ),
            "employer_contact_create_errors": "source_controlled_static_contract_not_live_run",
            "employer_contact_query_errors": (
                "source_controlled_static_contract_plus_live_cursor_validation"
            ),
            "employer_contact_read_errors": "source_controlled_static_contract_plus_live_not_found",
            "live_error_qualification": "safe_rows_passed",
        },
    }


def test_qualify_develop_deployment_records_controlled_error_no_store_matrix() -> None:
    module = load_module()

    result = module.qualify_develop_deployment(
        base_url="https://staff-tracer-abc123.a.run.app",
        expected_service_url="https://staff-tracer-abc123.a.run.app",
        demo_password=DEMO_PASSWORD,
        log_export_reader=lambda: SAFE_LOG_EXPORT,
        expected_image_digest=EXPECTED_IMAGE_DIGEST,
        allow_synthetic_writes=True,
        requester=FakeRequester(),
    )

    assert result["no_store_evidence"]["controlled_error_outcomes"] == {
        "employer_create_errors": "source_controlled_static_contract_not_live_run",
        "employer_detail_errors": "source_controlled_static_contract_plus_live_not_found",
        "employer_search_errors": ("source_controlled_static_contract_plus_live_cursor_validation"),
        "employer_revision_errors": (
            "source_controlled_static_contract_plus_live_stale_and_idempotency_conflict"
        ),
        "employer_contact_create_errors": "source_controlled_static_contract_not_live_run",
        "employer_contact_query_errors": (
            "source_controlled_static_contract_plus_live_cursor_validation"
        ),
        "employer_contact_read_errors": "source_controlled_static_contract_plus_live_not_found",
        "live_error_qualification": "safe_rows_passed",
    }


@pytest.mark.parametrize(
    "bad_url, expected_message",
    [
        ("http://staff-tracer-abc123.a.run.app", "https"),
        ("file:///tmp/not-allowed", "https"),
        ("ssh://staff-tracer-abc123.a.run.app", "https"),
        ("https://user:pass@staff-tracer-abc123.a.run.app", "userinfo"),
        ("https://evil.example.com", "approved IAM-private Cloud Run authority"),
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


def test_qualify_develop_deployment_fails_closed_on_missing_demo_password() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="private demo password is required"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            demo_password="",
            log_export_reader=lambda: SAFE_LOG_EXPORT,
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=True,
            requester=FakeRequester(),
        )


def test_qualification_contract_requires_non_argv_demo_password_handoff() -> None:
    module = load_module()
    args = module._parse_args(
        [
            "--base-url",
            "https://staff-tracer-abc123.a.run.app",
            "--expected-service-url",
            "https://staff-tracer-abc123.a.run.app",
            "--expected-image-digest",
            EXPECTED_IMAGE_DIGEST,
            "--log-export-file",
            "/private/log-export.json",
            "--demo-password-stdin",
        ]
    )

    assert args.demo_password_stdin is True
    assert args.demo_password_env is None
    assert args.demo_password_file is None
    assert not hasattr(args, "demo_password")


def test_qualify_develop_deployment_requires_explicit_live_write_acknowledgement() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="live-write acknowledgement"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            demo_password=DEMO_PASSWORD,
            log_export_reader=lambda: SAFE_LOG_EXPORT,
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=False,
            requester=FakeRequester(),
        )


def test_qualify_develop_deployment_fails_closed_on_non_minimized_readiness() -> None:
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
                {"status": "ready", "schema_revision": "must-not-be-public"},
            )
        raise AssertionError("later requests must not run after readiness failure")

    with pytest.raises(ValueError, match="probe minimization"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            demo_password=DEMO_PASSWORD,
            log_export_reader=lambda: SAFE_LOG_EXPORT,
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
            "platform_posture": {
                "immutable_image": "verified_by_prior_foundation_readback",
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


def test_parse_args_preserves_password_free_argv_surface() -> None:
    module = load_module()
    args = module._parse_args(
        [
            "--base-url",
            "https://staff-tracer-abc123.a.run.app",
            "--expected-service-url",
            "https://staff-tracer-abc123.a.run.app",
            "--expected-image-digest",
            EXPECTED_IMAGE_DIGEST,
            "--demo-password-env",
            "QUAL_DEMO_PASSWORD",
            "--log-export-file",
            "/private/log-export.json",
        ]
    )

    assert not hasattr(args, "demo_password")
    assert args.demo_password_env == "QUAL_DEMO_PASSWORD"
    assert args.log_export_file == "/private/log-export.json"


def test_main_reads_password_from_environment_and_writes_bounded_evidence(tmp_path: Path) -> None:
    module = load_module()
    requester = FakeRequester()
    os.environ["QUAL_DEMO_PASSWORD"] = DEMO_PASSWORD
    log_export = tmp_path / "log-export.json"
    log_export.write_text(SAFE_LOG_EXPORT, encoding="utf-8")
    log_export.chmod(0o600)
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
                "--demo-password-env",
                "QUAL_DEMO_PASSWORD",
                "--log-export-file",
                str(log_export),
                "--allow-synthetic-writes",
                "--artifact-root",
                str(tmp_path),
                "--evidence-name",
                "qualification-evidence.md",
            ]
        )
    finally:
        setattr(module, qualification_function_name, original)
        os.environ.pop("QUAL_DEMO_PASSWORD", None)

    assert exit_code == 0
    evidence_path = tmp_path / "qualification-evidence.md"
    assert evidence_path.exists()
    assert "top-secret-token" not in evidence_path.read_text(encoding="utf-8")


def test_qualification_failure_writes_minimized_atomic_failure_evidence(tmp_path: Path) -> None:
    module = load_module()
    os.environ["QUAL_DEMO_PASSWORD"] = DEMO_PASSWORD
    log_export = tmp_path / "log-export.json"
    log_export.write_text(SAFE_LOG_EXPORT, encoding="utf-8")
    log_export.chmod(0o600)

    def failing_requester(
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> FakeResponse:
        if path == "/health":
            return FakeResponse(200, {"status": "ok"})
        if path == "/readiness":
            return FakeResponse(503, {"status": "not_ready"})
        raise AssertionError("later requests must not run after readiness failure")

    qualification_function_name = "qualify_develop_deployment"
    original = getattr(module, qualification_function_name)
    try:
        setattr(
            module,
            qualification_function_name,
            lambda **kwargs: original(requester=failing_requester, **kwargs),
        )
        exit_code = module.main(
            [
                "--base-url",
                "https://staff-tracer-abc123.a.run.app",
                "--expected-service-url",
                "https://staff-tracer-abc123.a.run.app",
                "--expected-image-digest",
                EXPECTED_IMAGE_DIGEST,
                "--demo-password-env",
                "QUAL_DEMO_PASSWORD",
                "--log-export-file",
                str(log_export),
                "--allow-synthetic-writes",
                "--artifact-root",
                str(tmp_path),
                "--evidence-name",
                "qualification-failure.md",
            ]
        )
    finally:
        setattr(module, qualification_function_name, original)
        os.environ.pop("QUAL_DEMO_PASSWORD", None)

    assert exit_code == 1
    evidence_path = tmp_path / "qualification-failure.md"
    rendered = evidence_path.read_text(encoding="utf-8")
    assert evidence_path.exists()
    assert "qualification_status: failed" in rendered
    assert "failed_boundary: readiness" in rendered
    assert "cleanup_disposition: teardown/rebuild required before retry" in rendered
    assert "top-secret-token" not in rendered
    assert "request failed for" not in rendered


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
