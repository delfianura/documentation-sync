---
name: sync-cookbook
description: RAGO Sync — detect and fix drift between gl-sdk main → Gitbook → cookbook. Backed by the rago-sync Python CLI at /home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync. Use for any drift detection, sync, verify, or status check.
---

# sync-cookbook

LLM bridge to the rago-sync CLI. All logic lives in Python — this skill maps intent to the right command and ensures cookbook code conventions are followed.

## When to sync (trigger taxonomy)

Sync is **not** a single monolithic operation. There are three distinct scenarios, each with a different workflow:

### Trigger 1: Feature addition or major upgrade in gl-sdk

**What happened**: A gl-sdk PR added a new feature, renamed an API, or shipped a new major version. The GitBook docs were updated to reflect this. Now the cookbook entries need to follow.

**How to handle**:
1. Identify which GitBook pages changed (from the gl-sdk PR's docs diff, or `git log` on the `docs/gitbook-sync` branch).
2. For each changed page, run `uv run rago-sync sync --entry <path>` to pull the updated code from GitBook.
3. After sync, manually add `release_resources()`, make scripts self-contained, and run `uv run` to verify.
4. Bump the `pyproject.toml` version constraint to the exact latest published version (see "Version pinning" below).
5. Open a cookbook PR.

**Key risk**: GitBook may have multi-block pages where each `## Heading` is a separate code example. The CLI's `overwrite_script` handles this, but `create_entry` (for MISSING entries) only uses the first block — manually create additional `.py` files for the remaining blocks.

### Trigger 2: Code example changed in GitBook

**What happened**: Someone updated a code example in a GitBook tutorial page — maybe fixed a typo, changed a parameter, or restructured the example. The gl-sdk API didn't change, but the cookbook's `.py` file needs to match.

**How to handle**:
1. Run `uv run rago-sync detect` to find `CONTENT_DRIFT` entries.
2. For each drifted entry, inspect the current cookbook script vs the GitBook source:
   ```bash
   cat /home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook/gen-ai/<entry_path>/*.py
   ```
3. Run `uv run rago-sync sync --entry <path>` to overwrite from GitBook.
4. Re-add `release_resources()`, `load_dotenv()`, and self-contained setup (GitBook snippets are fragments — see "GitBook fragments" below).
5. Run `uv run <script>.py` to verify.
6. Open a PR.

**Key risk**: `sync` overwrites the entire `.py` file. If the cookbook script had local additions (not in GitBook), they will be lost. Always inspect before syncing.

### Trigger 3: Invalid code in GitBook (cookbook already verified)

**What happened**: The cookbook entry was running fine, but a GitBook edit introduced broken code — undefined variables, wrong imports, removed APIs. The cookbook verification catches this.

**How to handle**:
1. Run `uv run rago-sync verify` — entries that were previously `COMPLIANT` but now `NOT_RUNNABLE` indicate GitBook introduced a bug.
2. Read the error output to diagnose the issue (undefined variable, ImportError, etc.).
3. Fix the GitBook page directly (edit the `.md` in the gitbook repo, create a PR to `docs/gitbook-sync`).
4. After the GitBook PR merges, re-run `sync --entry` to pull the fixed code, then `verify` again.

**Key risk**: GitBook snippets are often **fragments** — they reference variables defined earlier in the tutorial page. A snippet that works in GitBook's narrative flow may fail as a standalone `.py` file. The cookbook script must be self-contained.

## Trigger 0: Merge doc subpages into a main page BEFORE syncing

**What happened**: A GitBook section is split across several small pages (e.g. `data-store/README.md` + `data-store/build-data-store.md` + `data-store/basic-crud-and-methods.md`) that overlap heavily. The cookbook mirrors GitBook page paths, so every redundant subpage becomes a redundant cookbook entry. Merging upstream saves downstream drift.

This is a **pre-sync documentation restructuring** decision. It does NOT use the rago-sync CLI — it edits the GitBook repo directly, following the gl-sdk `.ai/workflows`:
- `gitbook.check-for-update` (read-only completeness/coverage scan) to confirm the pages are redundant.
- `gitbook.update` (the tutorial/how-to/resource rule router) to apply and verify the merge.

Both live under the gl-sdk repo's `.ai/workflows/` and `.ai/rules/` (e.g. `.ai/rules/gitbook-update-tutorials.md`). Drive them via the gl-sdk worktree, not from this cookbook repo.

### When merging is the right call

Merge subpages into the main page when ALL of these hold:

1. **Heavy content overlap** — the same code examples / setup appear on 2+ pages (the data-store pages repeated chunk creation and `store.fulltext.create`/`retrieve` 3×).
2. **Comparable length to an existing single-page tutorial** — the merged result is on the order of the LM Invoker page (~3,000 words, one long page). LM Invoker is the house precedent: quickstart + all core features + a `build_lm_invoker` builder section all live on ONE page; only true "extra capabilities" get subpages.
3. **The subpages add little unique value** — their incremental content is a method reference table or a factory variant already implied by the main page.
4. **No breakage** — keep pure reference/advanced material as separate subpages (for data-store: `supported-datastores`, `encryption`, `batching`, `query-filter`).

### Decision checklist (apply before merging)

- [ ] Identify overlapping sections across the candidate pages (dedupe chunk creation, repeated `create`/`retrieve` examples, repeated capability registration).
- [ ] Confirm merged length is acceptable (mirror LM Invoker single-page style).
- [ ] Decide what STAYS a subpage (reference/advanced only) vs what gets appended to the main page.
- [ ] Inspect the main page's current git state in the gl-sdk worktree — a prior session may have already staged the merge (check `git status`, staged `D <subpage>.md` + modified `README.md`).
- [ ] Verify **no dangling references** to the old paths: `grep -r "basic-crud-and-methods\|build-data-store" gitbook/ --include="*.md"`.

### Merge mechanics (gl-sdk repo, `gitbook.update` workflow)

1. **Append** the subpage content into the main `README.md` under a general (feature/capability) section title — never an implementation-specific title.
2. **Arrange** logically: concept → install → quickstart → capability model → end-to-end CRUD → factory/alternative → advanced → API reference.
3. **Remove** the subpage files and drop their entries from `SUMMARY.md`.
4. **Add redirects** in `.gitbook.yaml` so old URLs 301 to the new anchors:
   ```yaml
   redirects:
     gen-ai-sdk/tutorials/data-store/build-data-store: gen-ai-sdk/tutorials/data-store#build-a-data-store-from-configuration
     gen-ai-sdk/tutorials/data-store/basic-crud-and-methods: gen-ai-sdk/tutorials/data-store#using-the-store-end-to-end
   ```
5. **Keep it gitbook-only** — docs branch must contain only `gitbook/**` changes (enforced by the update workflow, Step 7).

### Rule-compliance check (MANDATORY before considering the merge done)

Run the main page against `.ai/rules/gitbook-update-tutorials.md`. The data-store merge passed everything except one item, called out here so it is never missed again:

| Rule | Status | Note |
|---|---|---|
| Front matter `icon` | ✅ | `icon: server` |
| **§2 Title + Header Links bar** | ❌ **easy to miss** | Tutorial pages MUST open with `[**module**] \| Tutorial \| Use Case \| API Reference` under the `# Title`. The data-store page (and the original) lacked it. Add: `gllm-datastore` → `libs/gllm-datastore`, Tutorial → `README.md`, Use Case → `guides/index-your-data-with-vector-data-store.md` (or `your-first-rag-pipeline.md`), API Reference → `api.python.docs.gdplabs.id/gen-ai/library/gllm_datastore/api/data_store.html`. |
| §3 "What's a…" | ✅ | |
| Prerequisites (details) | ✅ | |
| General section titles | ✅ | "Build a Data Store from Configuration" generalizes the factory |
| No redundant headers | ✅ | single Prerequisites, single Installation |
| Impl details in hints | ✅ | credential/warning notes are hint boxes |
| API Reference | ✅ | |

**The Header Links bar (§2) is the single most commonly dropped item** — verify it exists on every merged tutorial page.

### Cookbook impact after a merge

- The merged main page keeps its `tutorials/data-store/README.md` path → cookbook entry path unchanged.
- The deleted subpages (e.g. `build-data-store.md`, `basic-crud-and-methods.md`) had **no cookbook entries** if they were pure prose — confirm with `rago-sync status` / `detect` so you don't chase phantom MISSING entries.
- If a deleted subpage DID have cookbook scripts, restructure the cookbook to mirror the merged page. The pattern from PR #92:
  1. **Replace** the old multi-directory layout (e.g. `basic_crud_and_methods/` + `build_data_store/`) with a single `basic_usage/` directory.
  2. **Create one `.py` per GitBook section** — not one per old entry directory. For data-store: `quickstart.py` → `#quick-start`, `capabilities.py` → `#using-the-store-end-to-end`, `builder.py` → `#build-a-data-store-from-configuration`.
  3. **Remove `supported_datastores/`** if it was a resource page (not a tutorial) — the merged page links to it as a subpage, but the cookbook only mirrors tutorial pages.
  4. **Add `legacy_data_store/`** for any legacy GitBook pages that still exist separately (e.g. `tutorials/data-store/legacy/vector-data-store`).
  5. **Update the parent `README.md`** with a table mapping each entry directory to its GitBook URL.
  6. Commit the restructure as a single commit — `git add` picks up renames automatically, so the diff is readable.

## CLI commands

| Command | What it does | Auth |
|---|---|---|
| `detect` | Scan GitBook ↔ cookbook for drift (may time out >120s on full scan) | No |
| `detect --email` | Same + email report | No |
| `status` | Show persisted drift status from last detect (fast, no scan) | No |
| `sync --entry <path>` | Overwrite cookbook script from GitBook for one entry | Yes (gcloud) |
| `sync` | Fix all drifted entries | Yes |
| `sync-all` | Bootstrap all missing entries | Yes |
| `verify` | Run `uv run` on drifted/synced entries | Yes |
| `verify --all` | Run `uv run` on every entry | Yes |

All commands run from the rago-sync project root:

```bash
cd /home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync
uv run rago-sync <command> [options]
```

## GitBook→cookbook mapping

**The CLI uses convention-based path mapping** (hyphen→underscore, `guides/`→`how-to-guides/`, strip numeric prefixes like `001_`). This is a heuristic, not a lookup table. It works for most entries but **has caused real bugs**:

- PR #75 created `lm_invoker_basic_usage/` (prefixed folder) instead of `basic_usage/` (GitBook section heading). This required PR #88 to delete 11 prefixed duplicates and rename them.
- Convention-based mapping can't handle pages where the GitBook heading doesn't match the folder slug.

**A CSV mapping file exists** at `/home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync/gitbook-to-cookbook-mapping.csv` (generated Jul 7, updated Jul 16). It has columns: `Type,GitBook Path,Cookbook Path,Status`. This is a snapshot, not a live lookup — but it MUST be kept in sync after structural changes.

**After any structural sync** (merging/restructuring cookbook directories), update the CSV to match the new layout — remove old entries that were deleted/merged, add new `SYNCED` entries for the new directories, and mark resource pages as `skip`. A stale CSV causes phantom `MISSING` results in future `detect` runs. New statuses: `SYNCED` (entry verified and up-to-date), `RESOURCE_PAGE` (not a tutorial, skip), `BLOCKED_ON_INFRA` (entry needs external infra to verify).

**When creating new entries**, don't rely on the convention. Decide the folder name based on the GitBook page's section heading (e.g., `basic_usage/`, not `lm_invoker_basic_usage/`). The parent directory mirrors the GitBook page hierarchy; the leaf folder name mirrors the section heading.

## Entry states

| State | Meaning | Auto-fixed? |
|---|---|---|
| `COMPLIANT` | All good | — |
| `MISSING` | No cookbook entry for a Gitbook page | Yes — creates 7-file entry |
| `TEMPLATE_MISSING` | Required files absent | Yes — recreates entry |
| `CONTENT_DRIFT` | Cookbook script diverged from Gitbook | Yes — overwrites script from Gitbook |
| `VERSION_STALE` | pyproject.toml behind latest published version | Yes — updates constraint + uv lock |
| `GITBOOK_DRIFT` | Gitbook code uses removed API | Opens GitHub issue (human fix) |
| `NOT_RUNNABLE` | uv run fails | Retries; escalates if still failing |
| `PENDING_REVIEW` | PR open for this entry | Paused until PR merged/closed |

## Procedure: syncing a cookbook entry

### A. Before running detect

1. Check sparse checkout — if `gen-ai/tutorials/` isn't checked out, everything shows as MISSING:
   ```bash
   git -C /home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook sparse-checkout list
   # If missing:
   git -C /home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook sparse-checkout add gen-ai/tutorials/retrieval
   git -C /home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook checkout
   ```
2. Verify branch is `main` (or the PR branch you're working on):
   ```bash
   git -C /home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook branch --show-current
   ```

### B. After `sync --entry` (before committing)

`sync` overwrites the `.py` file from GitBook. Three things GitBook won't have that you must add:

1. **`release_resources()`** — if the script creates an invoker (`OpenAIEMInvoker`, `OpenAILMInvoker`, `AnthropicLMInvoker`, etc.), wrap usage in `try/finally`:
   ```python
   async def main() -> None:
       em_invoker = OpenAIEMInvoker(model_name="text-embedding-3-small")
       try:
           # ... all invoker usage ...
       finally:
           await em_invoker.release_resources()
   ```
   Pattern matches gl-sdk PR #5319.

2. **Self-contained script** — GitBook snippets may reference variables defined earlier in the tutorial (e.g. `vector_datastore` used but never assigned). Cookbook scripts must be standalone. Add missing definitions or note them in the PR description.

3. **`load_dotenv()`** — if the script uses API keys, check that `load_dotenv()` is called and `.env.example` exists.

### C. Before opening a PR — mandatory verification

Run `uv run <script>.py` for every new or modified entry. **`uv lock` is not enough** — it only resolves dependencies, never imports/executes.

Even credential-blocked entries surface `NameError` and `ImportError` before hitting the credential wall. Only `uv run` gives you this signal.

For entries requiring external infra (Elasticsearch, SmartSearch, etc.): attempt `uv run`, confirm the error is infra-related (not a code bug), and note it in the PR description.

### D. Skip detect when you already know the entry

If the user gives a specific gl-sdk PR/feature and you've already located the GitBook page and confirmed the fix, skip `detect` — go straight to editing the cookbook entry, then verify + PR. `detect` is for discovering *what's* drifted across the whole cookbook and can time out (120s+) on large scans. Use `rago-sync status` instead to read persisted results from the last `detect` run without re-scanning.

**Two-way sync timing**: `rago-sync sync --entry` compares against the *live* published GitBook page. If the GitBook update is still an unmerged docs PR, edit the cookbook entry by hand to mirror that PR's diff — don't use `sync`.

### E. Use GitBook MCP tools to fetch current page content

When the CLI `sync` command is broken or you need to see the exact current GitBook code, use the GitBook MCP tools:
- `mcp__gitbook__searchDocumentation(query="...")` — find the page URL by topic.
- `mcp__gitbook__getPage(url="https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/...")` — fetch the full markdown content including all code blocks.

This is the primary method for manual sync when the CLI is unavailable. Always compare the GitBook quickstart code block with the cookbook script to identify the exact drift before editing.

### F. Use a worktree for sync work

Always create a git worktree for sync edits — never work directly on `main`:
```bash
cd /home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook
git worktree add /home/delfia-n-a-putri/Documents/Work/GEN_AI/worktrees/sync-<scope> -b feat/sync-<scope>-tutorials main
```
Set sparse checkout to include the tutorial directories you need:
```bash
cd <worktree> && git sparse-checkout set gen-ai/tutorials/core gen-ai/how-to-guides
```
After editing, commit with Conventional Commits format (GPG signed), then open a PR with `gh pr create`.

### G. Check latest published version for version pinning

Before pinning, check the latest published version on the internal index:
```bash
pip index versions gllm-core --extra-index-url "https://oauth2accesstoken:$(gcloud auth print-access-token)@glsdk.gdplabs.id/gen-ai-internal/simple/" 2>&1 | head -3
```
Pin to `>=<latest_version>,<next_major>.0`. For example, if latest is `0.4.37.post1`, pin `>=0.4.37,<0.5.0`.

### H. Codeblock coverage map — generate and verify (any lib)

A YAML coverage map at `references/codeblock-map.yaml` tracks every GitBook tutorial page → code block heading → cookbook `.py` file. This is the authoritative mapping of what the cookbook must cover. It works for **any lib** in the cookbook (core, inference, retrieval, etc.), not just gllm-core.

**entry_dir values must include the `tutorials/` prefix** (e.g., `tutorials/core/component`, not `core/component`). Without it, the verify script looks for files at `gen-ai/core/component` instead of `gen-ai/tutorials/core/component` and reports false MISSING errors.

#### Generating the map

`scripts/generate_map.py` auto-discovers all `.py` files in a cookbook checkout, extracts GitBook URLs from their docstrings (stripping anchors to group by page), and writes the YAML map. For files without docstrings, it falls back to the CSV mapping (`--csv`) or heuristic URL derivation from the entry_dir.

```bash
# Generate for a specific lib (e.g., core only):
python3 scripts/generate_map.py \
  --cookbook-root /path/to/gen-ai-sdk-cookbook \
  --map references/codeblock-map.yaml \
  --scope core

# Generate for the entire cookbook (all libs):
python3 scripts/generate_map.py \
  --cookbook-root /path/to/gen-ai-sdk-cookbook \
  --map references/codeblock-map.yaml \
  --csv /path/to/gitbook-to-cookbook-mapping.csv

# Merge with existing map (preserve manual annotations like headings/anchors/notes):
python3 scripts/generate_map.py \
  --cookbook-root /path/to/gen-ai-sdk-cookbook \
  --map references/codeblock-map.yaml \
  --scope inference --merge-existing
```

**URL resolution order**: docstring URL (anchor stripped) → CSV mapping → heuristic (`tutorials/<entry_dir>` → `gitbook.io/sdk/gen-ai-sdk/tutorials/<entry_dir>`).

#### Verifying the map

`scripts/verify_coverage.py` checks the map against the cookbook directory:

```bash
python3 scripts/verify_coverage.py \
  --cookbook-root /path/to/gen-ai-sdk-cookbook \
  --map references/codeblock-map.yaml \
  --ruff \
  --scope core   # optional: limit to one lib
```

Checks:
1. **Missing files** (ERROR): block in map but no `.py` file exists.
2. **Orphans** (WARNING): `.py` file not in map (aggregated across pages sharing the same `entry_dir`).
3. **Docstring URLs** (WARNING): each `.py` file references the correct GitBook page URL. Downgraded to warning because older entries predate the docstring convention.
4. **Duplicates** (ERROR): same `cookbook_file` listed twice.
5. **Ruff** (ERROR with `--ruff`): all mapped files pass `ruff check --select E,W,F`.

Exit code 0 = all pass (warnings allowed). Non-zero = errors found.

#### Typical workflow when syncing

1. **Before syncing**: run `generate_map.py --scope <lib> --merge-existing` to discover any new `.py` files added since last sync.
2. **After syncing**: run `verify_coverage.py --ruff --scope <lib>` to confirm no gaps.
3. **When GitBook adds a new code block**: create the `.py` file, run `generate_map.py --scope <lib> --merge-existing` to pick it up, then fill in heading/anchor/notes manually.

**Multi-page entry_dirs**: when two GitBook pages map to the same `entry_dir` (e.g., a how-to-guide and a tutorial page both covering `tutorials/core/component/`), the orphan check aggregates all mapped files across pages before comparing to the cookbook. This prevents false orphan warnings.

## Full code block coverage (mandatory)

A GitBook tutorial page typically contains **multiple code blocks** under different `## Heading` sections. The cookbook must cover **every runnable code block** — not just the quickstart.

### How to identify code blocks

1. Fetch the full GitBook page via `mcp__gitbook__getPage(url=...)`.
2. Enumerate every ```python ... ``` block on the page.
3. For each block, create a self-contained `.py` file in the entry directory.

### How-to-guide vs tutorial page distinction

Some cookbook entries were originally created from **how-to-guide** pages (e.g., `how-to-guides/add-a-custom-component`). The GitBook later reorganized content into **tutorial** pages (e.g., `tutorials/core/component`).

When a cookbook entry's docstring references a how-to-guide page but a tutorial page also exists:
- **Keep the existing `.py` file** referencing the how-to-guide page — do not replace it.
- **Add new `.py` files** for the tutorial page's code blocks.
- The `README.md` should list **both** references (how-to-guide + tutorial).

### Code block marking

Not every code block on a GitBook page is a standalone runnable example. Some are:
- **Fragments** that reference variables from earlier blocks.
- **Snippet excerpts** showing a partial concept.
- **Full standalone examples** meant to run as-is.

The coverage map (`references/codeblock-map.yaml`) is the authoritative registry. The `runnable` field on each block indicates whether the cookbook script is standalone runnable. The cookbook author makes each script self-contained by:
1. Adding missing variable definitions.
2. Adding necessary imports.
3. Wrapping in `async def main()` + `if __name__ == "__main__"`.

If a GitBook page adds new code blocks not in the map, the author must add them to `codeblock-map.yaml` and create the corresponding `.py` file. Run `verify_coverage.py` to confirm completeness.

### Ruff check (mandatory)

After writing/editing cookbook `.py` files, run ruff:
```bash
ruff check --select E,W,F <entry_dir>/ --exclude "*.venv"
```
Common issues to fix:
- **W292**: No newline at end of file (`--fix` auto-fixes this).
- **F401**: Unused imports (`--fix` auto-fixes this).
- **E501**: Line too long (88 chars default) — fix manually by wrapping.

Files must pass `ruff check` before committing.

### Check GitHub main for new releases before syncing

Before starting sync work:
1. Fetch latest main and rebase your branch:
   ```bash
   git fetch origin main
   git rebase origin/main
   ```
2. Check if there are new commits affecting your entry scope:
   ```bash
   git log origin/main --oneline <merge-base>..origin/main -- gen-ai/tutorials/<scope>/
   ```
3. Check the latest published version of the package:
   ```bash
   pip index versions gllm-core --extra-index-url "https://oauth2accesstoken:$(gcloud auth print-access-token)@glsdk.gdplabs.id/gen-ai-internal/simple/" 2>&1 | head -3
   ```
4. If a newer version exists than what's pinned in `pyproject.toml`, update the pin.

## Cookbook code conventions

Every cookbook `.py` file should:
- Have a module docstring with a reference link to the GitBook page (use `#anchor` for section-specific scripts)
- Use `async def main()` + `if __name__ == "__main__": asyncio.run(main())` (or `def main()` for sync-only scripts)
- Call `release_resources()` on all invokers in a `finally` block
- Be self-contained (no undefined variables)
- Call `load_dotenv()` if it needs API keys
- Pass `ruff check --select E,W,F`
- Have a trailing newline at end of file
- Have `.env.example`, `.python-version`, `pyproject.toml`, `uv.lock`, `setup.sh`, `setup.bat`, `README.md` (per entry directory, not per file)
- The `README.md` should list **all** `.py` files in the entry with `uv run` commands and all GitBook references

## Operational gotchas

### CLI `sync` command may be broken (typer/click incompatibility)

The rago-sync CLI's `sync --entry <path>` command may fail with `Option '--entry' does not take a value` or `Got unexpected extra argument` due to a typer/click version incompatibility in the `.venv` (typer 0.12.5 + click 8.x mismatch). If `sync --entry` fails:

1. Fetch the current GitBook page content using the GitBook MCP tools (`mcp__gitbook__getPage` with the page URL).
2. Read the current cookbook script (`cat` or `read_file`).
3. Manually edit the cookbook `.py` file to match the GitBook quickstart code block, following cookbook conventions (docstring, `async def main()`, self-contained, etc.).
4. Continue with `uv run` verification as normal.

This is the same as the "Two-way sync timing" fallback in section D — when `sync` can't be used (broken CLI or unmerged GitBook PR), edit by hand from the GitBook source.

### PYTHONPATH pollution breaks `uv run`

When running `uv run python <script>.py` from within Hermes, the agent's own Python 3.11 `pydantic_core` can leak into the subprocess path, causing:
```
ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'
```
Fix: prefix `uv run` with `PYTHONPATH=` to clear the inherited path:
```bash
export UV_INDEX_GEN_AI_INTERNAL_USERNAME=oauth2accesstoken
export UV_INDEX_GEN_AI_INTERNAL_PASSWORD="$(gcloud auth print-access-token)"
PYTHONPATH= uv run python <script>.py
```

### CONTENT_DRIFT sync overwrites the whole script

`sync` replaces the `.py` file with code from GitBook. If the cookbook script has local additions not in GitBook, they will be lost. Always inspect before syncing.

### Folder naming: use section headings, not prefixed slugs

PR #75 created folders like `lm_invoker_basic_usage/` by prefixing the parent directory name. PR #88 had to delete 11 such prefixed duplicates and rename them to `basic_usage/`, `context_management/`, etc. When creating new entries, use the GitBook section heading as the folder name — not a slug derived from the full path.

### Worktree sparse checkout does not inherit from parent repo

When you create a worktree from a repo that has `sparse-checkout` configured, the worktree starts with a **default cone** (no directories). You must explicitly run `git sparse-checkout set` inside the worktree:

```bash
cd <worktree> && git sparse-checkout set gen-ai/tutorials/data_store gen-ai/how-to-guides
```

Without this, `find gen-ai/tutorials/data_store/` returns nothing and all entries appear MISSING. Always run `git sparse-checkout set` right after creating the worktree, before any other command.

Also note: if the main checkout has untracked work-in-progress files (not committed on `main`), the worktree from `main` HEAD will **not** include them. Check `git status` in the main checkout to distinguish committed entries from WIP before relying on the worktree's file listing.

### `source` field required for sync

`status.json` stores the GitBook-relative path in `source`. If `source` is missing (old detect run), re-run `detect` before syncing.

### entry_dir in codeblock-map.yaml must include tutorials/ prefix

The `entry_dir` field in `codeblock-map.yaml` must be the full path relative to `gen-ai/` — e.g., `tutorials/core/component`, not `core/component`. Without the `tutorials/` prefix, `verify_coverage.py` looks for files at `gen-ai/core/component` instead of `gen-ai/tutorials/core/component` and reports false MISSING errors for every entry. This was a real bug found when generalizing the map for all libs.

### NOT_RUNNABLE after sync is expected for credential-dependent entries

Entries requiring Google service account credentials will always be `NOT_RUNNABLE` locally without auth. The code is valid — it just can't execute without credentials.

### Token expiry mid-run

`gcloud` tokens last ~1hr. For long `sync`/`verify --all` runs, rago-sync refreshes tokens before every subprocess call. If driving `uv`/`curl` manually outside the CLI, re-run `gcloud auth print-access-token` right before each call.

### Package extras

| Import | Required extra |
|---|---|
| `OpenAILMInvoker`, `OpenAIEMInvoker`, `OpenAIRealtimeSession` | `gllm-inference[openai]` |
| `GoogleLMInvoker`, `GoogleEMInvoker` | `gllm-inference[google]` |
| `AnthropicLMInvoker` | `gllm-inference[anthropic]` |
| `ChromaDataStore` | `gllm-datastore[chroma]` |
| Any `from gllm_datastore...` import | `gllm-datastore[chroma]` — `__init__` eagerly imports `chromadb` even for non-Chroma entries (e.g. `key_value_store` needs it). When in doubt, always add `[chroma]`. |
| Any `gllm_datastore.*` import (incl. `key_value_store`) | `gllm-datastore[chroma]` — the package `__init__` eagerly imports `ChromaDataStore`, so even non-Chroma entries (e.g. `OpenBaoKeyValueStore`) need the `[chroma]` extra or `ImportError: missing 'chromadb'` fires at import time. |

### Version pinning

Pin the exact latest version: `>=0.6.90,<0.7.0`, not a rounded-down floor like `>=0.6.0,<0.7.0`. A rounded-down floor may already satisfy the old lock, making `uv lock` a no-op.

#### Cross-package compatibility (critical)

Each `gllm-*` package pins its own `gllm-core` floor/ceiling. Pinning every package to "the latest" independently can produce an **unsatisfiable** resolution. Real failure during the data_store sync (PR #92): `gllm-inference==0.6.98` requires `gllm-core>=0.4.21,<0.4.37`, but the latest published `gllm-core` was `0.4.37.post1` — `uv lock` failed with "your project's requirements are unsatisfiable". Fix: drop to `gllm-inference>=0.6.95,<0.7.0` (0.6.95 allows `gllm-core<0.5.0`) so it coexists with `gllm-core>=0.4.37`. After editing any pin, always run `uv lock` and read the error — never assume "latest = compatible". Data-store-specific pin matrix and backend gotchas: see `references/datastore-gotchas.md`.

## Known limitations of the CLI

These are bugs filed as GitHub issues on `delfianura/documentation-sync`. The LLM bridge must compensate for them manually:

1. **Multi-block pages** (Issue #1, partially fixed): `overwrite_script` now writes one file per Python block. But `create_entry` (for MISSING entries) still only uses the first block — manually create additional files for multi-block pages.
2. **API drift detection is import-only** (Issue #4): The CLI checks if imported names exist in gl-sdk, but can't detect method renames or argument order changes. If a PR changes a method signature, the CLI won't flag it — manually diff the call site against the current API.
3. **Gap detection is page→folder, not per-example** (Issue #5): If a parent directory exists with some files, a deleted sub-entry won't show as MISSING. Manually verify that every code block on the GitBook page has a corresponding `.py` file.
4. **No stale link checker** (Issue #6): GitBook outbound links to the cookbook aren't validated. If you see a `github.com/gl-sdk/` or `github.com/GDP-ADMIN/gl-sdk-cookbook` link, it's probably stale — should be `github.com/gdplabs/gen-ai-sdk-cookbook`.

## Anti-pattern: carrying forward drift claims

Before writing any "X no longer exists" or "X changed to Y" claim in a PR body, issue, or report, re-fetch and quote the *current* source file (`git show`, `gh api`, or `cat`) in the same turn. Do not rely on an earlier scan's conclusion, even within the same session — the file may have been updated, or the earlier conclusion may have been wrong (Issue #7).

## Cron

`detect --email` runs automatically every Monday 9am (Hermes cron job: `rago-sync-weekly`). `sync` is always manual.

## Source

CLI source: `/home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync`
GitHub: https://github.com/delfianura/documentation-sync