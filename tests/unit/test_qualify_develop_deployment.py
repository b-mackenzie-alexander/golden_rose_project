import base64
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
EXPECTED_SERVICE_RESOURCE = (
    "//run.googleapis.com/projects/golden-rose-develop/locations/us-east4/services/staff-tracer"
)


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
        if path == "/readiness" and "Authorization" not in headers:
            return FakeResponse(401, {"status": "denied"})
        if path == "/readiness" and headers.get("Authorization") == "Bearer unapproved-token":
            return FakeResponse(403, {"status": "denied"})
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
    setattr(  # noqa: B010
        module, "_verify_google_identity_token", lambda token, audience, subject: subject
    )
    setattr(module, "_verify_effective_iam_absence", lambda subject, resource: None)  # noqa: B010
    return module


def load_real_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("qualify_develop_deployment_real", MODULE_PATH)
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
        expected_service_resource=EXPECTED_SERVICE_RESOURCE,
        expected_unapproved_subject="unapproved-subject",
        access_token="top-secret-token",
        unapproved_access_token="unapproved-token",
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

    assert requester.calls[0]["headers"] == {"Accept": "application/json"}
    assert requester.calls[0]["body"] is None
    assert requester.calls[1]["headers"]["Authorization"] == "Bearer unapproved-token"
    assert requester.calls[1]["body"] is None
    health_call = requester.calls[2]
    readiness_call = requester.calls[3]
    assert health_call["method"] == "GET"
    assert readiness_call["method"] == "GET"
    assert "Idempotency-Key" not in health_call["headers"]
    assert "Idempotency-Key" not in readiness_call["headers"]
    assert all(
        call["headers"]["Authorization"] == "Bearer top-secret-token"
        for call in requester.calls[2:]
    )


def test_qualify_develop_deployment_runs_minimized_denial_probes_before_approved_flow() -> None:
    module = load_module()
    requester = FakeRequester()

    def probing_requester(
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> FakeResponse:
        if len(requester.calls) == 0:
            requester.calls.append(
                {"method": method, "path": path, "headers": headers, "body": body}
            )
            assert "Authorization" not in headers
            assert body is None
            return FakeResponse(401, {"status": "denied"})
        if len(requester.calls) == 1:
            requester.calls.append(
                {"method": method, "path": path, "headers": headers, "body": body}
            )
            assert headers["Authorization"] == "Bearer unapproved-token"
            assert body is None
            return FakeResponse(403, {"status": "denied"})
        return requester(method, path, headers, body)

    result = module.qualify_develop_deployment(
        base_url="https://staff-tracer-abc123.a.run.app",
        expected_service_url="https://staff-tracer-abc123.a.run.app",
        expected_service_resource=EXPECTED_SERVICE_RESOURCE,
        expected_unapproved_subject="unapproved-subject",
        access_token="top-secret-token",
        unapproved_access_token="unapproved-token",
        expected_schema_revision="0005_database_authority",
        expected_image_digest=EXPECTED_IMAGE_DIGEST,
        allow_synthetic_writes=True,
        requester=probing_requester,
    )

    assert requester.calls[0] == {
        "method": "GET",
        "path": "/readiness",
        "headers": {"Accept": "application/json"},
        "body": None,
    }
    assert requester.calls[1] == {
        "method": "GET",
        "path": "/readiness",
        "headers": {
            "Accept": "application/json",
            "Authorization": "Bearer unapproved-token",
        },
        "body": None,
    }
    assert requester.calls[2]["headers"]["Authorization"] == "Bearer top-secret-token"
    assert result["access_denial_probes"] == {
        "unauthenticated": "denied_without_business_body",
        "authenticated_unapproved": "denied_after_verified_token_and_iam_absence",
    }
    rendered = module.render_qualification_evidence(result)
    assert "top-secret-token" not in rendered
    assert "unapproved-token" not in rendered
    assert "accounts.google.com" not in rendered


def test_qualify_develop_deployment_rejects_substituted_unapproved_token() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="separate authenticated access tokens"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            expected_service_resource=EXPECTED_SERVICE_RESOURCE,
            expected_unapproved_subject="unapproved-subject",
            access_token="same-token",
            unapproved_access_token="same-token",
            expected_schema_revision="0005_database_authority",
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=True,
            requester=FakeRequester(),
        )


def test_qualify_develop_deployment_rejects_malformed_unapproved_token_before_probe() -> None:
    module = load_module()
    requester = FakeRequester()
    with pytest.raises(ValueError, match="unapproved token verification boundary failed"):
        module._decode_jwt_claims("not-a-google-identity-token")

    assert requester.calls == []


def test_google_identity_verifier_binds_verified_issuer_audience_temporal_claims_and_subject() -> (
    None
):
    module = load_real_module()
    claims = {
        "iss": "https://accounts.google.com",
        "aud": "https://staff-tracer-abc123.a.run.app",
        "sub": "unapproved-subject",
        "iat": 1,
        "exp": 4_102_444_800,
        "nbf": 1,
    }
    encoded_claims = base64.urlsafe_b64encode(json.dumps(claims).encode("utf-8")).decode("ascii")
    token = f"header.{encoded_claims.rstrip('=')}.signature"
    setattr(  # noqa: B010
        module, "_google_verify_oauth2_token", lambda actual_token, audience: claims
    )

    assert (
        module._verify_google_identity_token(token, claims["aud"], "unapproved-subject")
        == "unapproved-subject"
    )

    with pytest.raises(ValueError, match="unapproved token verification boundary failed"):
        module._verify_google_identity_token(token, claims["aud"], "different-valid-subject")
    with pytest.raises(ValueError, match="unapproved token verification boundary failed"):
        module._verify_google_identity_token(token, claims["aud"], "")


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
            expected_service_resource=EXPECTED_SERVICE_RESOURCE,
            expected_unapproved_subject="unapproved-subject",
            access_token="top-secret-token",
            unapproved_access_token="unapproved-token",
            expected_schema_revision="0005_database_authority",
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=True,
            requester=missing_no_store_requester,
        )


def test_qualify_develop_deployment_result_marks_unperformed_manual_evidence_not_run() -> None:
    module = load_module()

    result = module.qualify_develop_deployment(
        base_url="https://staff-tracer-abc123.a.run.app",
        expected_service_url="https://staff-tracer-abc123.a.run.app",
        expected_service_resource=EXPECTED_SERVICE_RESOURCE,
        expected_unapproved_subject="unapproved-subject",
        access_token="top-secret-token",
        unapproved_access_token="unapproved-token",
        expected_schema_revision="0005_database_authority",
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
        expected_service_resource=EXPECTED_SERVICE_RESOURCE,
        expected_unapproved_subject="unapproved-subject",
        access_token="top-secret-token",
        unapproved_access_token="unapproved-token",
        expected_schema_revision="0005_database_authority",
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
            expected_service_resource=EXPECTED_SERVICE_RESOURCE,
            expected_unapproved_subject="unapproved-subject",
            access_token="top-secret-token",
            unapproved_access_token="unapproved-token",
            expected_schema_revision="0005_database_authority",
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
            expected_service_resource=EXPECTED_SERVICE_RESOURCE,
            expected_unapproved_subject="unapproved-subject",
            access_token="top-secret-token",
            unapproved_access_token="unapproved-token",
            expected_schema_revision="0005_database_authority",
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=True,
            requester=missing_no_store_requester,
        )


def test_qualify_develop_deployment_records_no_store_evidence_matrix() -> None:
    module = load_module()

    result = module.qualify_develop_deployment(
        base_url="https://staff-tracer-abc123.a.run.app",
        expected_service_url="https://staff-tracer-abc123.a.run.app",
        expected_service_resource=EXPECTED_SERVICE_RESOURCE,
        expected_unapproved_subject="unapproved-subject",
        access_token="top-secret-token",
        unapproved_access_token="unapproved-token",
        expected_schema_revision="0005_database_authority",
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
        expected_service_resource=EXPECTED_SERVICE_RESOURCE,
        expected_unapproved_subject="unapproved-subject",
        access_token="top-secret-token",
        unapproved_access_token="unapproved-token",
        expected_schema_revision="0005_database_authority",
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


def test_qualify_develop_deployment_fails_closed_on_non_private_auth_gap() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="private authenticated access token is required"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            expected_service_resource=EXPECTED_SERVICE_RESOURCE,
            expected_unapproved_subject="unapproved-subject",
            access_token="",
            unapproved_access_token="unapproved-token",
            expected_schema_revision="0005_database_authority",
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=True,
            requester=FakeRequester(),
        )


def test_qualification_contract_requires_reviewed_authenticated_proxy_or_token_path() -> None:
    module = load_module()
    args = module._parse_args(
        [
            "--base-url",
            "https://staff-tracer-abc123.a.run.app",
            "--expected-service-url",
            "https://staff-tracer-abc123.a.run.app",
            "--expected-service-resource",
            EXPECTED_SERVICE_RESOURCE,
            "--expected-image-digest",
            EXPECTED_IMAGE_DIGEST,
            "--access-token-stdin",
            "--unapproved-access-token-env",
            "UNAPPROVED_QUAL_TOKEN",
            "--expected-unapproved-subject-env",
            "EXPECTED_UNAPPROVED_SUBJECT",
        ]
    )

    assert args.access_token_stdin is True
    assert args.access_token_env is None
    assert args.access_token_file is None
    assert args.unapproved_access_token_env == "UNAPPROVED_QUAL_TOKEN"
    assert args.expected_service_resource == EXPECTED_SERVICE_RESOURCE


def test_qualify_develop_deployment_requires_explicit_live_write_acknowledgement() -> None:
    module = load_module()

    with pytest.raises(ValueError, match="live-write acknowledgement"):
        module.qualify_develop_deployment(
            base_url="https://staff-tracer-abc123.a.run.app",
            expected_service_url="https://staff-tracer-abc123.a.run.app",
            expected_service_resource=EXPECTED_SERVICE_RESOURCE,
            expected_unapproved_subject="unapproved-subject",
            access_token="top-secret-token",
            unapproved_access_token="unapproved-token",
            expected_schema_revision="0005_database_authority",
            expected_image_digest=EXPECTED_IMAGE_DIGEST,
            allow_synthetic_writes=False,
            requester=FakeRequester(),
        )


def test_qualify_develop_deployment_fails_closed_on_readiness_posture_mismatch() -> None:
    module = load_module()
    call_count = 0

    def failing_requester(
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> FakeResponse:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            assert "Authorization" not in headers
            assert body is None
            return FakeResponse(401, {"status": "denied"})
        if call_count == 2:
            assert headers["Authorization"] == "Bearer unapproved-token"
            assert body is None
            return FakeResponse(403, {"status": "denied"})
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
            expected_service_resource=EXPECTED_SERVICE_RESOURCE,
            expected_unapproved_subject="unapproved-subject",
            access_token="top-secret-token",
            unapproved_access_token="unapproved-token",
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
            "--expected-service-resource",
            EXPECTED_SERVICE_RESOURCE,
            "--expected-image-digest",
            EXPECTED_IMAGE_DIGEST,
            "--access-token-env",
            "QUAL_TOKEN",
            "--unapproved-access-token-env",
            "UNAPPROVED_QUAL_TOKEN",
            "--expected-unapproved-subject-env",
            "EXPECTED_UNAPPROVED_SUBJECT",
        ]
    )

    assert not hasattr(args, "access_token")
    assert not hasattr(args, "unapproved_access_token")
    assert args.access_token_env == "QUAL_TOKEN"
    assert args.unapproved_access_token_env == "UNAPPROVED_QUAL_TOKEN"


def test_main_reads_token_from_environment_and_writes_bounded_evidence(tmp_path: Path) -> None:
    module = load_module()
    requester = FakeRequester()
    os.environ["QUAL_TOKEN"] = "top-secret-token"
    os.environ["UNAPPROVED_QUAL_TOKEN"] = "unapproved-token"
    os.environ["EXPECTED_UNAPPROVED_SUBJECT"] = "unapproved-subject"
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
                "--expected-service-resource",
                EXPECTED_SERVICE_RESOURCE,
                "--expected-image-digest",
                EXPECTED_IMAGE_DIGEST,
                "--access-token-env",
                "QUAL_TOKEN",
                "--unapproved-access-token-env",
                "UNAPPROVED_QUAL_TOKEN",
                "--expected-unapproved-subject-env",
                "EXPECTED_UNAPPROVED_SUBJECT",
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
        os.environ.pop("UNAPPROVED_QUAL_TOKEN", None)

    assert exit_code == 0
    evidence_path = tmp_path / "qualification-evidence.md"
    assert evidence_path.exists()
    assert "top-secret-token" not in evidence_path.read_text(encoding="utf-8")


def test_qualification_failure_writes_minimized_atomic_failure_evidence(tmp_path: Path) -> None:
    module = load_module()
    os.environ["QUAL_TOKEN"] = "top-secret-token"
    os.environ["UNAPPROVED_QUAL_TOKEN"] = "unapproved-token"
    os.environ["EXPECTED_UNAPPROVED_SUBJECT"] = "unapproved-subject"
    call_count = 0

    def failing_requester(
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> FakeResponse:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            assert "Authorization" not in headers
            assert body is None
            return FakeResponse(401, {"status": "denied"})
        if call_count == 2:
            assert headers["Authorization"] == "Bearer unapproved-token"
            assert body is None
            return FakeResponse(403, {"status": "denied"})
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
                "--expected-service-resource",
                EXPECTED_SERVICE_RESOURCE,
                "--expected-image-digest",
                EXPECTED_IMAGE_DIGEST,
                "--access-token-env",
                "QUAL_TOKEN",
                "--unapproved-access-token-env",
                "UNAPPROVED_QUAL_TOKEN",
                "--expected-unapproved-subject-env",
                "EXPECTED_UNAPPROVED_SUBJECT",
                "--allow-synthetic-writes",
                "--artifact-root",
                str(tmp_path),
                "--evidence-name",
                "qualification-failure.md",
            ]
        )
    finally:
        setattr(module, qualification_function_name, original)
        os.environ.pop("QUAL_TOKEN", None)
        os.environ.pop("UNAPPROVED_QUAL_TOKEN", None)

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
