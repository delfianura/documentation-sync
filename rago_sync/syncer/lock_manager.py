import subprocess
from ..config import COOKBOOK_REPO


def run_uv_lock(entry_path: str) -> bool:
    result = subprocess.run(
        ["uv", "lock"],
        cwd=COOKBOOK_REPO / "gen-ai" / entry_path,
        capture_output=True, text=True,
    )
    return result.returncode == 0


def run_uv_sync(entry_path: str) -> bool:
    result = subprocess.run(
        ["uv", "sync"],
        cwd=COOKBOOK_REPO / "gen-ai" / entry_path,
        capture_output=True, text=True,
    )
    return result.returncode == 0
