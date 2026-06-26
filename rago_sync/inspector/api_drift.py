import re
import subprocess
from ..config import GL_SDK_REPO


def extract_gllm_identifiers(code: str) -> list[str]:
    """Extract class/function names imported from gllm_* packages."""
    identifiers = []
    for line in code.splitlines():
        if "from gllm" in line:
            match = re.search(r"import\s+(.+)$", line)
            if match:
                names = [n.strip().split(" as ")[0] for n in match.group(1).split(",")]
                identifiers.extend(names)
    return list(set(identifiers))


def is_stale_import(identifier: str, removed_set: set[str]) -> bool:
    return identifier in removed_set


def identifier_in_main(identifier: str) -> bool:
    """Check if identifier exists in gl-sdk main (HEAD) libs/."""
    result = subprocess.run(
        ["git", "grep", "-r", "--quiet", identifier, "HEAD", "--", "libs/"],
        cwd=GL_SDK_REPO, capture_output=True,
    )
    return result.returncode == 0


def check_api_drift(page_content: str) -> list[str]:
    """Returns list of identifiers from gitbook page that don't exist in gl-sdk main.

    Empty list = no API drift detected.
    """
    code_blocks = re.findall(r"```python\n(.*?)```", page_content, re.DOTALL)
    all_code = "\n".join(code_blocks)
    identifiers = extract_gllm_identifiers(all_code)
    return [ident for ident in identifiers
            if len(ident) >= 4 and not identifier_in_main(ident)]
