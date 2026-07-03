---
name: rag-o-doc-sync-orchestrator
description: Orchestrates the full RAG-O documentation sync flow — GitBook update and/or Cookbook sync, either as a routine drift check or an ad-hoc PR-driven update. Entry point for "update the docs", "sync gitbook and cookbook for PR #X", or the weekly drift report follow-up.
---

# RAG-O Documentation Sync Orchestrator

Ties together GitBook update (`gitbook-update` skill) and Cookbook sync (`sync-cookbook` skill / rago-sync CLI). Delegates all actual logic to those two skills — this skill only decides **what** to run and **how**.

> Do NOT reimplement GitBook-editing or cookbook-syncing logic here. Delegate to `gitbook-update`, `gitbook-check-for-update`, and `sync-cookbook`.

## Step 1 — Ask what to update (scope)

Unless the user's request already makes this obvious, ask:

**"Update GitBook, Cookbook, or both?"** (default: **both** — this is what "sync the docs" / "update docs for PR #X" implies unless the user names just one side)

| Scope | What runs |
|---|---|
| `gitbook` | `gitbook-update` (+ `gitbook-check-for-update` first if not already scoped) only |
| `cookbook` | `sync-cookbook` only |
| `both` (default) | `gitbook-update` first, then `sync-cookbook` for the same change |

## Step 2 — Ask the mode

**"Is this a routine drift check, or an ad-hoc update for a specific PR/feature?"**

| Mode | Trigger | What it means |
|---|---|---|
| **Routine check** | weekly cron report, "check for drift", no specific PR named | Discovery-driven — run `gitbook-check-for-update` (full audit or named branch) to find gaps, then `sync-cookbook`'s `detect`/`status` to find cookbook drift, before touching any files |
| **Ad-hoc update** | user names a specific PR/issue/feature ("update docs for gl-sdk PR #5171") | You already know the change and the affected page(s) — skip discovery, go straight to editing per the procedure below |

Default to **ad-hoc** whenever a PR number, PR URL, branch name, or specific feature is named in the request. Default to **routine check** when the request is generic ("check gitbook", "what's out of sync", weekly report follow-up).

## Ad-hoc procedure (scope = gitbook or both)

This is the concrete, verified procedure — not a generic description:

1. **Identify the change.** `gh pr view <PR>` to get the diff/summary. Search GitBook (`mcp__claude_ai_Gitbook__searchDocumentation`, then `getPage`) for the page(s) covering the changed component.
2. **Set up an isolated worktree on `docs/gitbook-sync`:**
   ```bash
   git -C <gl-sdk-repo> fetch origin docs/gitbook-sync main
   git worktree add <worktree-path> origin/docs/gitbook-sync -b docs/<feature-branch-name>
   ```
   Never edit `docs/gitbook-sync` directly — always branch off it into a new `docs/*` branch, in a worktree separate from any feature-branch checkout.
3. **Edit only `gitbook/**` files** in that worktree, following the `gitbook-update` skill's section-type rules (tutorials / how-to guides / resources).
4. **Verify against the real merged code**, not the doc's claims:
   - Install the library from that worktree's checked-out commit (`uv pip install -p <venv> -e <path-to-lib>` with `UV_INDEX_GEN_AI_INTERNAL_USERNAME`/`PASSWORD` set from `gcloud auth print-access-token`) and actually run every code example from the doc. If an example fails, fix the doc (or flag a real product bug) before proceeding — never leave a non-runnable example in place "because the PR author verified it."
5. **Commit only `gitbook/**`, push the branch, open a draft PR against `docs/gitbook-sync`** (not `main`) via `gh pr create --base docs/gitbook-sync`.

## Ad-hoc procedure (scope = cookbook or both)

Runs after (or independent of) the GitBook step above:

1. **Locate the cookbook entry** for the affected page (`gen-ai/tutorials/... ` etc. in the cookbook repo). If none exists yet, this is effectively a `MISSING` entry — consider `sync-cookbook`'s `sync --entry <path>` to bootstrap it, or `create_entry` conventions if fully ad-hoc.
2. **Two-way sync gotcha:** if the GitBook docs PR from the previous section is not yet merged, the *live* GitBook page hasn't changed — `rago-sync sync --entry` compares against the live page and won't see it. Edit the cookbook script by hand to mirror the (unmerged) docs PR's diff instead.
3. **Verify against the real *published* package version**, not source — cookbook entries install from the internal package index, not the gl-sdk repo. A feature just merged to `main` is not necessarily released yet:
   ```bash
   cd /home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync
   uv run python -c "from rago_sync.inspector.versions import get_latest_version; print(get_latest_version('<package>'))"
   ```
   If the currently-pinned floor predates the feature, binary-search published versions (download+grep each tarball, or just trust `get_latest_version`) to find the *first* version that has it, and pin the entry's `pyproject.toml` to exactly that version (not a rounded-down `X.Y.0` — see `sync-cookbook` gotcha 6). Re-run `uv lock && uv run <script>.py` and confirm output matches the README.
4. **Commit, push, open a PR** against the cookbook repo's `main` (separate PR from the GitBook one — different repos).

## Routine-check procedure

1. Run `gitbook-check-for-update` in Full Audit mode (no PR/branch given) or PR/branch mode (if a branch was named) — read-only, produces a gap report.
2. Run `sync-cookbook`'s `detect`/`status` — read-only, produces cookbook drift state.
3. Present both reports to the user and ask which items to act on before running the ad-hoc procedure per item.

## Configuration

Paths are environment-overridable (see `rago_sync/config.py`) so this is reproducible on any machine:

```bash
export RAGO_SYNC_GL_SDK_REPO=/path/to/gl-sdk
export RAGO_SYNC_COOKBOOK_REPO=/path/to/gen-ai-sdk-cookbook
```

## Human Gates

| Gate | Decision | Who |
|------|----------|-----|
| GitBook PR review | Approve/Request changes | You / assigned author |
| Cookbook PR review | Approve/Request changes | You / assigned author |
| Version bump breaking-change check | Fix/skip entry | You (rago-sync auto-opens an issue if `classify_version_bump` flags it breaking) |

## References

- `references/sync-flow.md` — background on the original cron-triggered flow (pre-dates the ad-hoc procedure above)
- `../gitbook-update/SKILL.md`, `../gitbook-check-for-update/SKILL.md` — GitBook-side detail
- `../sync-cookbook/SKILL.md` — Cookbook-side detail, including all known gotchas
