import re
import subprocess
from pathlib import Path
from ..config import GL_SDK_REPO, COOKBOOK_REPO, GITBOOK_BRANCH, SKIP_PATTERNS


def _slug(s: str) -> str:
    return s.lower().replace("-", "_").replace(" ", "_")


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

    Simple fallback: replace hyphens, guides/ → how-to-guides/.
    Does NOT handle numeric prefixes — use find_best_cookbook_match() for that.
    """
    path = gitbook_rel.replace("-", "_")
    path = path.removesuffix(".md").removesuffix("/README")
    if path.startswith("guides/"):
        path = "how-to-guides/" + path[len("guides/"):]
    return path


def find_best_cookbook_match(gitbook_rel: str, cookbook_entries: set[str]) -> str | None:
    """Robustly match a GitBook page to its cookbook entry.

    Handles:
    - Numeric prefixes in cookbook paths (001_your_first_rag_pipeline)
    - guides/ → how-to-guides/ section mapping
    - Hyphen-to-underscore normalization
    - Subdirectory equivalence checks

    Returns the exact cookbook entry path, or None if no match found.
    """
    gb = gitbook_rel.removesuffix(".md").removesuffix("/README")
    gb_section = gb.split("/")[0]
    target_section = "how-to-guides" if gb_section == "guides" else "tutorials"

    gb_parts = gb.split("/")
    gb_last = _slug(gb_parts[-1])
    gb_subdir = "/".join(gb_parts[1:-1]) if len(gb_parts) > 2 else ""

    best: str | None = None
    for cb in cookbook_entries:
        cb_parts = cb.split("/")
        if cb_parts[0] != target_section:
            continue
        cb_last_clean = re.sub(r"^\d+_", "", cb_parts[-1])
        if _slug(cb_last_clean) != gb_last:
            continue
        cb_subdir = "/".join(cb_parts[1:-1]) if len(cb_parts) > 2 else ""
        if _slug(gb_subdir) == _slug(cb_subdir):
            best = cb
            break

    return best
