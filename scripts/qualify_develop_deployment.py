from __future__ import annotations

import argparse
import base64
import json
import os
import re
import secrets
import stat
import subprocess
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
APPROVED_CLOUD_RUN_HOST_PATTERN = re.compile(
    r"^(?:staff-tracer-[a-z0-9-]+\.a\.run\.app|"
    r"staff-tracer-[0-9]{6,20}\.us-east4\.run\.app)$"
)
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
EVIDENCE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
PROJECT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
DEMO_USERNAME = "golden-rose-demo"
DEMO_CHALLENGE = 'Basic realm="Golden Rose synthetic develop", charset="UTF-8"'
WRONG_DEMO_PASSWORD = "intentionally-wrong-demo-password"


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
    parser.add_argument("--artifact-root")
    parser.add_argument("--evidence-name", default="qualification-evidence.md")
    parser.add_argument("--allow-synthetic-writes", action="store_true")
    password_source = parser.add_mutually_exclusive_group(required=True)
    password_source.add_argument("--demo-password-stdin", action="store_true")
    password_source.add_argument("--demo-password-file")
    password_source.add_argument("--demo-password-env")
    log_source = parser.add_mutually_exclusive_group(required=True)
    log_source.add_argument("--log-project-id")
    log_source.add_argument("--log-export-file")
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
        raise QualificationError("base URL host must be an approved Cloud Run service authority")
    return f"https://{parsed.hostname}"


def _validate_base_url(base_url: str, expected_service_url: str) -> str:
    normalized_base_url = _normalize_cloud_run_url(base_url)
    normalized_expected_url = _normalize_cloud_run_url(expected_service_url)
    if normalized_base_url != normalized_expected_url:
        raise QualificationError("base URL must match the reviewed service authority")
    return normalized_base_url


def _read_private_text_file(path: str | Path, *, label: str) -> str:
    candidate = Path(path)
    try:
        file_stat = candidate.lstat()
        if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_mode & 0o077:
            raise QualificationError(f"{label} private file boundary failed")
        if file_stat.st_size > 8 * 1024 * 1024:
            raise QualificationError(f"{label} private file boundary failed")
        return candidate.read_text(encoding="utf-8")
    except QualificationError:
        raise
    except (OSError, UnicodeError) as exc:
        raise QualificationError(f"{label} private file boundary failed") from exc


def _collect_cloud_run_logs(
    project_id: str,
    *,
    runner: Callable[..., Any] = subprocess.run,
) -> str:
    if not PROJECT_ID_PATTERN.fullmatch(project_id):
        raise QualificationError("log project boundary failed")
    command = [
        "gcloud",
        "logging",
        "read",
        'resource.type="cloud_run_revision" AND resource.labels.service_name="staff-tracer"',
        f"--project={project_id}",
        "--freshness=15m",
        "--limit=1000",
        "--format=json",
    ]
    try:
        completed = runner(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise QualificationError("post-qualification log collection failed") from exc
    if completed.returncode != 0:
        raise QualificationError("post-qualification log collection failed")
    return str(completed.stdout)


def _read_secret(
    *,
    stdin_selected: bool,
    file_path: str | None,
    env_name: str | None,
    label: str,
) -> str:
    secret_value: str | None = None
    if stdin_selected:
        secret_value = os.read(0, 1024 * 64).decode("utf-8")
    elif file_path:
        secret_value = _read_private_text_file(file_path, label=label)
    elif env_name:
        secret_value = os.environ.get(env_name)
    normalized_value = (secret_value or "").strip()
    if not normalized_value:
        raise QualificationError(f"{label} is required")
    return normalized_value


def _read_demo_password(args: argparse.Namespace) -> str:
    return _read_secret(
        stdin_selected=args.demo_password_stdin,
        file_path=args.demo_password_file,
        env_name=args.demo_password_env,
        label="private demo password",
    )


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


def _build_demo_headers(password: str) -> dict[str, str]:
    normalized_password = password.strip()
    if not normalized_password:
        raise QualificationError("private demo password is required")
    encoded = base64.b64encode(f"{DEMO_USERNAME}:{normalized_password}".encode()).decode("ascii")
    return {
        "Accept": "application/json",
        "Authorization": f"Basic {encoded}",
    }


def _verify_log_export_is_safe(
    log_export: str,
    *,
    prohibited_values: Sequence[str],
) -> str:
    normalized_export = log_export.casefold()
    fixed_markers = ("authorization", "basic ", "credential", "password")
    value_markers = tuple(value.strip().casefold() for value in prohibited_values if value.strip())
    if any(marker in normalized_export for marker in (*fixed_markers, *value_markers)):
        raise QualificationError("log export contains prohibited values")
    return "passed_no_prohibited_values"


def _require_no_store(boundary: str, headers: dict[str, str]) -> None:
    cache_control = ""
    for header_name, header_value in headers.items():
        if header_name.lower() == "cache-control":
            cache_control = header_value
            break
    directives = {
        directive.strip().lower().split("=", 1)[0]
        for directive in cache_control.split(",")
        if directive.strip()
    }
    forbidden_directives = {"public", "private", "max-age", "s-maxage", "immutable"}
    if "no-store" not in directives or directives & forbidden_directives:
        raise QualificationError(f"{boundary} cache-control boundary failed")


def _run_prequalification_denial_probes(
    *,
    requester: Requester,
) -> dict[str, str]:
    unauthenticated = requester(
        "GET", "/api/staff/v1/environment", {"Accept": "application/json"}, None
    )
    wrong = requester(
        "GET",
        "/api/staff/v1/environment",
        _build_demo_headers(WRONG_DEMO_PASSWORD),
        None,
    )
    for label, response in (("unauthenticated", unauthenticated), ("wrong basic", wrong)):
        status_code, response_headers, payload = _normalize_response(response)
        challenge = next(
            (
                value
                for name, value in response_headers.items()
                if name.lower() == "www-authenticate"
            ),
            "",
        )
        if status_code != 401 or payload or challenge != DEMO_CHALLENGE:
            raise QualificationError(f"{label} basic denial boundary failed")
        _require_no_store(f"{label} basic denial", response_headers)
    return {
        "unauthenticated": "fixed_basic_denial",
        "wrong_basic": "fixed_basic_denial",
    }


def _redact_text(text: str) -> str:
    redacted = re.sub(
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}",
        "[REDACTED]",
        text,
    )
    redacted = re.sub(r"postgresql\+[^\s]+", "[REDACTED]", redacted)
    redacted = re.sub(r"Bearer\s+[^\s]+", "Bearer [REDACTED]", redacted)
    redacted = re.sub(r"Basic\s+[^\s]+", "Basic [REDACTED]", redacted)
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


def _failure_boundary(exc: QualificationError) -> str:
    message = str(exc)
    if "health" in message:
        return "health"
    if "readiness" in message:
        return "readiness"
    if "employer create" in message:
        return "employer_create"
    if "employer replay" in message:
        return "employer_replay"
    if "employer read" in message:
        return "employer_read"
    if "employer search" in message:
        return "employer_search"
    if "revision" in message:
        return "employer_revision"
    if "contact create" in message:
        return "employer_contact_create"
    if "contact query" in message:
        return "employer_contact_query"
    if "contact read" in message:
        return "employer_contact_read"
    if "password" in message or "authenticated access" in message:
        return "authenticated_access"
    if "base URL" in message or "service authority" in message:
        return "network_reachability"
    return "qualification_contract"


def _failure_result(exc: QualificationError) -> dict[str, Any]:
    return {
        "qualification_status": "failed",
        "failed_boundary": _failure_boundary(exc),
        "qualification_executed": False,
        "cleanup_disposition": "teardown/rebuild required before retry",
    }


def _expect_boundary(
    *,
    boundary: str,
    response: Any,
    expected_status: int,
    expected_body_status: str,
) -> dict[str, Any]:
    status_code, response_headers, payload = _normalize_response(response)
    if status_code != expected_status or payload.get("status") != expected_body_status:
        raise QualificationError(f"{boundary} boundary failed")
    _require_no_store(boundary, response_headers)
    return payload


def qualify_develop_deployment(
    *,
    base_url: str,
    expected_service_url: str,
    demo_password: str,
    log_export_reader: Callable[[], str],
    expected_image_digest: str,
    allow_synthetic_writes: bool,
    requester: Requester | None = None,
) -> dict[str, Any]:
    validated_base_url = _validate_base_url(base_url, expected_service_url)
    _validate_expected_image_digest(expected_image_digest)
    headers = _build_demo_headers(demo_password)
    public_headers = {"Accept": "application/json"}
    request_impl = requester or (
        lambda method, path, req_headers, body: _request_json(
            validated_base_url, method, path, req_headers, body
        )
    )
    health_payload = _expect_boundary(
        boundary="health",
        response=request_impl("GET", "/health", public_headers, None),
        expected_status=200,
        expected_body_status="ok",
    )
    readiness_payload = _expect_boundary(
        boundary="readiness",
        response=request_impl("GET", "/readiness", public_headers, None),
        expected_status=200,
        expected_body_status="ready",
    )
    if set(health_payload) != {"status"} or set(readiness_payload) != {"status"}:
        raise QualificationError("public probe minimization boundary failed")
    access_denial_probes = _run_prequalification_denial_probes(requester=request_impl)
    environment_status, environment_headers, environment_payload = _normalize_response(
        request_impl("GET", "/api/staff/v1/environment", headers, None)
    )
    if (
        environment_status != 200
        or environment_payload.get("environment") != "develop"
        or environment_payload.get("data_boundary") != "fictional-synthetic-only"
        or "non-production" not in str(environment_payload.get("label", "")).lower()
        or "synthetic" not in str(environment_payload.get("label", "")).lower()
    ):
        raise QualificationError("environment synthetic boundary failed")
    _require_no_store("environment", environment_headers)
    if not allow_synthetic_writes:
        raise QualificationError("explicit live-write acknowledgement is required")

    employer_display_name = f"Synthetic Qual Employer {uuid4().hex[:8]}"
    revised_display_name = f"{employer_display_name} Revised"
    contact_full_name = f"Synthetic Contact {uuid4().hex[:8]}"
    create_idempotency_key = str(uuid4())
    revise_idempotency_key = str(uuid4())
    contact_idempotency_key = str(uuid4())

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
    _require_no_store("employer create", create_response_headers)
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
    _require_no_store("employer replay", replay_headers)

    detail_status, detail_headers, detail_payload = _normalize_response(
        request_impl(
            "GET",
            f"/api/staff/v1/employers/{employer_id}",
            headers,
            None,
        )
    )
    if detail_status != 200 or str(detail_payload.get("employer_id")) != employer_id:
        raise QualificationError("employer read boundary failed")
    _require_no_store("employer read", detail_headers)

    random_employer_id = str(uuid4())
    detail_not_found_status, detail_not_found_headers, _ = _normalize_response(
        request_impl("GET", f"/api/staff/v1/employers/{random_employer_id}", headers, None)
    )
    if detail_not_found_status != 404:
        raise QualificationError("employer detail not-found boundary failed")
    _require_no_store("employer detail not-found", detail_not_found_headers)

    search_status, search_headers, search_payload = _normalize_response(
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
    _require_no_store("employer search", search_headers)

    malformed_search_status, malformed_search_headers, _ = _normalize_response(
        request_impl(
            "POST",
            "/api/staff/v1/employers/search",
            headers,
            {
                "display_name_query": employer_display_name.split()[-1],
                "employer_type": "business",
                "page_size": 10,
                "cursor": "malformed-cursor",
            },
        )
    )
    if malformed_search_status != 422:
        raise QualificationError("employer search malformed-cursor boundary failed")
    _require_no_store("employer search malformed cursor", malformed_search_headers)

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
    _require_no_store("employer revision", revise_response_headers)

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
    _require_no_store("employer revision replay", revise_replay_headers)

    stale_revision_headers = dict(headers)
    stale_revision_headers["Idempotency-Key"] = str(uuid4())
    stale_revision_status, stale_revision_response_headers, _ = _normalize_response(
        request_impl(
            "POST",
            f"/api/staff/v1/employers/{employer_id}/revisions",
            stale_revision_headers,
            {
                "expected_version": employer_version,
                "employer_type": "business",
                "display_name": f"{revised_display_name} Stale",
            },
        )
    )
    if stale_revision_status != 412:
        raise QualificationError("employer revision stale boundary failed")
    _require_no_store("employer revision stale", stale_revision_response_headers)

    changed_key_conflict_status, changed_key_conflict_headers, _ = _normalize_response(
        request_impl(
            "POST",
            f"/api/staff/v1/employers/{employer_id}/revisions",
            revise_headers,
            {
                "expected_version": employer_version,
                "employer_type": "business",
                "display_name": f"{revised_display_name} Changed",
            },
        )
    )
    if changed_key_conflict_status != 409:
        raise QualificationError("employer revision idempotency-conflict boundary failed")
    _require_no_store("employer revision idempotency conflict", changed_key_conflict_headers)

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
    _require_no_store("employer contact create", contact_response_headers)
    contact_id = str(contact_payload["employer_contact_id"])

    contact_query_status, contact_query_headers, contact_query_payload = _normalize_response(
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
    _require_no_store("employer contact query", contact_query_headers)

    for label, cursor in (
        ("malformed cursor", "malformed-cursor"),
        ("overlength cursor", "x" * 2049),
    ):
        contact_cursor_status, contact_cursor_headers, _ = _normalize_response(
            request_impl(
                "POST",
                f"/api/staff/v1/employers/{employer_id}/contacts/query",
                headers,
                {"page_size": 10, "cursor": cursor},
            )
        )
        if contact_cursor_status != 422:
            raise QualificationError(f"employer contact query {label} boundary failed")
        _require_no_store(f"employer contact query {label}", contact_cursor_headers)

    contact_read_status, contact_read_headers, contact_read_payload = _normalize_response(
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
    _require_no_store("employer contact read", contact_read_headers)

    random_contact_id = str(uuid4())
    contact_not_found_status, contact_not_found_headers, _ = _normalize_response(
        request_impl(
            "GET",
            f"/api/staff/v1/employers/{employer_id}/contacts/{random_contact_id}",
            headers,
            None,
        )
    )
    if contact_not_found_status != 404:
        raise QualificationError("employer contact read not-found boundary failed")
    _require_no_store("employer contact read not-found", contact_not_found_headers)

    log_scan = _verify_log_export_is_safe(
        log_export_reader(),
        prohibited_values=[
            DEMO_USERNAME,
            demo_password,
            employer_display_name,
            revised_display_name,
            contact_full_name,
            employer_id,
            contact_id,
            random_employer_id,
            random_contact_id,
            create_idempotency_key,
            revise_idempotency_key,
            contact_idempotency_key,
        ],
    )

    return {
        "qualification_status": "passed",
        "health_status": str(health_payload["status"]),
        "readiness_status": str(readiness_payload["status"]),
        "log_scan": log_scan,
        "automated_qualification": {
            "status": "passed",
            "synthetic_writes": "explicitly_allowed",
        },
        "no_store_evidence": {
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
                "employer_contact_read_errors": (
                    "source_controlled_static_contract_plus_live_not_found"
                ),
                "live_error_qualification": "safe_rows_passed",
            },
        },
        "manual_browser": {"status": "not_run"},
        "accessibility": {
            "automated_axe": "not_evidenced",
            "manual_review": "not_run",
        },
        "fluent_language": {
            "english": "not_evidenced",
            "spanish": "not_evidenced",
        },
        "tester_access": {"status": "not_evidenced"},
        "monitoring": {"status": "not_evidenced"},
        "recovery": {"status": "not_evidenced"},
        "feedback": {
            "status": "not_run",
            "structured_artifact": "not_evidenced",
            "severity": "not_triaged",
            "workflow_blocking": "not_triaged",
            "accessibility_impact": "not_triaged",
            "privacy_impact": "not_triaged",
            "security_impact": "not_triaged",
            "language_impact": "not_triaged",
            "owner_disposition_retest": "not_triaged",
        },
        "access_denial_probes": access_denial_probes,
        "platform_posture": {
            "immutable_image": "verified_by_prior_foundation_readback",
            "private_database": "verified_by_prior_foundation_readback",
            "one_instance_cap": "verified_by_prior_foundation_readback",
            "credential_expiry": "verified_by_prior_foundation_readback",
            "budget_and_labels": "verified_by_prior_foundation_readback",
            "log_safety": "verified_by_post_qualification_log_scan",
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
            "create_result_version": create_response_headers.get("Idempotency-Result-Version"),
            "revise_result_version": revise_response_headers.get("Idempotency-Result-Version"),
            "contact_result_version": contact_response_headers.get("Idempotency-Result-Version"),
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    destination: Path | None = None
    if args.artifact_root:
        destination = _validated_evidence_destination(args.artifact_root, args.evidence_name)
    try:
        demo_password = _read_demo_password(args)
        log_export_reader = (
            (lambda: _collect_cloud_run_logs(args.log_project_id))
            if args.log_project_id
            else lambda: _read_private_text_file(
                args.log_export_file,
                label="log export",
            )
        )
        result = qualify_develop_deployment(
            base_url=args.base_url,
            expected_service_url=args.expected_service_url,
            demo_password=demo_password,
            log_export_reader=log_export_reader,
            expected_image_digest=args.expected_image_digest,
            allow_synthetic_writes=args.allow_synthetic_writes,
        )
    except QualificationError as exc:
        if destination is not None:
            _atomic_write_text(destination, render_qualification_evidence(_failure_result(exc)))
        print("qualification failed")
        return 1

    rendered = render_qualification_evidence(result)
    if destination is not None:
        _atomic_write_text(destination, rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
