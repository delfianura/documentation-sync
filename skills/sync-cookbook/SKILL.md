---
name: sync-cookbook
description: RAGO Sync — detect and fix drift between gl-sdk main → Gitbook → cookbook. Backed by the rago-sync Python CLI at /home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync. Use for any drift detection, sync, verify, or status check.
---

# sync-cookbook

LLM bridge to the rago-sync CLI. All logic lives in Python — this skill just maps intent to the right command and runs it.

## How triggering works

Previously this was a prompt-based skill (LLM did the steps). Now it is full Python code. The LLM's job is to:
1. Interpret what the user wants
2. Run the appropriate `uv run rago-sync <command>` call
3. Show the output

The CLI is the source of truth. Do not reimplement any logic here.

## Trigger phrases → commands

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

## Execution

Every command runs from the rago-sync project root:

```bash
cd /home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync
uv run rago-sync <command> [options]
```

## Auth

- `detect` and `status` — no auth needed (read-only)
- `sync`, `sync-all`, `verify` — require gcloud auth; the CLI handles `refresh_token()` automatically

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

### 7. When a PR is specifically named (e.g. "sync cookbook for gl-sdk PR #5171"), skip `detect`

If the user gives you a specific gl-sdk PR/feature and you have already (a) located the affected GitBook page/section, (b) updated and verified it (e.g. via the `gitbook-update` skill), and (c) confirmed the cookbook entry's runnability against the real merged code, you do not need to run `detect`/`status` first — go straight to editing the cookbook entry to match the new GitBook content and cookbook conventions, then verify + open a PR. `detect` is for discovering *what's* drifted across the whole cookbook; it's unnecessary overhead when the entry and the fix are already known.

Two-way sync note: `gitbook-update` writes to a `docs/*` branch/PR against `docs/gitbook-sync` — the live GitBook page doesn't update until that PR is merged and published. `rago-sync sync --entry` compares against the *live* published GitBook page, so it won't see an unmerged docs PR's content. When acting on a not-yet-merged docs PR, edit the cookbook entry by hand to mirror that PR's diff (not via `rago-sync sync`), and verify runnability against the real released package version — do not assume the just-merged gl-sdk feature is already published; check `get_latest_version` and bump the entry's floor to the exact first version that has it (see gotcha 6).

### 8. Token expiry mid-run

A `gcloud` access token lasts ~1hr. Long `sync`/`sync-all`/`verify --all` runs over many entries can outlive it, causing spurious 401s partway through. This is now handled inside rago-sync (`refresh_token()` is called immediately before every `uv lock`/`uv sync`/`uv run` subprocess call, and the verifier retries once via `uv sync` on an `AUTH_ERROR` failure category). If you're driving `uv`/`curl` manually outside the CLI (e.g. probing package versions by hand), re-run `gcloud auth print-access-token` right before each call rather than reusing an old export, and remember raw `curl` needs `-L` — the internal registry 307-redirects tarball downloads.

## Cron

`detect --email` runs automatically every Monday 9am (Hermes cron job: `rago-sync-weekly`).
`sync` is always manual — never triggered from cron.

## Example session

```
You: run detect
→ uv run rago-sync detect

You: what's drifted?
→ uv run rago-sync status

You: sync tutorials/inference/lm_invoker
→ uv run rago-sync sync --entry tutorials/inference/lm_invoker

You: verify all
→ uv run rago-sync verify --all
```

## Source

CLI source: `/home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync`
GitHub: https://github.com/delfianura/documentation-sync
