#!/usr/bin/env bash
# Apply the reviewed desired GitHub repository policy. Run only from the repo root
# after the policy PR is merged into develop and the required workflow checks exist.
set -euo pipefail

repo="${GH_REPO:-b-mackenzie-alexander/golden_rose_project}"
policy="infra/github/repo-policy.json"

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 1; }
}
require gh
require python3

gh auth status >/dev/null
python3 -m json.tool "$policy" >/dev/null

# Repository-level merge controls are global. Feature PRs may squash merge into
# develop; main promotions must manually select a merge commit as documented.
gh api --method PATCH "repos/$repo" \
  -f allow_squash_merge=true \
  -f allow_merge_commit=true \
  -f allow_rebase_merge=false \
  -f allow_auto_merge=false \
  -f delete_branch_on_merge=true >/dev/null

apply_branch() {
  local branch="$1"
  local contexts
  contexts=$(python3 - "$policy" "$branch" <<'PY'
import json, sys
policy = json.load(open(sys.argv[1]))
branch = policy["branches"][sys.argv[2]]
print(json.dumps(branch["required_status_checks"]))
PY
)

  gh api --method PUT "repos/$repo/branches/$branch/protection" \
    --input - <<JSON
{
  "required_status_checks": {"strict": true, "contexts": $contexts},
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 0,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "lock_branch": false,
  "allow_fork_syncing": false
}
JSON
}

apply_branch develop
apply_branch main

echo "Applied repository and branch-protection policy for $repo."
echo "Run infra/github/verify-repo-policy.sh to detect drift."
