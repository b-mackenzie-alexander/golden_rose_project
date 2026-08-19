from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import stat
from collections.abc import Callable, Sequence
from contextlib import suppress
from pathlib import Path
from typing import Any
from urllib import error, parse, request
from uuid import uuid4


class QualificationError(ValueError):
    pass


class _NoRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise error.HTTPError(newurl, code, msg, headers, fp)


Requester = Callable[[str, str, dict[str, str], dict[str, Any] | None], Any]
APPROVED_DEPLOYMENT_TARGET = "gcp-develop-private-synthetic"
APPROVED_CLOUD_RUN_HOST_PATTERN = re.compile(r"^staff-tracer-[a-z0-9-]+\.a\.run\.app$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
EVIDENCE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


def _normalize_response(response: Any) -> tuple[int, dict[str, str], dict[str, Any]]:
    if isinstance(response, tuple) and len(response) == 3:
        status_code, headers, payload = response
        return int(status_code), dict(headers), dict(payload)

    status_code = getattr(response, "status_code", None)
    headers = getattr(response, "headers", None)
    payload = getattr(response, "payload", None)
    if isinstance(status_code, int) and isinstance(headers, dict) and isinstance(payload, dict):
        return status_code, headers, payload

    raise QualificationError("requester returned an unsupported response shape")


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Qualify the private synthetic develop deployment with minimized evidence."
    )
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-service-url", required=True)
    parser.add_argument("--expected-image-digest", required=True)
    parser.add_argument("--expected-schema-revision", default="0005_database_authority")
    parser.add_argument("--artifact-root")
    parser.add_argument("--evidence-name", default="qualification-evidence.md")
    parser.add_argument("--allow-synthetic-writes", action="store_true")
    token_source = parser.add_mutually_exclusive_group(required=True)
    token_source.add_argument("--access-token-stdin", action="store_true")
    token_source.add_argument("--access-token-file")
    token_source.add_argument("--access-token-env")
    return parser.parse_args(argv)


def _validate_expected_image_digest(expected_image_digest: str) -> str:
    if not DIGEST_PATTERN.fullmatch(expected_image_digest):
        raise QualificationError("expected image digest must be an immutable sha256")
    return expected_image_digest


def _normalize_cloud_run_url(base_url: str) -> str:
    parsed = parse.urlparse(base_url)
    if parsed.scheme != "https":
        raise QualificationError("base URL must use https")
    if parsed.username or parsed.password:
        raise QualificationError("base URL must not include userinfo")
    if parsed.query:
        raise QualificationError("base URL must not include a query string")
    if parsed.fragment:
        raise QualificationError("base URL must not include a fragment")
    if parsed.params:
        raise QualificationError("base URL must not include path parameters")
    if parsed.path not in ("", "/"):
        raise QualificationError("base URL must not include a path")
    if parsed.port not in (None, 443):
        raise QualificationError("base URL must use the approved https authority only")
    if parsed.hostname is None or not APPROVED_CLOUD_RUN_HOST_PATTERN.fullmatch(parsed.hostname):
        raise QualificationError("base URL host must be an approved private Cloud Run authority")
    return f"https://{parsed.hostname}"


def _validate_base_url(base_url: str, expected_service_url: str) -> str:
    normalized_base_url = _normalize_cloud_run_url(base_url)
    normalized_expected_url = _normalize_cloud_run_url(expected_service_url)
    if normalized_base_url != normalized_expected_url:
        raise QualificationError("base URL must match the reviewed service authority")
    return normalized_base_url


def _read_access_token(args: argparse.Namespace) -> str:
    token: str | None = None
    if args.access_token_stdin:
        token = os.read(0, 1024 * 64).decode("utf-8")
    elif args.access_token_file:
        token = Path(args.access_token_file).read_text(encoding="utf-8")
    elif args.access_token_env:
        token = os.environ.get(args.access_token_env)
    normalized_token = (token or "").strip()
    if not normalized_token:
        raise QualificationError("private authenticated access token is required")
    return normalized_token


def _request_json(
    base_url: str,
    method: str,
    path: str,
    headers: dict[str, str],
    body: dict[str, Any] | None,
) -> tuple[int, dict[str, str], dict[str, Any]]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    request_headers = dict(headers)
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    req = request.Request(
        url=base_url.rstrip("/") + path,
        data=payload,
        headers=request_headers,
        method=method,
    )
    opener = request.build_opener(_NoRedirectHandler())
    try:
        with opener.open(req, timeout=30) as response:
            raw_body = response.read().decode("utf-8")
            response_headers = dict(response.headers.items())
            return int(response.status), response_headers, json.loads(raw_body)
    except error.HTTPError as exc:
        if 300 <= int(exc.code) < 400:
            raise QualificationError(
                "cross-origin redirects are not allowed during qualification"
            ) from exc
        try:
            response_body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            response_body = {}
        return int(exc.code), dict(exc.headers.items()), response_body
    except error.URLError as exc:
        raise QualificationError(f"request failed for {path}: {exc.reason}") from exc


def _build_private_headers(access_token: str) -> dict[str, str]:
    normalized_token = access_token.strip()
    if not normalized_token:
        raise QualificationError("private authenticated access token is required")
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {normalized_token}",
    }


def _redact_text(text: str) -> str:
    redacted = re.sub(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}",
        "[REDACTED]",
        text,
    )
    redacted = re.sub(r"postgresql\+[^\s]+", "[REDACTED]", redacted)
    redacted = re.sub(r"Bearer\s+[^\s]+", "Bearer [REDACTED]", redacted)
    redacted = re.sub(r"cursor[^\s]*", "[REDACTED]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"token[^\s]*", "[REDACTED]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"Synthetic Qual Employer[^\n]*", "[REDACTED]", redacted)
    redacted = re.sub(r"Synthetic Contact[^\n]*", "[REDACTED]", redacted)
    return redacted


def _validated_evidence_destination(artifact_root: str, evidence_name: str) -> Path:
    root = _reject_symlink_path_components(Path(artifact_root).expanduser(), "artifact root")
    if not EVIDENCE_NAME_PATTERN.fullmatch(evidence_name):
        raise QualificationError("evidence name must be a simple reviewed basename")
    root.mkdir(parents=True, exist_ok=True)
    root = _reject_symlink_path_components(root, "artifact root")
    destination = root / evidence_name
    if destination.exists() and destination.is_symlink():
        raise QualificationError("evidence destination must not be a symlink")
    return destination


def _open_directory_no_follow(path: Path) -> int:
    absolute_path = path if path.is_absolute() else Path.cwd() / path
    descriptor = os.open(absolute_path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in absolute_path.parts[1:]:
            next_descriptor = os.open(
                part,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = next_descriptor
    except OSError as exc:
        os.close(descriptor)
        raise QualificationError(
            "artifact parent must be a real directory without symlink components"
        ) from exc
    return descriptor


def _directory_identity(path: Path) -> tuple[int, int]:
    try:
        path_stat = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise QualificationError("artifact parent path cannot be revalidated") from exc
    if stat.S_ISLNK(path_stat.st_mode) or not stat.S_ISDIR(path_stat.st_mode):
        raise QualificationError("artifact parent path is not the reviewed directory")
    return (path_stat.st_dev, path_stat.st_ino)


def _atomic_write_text(
    path: Path, content: str, *, before_replace: Callable[[], None] | None = None
) -> None:
    directory_fd = _open_directory_no_follow(path.parent)
    expected_directory_identity = os.fstat(directory_fd)
    temporary_name = f".{path.name}.{secrets.token_hex(16)}.tmp"
    try:
        try:
            destination_stat = os.stat(path.name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            destination_stat = None
        if destination_stat is not None and stat.S_ISLNK(destination_stat.st_mode):
            raise QualificationError("evidence destination must not be a symlink")
        temporary_fd = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(temporary_fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if before_replace is not None:
            before_replace()
        if _directory_identity(path.parent) != (
            expected_directory_identity.st_dev,
            expected_directory_identity.st_ino,
        ):
            raise QualificationError(
                "artifact parent identity changed during descriptor-anchored write"
            )
        try:
            os.replace(temporary_name, path.name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        except OSError as exc:
            raise QualificationError(
                "artifact parent changed during descriptor-anchored write"
            ) from exc
    finally:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name, dir_fd=directory_fd)
        os.close(directory_fd)


def _reject_symlink_path_components(path: Path, label: str) -> Path:
    candidate = path if path.is_absolute() else Path.cwd() / path
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise QualificationError(f"{label} must not contain symlink components")
    return candidate.resolve(strict=False)


def render_qualification_evidence(result: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in result.items():
        if key == "internal_debug":
            continue
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for nested_key, nested_value in value.items():
                lines.append(f"  {nested_key}: {_redact_text(str(nested_value))}")
        else:
            lines.append(f"{key}: {_redact_text(str(value))}")
    return "\n".join(lines) + "\n"


def _expect_boundary(
    *,
    boundary: str,
    response: Any,
    expected_status: int,
    expected_body_status: str,
) -> dict[str, Any]:
    status_code, _, payload = _normalize_response(response)
    if status_code != expected_status or payload.get("status") != expected_body_status:
        raise QualificationError(f"{boundary} boundary failed")
    return payload


def qualify_develop_deployment(
    *,
    base_url: str,
    expected_service_url: str,
    access_token: str,
    expected_schema_revision: str,
    expected_image_digest: str,
    allow_synthetic_writes: bool,
    requester: Requester | None = None,
) -> dict[str, Any]:
    validated_base_url = _validate_base_url(base_url, expected_service_url)
    validated_expected_image_digest = _validate_expected_image_digest(expected_image_digest)
    headers = _build_private_headers(access_token)
    request_impl = requester or (
        lambda method, path, req_headers, body: _request_json(
            validated_base_url, method, path, req_headers, body
        )
    )

    employer_display_name = f"Synthetic Qual Employer {uuid4().hex[:8]}"
    revised_display_name = f"{employer_display_name} Revised"
    contact_full_name = f"Synthetic Contact {uuid4().hex[:8]}"
    create_idempotency_key = str(uuid4())
    revise_idempotency_key = str(uuid4())
    contact_idempotency_key = str(uuid4())

    health_payload = _expect_boundary(
        boundary="health",
        response=request_impl("GET", "/health", headers, None),
        expected_status=200,
        expected_body_status="ok",
    )
    readiness_payload = _expect_boundary(
        boundary="readiness",
        response=request_impl("GET", "/readiness", headers, None),
        expected_status=200,
        expected_body_status="ready",
    )
    if readiness_payload.get("deployment_target") != APPROVED_DEPLOYMENT_TARGET:
        raise QualificationError("readiness deployment target boundary failed")
    if readiness_payload.get("schema_revision") != expected_schema_revision:
        raise QualificationError("readiness schema revision boundary failed")
    if readiness_payload.get("deployed_image_digest") != validated_expected_image_digest:
        raise QualificationError("readiness image digest boundary failed")
    if not allow_synthetic_writes:
        raise QualificationError("explicit live-write acknowledgement is required")

    create_headers = dict(headers)
    create_headers["Idempotency-Key"] = create_idempotency_key
    create_status, create_response_headers, create_payload = _normalize_response(
        request_impl(
            "POST",
            "/api/staff/v1/employers",
            create_headers,
            {"employer_type": "business", "display_name": employer_display_name},
        )
    )
    if create_status != 201 or "employer_id" not in create_payload:
        raise QualificationError("employer create boundary failed")
    employer_id = str(create_payload["employer_id"])
    employer_version = int(create_payload["version"])

    replay_status, replay_headers, replay_payload = _normalize_response(
        request_impl(
            "POST",
            "/api/staff/v1/employers",
            create_headers,
            {"employer_type": "business", "display_name": employer_display_name},
        )
    )
    if replay_status != 201 or replay_headers.get("Idempotency-Replayed") != "true":
        raise QualificationError("employer replay boundary failed")
    if str(replay_payload.get("employer_id")) != employer_id:
        raise QualificationError("employer replay boundary failed")

    detail_status, _, detail_payload = _normalize_response(
        request_impl(
            "GET",
            f"/api/staff/v1/employers/{employer_id}",
            headers,
            None,
        )
    )
    if detail_status != 200 or str(detail_payload.get("employer_id")) != employer_id:
        raise QualificationError("employer read boundary failed")

    search_status, _, search_payload = _normalize_response(
        request_impl(
            "POST",
            "/api/staff/v1/employers/search",
            headers,
            {
                "display_name_query": employer_display_name.split()[-1],
                "employer_type": "business",
                "page_size": 10,
            },
        )
    )
    search_items = search_payload.get("items") if isinstance(search_payload, dict) else None
    if (
        search_status != 200
        or not isinstance(search_items, list)
        or not any(
            str(item.get("employer_id")) == employer_id
            for item in search_items
            if isinstance(item, dict)
        )
    ):
        raise QualificationError("employer search boundary failed")

    revise_headers = dict(headers)
    revise_headers["Idempotency-Key"] = revise_idempotency_key
    revise_status, revise_response_headers, revise_payload = _normalize_response(
        request_impl(
            "POST",
            f"/api/staff/v1/employers/{employer_id}/revisions",
            revise_headers,
            {
                "expected_version": employer_version,
                "employer_type": "business",
                "display_name": revised_display_name,
            },
        )
    )
    if revise_status != 200 or str(revise_payload.get("employer_id")) != employer_id:
        raise QualificationError("employer revision boundary failed")

    revise_replay_status, revise_replay_headers, revise_replay_payload = _normalize_response(
        request_impl(
            "POST",
            f"/api/staff/v1/employers/{employer_id}/revisions",
            revise_headers,
            {
                "expected_version": employer_version,
                "employer_type": "business",
                "display_name": revised_display_name,
            },
        )
    )
    if revise_replay_status != 200 or revise_replay_headers.get("Idempotency-Replayed") != "true":
        raise QualificationError("employer revision replay boundary failed")
    if str(revise_replay_payload.get("employer_id")) != employer_id:
        raise QualificationError("employer revision replay boundary failed")

    contact_headers = dict(headers)
    contact_headers["Idempotency-Key"] = contact_idempotency_key
    contact_status, contact_response_headers, contact_payload = _normalize_response(
        request_impl(
            "POST",
            f"/api/staff/v1/employers/{employer_id}/contacts",
            contact_headers,
            {"full_name": contact_full_name},
        )
    )
    if contact_status != 201 or "employer_contact_id" not in contact_payload:
        raise QualificationError("employer contact create boundary failed")
    contact_id = str(contact_payload["employer_contact_id"])

    contact_query_status, _, contact_query_payload = _normalize_response(
        request_impl(
            "POST",
            f"/api/staff/v1/employers/{employer_id}/contacts/query",
            headers,
            {"page_size": 10},
        )
    )
    contact_items = (
        contact_query_payload.get("items") if isinstance(contact_query_payload, dict) else None
    )
    if (
        contact_query_status != 200
        or not isinstance(contact_items, list)
        or not any(
            str(item.get("employer_contact_id")) == contact_id
            for item in contact_items
            if isinstance(item, dict)
        )
    ):
        raise QualificationError("employer contact query boundary failed")

    contact_read_status, _, contact_read_payload = _normalize_response(
        request_impl(
            "GET",
            f"/api/staff/v1/employers/{employer_id}/contacts/{contact_id}",
            headers,
            None,
        )
    )
    if (
        contact_read_status != 200
        or str(contact_read_payload.get("employer_contact_id")) != contact_id
    ):
        raise QualificationError("employer contact read boundary failed")

    return {
        "qualification_status": "passed",
        "health_status": str(health_payload["status"]),
        "readiness_status": str(readiness_payload["status"]),
        "readiness_posture": {
            "deployment_target": readiness_payload.get("deployment_target"),
            "schema_revision": readiness_payload.get("schema_revision"),
            "deployed_image_digest": readiness_payload.get("deployed_image_digest"),
        },
        "employer_flow": {
            "create": "fresh",
            "replay": "confirmed",
            "read": "passed",
            "search": "passed",
            "revision": "fresh",
            "revision_replay": "confirmed",
        },
        "employer_contact_flow": {
            "create": "fresh",
            "query": "passed",
            "read": "passed",
        },
        "cleanup_disposition": "no delete semantics exercised; use teardown/rebuild runbook",
        "internal_debug": {
            "display_name": employer_display_name,
            "revised_display_name": revised_display_name,
            "contact_full_name": contact_full_name,
            "employer_id": employer_id,
            "contact_id": contact_id,
            "create_idempotency_key": create_idempotency_key,
            "revise_idempotency_key": revise_idempotency_key,
            "contact_idempotency_key": contact_idempotency_key,
            "cursor": search_payload.get("next_cursor"),
            "token": access_token,
            "create_result_version": create_response_headers.get("Idempotency-Result-Version"),
            "revise_result_version": revise_response_headers.get("Idempotency-Result-Version"),
            "contact_result_version": contact_response_headers.get("Idempotency-Result-Version"),
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parse_args(argv)
        access_token = _read_access_token(args)
        result = qualify_develop_deployment(
            base_url=args.base_url,
            expected_service_url=args.expected_service_url,
            access_token=access_token,
            expected_schema_revision=args.expected_schema_revision,
            expected_image_digest=args.expected_image_digest,
            allow_synthetic_writes=args.allow_synthetic_writes,
        )
    except QualificationError as exc:
        print(str(exc))
        return 1

    rendered = render_qualification_evidence(result)
    if args.artifact_root:
        destination = _validated_evidence_destination(args.artifact_root, args.evidence_name)
        _atomic_write_text(destination, rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
