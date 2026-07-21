#!/usr/bin/env python3
"""Verify cookbook scripts have no module-level side effects.

Checks .py files under a root directory for AST-level anti-patterns that
reviewers flag on PRs:

1. ``os.environ[...] = ...`` at module top level
2. ``logging.FileHandler(...)`` or ``logging.basicConfig(...)`` at module top level
3. ``async def main()`` at module top level combined with an un-aliased
   ``from gllm_core.schema import main`` decorator import (shadowing risk —
   see PR #77 review)

Exit 0 = clean, exit 1 = issues found (printed to stdout).
"""
import argparse
import ast
import pathlib
import sys


def iter_python_files(root: pathlib.Path) -> list[pathlib.Path]:
    return sorted(root.rglob("*.py"))


def module_level_os_environ_assign(tree: ast.AST) -> bool:
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Attribute)
                    and isinstance(target.value.value, ast.Name)
                    and target.value.value.id == "os"
                    and target.value.attr == "environ"
                ):
                    return True
    return False


def module_level_logging_call(tree: ast.AST, names: tuple[str, ...]) -> bool:
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            func = call.func
            if isinstance(func, ast.Attribute) and func.attr in names:
                if isinstance(func.value, ast.Name) and func.value.id == "logging":
                    return True
    return False


def module_level_async_main(tree: ast.AST) -> bool:
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "main":
            return True
    return False


def has_import_main_from_schema(tree: ast.AST) -> bool:
    for node in ast.iter_child_nodes(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "gllm_core.schema"
            and any(a.name == "main" and a.asname is None for a in node.names)
        ):
            return True
    return False


def check_file(path: pathlib.Path, check_shadow: bool = False) -> list[str]:
    issues: list[str] = []
    try:
        source = path.read_text()
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"syntax error: {exc}"]

    if module_level_os_environ_assign(tree):
        issues.append("os.environ[...] = ... at module top level")

    if module_level_logging_call(tree, ("FileHandler", "basicConfig")):
        issues.append("logging.FileHandler / basicConfig at module top level")

    if check_shadow and module_level_async_main(tree) and has_import_main_from_schema(tree):
        issues.append(
            "import main without alias + async def main() in same module "
            "(decorator shadowed by entrypoint function)"
        )

    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="Detect import-time side-effect anti-patterns in cookbook scripts")
    ap.add_argument("root", type=pathlib.Path, help="Root directory to scan")
    ap.add_argument("--check-import-shadow", action="store_true",
                    help="Also flag cases where an un-aliased 'main' decorator import is shadowed by a module-level main()")
    args = ap.parse_args()

    files = [p for p in iter_python_files(args.root) if p.name != "__init__.py"]
    if not files:
        print("No .py files found.")
        return 0

    bad = 0
    for path in files:
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue

        issues = check_file(path, check_shadow=args.check_import_shadow)

        if issues:
            bad += 1
            rel = path.relative_to(args.root)
            for issue in issues:
                print(f"  {rel}: {issue}")

    if bad:
        print(f"\nIssues in {bad} file(s)")
        return 1
    print("All files clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
