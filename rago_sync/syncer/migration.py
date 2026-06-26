import re
import subprocess
from ..config import GL_SDK_REPO, GITBOOK_BRANCH


def find_migration_guide(pkg: str, from_ver: str, to_ver: str) -> str | None:
    """Fetch migration guide content from gitbook branch. Returns None if not found."""
    pkg_name = pkg.removeprefix("gllm-")
    from_mm = ".".join(from_ver.split(".")[:2])
    to_mm = ".".join(to_ver.split(".")[:2])
    fname = f"{pkg}-v{from_mm}-to-v{to_mm}.md"
    path = f"gitbook/gen-ai-sdk/tutorials/{pkg_name}/migration-guide/{fname}"
    result = subprocess.run(
        ["git", "show", f"{GITBOOK_BRANCH}:{path}"],
        cwd=GL_SDK_REPO, capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else None


def parse_breaking_changes(guide_content: str) -> list[dict]:
    """Parse migration guide markdown into list of breaking change dicts."""
    changes = []
    current_section = "General"
    for line in guide_content.splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        removed = re.findall(r"`(\w+)`[^`]*(?:is removed|are removed)", line, re.IGNORECASE)
        for sym in removed:
            changes.append({"symbol": sym, "change": "removed",
                             "section": current_section, "breaking": True})
        renamed = re.findall(
            r"`(\w+)`[^`]*(?:renamed to|replaced by)[^`]*`(\w+)`", line, re.IGNORECASE
        )
        for old, new in renamed:
            changes.append({"symbol": old, "change": f"renamed to {new}",
                             "section": current_section, "breaking": True})
    return changes


def classify_version_bump(
    pkg: str,
    constraint: str,
    latest_ver: str,
    cookbook_code: str,
    guide_content: str | None = None,
) -> dict:
    """Classify whether a version bump involves breaking changes for this cookbook entry."""
    if guide_content is None:
        from_match = re.search(r">=(\d+\.\d+)", constraint)
        if not from_match:
            return {"breaking": False, "changes": [], "guide_path": None}
        from_ver = from_match.group(1)
        guide_content = find_migration_guide(pkg, from_ver, latest_ver)

    if not guide_content:
        return {"breaking": False, "changes": [], "guide_path": None}

    all_changes = parse_breaking_changes(guide_content)
    relevant = [c for c in all_changes if c["symbol"] in cookbook_code]
    breaking = any(c["breaking"] for c in relevant)
    return {"breaking": breaking, "changes": relevant, "guide_path": None}
