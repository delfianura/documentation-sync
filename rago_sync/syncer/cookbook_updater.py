"""Create and update cookbook entries from gitbook content."""
import re
from pathlib import Path

from ..config import COOKBOOK_REPO


def _extract_first_python_block(content: str) -> str:
    """Extract the first ```python ... ``` block from markdown content."""
    match = re.search(r"```python\n(.*?)```", content, re.DOTALL)
    return match.group(1) if match else ""


def extract_all_python_blocks(content: str) -> list[tuple[str | None, str]]:
    """Extract all ```python ... ``` blocks with their preceding heading.

    Returns list of (heading_text, code) pairs.
    """
    blocks: list[tuple[str | None, str]] = []
    # Split on headings to find context for each block
    parts = re.split(r"^(#{1,6}\s+.+)$", content, flags=re.MULTILINE)
    current_heading: str | None = None
    for i, part in enumerate(parts):
        if re.match(r"^#{1,6}\s+", part):
            current_heading = part.strip()
        for m in re.finditer(r"```python\n(.*?)```", part, re.DOTALL):
            code = m.group(1)
            blocks.append((current_heading, code))
    return blocks


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


# Map invoker class names to required package extras
_INVOKER_EXTRAS: dict[str, str] = {
    "OpenAILMInvoker": "openai",
    "OpenAIChatCompletionsLMInvoker": "openai",
    "OpenAIEMInvoker": "openai",
    "OpenAIRealtimeSession": "openai",
    "AnthropicLMInvoker": "anthropic",
    "GoogleLMInvoker": "google",
    "GoogleEMInvoker": "google",
    "ChromaDataStore": "chroma",
}

# Map package names to their available extras
_PKG_EXTRAS: dict[str, set[str]] = {
    "gllm-inference": {"openai", "anthropic", "google"},
    "gllm-datastore": {"chroma", "sql"},
}


def _detect_gllm_packages(code: str) -> list[str]:
    """Return gllm_* package names (with dashes) imported in code."""
    pkgs = set()
    for m in re.finditer(r'(?:from|import)\s+(gllm_\w+)', code):
        pkg_module = m.group(1)
        # convert gllm_inference -> gllm-inference
        pkgs.add(pkg_module.replace("_", "-"))
    return sorted(pkgs)


def _detect_required_extras(code: str) -> dict[str, list[str]]:
    """Detect package extras required by invoker class names in the code.

    Returns {package_name: [extra1, extra2, ...]}.
    """
    extras_map: dict[str, set[str]] = {}
    for class_name, extra in _INVOKER_EXTRAS.items():
        if class_name in code:
            for pkg, pkg_extras in _PKG_EXTRAS.items():
                if extra in pkg_extras:
                    extras_map.setdefault(pkg, set()).add(extra)
    return {pkg: sorted(extras) for pkg, extras in extras_map.items()}


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
        'echo "Setting up UV authentication..."\n'
        'export UV_INDEX_GEN_AI_INTERNAL_USERNAME=oauth2accesstoken\n'
        'export UV_INDEX_GEN_AI_INTERNAL_PASSWORD="$(gcloud auth print-access-token)"\n'
        '\n'
        'echo "Installing dependencies via UV..."\n'
        'uv lock\n'
        'uv sync\n'
        '\n'
        'echo "Setup completed successfully!"\n'
    )

    # setup.bat
    (entry_dir / "setup.bat").write_text(
        '@echo off\n'
        '\n'
        'REM Setup script for Windows systems\n'
        '\n'
        'echo Setting up UV authentication...\n'
        'set UV_INDEX_GEN_AI_INTERNAL_USERNAME=oauth2accesstoken\n'
        'for /f "delims=" %%i in (\'gcloud auth print-access-token\') do set UV_INDEX_GEN_AI_INTERNAL_PASSWORD=%%i\n'
        '\n'
        'echo Installing dependencies via UV...\n'
        'uv lock\n'
        'uv sync\n'
        '\n'
        'echo Setup completed successfully!\n'
    )

    # README.md
    (entry_dir / "README.md").write_text(
        f"# {entry_name}\n\nRun: uv run {script_file}\n"
    )

    # pyproject.toml
    gllm_pkgs = _detect_gllm_packages(script)
    extras_map = _detect_required_extras(script)
    _VERSIONS = {
        "gllm-core": ("0.3.0", "0.5.0"),
        "gllm-retrieval": ("0.5.0", "0.6.0"),
        "gllm-datastore": ("0.5.0", "0.6.0"),
        "gllm-inference": ("0.6.0", "0.7.0"),
    }
    def _version_lower(pkg: str) -> str:
        return _VERSIONS.get(pkg, ("0.6.0", "0.7.0"))[0]
    def _version_upper(pkg: str) -> str:
        return _VERSIONS.get(pkg, ("0.6.0", "0.7.0"))[1]
    # Build dependency lines with extras where needed
    dep_lines_list = []
    for pkg in gllm_pkgs:
        extras = extras_map.get(pkg, [])
        if extras:
            dep_lines_list.append(
                f'    "{pkg}[{",".join(extras)}]>={_version_lower(pkg)},<{_version_upper(pkg)}",'
            )
        else:
            dep_lines_list.append(
                f'    "{pkg}>={_version_lower(pkg)},<{_version_upper(pkg)}",'
            )
    dep_lines = "\n".join(dep_lines_list)
    source_lines = "\n".join(
        f'{pkg} = {{ index = "gen-ai-internal" }}' for pkg in gllm_pkgs
    )
    pyproject = f"""[project]
name = "{entry_name}"
version = "0.0.0"
description = "{entry_name} usage example"
requires-python = ">=3.11,<3.14"
readme = "README.md"
dependencies = [
{dep_lines}
]

[[tool.uv.index]]
name = "gen-ai-internal"
url = "https://glsdk.gdplabs.id/gen-ai-internal/simple/"

[tool.uv.sources]
{source_lines}
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
    """Overwrite existing .py script with code from gitbook content.

    For multi-block pages, writes one file per block using the heading as filename.
    Falls back to single-file overwrite for backward compatibility.
    """
    entry_dir = COOKBOOK_REPO / "gen-ai" / entry_path
    blocks = extract_all_python_blocks(gitbook_content)

    if not blocks:
        return False

    if len(blocks) == 1:
        script = blocks[0][1]
        existing = _find_script(entry_dir)
        if existing is None:
            return False
        existing.write_text(script)
        return True

    # Multi-block: write one file per block using heading-derived filename
    import re as _re
    entry_name = Path(entry_path).name
    wrote_any = False
    for heading, code in blocks:
        if heading:
            label = _re.sub(r"^#+\s+", "", heading)
            slug = _re.sub(r"[^a-zA-Z0-9]+", "_", label).lower().strip("_")
            filename = f"{entry_name}_{slug}.py"
        else:
            filename = f"{entry_name}.py" if not wrote_any else f"{entry_name}_block.py"
        (entry_dir / filename).write_text(code)
        wrote_any = True

    return wrote_any


def update_version_constraint(entry_path: str, package: str, new_version: str) -> bool:
    """Update pyproject.toml version constraint for package to >=new_version,<next_minor.

    Pins the lower bound to the exact `new_version` rather than rounding down to
    `X.Y.0`. Rounding down previously produced the *same* lower bound already
    satisfied by the stale pinned version (e.g. 0.6.1 -> floor 0.6.0, which a
    stale 0.6.1 already satisfies), so `uv lock` had no reason to re-resolve and
    silently kept the old version. Pinning the exact version forces the upgrade.
    """
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

    upper = _next_minor(_base_minor(new_version))
    new_constraint = f">={new_version},<{upper}"

    new_text = pattern.sub(
        lambda m: m.group(1) + new_constraint,
        text,
    )
    if new_text == text:
        return False
    pyproject_path.write_text(new_text)
    return True
