import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from ..config import COOKBOOK_REPO, MAX_VERIFY_ITERATIONS


@dataclass
class VerifyResult:
    passed: bool
    output: str
    iterations: int
    error: str = ""
    failure_category: str = ""


def _parse_failure_category(output: str) -> str:
    if "ImportError" in output or "cannot import name" in output:
        return "IMPORT_ERROR"
    if "ModuleNotFoundError" in output:
        return "MODULE_NOT_FOUND"
    if "AuthenticationError" in output or "401" in output:
        return "AUTH_ERROR"
    if "TypeError" in output and "argument" in output:
        return "SIGNATURE_ERROR"
    return "UNKNOWN"


def _find_script(entry_path: str) -> Path | None:
    base = COOKBOOK_REPO / "gen-ai" / entry_path
    scripts = [f for f in base.glob("*.py") if not f.name.startswith("_")]
    return scripts[0] if scripts else None


def _run_script(script: Path, cwd: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["uv", "run", script.name],
        cwd=cwd, capture_output=True, text=True, timeout=120,
    )
    output = result.stdout + result.stderr
    return result.returncode == 0, output


def verify_entry(entry_path: str) -> VerifyResult:
    """Run cookbook entry script with up to MAX_VERIFY_ITERATIONS debug attempts."""
    script = _find_script(entry_path)
    if script is None:
        return VerifyResult(passed=False, output="No .py script found", iterations=0,
                             failure_category="NO_SCRIPT")

    cwd = COOKBOOK_REPO / "gen-ai" / entry_path
    last_output = ""

    for i in range(1, MAX_VERIFY_ITERATIONS + 1):
        passed, output = _run_script(script, cwd)
        last_output = output
        if passed:
            return VerifyResult(passed=True, output=output, iterations=i)

        category = _parse_failure_category(output)
        if i == 1 and category in ("MODULE_NOT_FOUND", "IMPORT_ERROR"):
            subprocess.run(["uv", "sync"], cwd=cwd, capture_output=True)

    return VerifyResult(
        passed=False, output=last_output, iterations=MAX_VERIFY_ITERATIONS,
        failure_category=_parse_failure_category(last_output),
    )
