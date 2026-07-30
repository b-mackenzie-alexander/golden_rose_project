#!/usr/bin/env bash
# Verify selected GitHub repository controls against the committed policy.
set -euo pipefail

repo="${GH_REPO:-b-mackenzie-alexander/golden_rose_project}"
policy="infra/github/repo-policy.json"

command -v gh >/dev/null 2>&1 || { echo "Missing required command: gh" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Missing required command: python3" >&2; exit 1; }
gh auth status >/dev/null

repo_actual=$(mktemp)
develop_actual=$(mktemp)
main_actual=$(mktemp)
trap 'rm -f "$repo_actual" "$develop_actual" "$main_actual"' EXIT

gh api "repos/$repo" >"$repo_actual"
gh api "repos/$repo/branches/develop/protection" >"$develop_actual"
gh api "repos/$repo/branches/main/protection" >"$main_actual"

python3 - "$policy" "$repo_actual" "$develop_actual" "$main_actual" <<'PY'
import json, sys
policy = json.load(open(sys.argv[1]))
repo, develop, main = (json.load(open(p)) for p in sys.argv[2:])
errors = []
for key, expected in policy["repository"].items():
    if repo.get(key) != expected:
        errors.append(f"repository.{key}: expected {expected!r}, got {repo.get(key)!r}")
for name, actual in (("develop", develop), ("main", main)):
    expected = policy["branches"][name]
    actual_contexts = sorted(item["context"] for item in actual["required_status_checks"]["contexts"])
    if actual_contexts != sorted(expected["required_status_checks"]):
        errors.append(f"{name}.required_status_checks: expected {expected['required_status_checks']!r}, got {actual_contexts!r}")
    for key in ("enforce_admins", "required_linear_history", "allow_force_pushes", "allow_deletions", "required_conversation_resolution"):
        actual_value = actual.get(key, {}).get("enabled") if isinstance(actual.get(key), dict) else actual.get(key)
        if actual_value != expected[key]:
            errors.append(f"{name}.{key}: expected {expected[key]!r}, got {actual_value!r}")
    reviews = actual["required_pull_request_reviews"]
    if reviews["required_approving_review_count"] != expected["required_approving_review_count"]:
        errors.append(f"{name}.required_approving_review_count drift")
if errors:
    print("Policy drift detected:")
    print("\n".join(f"- {error}" for error in errors))
    raise SystemExit(1)
print("Repository policy matches the checked committed controls.")
PY
