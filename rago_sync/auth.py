import os
import subprocess


def refresh_token() -> bool:
    """Refresh gcloud token and set UV env vars. Returns True on success."""
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True, text=True,
    )
    token = result.stdout.strip()
    if not token or len(token) < 20:
        return False
    os.environ["UV_INDEX_GEN_AI_INTERNAL_USERNAME"] = "oauth2accesstoken"
    os.environ["UV_INDEX_GEN_AI_INTERNAL_PASSWORD"] = token
    return True


def require_auth() -> None:
    """Raise RuntimeError if auth fails."""
    if not refresh_token():
        raise RuntimeError(
            "gcloud auth failed. Run: gcloud auth login"
        )
