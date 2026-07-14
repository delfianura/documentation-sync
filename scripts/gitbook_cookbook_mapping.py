"""Generate clean 1-1 mapping markdown file with gap/drift analysis."""
import os, re, json
from pathlib import Path

GITBOOK = Path("/home/delfia-n-a-putri/Documents/Work/GEN_AI/dev5/gitbook/gen-ai-sdk")
COOKBOOK = Path("/home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook/gen-ai")
SKIP_DIRS = {'.git', '__pycache__', '.github', 'node_modules', '.venv', '.mypy_cache', '.pytest_cache', '.venv_build'}

def slug(s):
    return s.lower().replace('-', '_').replace(' ', '_')

def read_file(p):
    try: return p.read_text(encoding='utf-8', errors='replace')
    except: return ''

def get_last_part(path):
    return path.rstrip('/').split('/')[-1]

# ── Collect GitBook pages ──
gitbook = {}
for root, dirs, files in os.walk(GITBOOK):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
    rel = Path(root).relative_to(GITBOOK)
    for f in sorted(files):
        if not f.endswith('.md') or f == 'README.md':
            continue
        r = str(rel / f) if str(rel) != '.' else f
        if not r.startswith(('tutorials/', 'guides/')):
            continue
        gitbook[r] = Path(root) / f

# ── Collect cookbook entries ──
cookbook = {}
for root, dirs, files in os.walk(COOKBOOK):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.') and d != '__pycache__' and d != '.venv']
    rel = Path(root).relative_to(COOKBOOK)
    r = str(rel) if str(rel) != '.' else ''
    if not r or not r.startswith(('tutorials/', 'how-to-guides/')):
        continue
    has_py = any(f.endswith('.py') for f in files)
    has_readme = 'README.md' in files
    has_pyproject = 'pyproject.toml' in files
    if has_py and (has_readme or has_pyproject):
        if '.venv' not in r:
            cookbook[r] = Path(root)

# ── Match ──
matched = []
gb_only = []
cb_only = []

for gb, gb_fullpath in sorted(gitbook.items()):
    gb_last = slug(gb.removesuffix('.md').split('/')[-1])
    gb_parent = gb.split('/')[0]
    cb_section = 'how-to-guides' if gb_parent == 'guides' else 'tutorials'

    found = None
    for cb in cookbook:
        cb_last = get_last_part(cb)
        cb_last_clean = re.sub(r'^\d+_', '', cb_last)
        cb_last_slug = slug(cb_last_clean)
        if cb_last_slug != gb_last:
            continue
        cb_top = cb.split('/')[0]
        if cb_top != cb_section:
            continue
        # Subdirectory check
        gb_sub = '/'.join(gb.removesuffix('.md').split('/')[1:-1])
        cb_sub = '/'.join(cb.split('/')[1:-1])
        if slug(gb_sub) == slug(cb_sub):
            found = cb
            break

    if found:
        matched.append((gb, found))
    else:
        gb_only.append(gb)

matched_cb = set(cb for _, cb in matched)
for cb in sorted(cookbook):
    if cb not in matched_cb:
        cb_only.append(cb)

# ── Content drill-down for matched entries ──
def check_drift(gb, cb):
    gb_text = read_file(GITBOOK / gb)
    cb_dir = cookbook[cb]
    py_files = sorted(cb_dir.glob('*.py'))
    cb_code = read_file(py_files[0]) if py_files else ''

    code_blocks = re.findall(r'```python\n(.*?)```', gb_text, re.DOTALL)
    gb_code = '\n'.join(code_blocks).strip()
    return re.sub(r'\s+', ' ', gb_code) != re.sub(r'\s+', ' ', cb_code.strip())

# ── Generate markdown ──
lines = []
lines.append("# GitBook ↔ Cookbook 1:1 Mapping")
lines.append(f"")
lines.append(f"- Generated: _(see file timestamp)_")
lines.append(f"- GitBook root: `{GITBOOK}`")
lines.append(f"- Cookbook root: `{COOKBOOK}`")
lines.append(f"- GitBook pages (guides+tutorials, non-README): **{len(gitbook)}**")
lines.append(f"- Cookbook entries (dir with .py + README|pyproject): **{len(cookbook)}**")
lines.append(f"- Matched 1:1: **{len(matched)}**")
lines.append(f"- GitBook only (no cookbook entry): **{len(gb_only)}**")
lines.append(f"- Cookbook only (no GitBook page): **{len(cb_only)}**")
lines.append(f"")

# A. Matched
lines.append("## A. Matched Entries (GitBook → Cookbook)")
lines.append("")
n_drift = 0
for gb, cb in sorted(matched):
    drift = check_drift(gb, cb)
    if drift: n_drift += 1
    status = "⚠️  CONTENT_DRIFT" if drift else "✅  OK"
    lines.append(f"| `{gb}` | `{cb}/` | {status} |")

lines.append("")
lines.append(f"**{len(matched)-n_drift} OK, {n_drift} with content drift**")
lines.append("")

# B. GitBook only (MISSING from cookbook)
lines.append("## B. GitBook Pages — No Cookbook Entry (MISSING)")
lines.append("")
for gb in sorted(gb_only):
    lines.append(f"- `{gb}`")
lines.append("")

# C. Cookbook only (extra entries)
lines.append("## C. Cookbook Entries — No GitBook Page (EXTRA)")
lines.append("")
for cb in sorted(cb_only):
    lines.append(f"- `{cb}/`")
lines.append("")

# ── Write output ──
out = '/home/delfia-n-a-putri/Documents/Work/GEN_AI/dev5/gitbook-to-cookbook-mapping.md'
with open(out, 'w') as f:
    f.write('\n'.join(lines) + '\n')
print(f"Written to {out}")
print(f"\nStats: {len(matched)} matched, {len(gb_only)} gitbook-only, {len(cb_only)} cookbook-only")
print(f"Content drift: {n_drift} out of {len(matched)} matched entries")
