"""Create and update cookbook entries from gitbook content."""
import re
from pathlib import Path

from ..config import COOKBOOK_REPO


def _extract_first_python_block(content: str) -> str:
    """Extract the first ```python ... ``` block from markdown content."""
    match = re.search(r"```python\n(.*?)```", content, re.DOTALL)
    return match.group(1) if match else ""


def _extract_env_vars(code: str) -> list[str]:
    """Extract environment variable names from code."""
    vars_ = set()
    for m in re.finditer(r'os\.environ\[[\'"]([\w]+)[\'"]\]', code):
        vars_.add(m.group(1))
    for m in re.finditer(r'os\.environ\.get\([\'"]([\w]+)[\'"]', code):
        vars_.add(m.group(1))
    # load_dotenv-style: just scan for any ALL_CAPS = os.getenv patterns
    for m in re.finditer(r'os\.getenv\([\'"]([\w]+)[\'"]', code):
        vars_.add(m.group(1))
    return sorted(vars_)


def _detect_gllm_packages(code: str) -> list[str]:
    """Return gllm_* package names (with dashes) imported in code."""
    pkgs = set()
    for m in re.finditer(r'(?:from|import)\s+(gllm_\w+)', code):
        pkg_module = m.group(1)
        # convert gllm_inference -> gllm-inference
        pkgs.add(pkg_module.replace("_", "-"))
    return sorted(pkgs)


def _next_minor(version: str) -> str:
    """0.6.1 -> 0.7.0, 1.2.3 -> 1.3.0"""
    parts = version.split(".")
    if len(parts) >= 2:
        parts[1] = str(int(parts[1]) + 1)
        if len(parts) >= 3:
            parts[2] = "0"
    return ".".join(parts)


def _base_minor(version: str) -> str:
    """0.6.1 -> 0.6.0"""
    parts = version.split(".")
    if len(parts) >= 3:
        parts[2] = "0"
    return ".".join(parts)


def create_entry(entry_path: str, gitbook_content: str) -> bool:
    """Create the full 7-file cookbook entry structure."""
    entry_dir = COOKBOOK_REPO / "gen-ai" / entry_path
    entry_dir.mkdir(parents=True, exist_ok=True)

    script = _extract_first_python_block(gitbook_content)
    if not script:
        return False

    entry_name = Path(entry_path).name
    script_file = entry_name + ".py"

    # Write script
    (entry_dir / script_file).write_text(script)

    # .env.example
    env_vars = _extract_env_vars(script)
    env_lines = "\n".join(f"{v}=" for v in env_vars)
    (entry_dir / ".env.example").write_text(env_lines + "\n" if env_lines else "")

    # .python-version
    (entry_dir / ".python-version").write_text("3.12\n")

    # setup.sh
    (entry_dir / "setup.sh").write_text(
        "#!/bin/bash\nuv sync\n"
    )

    # setup.bat
    (entry_dir / "setup.bat").write_text(
        "@echo off\nuv sync\n"
    )

    # README.md
    (entry_dir / "README.md").write_text(
        f"# {entry_name}\n\nRun: uv run {script_file}\n"
    )

    # pyproject.toml
    gllm_pkgs = _detect_gllm_packages(script)
    dep_lines = "\n".join(
        f'    "{pkg}>=0.6.0,<0.7.0",' for pkg in gllm_pkgs
    )
    pyproject = f"""[project]
name = "{entry_name}"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
{dep_lines}
]
"""
    (entry_dir / "pyproject.toml").write_text(pyproject)

    return True


def _find_script(entry_dir: Path) -> Path | None:
    """Find the main .py script (exclude _-prefixed)."""
    for p in entry_dir.glob("*.py"):
        if not p.name.startswith("_"):
            return p
    return None


def overwrite_script(entry_path: str, gitbook_content: str) -> bool:
    """Overwrite existing .py script with first Python block from gitbook content."""
    entry_dir = COOKBOOK_REPO / "gen-ai" / entry_path
    script = _extract_first_python_block(gitbook_content)
    if not script:
        return False
    existing = _find_script(entry_dir)
    if existing is None:
        return False
    existing.write_text(script)
    return True


def update_version_constraint(entry_path: str, package: str, new_version: str) -> bool:
    """Update pyproject.toml version constraint for package to >=base_minor,<next_minor."""
    pyproject_path = COOKBOOK_REPO / "gen-ai" / entry_path / "pyproject.toml"
    if not pyproject_path.exists():
        return False
    text = pyproject_path.read_text()

    # Match: "package>=X.Y.Z,<A.B.C" or "package>=X.Y,<A.B"
    pattern = re.compile(
        r'("' + re.escape(package) + r'")([>=<,\d.]+)',
    )
    if not pattern.search(text):
        return False

    base = _base_minor(new_version)
    upper = _next_minor(base)
    new_constraint = f">={base},<{upper}"

    new_text = pattern.sub(
        lambda m: m.group(1) + new_constraint,
        text,
    )
    if new_text == text:
        return False
    pyproject_path.write_text(new_text)
    return True
