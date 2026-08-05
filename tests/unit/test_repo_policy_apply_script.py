import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_apply_script_derives_every_payload_value_from_policy(tmp_path: Path) -> None:
    calls_path = tmp_path / "calls.jsonl"
    fake_gh = tmp_path / "gh"
    fake_gh.write_text(
        """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
if args == ["auth", "status"]:
    raise SystemExit(0)
resource = next(arg for arg in args if arg.startswith("repos/"))
payload = sys.stdin.read()
with Path(os.environ["FAKE_GH_CALLS"]).open("a") as calls:
    calls.write(json.dumps({"resource": resource, "payload": payload}) + "\\n")
print("{}")
"""
    )
    fake_gh.chmod(0o755)
    environment = os.environ | {
        "FAKE_GH_CALLS": str(calls_path),
        "GH_REPO": "example/golden-rose",
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
    }

    completed = subprocess.run(
        ["bash", "infra/github/apply-repo-policy.sh"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    calls = [json.loads(line) for line in calls_path.read_text().splitlines()]
    assert len(calls) == 3
    policy = json.loads((ROOT / "infra/github/repo-policy.json").read_text())
    assert json.loads(calls[0]["payload"]) == policy["repository"]
    for call, branch_name in zip(calls[1:], ["develop", "main"], strict=True):
        branch = policy["branches"][branch_name]
        payload = json.loads(call["payload"])
        assert payload["required_status_checks"] == {
            "strict": branch["strict_required_status_checks"],
            "contexts": branch["required_status_checks"],
        }
        assert payload["required_pull_request_reviews"] == {
            "dismiss_stale_reviews": branch["dismiss_stale_reviews"],
            "require_code_owner_reviews": branch["require_code_owner_reviews"],
            "required_approving_review_count": branch["required_approving_review_count"],
            "require_last_push_approval": branch["require_last_push_approval"],
        }
        for key in (
            "enforce_admins",
            "restrictions",
            "required_linear_history",
            "allow_force_pushes",
            "allow_deletions",
            "required_conversation_resolution",
            "lock_branch",
            "allow_fork_syncing",
            "block_creations",
        ):
            assert payload[key] == branch[key]
