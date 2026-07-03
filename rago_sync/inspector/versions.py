import base64
import os
import re
import urllib.error
import urllib.request
from ..auth import refresh_token
from ..config import COOKBOOK_REPO, REGISTRY_URL, RAGO_PACKAGES


def is_stale(constraint: str, latest: str) -> bool:
    """Return True if latest version exceeds the upper bound in constraint."""
    upper_match = re.search(r"<(\d+)\.(\d+)", constraint)
    if not upper_match:
        return False
    upper = (int(upper_match.group(1)), int(upper_match.group(2)))
    latest_parts = tuple(int(x) for x in latest.split(".")[:2])
    return latest_parts >= upper


def _version_key(version: str) -> tuple:
    return tuple(int(p) for p in re.findall(r"\d+", version))


def get_latest_version(package: str) -> str | None:
    """Query internal registry for latest version.

    NOTE: this used to shell out to `uv pip index versions`, but that subcommand
    no longer exists as of uv 0.9.17 ("error: unrecognized subcommand 'index'").
    That made this function silently return None for every package, which meant
    VERSION_STALE was never detected. Query the PEP 503 simple index directly
    instead.
    """
    if not refresh_token():
        return None
    token = os.environ.get("UV_INDEX_GEN_AI_INTERNAL_PASSWORD", "")
    url = REGISTRY_URL.rstrip("/") + "/" + package + "/"
    req = urllib.request.Request(url)
    auth = base64.b64encode(f"oauth2accesstoken:{token}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode()
    except urllib.error.URLError:
        return None

    dist_name = package.replace("-", "_")
    versions = sorted(
        set(re.findall(rf"{re.escape(dist_name)}-([\d.]+(?:\.\d+)*)\.(?:tar\.gz|whl)", html)),
        key=_version_key,
    )
    return versions[-1] if versions else None


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
