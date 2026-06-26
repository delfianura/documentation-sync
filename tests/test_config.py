from pathlib import Path
from rago_sync.config import (
    GL_SDK_REPO, COOKBOOK_REPO, GITBOOK_BRANCH, STATUS_FILE,
    ASSIGNEES, RAGO_PACKAGES, REQUIRED_FILES, SKIP_PATTERNS,
    PENDING_REVIEW_STALE_DAYS, MAX_VERIFY_ITERATIONS
)

def test_repo_paths_are_paths():
    assert isinstance(GL_SDK_REPO, Path)
    assert isinstance(COOKBOOK_REPO, Path)
    assert isinstance(STATUS_FILE, Path)

def test_gitbook_branch():
    assert GITBOOK_BRANCH == "origin/docs/gitbook-sync"

def test_assignees():
    assert set(ASSIGNEES) == {"henry-wicaksono", "delfianura", "denayaraha", "kevin-yauris"}

def test_rago_packages_complete():
    expected = {"gllm-core", "gllm-inference", "gllm-generation",
                "gllm-datastore", "gllm-retrieval", "gllm-pipeline", "gllm-guardrail"}
    assert set(RAGO_PACKAGES) == expected

def test_required_files():
    assert set(REQUIRED_FILES) == {
        ".env.example", ".python-version", "pyproject.toml",
        "uv.lock", "setup.sh", "setup.bat", "README.md"
    }

def test_stale_days():
    assert PENDING_REVIEW_STALE_DAYS == 7

def test_max_verify_iterations():
    assert MAX_VERIFY_ITERATIONS == 3
