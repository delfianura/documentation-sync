#!/bin/bash
# verify_cross_package_imports.sh
# Probes installed gllm-* packages for cross-package import breaks.
# Run after uv sync and after any version-bump.
#
# Usage: bash verify_cross_package_imports.sh <venv_dir>
#   <venv_dir> defaults to .venv if omitted.

set -euo pipefail

VENV_DIR="${1:-.venv}"
PYTHON="$VENV_DIR/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "FAIL: Python not found at $PYTHON"
  exit 1
fi

echo "=== Cross-package import probe ==="
echo "Python: $("$PYTHON" -c 'import sys; print(sys.version)')"

IMP_PROBE='import sys; failed=[];
try: import gllm_pipeline.pipeline.pipeline as _p;
except Exception as e: failed.append(f"gllm_pipeline.pipeline: {e}");
try: import gllm_pipeline.steps._func as _s;
except Exception as e: failed.append(f"gllm_pipeline.steps._func: {e}");
try: from gllm_core.concurrency import parallel_gather as _g;
except Exception as e: failed.append(f"gllm_core.concurrency.parallel_gather: {e}");
if failed:
    for f in failed: print(f"FAIL: {f}");
    sys.exit(1);
else:
    print("OK: all cross-package imports resolved")'

rc=0
"$PYTHON" -c "$IMP_PROBE" 2>&1 || rc=$?

if [ $rc -ne 0 ]; then
  echo ""
  echo "HINT: This is a GL SDK publishing issue, not a cookbook bug."
  echo "  1. Check https://github.com/GDP-ADMIN/gl-sdk/issues for existing reports."
  echo "  2. If new, file an issue with the ImportError traceback and installed versions:"
  echo "     $PYTHON -c \"import gllm_pipeline, gllm_core; print(gllm_pipeline.__version__ if hasattr(gllm_pipeline,'__version__') else 'unknown', gllm_core.__version__ if hasattr(gllm_core,'__version__') else 'unknown')\""
  echo "  3. Mark the affected cookbook entry BLOCKED_ON_INFRA until the fix releases."
  exit 1
fi

echo "=== Version check ==="
"$PYTHON" -c "
import sys
versions = {}
for mod in ['gllm_core', 'gllm_pipeline', 'gllm_inference', 'gllm_datastore']:
    try:
        m = __import__(mod)
        v = getattr(m, '__version__', 'unknown')
    except Exception:
        v = 'IMPORT_FAILED'
    versions[mod] = v
for k,v in versions.items():
    print(f'  {k}: {v}')
" 2>&1

exit 0
