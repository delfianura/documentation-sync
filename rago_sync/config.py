from pathlib import Path

GL_SDK_REPO = Path("/home/delfia-n-a-putri/Documents/Work/GEN_AI/gl-sdk")
COOKBOOK_REPO = Path("/home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook")
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
