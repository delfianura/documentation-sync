import os
from pathlib import Path

# Override on other machines via env vars, e.g.:
#   export RAGO_SYNC_GL_SDK_REPO=/path/to/gl-sdk
#   export RAGO_SYNC_COOKBOOK_REPO=/path/to/gen-ai-sdk-cookbook
# Defaults below match the original author's machine layout.
GL_SDK_REPO = Path(os.environ.get(
    "RAGO_SYNC_GL_SDK_REPO",
    "/home/delfia-n-a-putri/Documents/Work/GEN_AI/gl-sdk",
))
COOKBOOK_REPO = Path(os.environ.get(
    "RAGO_SYNC_COOKBOOK_REPO",
    "/home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook",
))
GITBOOK_BRANCH = "origin/docs/gitbook-sync"
GITBOOK_PREFIX = "gitbook/gen-ai-sdk"

_TOOL_ROOT = Path(__file__).parent.parent
STATUS_FILE = _TOOL_ROOT / "status.json"
REPORT_FILE = _TOOL_ROOT / "report.html"

ASSIGNEES = ["henry-wicaksono", "delfianura", "denayaraha", "kevin-yauris"]

RAGO_PACKAGES = [
    "gllm-core", "gllm-inference", "gllm-generation",
    "gllm-datastore", "gllm-retrieval", "gllm-pipeline", "gllm-guardrail",
]

REGISTRY_URL = "https://glsdk.gdplabs.id/gen-ai-internal/simple/"

SKIP_PATTERNS = [
    "README.md", "migration-guide", "/legacy/", "troubleshooting",
    "whats-new.md", "evaluate-glchat-google-colab", "getting-started.md",
]

REQUIRED_FILES = [
    ".env.example", ".python-version", "pyproject.toml",
    "uv.lock", "setup.sh", "setup.bat", "README.md",
]

PENDING_REVIEW_STALE_DAYS = 7
MAX_VERIFY_ITERATIONS = 3
AUTH_REFRESH_EVERY_N = 10
