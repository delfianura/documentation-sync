from ..config import COOKBOOK_REPO, REQUIRED_FILES


def check_template(entry_path: str) -> list[str]:
    """Returns list of missing required files. Empty list = template compliant."""
    base = COOKBOOK_REPO / "gen-ai" / entry_path

    return [f for f in REQUIRED_FILES if not (base / f).exists()]
