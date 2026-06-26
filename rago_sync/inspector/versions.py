import re
import subprocess
from ..config import COOKBOOK_REPO, REGISTRY_URL, RAGO_PACKAGES


def is_stale(constraint: str, latest: str) -> bool:
    """Return True if latest version exceeds the upper bound in constraint."""
    upper_match = re.search(r"<(\d+)\.(\d+)", constraint)
    if not upper_match:
        return False
    upper = (int(upper_match.group(1)), int(upper_match.group(2)))
    latest_parts = tuple(int(x) for x in latest.split(".")[:2])
    return latest_parts >= upper


def get_latest_version(package: str) -> str | None:
    """Query internal registry for latest version via uv pip index."""
    result = subprocess.run(
        ["uv", "pip", "index", "versions", package,
         "--index", REGISTRY_URL],
        capture_output=True, text=True, timeout=30,
    )
    match = re.search(r"Available versions: ([\d., ]+)", result.stdout)
    if match:
        versions = [v.strip() for v in match.group(1).split(",") if v.strip()]
        return versions[0] if versions else None
    return None


def get_pinned_constraints(entry_path: str) -> dict[str, str]:
    """Parse pyproject.toml and return {package: constraint_string}."""
    pyproject = COOKBOOK_REPO / "gen-ai" / entry_path / "pyproject.toml"
    if not pyproject.exists():
        return {}
    content = pyproject.read_text()
    result = {}
    for pkg in RAGO_PACKAGES:
        pattern = rf'"{re.escape(pkg)}([^"]*)"'
        match = re.search(pattern, content)
        if match:
            result[pkg] = match.group(1).strip()
    return result


def check_version_stale(entry_path: str) -> dict[str, dict]:
    """Returns {pkg: {constraint, latest}} for packages where latest > upper bound."""
    pinned = get_pinned_constraints(entry_path)
    stale = {}
    for pkg, constraint in pinned.items():
        latest = get_latest_version(pkg)
        if latest and is_stale(constraint, latest):
            stale[pkg] = {"constraint": constraint, "latest": latest}
    return stale
