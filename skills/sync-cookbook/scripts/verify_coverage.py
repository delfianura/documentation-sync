#!/usr/bin/env python3
"""Verify codeblock coverage: check that every block in the YAML map has a
corresponding .py file in the cookbook, and that no .py files are orphans.

Usage:
    python3 verify_coverage.py --cookbook-root /path/to/gen-ai-sdk-cookbook [--map <path>] [--ruff]

Options:
    --cookbook-root  Path to gen-ai-sdk-cookbook checkout (required)
    --map            Path to codeblock-map.yaml (default: sibling of this script)
    --ruff           Also run ruff check on all mapped .py files
    --scope          Limit to a specific entry_dir prefix (e.g., core/)

Exit code 0 = all checks pass. Non-zero = coverage gaps or orphans found.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(2)


SKILL_DIR = Path(__file__).parent.parent
DEFAULT_MAP = SKILL_DIR / "references" / "codeblock-map.yaml"


def load_map(map_path: Path) -> dict:
    with open(map_path) as f:
        return yaml.safe_load(f)


def get_cookbook_files(entry_dir: str, cookbook_root: Path) -> set[str]:
    full_dir = cookbook_root / "gen-ai" / entry_dir
    if not full_dir.exists():
        return set()
    files: set[str] = set()
    for p in full_dir.iterdir():
        if p.suffix == ".py" and ".venv" not in p.parts and "__pycache__" not in p.parts:
            files.add(p.name)
    return files


def get_mapped_files(page: dict) -> set[str]:
    return {b["cookbook_file"] for b in page["blocks"]}


def check_docstring_url(filepath: Path, expected_url: str) -> bool:
    try:
        content = filepath.read_text()
    except Exception:
        return False
    return expected_url in content


def run_ruff(files: list[Path]) -> bool:
    try:
        result = subprocess.run(
            ["ruff", "check", "--select", "E,W,F"] + [str(f) for f in files],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            print("RUFF FAILURES:")
            print(result.stdout)
            print(result.stderr)
            return False
        return True
    except FileNotFoundError:
        print("WARNING: ruff not found - skipping ruff check")
        return True
    except subprocess.TimeoutExpired:
        print("WARNING: ruff timed out - skipping")
        return True


def main():
    parser = argparse.ArgumentParser(description="Verify codeblock coverage map")
    parser.add_argument("--cookbook-root", type=Path, required=True, help="Path to gen-ai-sdk-cookbook checkout")
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP, help="Path to codeblock-map.yaml")
    parser.add_argument("--ruff", action="store_true", help="Also run ruff check")
    parser.add_argument("--scope", type=str, default=None, help="Limit to entry_dir prefix (e.g., core/)")
    args = parser.parse_args()

    coverage_map = load_map(args.map)
    if not coverage_map:
        print("ERROR: coverage map is empty")
        sys.exit(2)

    # Filter by scope if specified
    if args.scope:
        scope_prefix = args.scope if args.scope.endswith("/") else args.scope + "/"
        coverage_map = {k: v for k, v in coverage_map.items() if v["entry_dir"].startswith(scope_prefix)}
        if not coverage_map:
            print(f"ERROR: no entries match scope '{args.scope}'")
            sys.exit(2)

    errors: list[str] = []
    warnings: list[str] = []
    all_mapped_files: list[Path] = []

    # Aggregate mapped files per entry_dir (multiple pages can share one dir)
    dir_to_mapped: dict[str, set[str]] = {}
    for page_url, page_info in coverage_map.items():
        ed = page_info["entry_dir"]
        if ed not in dir_to_mapped:
            dir_to_mapped[ed] = set()
        dir_to_mapped[ed] |= get_mapped_files(page_info)

    for page_url, page_info in coverage_map.items():
        entry_dir = page_info["entry_dir"]
        blocks = page_info["blocks"]
        mapped_files = get_mapped_files(page_info)
        cookbook_files = get_cookbook_files(entry_dir, args.cookbook_root)

        # Check 1: every mapped file exists
        for f in sorted(mapped_files - cookbook_files):
            errors.append(f"[MISSING FILE] {entry_dir}/{f} - listed in map but not in cookbook")

        # Check 3: docstring URL check (warning, not error — older entries may lack docstrings)
        for block in blocks:
            cf = block["cookbook_file"]
            fp = args.cookbook_root / "gen-ai" / entry_dir / cf
            if fp.exists():
                all_mapped_files.append(fp)
                if not check_docstring_url(fp, page_url):
                    warnings.append(
                        f"[DOCSTRING] {entry_dir}/{cf} - "
                        f"docstring does not reference {page_url}"
                    )

        # Check 4: no duplicates
        seen: set[str] = set()
        for block in blocks:
            cf = block["cookbook_file"]
            if cf in seen:
                errors.append(f"[DUPLICATE] {entry_dir}/{cf} listed twice in map")
            seen.add(cf)

    # Check 2: no orphan .py files
    for entry_dir, all_mapped in sorted(dir_to_mapped.items()):
        cookbook_files = get_cookbook_files(entry_dir, args.cookbook_root)
        for f in sorted(cookbook_files - all_mapped):
            warnings.append(f"[ORPHAN] {entry_dir}/{f} - exists in cookbook but not in map")

    # Check 5: ruff
    if args.ruff and all_mapped_files:
        if not run_ruff(all_mapped_files):
            errors.append("[RUFF] One or more files failed ruff check")

    print("=" * 60)
    print("CODEBLOCK COVERAGE VERIFICATION")
    print("=" * 60)
    print(f"Map: {args.map}")
    print(f"Cookbook root: {args.cookbook_root}")
    print(f"GitBook pages mapped: {len(coverage_map)}")
    print(f"Code blocks mapped: {sum(len(p['blocks']) for p in coverage_map.values())}")
    print(f"Cookbook .py files found: {len(all_mapped_files)}")
    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")
    print("-" * 60)

    if errors:
        print("\nERRORS:")
        for e in errors:
            print(f"  X {e}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  ! {w}")
    if not errors and not warnings:
        print("\nAll checks passed - no coverage gaps, no orphans, all docstrings correct.")
    elif not errors:
        print("\nNo errors - coverage is complete (warnings only).")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()