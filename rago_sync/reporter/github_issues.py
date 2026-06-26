import subprocess

from ..config import ASSIGNEES

GITHUB_REPO = "gdplabs/gl-sdk"
COOKBOOK_REPO_GH = "gdplabs/gen-ai-sdk-cookbook"


def create_issue(title: str, body: str, labels: list[str], repo: str = COOKBOOK_REPO_GH) -> str | None:
    """Create GitHub issue assigned to all 4 members. Returns issue URL or None."""
    cmd = [
        "gh", "issue", "create",
        "--repo", repo,
        "--title", title,
        "--body", body,
    ]
    for label in labels:
        cmd += ["--label", label]
    for assignee in ASSIGNEES:
        cmd += ["--assignee", assignee]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    print(f"Issue creation failed: {result.stderr}")
    return None


def get_pr_state(pr_number: int, repo: str = GITHUB_REPO) -> str:
    """Returns 'open', 'merged', or 'closed'."""
    result = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--repo", repo,
         "--json", "state,merged", "--jq", ".state + \",\" + (.merged|tostring)"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return "open"
    parts = result.stdout.strip().split(",")
    if len(parts) == 2 and parts[1] == "true":
        return "merged"
    return parts[0].lower() if parts else "open"


def open_gitbook_pr(branch: str, title: str, body: str) -> str | None:
    """Create PR against docs/gitbook-sync. Returns PR URL or None."""
    result = subprocess.run(
        ["gh", "pr", "create",
         "--repo", GITHUB_REPO,
         "--title", title,
         "--body", body,
         "--base", "docs/gitbook-sync",
         "--head", branch],
        capture_output=True, text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None
