import subprocess
from ..auth import refresh_token
from ..config import COOKBOOK_REPO


def run_uv_lock(entry_path: str) -> bool:
    # Sync runs can process many entries; a gcloud access token (~1hr TTL) can expire
    # mid-run and every subsequent `uv lock`/`uv sync` fails with a 401 against the
    # internal index. Refresh right before each call rather than once per CLI invocation.
    refresh_token()
    result = subprocess.run(
        ["uv", "lock"],
        cwd=COOKBOOK_REPO / "gen-ai" / entry_path,
        capture_output=True, text=True,
    )
    return result.returncode == 0


def run_uv_sync(entry_path: str) -> bool:
    refresh_token()
    result = subprocess.run(
        ["uv", "sync"],
        cwd=COOKBOOK_REPO / "gen-ai" / entry_path,
        capture_output=True, text=True,
    )
    return result.returncode == 0
