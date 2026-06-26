import re
from pathlib import Path
from ..config import COOKBOOK_REPO


def extract_code_blocks(markdown: str) -> list[str]:
    return re.findall(r"```python\n(.*?)```", markdown, re.DOTALL)


def normalize_code(code: str) -> str:
    lines = []
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        lines.append(stripped)
    return "\n".join(sorted(l for l in lines if l.startswith(("from ", "import "))) +
                     [l for l in lines if not l.startswith(("from ", "import "))])


def similarity_score(gitbook_code: str, cookbook_code: str) -> int:
    score = 0
    gb_imports = set(re.findall(r"^(?:from|import)\s+\S+", gitbook_code, re.MULTILINE))
    cb_imports = set(re.findall(r"^(?:from|import)\s+\S+", cookbook_code, re.MULTILINE))
    if gb_imports and gb_imports == cb_imports:
        score += 30
    elif gb_imports and gb_imports & cb_imports:
        score += 15

    gb_calls = set(re.findall(r"\w+\.(?:invoke|process|build|run|sync|get|create)\(", gitbook_code))
    cb_calls = set(re.findall(r"\w+\.(?:invoke|process|build|run|sync|get|create)\(", cookbook_code))
    if gb_calls and gb_calls == cb_calls:
        score += 40
    elif gb_calls and gb_calls & cb_calls:
        score += 20

    gb_envs = set(re.findall(r'["\']([A-Z_]{3,})["\']', gitbook_code))
    cb_envs = set(re.findall(r'["\']([A-Z_]{3,})["\']', cookbook_code))
    if gb_envs == cb_envs:
        score += 20

    if "asyncio.run" in gitbook_code and "asyncio.run" in cookbook_code:
        score += 10

    return score


def classify_drift(gitbook_code: str, cookbook_code: str) -> str:
    """Classify drift between gitbook and cookbook code.

    Returns: COMPLIANT | NEEDS_LLM_JUDGE | CONTENT_DRIFT | NO_GITBOOK_CODE
    """
    if not gitbook_code.strip():
        return "NO_GITBOOK_CODE"

    gb_norm = normalize_code(gitbook_code)
    cb_norm = normalize_code(cookbook_code)

    if gb_norm == cb_norm:
        return "COMPLIANT"

    score = similarity_score(gitbook_code, cookbook_code)
    if score >= 85:
        return "NEEDS_LLM_JUDGE"
    return "CONTENT_DRIFT"


def check_content_drift(entry_path: str, page_content: str) -> str:
    """Compare cookbook entry against gitbook page content."""
    blocks = extract_code_blocks(page_content)
    if not blocks:
        return "NO_GITBOOK_CODE"

    gitbook_code = "\n".join(blocks)

    py_files = [
        f for f in (COOKBOOK_REPO / "gen-ai" / entry_path).glob("*.py")
        if not f.name.startswith("_")
    ]
    if not py_files:
        return "CONTENT_DRIFT"

    cookbook_code = "\n".join(f.read_text() for f in py_files)
    return classify_drift(gitbook_code, cookbook_code)
