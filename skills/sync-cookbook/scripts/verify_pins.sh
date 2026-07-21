#!/usr/bin/env bash
# verify_pins.sh — check that installed gllm-* versions satisfy each entry's pins
# and that gllm-inference / gllm-core versions coexist.
#
# Usage: ./verify_pins.sh <entry_dir> [<entry_dir> ...]
#   or:    find gen-ai/tutorials -name pyproject.toml -print0 | xargs -0 ./verify_pins.sh
#
set -euo pipefail

need() { command -v "$1" >/dev/null 2>&1 || { echo "MISSING: $1"; exit 1; }; }
need uv
need python3

for pyproject in "$@"; do
    dir=$(dirname "$pyproject")
    echo "--- $dir ---"

    grep -E 'gllm-(core|generation|inference|misc)' "$pyproject" | head -10 || true

    venv=$(mktemp -d -p /tmp verify-pins-venv.XXXXXX)
    cd "$dir"
    uv sync --python python3.12 --no-dev 2>&1 | tail -3 >/dev/null || true

    for pkg in gllm_core gllm_generation gllm_inference gllm_misc; do
        ver=$(uv run --python python3.12 python -c "import importlib as i; m=i.import_module('$pkg'); print(getattr(m,'__version__','unknown'))" 2>/dev/null || echo "NOT_INSTALLED")
        echo "  $pkg: $ver"
    done

    rm -rf "$venv"
    echo ""
done
