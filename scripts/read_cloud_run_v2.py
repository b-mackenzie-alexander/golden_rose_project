"""Read Cloud Run v2 projections using the existing active gcloud identity.

Only GET/list requests are supported. Tokens stay in memory; HTTP errors never
reflect response bodies or URLs. The CLI writes resource JSON for private capture.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener


class ReadbackError(Exception):
    """A bounded readback failure, suitable for operator output."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str
    ) -> None:
        return None


def read_resource(project: str, region: str, kind: str, name: str | None = None) -> Any:
    if (
        not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]|[0-9]+", project)
        or not re.fullmatch(r"[a-z]+-[a-z]+[0-9]+", region)
        or kind not in {"jobs", "services"}
        or (name is not None and not re.fullmatch(r"[a-z][a-z0-9-]{0,61}[a-z0-9]", name))
        or (name is None and kind != "jobs")
    ):
        raise ReadbackError("Cloud Run readback scope is malformed")
    try:
        auth = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ReadbackError("Cloud Run authentication failed") from None
    token = auth.stdout.strip()
    if auth.returncode or not token or any(c.isspace() for c in token):
        raise ReadbackError("Cloud Run authentication failed")
    base = f"https://run.googleapis.com/v2/projects/{project}/locations/{region}/{kind}"
    if name is not None:
        base += "/" + name
    opener = build_opener(NoRedirect())
    jobs: list[dict[str, Any]] = []
    seen: set[str] = set()
    page = ""
    for _ in range(100):
        url = base + ("?" + urlencode({"pageToken": page}) if page else "")
        request = Request(url, headers={"Authorization": "Bearer " + token}, method="GET")
        try:
            with opener.open(request, timeout=30) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ReadbackError("Cloud Run response exceeds readback limit")
            payload = json.loads(raw)
        except HTTPError as exc:
            label = "NOT_FOUND" if exc.code == 404 else f"HTTP {exc.code}"
            raise ReadbackError("Cloud Run readback " + label) from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise ReadbackError("Cloud Run readback response unavailable or malformed") from None
        if not isinstance(payload, dict) or "apiVersion" in payload:
            raise ReadbackError("Cloud Run v2 response is malformed")
        if name is not None:
            resource_name = payload.get("name")
            if not isinstance(resource_name, str) or not re.fullmatch(
                rf"projects/[^/]+/locations/{re.escape(region)}/{kind}/{re.escape(name)}",
                resource_name,
            ):
                raise ReadbackError("Cloud Run v2 resource identity is malformed")
            return payload
        items = payload.get("jobs", [])
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ReadbackError("Cloud Run v2 job inventory is malformed")
        jobs.extend(items)
        page = payload.get("nextPageToken", "")
        if not isinstance(page, str) or page in seen:
            raise ReadbackError("Cloud Run pagination is malformed or repeated")
        if not page:
            return jobs
        seen.add(page)
    raise ReadbackError("Cloud Run pagination limit exceeded")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--kind", choices=["jobs", "services"], required=True)
    parser.add_argument("--name")
    args = parser.parse_args()
    try:
        result = read_resource(args.project, args.region, args.kind, args.name)
    except ReadbackError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
