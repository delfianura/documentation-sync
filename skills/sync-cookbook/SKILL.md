---
name: sync-cookbook
description: RAGO Sync — detect and fix drift between gl-sdk main → Gitbook → cookbook. Backed by the rago-sync Python CLI at $RAGO_SYNC_DIR. Use for any drift detection, sync, verify, or status check.
---

# sync-cookbook

LLM bridge to the rago-sync CLI. All logic lives in Python — this skill maps intent to the right command and ensures cookbook code conventions are followed.

## Step 0 — Setup (first run only)

Before running any rago-sync command, check if `$RAGO_SYNC_DIR/.env` exists. If it does **not**, create it from `.env.example` and fill in the user's actual paths:

```bash
cp $RAGO_SYNC_DIR/.env.example $RAGO_SYNC_DIR/.env
```

Then ask the user for (or detect from their filesystem) the following paths and write them into `.env`:

| Variable | What to set it to | How to detect |
|---|---|---|
| `RAGO_SYNC_DIR` | Path to this documentation-sync repo | `git rev-parse --show-toplevel` from the skill location |
| `RAGO_SYNC_GL_SDK_REPO` | Path to gl-sdk checkout (has `gitbook/` and `libs/`) | `find ~ -maxdepth 4 -name gl-sdk -type d 2>/dev/null` |
| `RAGO_SYNC_COOKBOOK_REPO` | Path to gen-ai-sdk-cookbook checkout (has `gen-ai/`) | `find ~ -maxdepth 4 -name gen-ai-sdk-cookbook -type d 2>/dev/null` |
| `RAGO_SYNC_GITBOOK_DIR` | Path to GitBook docs inside gl-sdk (usually `$RAGO_SYNC_GL_SDK_REPO/gitbook/gen-ai-sdk`) | Append `/gitbook/gen-ai-sdk` to the gl-sdk path |

After writing `.env`, source it for the current session:

```bash
set -a && source $RAGO_SYNC_DIR/.env && set +a
```

**Do not skip this step.** Every subsequent command (`uv run rago-sync detect`, `sync`, `verify`) depends on these paths being set. `.env` is gitignored — each user maintains their own copy.

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
   cat $COOKBOOK_REPO/gen-ai/<entry_path>/*.py
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

## Trigger 0.5: Pre-flight `gitbook.check-for-update` (MANDATORY before any sync)

Before running `rago-sync detect`, `sync`, or manually syncing any entry, run the gl-sdk
`gitbook.check-for-update` workflow in **read-only / Mode 2 (Full Audit)** mode against the
target guide/tutorial pages.

Why mandatory: `docs/gitbook-sync` can advance ahead of `gl-sdk main`. When that happens the
GitBook pages document APIs that do not yet exist in the released packages. Blindly syncing
from those pages overwrites working cookbook scripts with broken examples, converts a
`COMPLIANT` entry into `NOT_RUNNABLE`, and produces `GITBOOK_DRIFT` — an entry state that
means *"the docs are wrong, not the cookbook"*.

How to run (read-only — no edits, no commits):
1. Switch to the gl-sdk worktree that has `.ai/workflows/gitbook-check-for-update.md`
   (e.g. `$GL_SDK_REPO` or any feature worktree derived from it).
2. Run the workflow in Mode 2 (no `$ARGUMENTS`) or Mode 1 (provide the relevant PR/branch).
   The workflow produces a structured gap report listing every affected GitBook file and its
   coverage classification.
3. Inspect the report. If any page is classified `GITBOOK_DRIFT` (documented APIs don't exist
   on `main`) or `OUTDATED` / `UNDOCUMENTED` for the current feature scope, **STOP**.

### Response rules for `GITBOOK_DRIFT`

| Situation | Action |
|---|---|
| GitBook docs a method that doesn't exist on `main` yet | Open a GitHub issue in `GDP-ADMIN/gl-sdk`; do **not** sync the cookbook. |
| GitBook docs were correct but an intermediate `docs/gitbook-sync` commit broke them | File issue against the docs branch; wait for the docs PR to fix before syncing. |
| A gl-sdk feature branch already has the new API but `main` doesn't | Wait for the feature branch to merge, then re-run the check before syncing. |
| Multiple cookbook entries already drifted toward the future API | Revert the cookbook scripts to the last known-good version; re-apply after `main` catches up. |

**Never** run `rago-sync sync --entry` against a `GITBOOK_DRIFT` page. `sync` would overwrite
the cookbook `.py` with the broken example and then `verify` would mark it `NOT_RUNNABLE` —
conflating *"docs are wrong"* with *"cookbook code is wrong"*. These are different failure
modes and require different fixes.

### When this check produces `COMPLIANT` / `DOCUMENTED`

Continue to the normal sync flow (Trigger 1, 2, or 3 as appropriate).

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

## Router / multi-variant tutorial layout

Some GitBook tutorial pages are a **hub with variant subpages** instead of a single page with sections. Examples: `tutorials/orchestration/routing/` with `rule-based-router/`, `semantic-router/`, `lm-based-router/`, `similarity-based-router/`.

For these:
- The parent directory is a **real cookbook entry** and needs the standard boilerplate: `.env.example`, `.python-version`, `pyproject.toml`, `README.md`, `setup.bat`, `setup.sh`, `uv.lock`.
- Each variant subdirectory **also** needs the same boilerplate because users need to `cd` into it and run `setup.sh` / `uv run python <script>.py`. User feedback: missing per-variant boilerplate is incomplete work.
- The parent `README.md` should link to each subdirectory; each subdirectory `README.md` can be minimal or omitted if the parent links are sufficient.
- When a variant needs extra deps, do not drop to reference-only by default. Add the necessary extra to the subdirectory `pyproject.toml` and attempt a real run. If the installed package still blocks at import time because a named backend is not available, document that exact blocker in the subdirectory README and keep the script in place—do not delete it.
- Real runnable router examples must use runtime-loadable credentials (`os.getenv("OPENAI_API_KEY")`, with `load_dotenv()`), never a literal placeholder.
- **Mandatory pre-push verification**: run each subdirectory's `setup.sh`, then `uv run python <script>.py`. If a script still fails at runtime because an optional dependency is missing, note it explicitly in the README and do not claim that page as `COMPLIANT`.

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
cd $RAGO_SYNC_DIR
uv run rago-sync <command> [options]
```

## GitBook→cookbook mapping

**The CLI uses convention-based path mapping** (hyphen→underscore, `guides/`→`how-to-guides/`, strip numeric prefixes like `001_`). This is a heuristic, not a lookup table. It works for most entries but **has caused real bugs**:

- PR #75 created `lm_invoker_basic_usage/` (prefixed folder) instead of `basic_usage/` (GitBook section heading). This required PR #88 to delete 11 prefixed duplicates and rename them.
- Convention-based mapping can't handle pages where the GitBook heading doesn't match the folder slug.

**A CSV mapping file exists** at `$RAGO_SYNC_DIR/gitbook-to-cookbook-mapping.csv` (generated Jul 7, updated Jul 16). It has columns: `Type,GitBook Path,Cookbook Path,Status`. This is a snapshot, not a live lookup — but it MUST be kept in sync after structural changes.

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
| `BLOCKED_ON_INFRA` | Needs optional backend/tooling not installable here | Manual README note + reference-only if unverifiable |

## Procedure: syncing a cookbook entry

### A. Before running detect

1. Check sparse checkout — if `gen-ai/tutorials/` isn't checked out, everything shows as MISSING:
   ```bash
   git -C $COOKBOOK_REPO sparse-checkout list
   # If missing:
   git -C $COOKBOOK_REPO sparse-checkout add gen-ai/tutorials/retrieval
   git -C $COOKBOOK_REPO checkout
   ```
2. Verify branch is `main` (or the PR branch you're working on):
   ```bash
   git -C $COOKBOOK_REPO branch --show-current
   ```

### B. After `sync --entry` (before committing)

`sync` overwrites the `.py` file from GitBook. Four mandatory things GitBook won't have that you must add:

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

4. **No side-effects at import time** — module body must not:
   - Mutate global process state (`os.environ[...] = ...`, `logging.basicConfig(...)`).
   - Create files or network connections.
   - Instantiate objects that hold resources (e.g. `logging.FileHandler("app.log")`).
   Wrap all such calls inside `main()` / `run_example()` guarded by `if __name__ == "__main__":`.

### C. Before opening a PR — mandatory verification

Run `uv run <script>.py` for every new or modified entry. **`uv lock` is not enough** — it only resolves dependencies, never imports/executes.

Even credential-blocked entries surface `NameError` and `ImportError` before hitting the credential wall. Only `uv run` gives you this signal.

For entries requiring external infra (Elasticsearch, SmartSearch, etc.): attempt `uv run`, confirm the error is infra-related (not a code bug), and note it in the PR description.

For AST-level checks against imported name-shadowing and import-time side-effect anti-patterns, run:
```bash
python3 scripts/verify_import_side_effects.py --root <entry_dir>
# or for the shadow-specific rule:
python3 scripts/verify_import_side_effects.py --check-import-shadow <entry_dir>
```
For full codeblock coverage verification, see `scripts/verify_coverage.py`.

### D. Skip detect when you already know the entry... [full existing text] ...

**Two-way sync timing**: `rago-sync sync --entry` compares against the *live* published GitBook page. If the GitBook update is still an unmerged docs PR, edit the cookbook entry by hand to mirror that PR's diff — don't use `sync`.

### Trigger -1: Pre-flight GitBook drift check (MANDATORY before any sync)

Before running `sync` / `sync --entry`, ALWAYS run the gl-sdk `gitbook-check-for-update` workflow
as a read-only pre-flight. This surfaces `GITBOOK_DRIFT` (docs reference APIs not yet on main)
and `CONTENT_DRIFT` conditions that the rago-sync CLI alone cannot detect.

Invocation (run from gl-sdk worktree, **never from the cookbook repo**):

```
gitbook.check-for-update
# or with a specific scope:
gitbook.check-for-update tutorials/orchestration/pipeline
gitbook.check-for-update guides/human-in-the-loop
```

If the workflow reports `GITBOOK_DRIFT`:
  → DO NOT run `sync` yet.
  → Either (a) open a GitHub issue in gl-labs/gl-sdk describing the drifted pages, or
        (b) wait for the feature branch to land on main, then re-run the check.
  → Only sync after GitBook is consistent with what main actually ships.

If the workflow reports `CONTENT_DRIFT` only:
  → Continue to the normal sync flow above.

The `sync-cookbook` skill itself does not implement this workflow; it delegates to the gl-sdk
`.ai/workflows/gitbook-check-for-update.md` file, which any agent running inside the gl-sdk
worktree can follow.

**API-grounding check (MANDATORY before syncing how-to / pipeline / orchestration pages)**: The GitBook pipeline/orchestration guides have historically documented APIs (`enable_debug_tracing`, `disable_debug_tracing`, `include_outputs_from`, `get_state_history`, `fork_from`, `get_state`, `update_state`, `Pipeline.resume()`, `Pipeline.invoke(..., context=...)`) before those methods land on `gl-sdk main`. Before running `rago-sync sync --entry` on any entry that touches `Pipeline`, verify each method used in the GitBook page actually exists on the currently installed `gllm-pipeline`:

```bash
uv run python -c "from gllm_pipeline.pipeline.pipeline import Pipeline; print([m for m in dir(Pipeline) if m in ['enable_debug_tracing','fork_from','get_state','get_state_history','resume','update_state','invoke']])"
```

If any expected method is missing, **do not sync** — report `GITBOOK_DRIFT` and open a GitHub issue instead. See `GITBOOK_DRIFT: docs are wrong, not the cookbook` below.

### E. Use GitBook MCP tools to fetch current page content

When the CLI `sync` command is broken or you need to see the exact current GitBook code, use the GitBook MCP tools:
- `mcp__gitbook__searchDocumentation(query="...")` — find the page URL by topic.
- `mcp__gitbook__getPage(url="https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/...")` — fetch the full markdown content including all code blocks.

This is the primary method for manual sync when the CLI is unavailable. Always compare the GitBook quickstart code block with the cookbook script to identify the exact drift before editing.

### F. Use a worktree for sync work

Always create a git worktree for sync edits — never work directly on `main`:
```bash
cd $COOKBOOK_REPO
git worktree add $WORKTREE_DIR/sync-<scope> -b feat/sync-<scope>-tutorials main
```
Set sparse checkout to include the tutorial directories you need:
```bash
cd <worktree> && git sparse-checkout set gen-ai/tutorials/core gen-ai/how-to-guides
```
After editing, commit with Conventional Commits format (GPG signed), then open a PR with `gh pr create`:
```bash
git push -u origin feat/sync-<scope>-tutorials
gh pr create --base main --head feat/sync-<scope>-tutorials --title "..." --body "..."
```

**`gh pr create` remote-head format**: if the branch is on a forked account (e.g. `delfianura`), either omit `--head` entirely after pushing with `-u`, or pass the bare branch name without a username prefix. Passing `--head delfianura:feat/...` causes "No commits between main and branch" because GitHub does not resolve the colon form from a non-owner fork in the same repo context.

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
3. Wrapping in `async def main()` + `if __name__ == "__main__": asyncio.run(main())` (or `def main()` for sync-only scripts).

#### Fragile-standalone guardrail

GitBook code blocks often omit boilerplate that `gllm-pipeline` requires at runtime. After creating a new script from a snippet, always run `uv run`; **do not mark it verified just because it imports successfully**. Known failure modes:
- **Missing `state_type` / wrong type**: GitBook often omits `state_type` entirely, but the installed resolver requires `TypedDict` or `BaseModel`. `state_type=dict` raises `ValueError`. Fix: define a minimal `TypedDict` with only the fields this block reads/writes.
- **Conditional/control-flow steps without a checkpointer**: `if_else`, `switch`, `toggle`, `no_op`, `guard`, `try_catch`, and `map_reduce` have hit `RuntimeError: 'NoneType' object is not iterable` inside LangGraph when run without a checkpointer. Fix: add `checkpointer=InMemorySaver()` or use the verified pipeline pattern.
- **Imports that only resolve in the full package context**: Some names are exported under different modules than the docs imply. Verify with: `PYTHONPATH= uv run python -c "from gllm_pipeline.steps import X"`.
- **`goto` target resolution**: `goto(target=...)` expects target names to be reachable in the state/config; missing keys produce `KeyError`. Skipping unverifiable control-flow blocks is acceptable.

If a GitBook page is **prose/reference with no runnable blocks** (e.g., Routing), record it in the `README.md` as reference-only and skip `.py` creation rather than uploading fragile wrappers.

### Multi-variant sections: one section, multiple files when justified

If a GitBook page adds new code blocks not in the map, the author must add them to `codeblock-map.yaml` and create the corresponding `.py` file. Run `verify_coverage.py` to confirm completeness. Collected failure patterns from standalone-wrapping GitBook snippets live in `references/standalone-failure-patterns.md`.

### Import simplification checklist from PR #94 review

After writing/editing cookbook `.py` files, normalize imports before committing:
- Use `from gllm_pipeline.pipeline.pipeline import Pipeline` consistently across examples.
- Placeholder `main` imports under `gllm_core.schema` are not a universal simplification target; only remove them when the file truly does not use the `@main` decorator.
- For standalone scripts that need sibling imports, prefer direct parent-directory path injection rather than introducing `.agent_scripts` directories.
- Accept `E402` as expected noise whenever `load_dotenv()` intentionally precedes package imports.

### `async def main()` anti-pattern from GitBook copy-paste

GitBook sometimes shows `async def main()` even when the function body only calls `asyncio.run(...)` internally. If the entry point calls `main()` without `asyncio.run(main())`, Python emits `RuntimeWarning: coroutine 'main' was never awaited` and the function's body silently does not execute.

**Fix patterns**:
- If `main()` internally calls `asyncio.run(...)` → change `main` to `def main()` and call it directly.
- If `main()` genuinely awaits coroutines → keep `async def main()` and use `if __name__ == "__main__": asyncio.run(main())`.

Check for this immediately after creating a new script from a GitBook snippet.

If a GitBook page adds new code blocks not in the map, the author must add them to `codeblock-map.yaml` and create the corresponding `.py` file. Run `verify_coverage.py` to confirm completeness. Collected failure patterns from standalone-wrapping GitBook snippets live in `references/standalone-failure-patterns.md`.

### `async def main()` anti-pattern from GitBook copy-paste

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
   uv pip index versions gllm-core --extra-index-url "https://oauth2accesstoken:$(gcloud auth print-access-token)@glsdk.gdplabs.id/gen-ai-internal/simple/" 2>&1 | head -3
   ```
4. If a newer version exists than what's pinned in `pyproject.toml`, update the pin.

## Cookbook code conventions

Every cookbook `.py` file should:
- Have a module docstring with a reference link to the GitBook page (use `#anchor` for section-specific scripts)
- Use `async def main()` + `if __name__ == "__main__": asyncio.run(main())` (or `def main()` for sync-only scripts)
- **GitBook often shows `async def main()` with `asyncio.run(...)` inside the body** — calling `main()` directly produces `RuntimeWarning: coroutine 'main' was never awaited`. Fix by changing `main()` to `def main()` when it internally uses `asyncio.run(...)`.
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

### Do not leave generated review artifacts in the repo

Files like `COOKBOOK_REVIEW_REPORT.md` are session-specific review output. Delete them before pushing; they do not belong in the cookbook and will confuse future syncs.

### Prefer `write_file` or direct Python edits over brittle patches for small files

`patch` can fail with "unexpected end of file" on small inline rewrites. For single-file fixes, prefer:
- `write_file` for full rewrites of small `.py` / markdown files
- A short Python script using `pathlib.Path.write_text` for surgical replacements

After any edit, read the file back and verify the change landed before running verification.

### Verify subproject scripts from inside the subproject directory

`uv run python <script>.py` must be run from the entry's own directory so the subproject `.venv` is selected. Running from a parent directory can pick up the wrong interpreter or missing dependencies.

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

### Router subpackage import side-effect blocks runtime verification

`gllm_pipeline.router` eagerly imports `classifier_router` at module import time. In a minimal venv, that pulls `torch` indirectly, so **even a syntax-correct router script fails before reaching `router.route(...)`** with `ModuleNotFoundError: No module named 'torch'`.

This means:
- `ruff check` and `py_compile` can pass for router examples.
- `uv run python <router_script>.py` may still fail at import time.
- Do not mark router coverage as fully verified until the actual import path is resolved; record it as `BLOCKED_ON_INFRA` / reference-only in the README until the package installs the optional `torch` dependency or its `__init__` stops eagerly importing classifier backends.

### GitBook router credential shape may be stale

The live GitBook routing pages still show:
```python
credentials="<YOUR_OPENAI_API_KEY>"
```
but the installed `gllm-pipeline v0.5.18` `build_em_invoker` / `build_lm_request_processor` APIs expect credentials as a mapping:
```python
credentials={"api_key": "<YOUR_OPENAI_API_KEY>"}
```
When manually syncing router examples, ground the credential shape against the currently installed package, not the GitBook prose.

### Token expiry mid-run

`gcloud` tokens last ~1hr. For long `sync`/`verify --all` runs, rago-sync refreshes tokens before every subprocess call. If driving `uv`/`curl` manually outside the CLI, re-run `gcloud auth print-access-token` right before each call.

### Package extras

| Import | Required extra |
|---|---|
| `OpenAILMInvoker`, `OpenAIEMInvoker`, `OpenAIRealtimeSession` | `gllm-inference[openai]` |
| `GoogleLMInvoker`, `GoogleEMInvoker` | `gllm-inference[google]` |
| `AnthropicLMInvoker` | `gllm-inference[anthropic]` |
| `ChromaDataStore` | `gllm-datastore[chroma]` |
| Any `from gllm_datastore...` import (incl. non-Chroma entries like `key_value_store`) | `gllm-datastore[chroma]` — the package `__init__` eagerly imports `ChromaDataStore`, so even entries that never touch Chroma (e.g. `OpenBaoKeyValueStore`) need the `[chroma]` extra or `ImportError: missing 'chromadb'` fires at import time. When in doubt, always add `[chroma]`. |

### Version pinning

Pin the exact latest version: `>=0.6.90,<0.7.0`, not a rounded-down floor like `>=0.6.0,<0.7.0`. A rounded-down floor may already satisfy the old lock, making `uv lock` a no-op.

#### Cross-package compatibility (critical)

Each `gllm-*` package pins its own `gllm-core` floor/ceiling. Pinning every package to "the latest" independently can produce an **unsatisfiable** resolution. Real failure during the data_store sync (PR #92): `gllm-inference==0.6.98` requires `gllm-core>=0.4.21,<0.4.37`, but the latest published `gllm-core` was `0.4.37.post1` — `uv lock` failed with "your project's requirements are unsatisfiable". Fix: drop to `gllm-inference>=0.6.95,<0.7.0` (0.6.95 allows `gllm-core<0.5.0`) so it coexists with `gllm-core>=0.4.37`. After editing any pin, always run `uv lock` and read the error — never assume "latest = compatible". Data-store-specific pin matrix and backend gotchas: see `references/datastore-gotchas.md`.

#### Cross-package import break (known GL SDK release hazard)

Even when the resolver succeeds and `uv sync` completes, the installed packages may fail at **import time** because one package imports a symbol from another that was never published.

**Observed July 2026**: `gllm-pipeline==0.5.18` imports `parallel_gather` from `gllm_core.concurrency`, but `gllm-core==0.4.24` (latest published at the same time) does not provide that symbol. Result: every cookbook script that imports `gllm_pipeline.pipeline` or `gllm_pipeline.steps` fails with `ImportError: cannot import name 'parallel_gather'` — before any cookbook logic runs. `ruff check` and `py_compile` still pass because the import is syntactically valid.

**Resolution pattern**: if the cross-package break can be resolved locally by bumping only the cookbook entry's floor pin:
1. Update cookbook `pyproject.toml` from `gllm-core==0.4.24` to `gllm-core>=0.4.37,<0.5.0` (lower-bound convention).
2. Also patch the upstream package's own minimum requirement in the gl-sdk source tree, e.g.:
   `libs/gllm-pipeline/pyproject.toml: "gllm-core>=0.3.0,<0.5.0"` → `"gllm-core>=0.4.37,<0.5.0"`.
3. Commit + open a PR in `GDP-ADMIN/gl-sdk` with the title `fix(gllm-pipeline): bump gllm-core minimum to >=0.4.37`.
4. If the user does not want the gl-sdk edit made directly, delegate it via the `ai-coding-agents` skill to Claude Code (Sonnet) so the cookbook fix and the upstream minimum-bump PR are produced in parallel.

This two-sided fix prevents every future cookbook entry from hitting the same import wall.

**Guardrail**: after `uv sync`, probe the installed packages with `scripts/verify_cross_package_imports.sh` before declaring `COMPLIANT`. The script tests the exact import chains the cookbook scripts need. If it fails, the GL SDK release is broken — file a GitHub issue in `GDP-ADMIN/gl-sdk` and mark the entry `BLOCKED_ON_INFRA`.

**Re-run this probe after bumping any `gllm-*` version pin** — the next published `gllm-pipeline` may fix the issue, or may introduce a different cross-package break.

#### `tool.uv.sources` override trap

If `pyproject.toml` uses `tool.uv.sources` to redirect packages to `gen-ai-internal`, the resolver may still pick incompatible versions from that index. Symptom: `uv lock` resolves version X in `uv.lock`, but at runtime (`uv run`) an older/newer version is silently installed because the index returned a different version during sync. Always verify the actually-installed version after `uv sync`:

```bash
uv run python -c "import gllm_inference; print(gllm_inference.__version__)"
```

If the resolved version conflicts with `gllm-core` constraints, tighten the pin (e.g. `<0.6.98` instead of `<0.7.0`) and re-lock. When in doubt, delete `.venv` before re-syncing to avoid stale package retention:

```bash
rm -rf .venv
uv lock && uv sync
```

#### `E402` (`load_dotenv()` before `gllm_*` imports) is intentional
- `rm -rf .venv` before re-syncing if the runtime-installed version disagrees with `uv.lock`
- accept `E402` as expected noise whenever `load_dotenv()` intentionally precedes `gllm_*` imports

## Router verification playbook

Router entries need more than a single README stub: every variant subdirectory also needs the standard boilerplate, and verification must use the router-specific notes in `references/routing-verification-notes.md`.

Key points from that reference:
- Hub + subdirectory boilerplate pattern for routing-style pages
- Working `pyproject.toml` with `gllm-pipeline[llmrouter]` + `gllm-inference[openai]`
- Runtime blocker: `gllm_pipeline.router` eager-imports `classifier_router` → `torch`; `ruff`/`py_compile` may pass while `uv run` still fails at import time
- GitBook router credential shape mismatch (`credentials="..."` vs installed `{"api_key": "..."}`)
- Retry pattern: delete `.venv` + `uv.lock` after editing `pyproject.toml`, then re-run `setup.sh`

## GITBOOK_DRIFT: docs are wrong, not the cookbook

`GITBOOK_DRIFT` is one of the entry states returned by `rago-sync detect`. It means *the
GitBook page documents code that cannot possibly run against the currently published package* —
an API that was renamed, removed, or never shipped to `main`.

When you see `GITBOOK_DRIFT`:
1. **Do not** run `rago-sync sync --entry`. That would fetch the broken example from GitBook
   and overwrite the cookbook script, turning a `COMPLIANT` entry into `NOT_RUNNABLE`.
2. **Do not** try to "fix" the cookbook to match the broken GitBook example.
3. **Do** open a GitHub issue in `GDP-ADMIN/gl-sdk` linking the affected GitBook page and the
   missing API name(s), tagged `documentation`.
4. Re-run `rago-sync detect` **after** the docs PR merges and the page is corrected, then
   continue with `sync --entry` + `verify`.

Typical triggers for `GITBOOK_DRIFT`:
- A `docs/gitbook-sync` commit advanced the tutorial prose ahead of `gl-sdk main` (e.g.
  `docs(gllm-pipeline): add interrupted and resumable pipeline lifecycle into HITL guide`
  was merged into `docs/gitbook-sync` before `enable_debug_tracing()` / `fork_from()` /
  `Pipeline.resume()` / `Pipeline.get_state()` landed on `main`).
- A docs PR for one feature accidentally rewrote an unrelated page with future-API copy-paste.
- A page describes a `config=` key (e.g. `debug_state`, `context=`) that the current
  `Pipeline.invoke` signature does not accept.

Resolved drift sets — do not reopen as `GITBOOK_DRIFT` without re-verification:

| Drift set | Resolution | Reference |
|---|---|---|
| Pipeline how-to pages (`execute-a-pipeline`, `debug-a-pipeline`, `human-in-the-loop`, `pausing-flow-for-debugging`) | All previously-missing APIs (`enable_debug_tracing`, `disable_debug_tracing`, `include_outputs_from`, `get_state`, `get_state_history`, `update_state`, `resume`, `fork_from`, `context=`) landed on `docs/gitbook-sync` HEAD `61a407b04`. Current four pages + three cookbook scripts all verified GREEN. | `references/gitbook-drift-pipeline-how-to-jul2026.md` (RESOLVED) |

If you encounter these four pages again, re-run the API-grounding check from that reference
before opening a new issue — `main` may have advanced further since the last check.

Session-specific incident record: see `references/gitbook-drift-pipeline-how-to-jul2026.md`
for the exact commit SHAs, method list, and corrective path for the July 2026 pipeline
how-to page drift.

## Anti-pattern: carrying forward drift claims

Before writing any "X no longer exists" or "X changed to Y" claim in a PR body, issue, or report, re-fetch and quote the *current* source file (`git show`, `gh api`, or `cat`) in the same turn. Do not rely on an earlier scan's conclusion, even within the same session — the file may have been updated, or the earlier conclusion may have been wrong (Issue #7).

## Cron

`detect --email` runs automatically every Monday 9am (Hermes cron job: `rago-sync-weekly`). `sync` is always manual.

## Source

CLI source: `$RAGO_SYNC_DIR`
GitHub: https://github.com/delfianura/documentation-sync