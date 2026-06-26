import subprocess
from ..config import GL_SDK_REPO, COOKBOOK_REPO, GITBOOK_BRANCH, SKIP_PATTERNS


def list_gitbook_pages() -> list[str]:
    """List all gitbook .md paths (relative to gitbook/gen-ai-sdk/) excluding skips."""
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", GITBOOK_BRANCH],
        cwd=GL_SDK_REPO, capture_output=True, text=True, check=True,
    )
    pages = []
    for line in result.stdout.splitlines():
        if not line.startswith("gitbook/gen-ai-sdk/"):
            continue
        if not line.endswith(".md"):
            continue
        if any(pat in line for pat in SKIP_PATTERNS):
            continue
        rel = line.removeprefix("gitbook/gen-ai-sdk/")
        pages.append(rel)
    return pages


def get_page_content(gitbook_rel: str) -> str:
    """Fetch raw content of a gitbook page from the branch."""
    result = subprocess.run(
        ["git", "show", f"{GITBOOK_BRANCH}:gitbook/gen-ai-sdk/{gitbook_rel}"],
        cwd=GL_SDK_REPO, capture_output=True, text=True,
    )
    return result.stdout if result.returncode == 0 else ""


def has_gllm_imports(content: str) -> bool:
    """Return True if the content has any gllm_* imports."""
    return "from gllm" in content or "import gllm" in content


def list_cookbook_entries() -> list[str]:
    """List all cookbook entry paths relative to gen-ai/."""
    entries = []
    for p in (COOKBOOK_REPO / "gen-ai").rglob("pyproject.toml"):
        if ".venv" in p.parts:
            continue
        rel = str(p.parent.relative_to(COOKBOOK_REPO / "gen-ai"))
        entries.append(rel)
    return sorted(entries)


def gitbook_to_cookbook_path(gitbook_rel: str) -> str:
    """Map gitbook relative path to cookbook entry path.

    tutorials/inference/lm-invoker/README.md  ->  tutorials/inference/lm_invoker
    guides/build-end-to-end-rag-pipeline/...  ->  how-to-guides/build_end_to_end_rag_pipeline/...
    """
    path = gitbook_rel.replace("-", "_")
    path = path.removesuffix(".md").removesuffix("/README")
    if path.startswith("guides/"):
        path = "how-to-guides/" + path[len("guides/"):]
    return path
