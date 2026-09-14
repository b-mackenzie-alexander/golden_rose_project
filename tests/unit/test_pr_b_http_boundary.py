"""Every PR B namespace retains the same bounded, value-safe HTTP boundary."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from golden_rose.api.dependencies import get_staff_principal
from golden_rose.main import create_app


@pytest.mark.parametrize("namespace", ["intakes", "work-interests"])
@pytest.mark.parametrize(
    ("method", "suffix", "body", "headers", "status"),
    [
        ("get", "/not/a/route", None, {}, 404),
        ("delete", "", None, {}, 405),
        ("post", "/query", "not-json", {"Content-Type": "text/plain"}, 415),
        ("post", "/query", "{}" * 20000, {"Content-Type": "application/json"}, 413),
        (
            "post",
            "/query",
            '{"unexpected":"PRIVATE_VALUE"}',
            {"Content-Type": "application/json"},
            422,
        ),
    ],
    ids=["not-found", "method", "media-type", "body-limit", "validation"],
)
def test_pr_b_namespace_errors_are_private(namespace, method, suffix, body, headers, status):
    with TestClient(create_app(), raise_server_exceptions=False) as client:
        response = client.request(
            method, f"/api/staff/v1/{namespace}{suffix}", content=body, headers=headers
        )
    assert response.status_code == status
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-type"] == "application/problem+json"
    assert "etag" not in response.headers and "last-modified" not in response.headers
    assert "PRIVATE_VALUE" not in response.text
    assert "input" not in response.json() and "ctx" not in response.json()
    if status == 413:
        assert response.json()["code"] == "payload_too_large"


@pytest.mark.parametrize("namespace", ["intakes", "work-interests"])
@pytest.mark.parametrize("status", [401, 403])
def test_pr_b_authorization_denial_has_safe_transport(namespace, status):
    def deny():
        raise HTTPException(status, "PRIVATE_PERMISSION_DETAIL")

    app = create_app()
    app.dependency_overrides[get_staff_principal] = deny
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            f"/api/staff/v1/{namespace}/query",
            json={"kind": "worker"} if namespace == "intakes" else {},
        )
    assert response.status_code == status
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["vary"] == "Authorization"
    assert response.headers["content-type"] == "application/problem+json"
    assert "PRIVATE_PERMISSION_DETAIL" not in response.text
    assert response.json()["code"] == ("unauthenticated" if status == 401 else "forbidden")


@pytest.mark.parametrize(
    ("code", "status", "expected"),
    [
        ("incomplete", 422, ["interests", "phone"]),
        ("forbidden", 403, None),
        ("not_found", 404, None),
        ("invalid_request", 422, None),
        ("persistence_unavailable", 503, None),
    ],
)
def test_completeness_error_only_discloses_allowlisted_codes(code, status, expected):
    import json

    from golden_rose.api.intake_transport import intake_problem

    response = intake_problem(
        code, status, missing_fields=["PRIVATE_FIELD_VALUE", "phone", "interests", "phone"]
    )
    body = json.loads(bytes(response.body))
    assert body.get("missing_fields") == expected
    assert b"PRIVATE_FIELD_VALUE" not in response.body
    if status == 503:
        assert response.headers["Retry-After"] == "1"
