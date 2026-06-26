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
| `CONTENT_DRIFT` | Cookbook script diverged from Gitbook | Yes — overwrites script |
| `VERSION_STALE` | pyproject.toml behind latest published version | Yes — updates constraint + uv lock |
| `GITBOOK_DRIFT` | Gitbook code uses removed API | Opens GitHub issue (human must fix) |
| `NOT_RUNNABLE` | uv run fails | Retries verify; escalates to human if still failing |
| `PENDING_REVIEW` | PR open for this entry | Paused; resumes after PR merged/closed |

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
