---
name: sync-docs
description: RAGO doc sync — GitBook and/or Cookbook, as a routine drift check or an ad-hoc PR-driven update. Entry point for "update the docs", "sync gitbook/cookbook for PR #X", "what's out of sync", or the weekly drift report follow-up. Backed by the rago-sync Python CLI plus the gitbook-update/gitbook-check-for-update skills.
---

# sync-docs

Single entry point for keeping GitBook and the Cookbook in sync with gl-sdk. Delegates all actual logic elsewhere — this skill only decides **what** to run and **how**, then runs it.

- GitBook edits/detection → `gitbook-update` / `gitbook-check-for-update` skills
- Cookbook edits/detection → the rago-sync CLI (`uv run rago-sync <command>`) at `/home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync`

Do not reimplement GitBook-editing or cookbook-syncing logic here.

## Step 1 — Scope: GitBook, Cookbook, or both?

Ask unless the request already makes it obvious. **Default: both** — "sync the docs" / "update docs for PR #X" implies both sides unless the user names just one.

| Scope | What runs |
|---|---|
| `gitbook` | `gitbook-update` (+ `gitbook-check-for-update` first, if in routine mode) |
| `cookbook` | rago-sync CLI only |
| `both` (default) | `gitbook-update` first, then the cookbook side, for the same change |

## Step 2 — Mode: routine check, or ad-hoc for a named PR?

| Mode | Trigger | What it means |
|---|---|---|
| **Routine check** | weekly cron report, "check for drift", no specific PR named | Discovery first: `gitbook-check-for-update` (full audit or named branch) + rago-sync `detect`/`status`, before touching any files |
| **Ad-hoc update** | user names a specific PR/issue/feature ("update docs for gl-sdk PR #5171") | You already know the change and the affected page(s) — skip discovery, edit directly per the procedure below |

Default to **ad-hoc** whenever a PR number, PR URL, branch name, or specific feature is named. Default to **routine check** for generic requests ("check gitbook", "what's out of sync", weekly report follow-up).

## Routine-check procedure

1. Run `gitbook-check-for-update` (full audit, or PR/branch mode if a branch was named) — read-only, produces a gap report.
2. Run `uv run rago-sync detect` / `status` — read-only, produces cookbook drift state.
3. Present both reports and ask which items to act on, then run the ad-hoc procedure below per item.

## Ad-hoc procedure — GitBook side (scope = gitbook or both)

1. **Identify the change.** `gh pr view <PR>` for the diff/summary. Search GitBook (`mcp__claude_ai_Gitbook__searchDocumentation`, then `getPage`) for the page(s) covering the changed component.
2. **Set up an isolated worktree on `docs/gitbook-sync`** — never edit that branch directly:
   ```bash
   git -C <gl-sdk-repo> fetch origin docs/gitbook-sync main
   git worktree add <worktree-path> origin/docs/gitbook-sync -b docs/<feature-branch-name>
   ```
3. **Edit only `gitbook/**`** in that worktree, following the `gitbook-update` skill's section-type rules (tutorials / how-to guides / resources).
4. **Verify against the real merged code, not the doc's claims.** Install the library from that worktree's checked-out commit into a venv (`uv pip install -p <venv> -e <path-to-lib>`, with `UV_INDEX_GEN_AI_INTERNAL_USERNAME`/`PASSWORD` set from `gcloud auth print-access-token`) and actually run every code example. Fix the doc before proceeding if any example fails.
5. **Commit only `gitbook/**`, push, open a draft PR against `docs/gitbook-sync`** (not `main`) via `gh pr create --base docs/gitbook-sync`.

## Ad-hoc procedure — Cookbook side (scope = cookbook or both)

1. **Locate the cookbook entry** for the affected page. If none exists, this is effectively `MISSING` — bootstrap via `uv run rago-sync sync --entry <path>` or by hand following the 7-file convention.
2. **Two-way sync gotcha:** if the GitBook docs PR above isn't merged yet, the *live* GitBook page hasn't changed — `rago-sync sync --entry` compares against the live page and won't see it. Edit the cookbook script by hand to mirror the unmerged docs PR's diff instead.
3. **Verify against the real *published* package version**, not source — cookbook entries install from the internal package index, and a feature just merged to `main` is not necessarily released yet:
   ```bash
   cd /home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync
   uv run python -c "from rago_sync.inspector.versions import get_latest_version; print(get_latest_version('<package>'))"
   ```
   If the pinned floor predates the feature, find the first published version that has it and pin the entry's `pyproject.toml` to exactly that version (not a rounded-down `X.Y.0` — see gotcha 6 below). Re-run `uv lock && uv run <script>.py` and confirm output matches the README.
4. **Gate before opening the PR:** if verification found an entry fails for any reason other than missing credentials/infra (`NOT_RUNNABLE` per gotcha #4) — e.g. `NameError` from an undefined variable copied verbatim from GitBook pseudocode — fix it or drop it from this PR. Do not ship an entry with a "Notes" column admitting it's broken; that's not a status report, it's an unfixed bug. See `references/verification_failure_patterns.md` #7–9 (found via PR #78 review: three entries were opened as known-broken pseudocode, plus an import-path mismatch and a dropped `load_dotenv()`/`python-dotenv` pairing slipped through).
5. **Verify codeblock coverage** before opening the PR:
   ```bash
   python3 skills/sync-docs/scripts/verify_coverage.py --ruff \
     --cookbook-root /path/to/gen-ai-sdk-cookbook
   ```
   This checks the coverage map (`references/codeblock-map.yaml`) for missing files, orphans, docstring URLs, and ruff. If you added/removed code blocks, update `codeblock-map.yaml` first (see "Codeblock coverage map" below).

6. **Commit, push, open a PR** against the cookbook repo's `main` (a separate PR from the GitBook one — different repos).

## Codeblock coverage map

A YAML file at `references/codeblock-map.yaml` maps every GitBook tutorial page → code block headings → cookbook `.py` file. This is the authoritative registry of what the cookbook must cover.

**Structure:**
```yaml
https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/core/component:
  entry_dir: core/component
  blocks:
    - heading: "Quickstart: Define Your First Component"
      gitbook_anchor: "#quickstart"
      cookbook_file: quickstart.py
      runnable: true
      notes: "TextFormatter with @main + execute + input schema"
```

**When adding new tutorial entries**: add a new top-level key with the GitBook page URL, `entry_dir`, and a `blocks` list.

**When GitBook adds a new code block**: add a new entry to the page's `blocks` list, create the `.py` file, and re-run `verify_coverage.py`.

**How-to-guide vs tutorial page**: some cookbook entries reference how-to-guide pages (e.g. `how-to-guides/add-a-custom-component`) while a tutorial page also exists for the same topic. Keep the existing `.py` file referencing the how-to-guide and add new `.py` files for the tutorial page's blocks. Both map to the same `entry_dir`. The README should list both references.

**Verification script checks:**
1. Missing files — block in map but no `.py` file
2. Orphans — `.py` file not in map (aggregated per `entry_dir`)
3. Docstring URLs — each `.py` references correct GitBook page
4. Duplicates — same `cookbook_file` listed twice
5. Ruff (with `--ruff`) — all mapped files pass `ruff check --select E,W,F`

## Trigger phrases → rago-sync commands (cookbook-only shortcuts)

| What you say | Command to run |
|---|---|
| "detect drift", "run detect", "check sync status", "weekly check" | `detect` |
| "detect and email", "send report" | `detect --email` |
| "sync everything", "fix all drift" | `sync` |
| "sync `<entry path>`" | `sync --entry <path>` |
| "initial sync", "bootstrap cookbook", "sync-all" | `sync-all` |
| "verify entries", "check runnable" | `verify` |
| "verify all entries" | `verify --all` |
| "show status", "what's drifted" | `status` |

Every command runs from the rago-sync project root:
```bash
cd /home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync
uv run rago-sync <command> [options]
```

## Configuration

Paths are environment-overridable (`rago_sync/config.py`) — reproducible on any machine, not just the original author's:
```bash
export RAGO_SYNC_GL_SDK_REPO=/path/to/gl-sdk
export RAGO_SYNC_COOKBOOK_REPO=/path/to/gen-ai-sdk-cookbook
```

## Auth

- `detect` and `status` — no auth needed (read-only)
- `sync`, `sync-all`, `verify` — require gcloud auth; the CLI refreshes the token before every `uv lock`/`uv sync`/`uv run` call automatically

## Output files

| File | Purpose |
|---|---|
| `rago_sync/status.json` | Persistent state across runs |
| `rago_sync/report.html` | Latest HTML report (written by `detect`) |

## Entry states reference

| State | Meaning | Auto-fixed by sync? |
|---|---|---|
| `COMPLIANT` | All good | — |
| `MISSING` | No cookbook entry for a Gitbook page | Yes — creates 7-file entry |
| `TEMPLATE_MISSING` | Required files absent | Yes — recreates entry |
| `CONTENT_DRIFT` | Cookbook script diverged from Gitbook | Yes — overwrites script from Gitbook |
| `VERSION_STALE` | pyproject.toml behind latest published version | Yes — updates constraint + uv lock |
| `GITBOOK_DRIFT` | Gitbook code uses removed API | Opens GitHub issue (human must fix) |
| `NOT_RUNNABLE` | uv run fails | Retries verify; escalates to human if still failing |
| `PENDING_REVIEW` | PR open for this entry | Paused; resumes after PR merged/closed |

## Known gotchas (from real usage)

### 1. Sparse checkout — entries appear MISSING when they are not

The cookbook repo may use sparse checkout. If `gen-ai/tutorials/` is not checked out locally, `detect` will mark everything in it as `MISSING` even though the entries exist on `main`.

Before running detect, check:
```bash
git -C /home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook sparse-checkout list
```

If the section you care about is missing, add it:
```bash
git -C /home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook sparse-checkout add gen-ai/tutorials/inference
git -C /home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook checkout
```

Also verify the branch:
```bash
git -C /home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook branch --show-current
```

If it is not `main`, switch first: `git -C ... checkout main`

### 2. CONTENT_DRIFT sync overwrites the whole script

`sync` on a `CONTENT_DRIFT` entry replaces the `.py` file with the first Python block from Gitbook. If the cookbook script has additions that are not in Gitbook (e.g. `catalog = PromptBuilderCatalog.from_records(records=records)`), those lines will be lost.

Before syncing CONTENT_DRIFT entries, inspect what will be overwritten:
```bash
cat /home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook/gen-ai/<entry_path>/*.py
```

If the file has intentional local additions, do not run `sync` on that entry. Restore manually after if needed.

### 3. `source` field required for correct Gitbook content lookup

The `source` field in `status.json` stores the original Gitbook-relative path (e.g. `tutorials/inference/lm-invoker/README.md`). The entry key is the cookbook path (e.g. `tutorials/inference/lm_invoker`). `sync` uses `source` internally to fetch the right Gitbook page. If `source` is missing from a status entry (old detect run), re-run `detect` before syncing.

### 4. NOT_RUNNABLE after sync is expected for credential-dependent entries

Entries that require Google service account credentials will always be `NOT_RUNNABLE` locally without auth. The generated code is valid — it just cannot execute without real credentials. This is not a bug.

### 5. `uv pip index versions` no longer exists (uv 0.9.17+) — fixed upstream

`get_latest_version()` used to shell out to `uv pip index versions <pkg>`. That subcommand was removed and now errors with `unrecognized subcommand 'index'`, so on older builds of rago-sync `VERSION_STALE` was **never detected** — the function silently returned `None` for every package. This has been fixed in rago-sync to query the PEP 503 simple index directly (`GET <registry>/<package>/`, parsed for `pkg-X.Y.Z.tar.gz` links, highest version wins). If `check_version_stale` ever reports nothing changed for a long time, suspect this path first — verify with:
```bash
cd /home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync
uv run python -c "from rago_sync.inspector.versions import get_latest_version; print(get_latest_version('gllm-inference'))"
```
It should print a real version, not `None`.

### 6. VERSION_STALE fix must pin the exact latest version, not round down

`update_version_constraint` used to set the floor to `_base_minor(latest)` (e.g. latest `0.6.90` → floor `0.6.0`). If the stale pinned version (e.g. `0.6.77`) already satisfied that same rounded-down floor, `uv lock` had nothing forcing it to re-resolve and silently kept the old version — the "fix" was a no-op. This is now fixed to pin `>=<exact latest>,<next-minor>`, which invalidates the old lock entry and forces `uv lock` to actually upgrade. When manually bumping a cookbook entry's version floor, always pin the exact version you verified works, not a rounded-down one.

### 7. When a PR is specifically named, this is ad-hoc mode — skip `detect`

See Step 2 above. `detect` is for discovering *what's* drifted across the whole cookbook; it's unnecessary overhead when the entry and the fix are already known.

### 8. Token expiry mid-run

A `gcloud` access token lasts ~1hr. Long `sync`/`sync-all`/`verify --all` runs over many entries can outlive it, causing spurious 401s partway through. This is now handled inside rago-sync (`refresh_token()` is called immediately before every `uv lock`/`uv sync`/`uv run` subprocess call, and the verifier retries once via `uv sync` on an `AUTH_ERROR` failure category). If you're driving `uv`/`curl` manually outside the CLI (e.g. probing package versions by hand), re-run `gcloud auth print-access-token` right before each call rather than reusing an old export, and remember raw `curl` needs `-L` — the internal registry 307-redirects tarball downloads.

### 9. `NOT_RUNNABLE` due to missing infra/credentials vs. actually broken — don't conflate them

Gotcha #4 says missing-credential `NOT_RUNNABLE` is expected and fine to ship. That is NOT the same as a `NameError` from a variable GitBook's snippet never defined (pseudocode copied verbatim), a wrong import path, or a dropped `load_dotenv()`/`python-dotenv` pairing — those are real bugs that must be fixed or the entry dropped before the PR is opened, not noted and shipped anyway. See gate in the ad-hoc Cookbook procedure step 4 and `references/verification_failure_patterns.md` #7–10. (Found via gen-ai-sdk-cookbook PR #78 review — three entries were opened as known-broken, plus an import mismatch and inconsistent env-loading slipped past.)

## Human Gates

| Gate | Decision | Who |
|---|---|---|
| GitBook PR review | Approve/Request changes | You / assigned author |
| Cookbook PR review | Approve/Request changes | You / assigned author |
| Version bump breaking-change check | Fix/skip entry | You (rago-sync auto-opens an issue if `classify_version_bump` flags it breaking) |

## Cron

`detect --email` runs automatically every Monday 9am (Hermes cron job: `rago-sync-weekly`).
`sync` is always manual — never triggered from cron.

## Example session

```
You: what's out of sync with gitbook?
→ scope=gitbook, mode=routine → gitbook-check-for-update (full audit)

You: update docs and cookbook for gl-sdk PR #5171
→ scope=both, mode=ad-hoc → gitbook-update, then cookbook procedure above

You: sync everything
→ scope=both, mode=routine → gitbook-check-for-update + uv run rago-sync detect

You: sync tutorials/inference/lm_invoker
→ uv run rago-sync sync --entry tutorials/inference/lm_invoker

You: verify all
→ uv run rago-sync verify --all
```

## Source

CLI source: `/home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync`
GitHub: https://github.com/delfianura/documentation-sync
