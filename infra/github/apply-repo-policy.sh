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

supported_branches=(develop main)
policy_branches=$(python3 - "$policy" <<'PY'
import json, sys
print("\n".join(sorted(json.load(open(sys.argv[1]))["branches"])))
PY
)
if [[ "$policy_branches" != $'develop\nmain' ]]; then
  echo "Unsupported policy branch scope: $policy_branches" >&2
  echo "Supported branch scope: ${supported_branches[*]}" >&2
  exit 1
fi

# Repository-level merge controls are global. Feature PRs may squash merge into
# develop; main promotions must manually select a merge commit as documented.
repository_payload=$(python3 - "$policy" <<'PY'
import json, sys
print(json.dumps(json.load(open(sys.argv[1]))["repository"]))
PY
)
gh api --method PATCH "repos/$repo" \
  --input - <<<"$repository_payload" >/dev/null

apply_branch() {
  local branch="$1"
  local protection_payload
  protection_payload=$(python3 - "$policy" "$branch" <<'PY'
import json, sys
policy = json.load(open(sys.argv[1]))
branch = policy["branches"][sys.argv[2]]
print(json.dumps({
    "required_status_checks": {
        "strict": branch["strict_required_status_checks"],
        "contexts": branch["required_status_checks"],
    },
    "enforce_admins": branch["enforce_admins"],
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": branch["dismiss_stale_reviews"],
        "require_code_owner_reviews": branch["require_code_owner_reviews"],
        "required_approving_review_count": branch["required_approving_review_count"],
        "require_last_push_approval": branch["require_last_push_approval"],
    },
    "restrictions": branch["restrictions"],
    "required_linear_history": branch["required_linear_history"],
    "allow_force_pushes": branch["allow_force_pushes"],
    "allow_deletions": branch["allow_deletions"],
    "required_conversation_resolution": branch["required_conversation_resolution"],
    "lock_branch": branch["lock_branch"],
    "allow_fork_syncing": branch["allow_fork_syncing"],
    "block_creations": branch["block_creations"],
}))
PY
)

  gh api --method PUT "repos/$repo/branches/$branch/protection" \
    --input - <<<"$protection_payload"
}

while IFS= read -r branch; do
  apply_branch "$branch"
done <<<"$policy_branches"

echo "Applied repository and branch-protection policy for $repo."
echo "Run infra/github/verify-repo-policy.sh to detect drift."
