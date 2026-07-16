#!/usr/bin/env python3
"""Generate or update a codeblock-map.yaml from a cookbook checkout.

Discovers all .py files in a cookbook's gen-ai/tutorials/ (and optionally
gen-ai/how-to-guides/) directory tree, groups them by GitBook page URL,
and writes a YAML coverage map.

For .py files with docstrings referencing GitBook URLs, those URLs are used
directly (anchor stripped, grouped by page). For files without docstrings,
the entry gets a heuristic URL. Can also read the existing CSV mapping
(gitbook-to-cookbook-mapping.csv) to pre-fill GitBook URLs.

Usage:
    python3 generate_map.py --cookbook-root /path/to/gen-ai-sdk-cookbook
                           [--map codeblock-map.yaml]
                           [--csv gitbook-to-cookbook-mapping.csv]
                           [--scope core]
                           [--include-how-to-guides]
                           [--merge-existing]

Exit code 0 = map written successfully.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML not installed. Install with: pip install pyyaml")
    sys.exit(2)


SKILL_DIR = Path(__file__).parent.parent
DEFAULT_MAP = SKILL_DIR / "references" / "codeblock-map.yaml"
GITBOOK_BASE = "https://gdplabs.gitbook.io/sdk"

URL_RE = re.compile(r"https?://gdplabs\.gitbook\.io/sdk/[^\s\"']+")


def find_py_files(cookbook_root: Path, scope: str | None, include_how_to: bool) -> list[Path]:
    results: list[Path] = []
    search_dirs: list[Path] = []

    tutorials = cookbook_root / "gen-ai" / "tutorials"
    if tutorials.exists():
        if scope:
            if scope.startswith("tutorials/"):
                scope_path = scope[len("tutorials/"):]
            else:
                scope_path = scope
            scoped = tutorials / scope_path
            if scoped.exists():
                search_dirs.append(scoped)
        else:
            search_dirs.append(tutorials)

    if include_how_to:
        how_to = cookbook_root / "gen-ai" / "how-to-guides"
        if how_to.exists():
            search_dirs.append(how_to)

    for d in search_dirs:
        for p in d.rglob("*.py"):
            if ".venv" in p.parts or "__pycache__" in p.parts:
                continue
            results.append(p)
    return sorted(results)


def strip_anchor(url: str) -> str:
    idx = url.find("#")
    return url[:idx] if idx >= 0 else url


def extract_gitbook_url(filepath: Path) -> str | None:
    try:
        content = filepath.read_text()
    except Exception:
        return None
    match = URL_RE.search(content)
    if match:
        return match.group(0).rstrip(")\"',;]")
    return None


def file_to_entry_dir(filepath: Path, cookbook_root: Path) -> str:
    rel = filepath.relative_to(cookbook_root / "gen-ai")
    return str(Path(*rel.parts[:-1]))


def load_csv_mapping(csv_path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not csv_path or not csv_path.exists():
        return mapping
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            cb_path = row.get("Cookbook Path", "").strip().rstrip("/")
            gt_path = row.get("GitBook Path", "").strip()
            if cb_path and gt_path:
                mapping[cb_path] = gt_path
    return mapping


def csv_path_to_url(gitbook_rel_path: str) -> str:
    if not gitbook_rel_path:
        return ""
    path = gitbook_rel_path
    if path.endswith(".md"):
        path = path[:-3]
    if path.startswith("guides/"):
        path = "how-to-guides/" + path[len("guides/"):]
    return f"{GITBOOK_BASE}/{path}"


def heuristic_url(entry_dir: str) -> str:
    if entry_dir.startswith("tutorials/"):
        return f"{GITBOOK_BASE}/gen-ai-sdk/{entry_dir}"
    return f"{GITBOOK_BASE}/{entry_dir}"


def generate_map(
    cookbook_root: Path,
    scope: str | None,
    include_how_to: bool,
    csv_path: Path | None,
) -> dict:
    """Generate coverage map grouped by GitBook page URL (anchors stripped)."""
    py_files = find_py_files(cookbook_root, scope, include_how_to)
    if not py_files:
        print("No .py files found")
        return {}

    csv_mapping = load_csv_mapping(csv_path) if csv_path else {}

    # Determine page URL for each file
    file_to_url: dict[Path, str] = {}
    for f in py_files:
        url = extract_gitbook_url(f)
        if url:
            file_to_url[f] = strip_anchor(url)
        else:
            entry_dir = file_to_entry_dir(f, cookbook_root)
            found = False
            if entry_dir in csv_mapping:
                file_to_url[f] = csv_path_to_url(csv_mapping[entry_dir])
                found = True
            else:
                for k, v in csv_mapping.items():
                    if k.rstrip("/") == entry_dir.rstrip("/"):
                        file_to_url[f] = csv_path_to_url(v)
                        found = True
                        break
            if not found:
                file_to_url[f] = heuristic_url(entry_dir)

    # Group by page URL
    url_to_files: dict[str, list[Path]] = defaultdict(list)
    for f in py_files:
        url_to_files[file_to_url[f]].append(f)

    coverage_map: dict[str, dict] = {}
    for page_url, files in sorted(url_to_files.items()):
        entry_dirs = {file_to_entry_dir(f, cookbook_root) for f in files}
        entry_dir = sorted(entry_dirs)[0]

        blocks = []
        for f in sorted(files):
            blocks.append({
                "heading": "",
                "gitbook_anchor": "",
                "cookbook_file": f.name,
                "runnable": True,
                "notes": "",
            })

        if page_url in coverage_map:
            existing = {b["cookbook_file"] for b in coverage_map[page_url]["blocks"]}
            for b in blocks:
                if b["cookbook_file"] not in existing:
                    coverage_map[page_url]["blocks"].append(b)
        else:
            coverage_map[page_url] = {"entry_dir": entry_dir, "blocks": blocks}

    return coverage_map


def merge_maps(existing: dict, generated: dict) -> dict:
    merged: dict[str, dict] = {}
    all_keys = set(existing.keys()) | set(generated.keys())

    for key in sorted(all_keys):
        if key in existing and key in generated:
            ex_by_file = {b["cookbook_file"]: b for b in existing[key]["blocks"]}
            gen_by_file = {b["cookbook_file"]: b for b in generated[key]["blocks"]}
            merged_blocks = []
            for f in sorted(set(ex_by_file) | set(gen_by_file)):
                merged_blocks.append(ex_by_file.get(f, gen_by_file[f]))
            merged[key] = {
                "entry_dir": existing[key].get("entry_dir", generated[key]["entry_dir"]),
                "blocks": merged_blocks,
            }
        elif key in existing:
            merged[key] = existing[key]
        else:
            merged[key] = generated[key]

    return merged


def dump_yaml(data: dict, path: Path, cookbook_root: str):
    header = (
        "# Codeblock Coverage Map\n"
        "# Auto-generated by generate_map.py. Edit manually to add headings,\n"
        "# anchors, and notes. Re-run with --merge-existing to preserve edits.\n"
        "#\n"
        f"# Cookbook root: {cookbook_root}\n"
        f"# Generated: {datetime.datetime.now().isoformat()}\n"
    )
    body = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    path.write_text(header + "\n" + body + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generate codeblock coverage map")
    parser.add_argument("--cookbook-root", type=Path, required=True, help="Path to gen-ai-sdk-cookbook checkout")
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP, help="Output YAML map path")
    parser.add_argument("--csv", type=Path, default=None, help="CSV mapping file for URL lookup")
    parser.add_argument("--scope", type=str, default=None, help="Limit to scope (e.g., core, inference)")
    parser.add_argument("--include-how-to-guides", action="store_true", help="Also scan how-to-guides/")
    parser.add_argument("--merge-existing", action="store_true", help="Merge with existing map, preserving edits")
    args = parser.parse_args()

    scope = args.scope
    if scope and not scope.startswith("tutorials/") and not scope.startswith("how-to-guides/"):
        scope = f"tutorials/{scope}"

    existing_map: dict = {}
    if args.merge_existing and args.map.exists():
        with open(args.map) as f:
            existing_map = yaml.safe_load(f) or {}

    generated = generate_map(args.cookbook_root, scope, args.include_how_to_guides, args.csv)

    if args.merge_existing and existing_map:
        final = merge_maps(existing_map, generated)
    else:
        final = generated

    if not final:
        print("WARNING: generated map is empty")
        sys.exit(1)

    dump_yaml(final, args.map, str(args.cookbook_root))

    total_blocks = sum(len(p["blocks"]) for p in final.values())
    print(f"Generated coverage map: {args.map}")
    print(f"  GitBook pages: {len(final)}")
    print(f"  Code blocks: {total_blocks}")
    print(f"  Cookbook root: {args.cookbook_root}")
    if scope:
        print(f"  Scope: {scope}")
    print(f"  Merge: {'yes' if args.merge_existing and existing_map else 'no'}")


if __name__ == "__main__":
    main()