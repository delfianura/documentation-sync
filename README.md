# rago-sync

A local CLI tool that detects and resolves drift between **gl-sdk main → Gitbook → cookbook**. It keeps cookbook entries in sync with the canonical Gitbook documentation and the gl-sdk API surface.

---

## How it works

```
gl-sdk main  ──→  Gitbook docs  ──→  cookbook entries
                  (source of truth)    (must stay in sync)
```

`rago-sync` runs three layers of checks:

| Layer | What it checks |
|---|---|
| **Gap** | Gitbook pages with `gllm_*` imports that have no matching cookbook entry |
| **API drift** | Gitbook code uses identifiers removed from gl-sdk main |
| **Content drift** | Cookbook script diverged from the Gitbook code block |
| **Version stale** | `pyproject.toml` constraint is behind the latest published package |

---

## Requirements

- Python 3.11–3.13
- [uv](https://github.com/astral-sh/uv)
- [gh CLI](https://cli.github.com/) (for GitHub issue creation and PR polling)
- Access to the internal package registry

---

## Installation

```bash
git clone https://github.com/delfianura/documentation-sync
cd documentation-sync
uv sync
```

The CLI entry point is installed as `rago-sync`:

```bash
uv run rago-sync --help
```

---

## Configuration

Paths are set in `rago_sync/config.py`:

```python
GL_SDK_REPO      = Path("/path/to/gl-sdk")
COOKBOOK_REPO    = Path("/path/to/gen-ai-sdk-cookbook")
GITBOOK_BRANCH   = "origin/docs/gitbook-sync"
```

Update these to match your local checkout locations before running.

---

## Commands

### `detect`

Read-only scan. Writes `status.json` and `report.html`. Safe to run on a cron.

```bash
uv run rago-sync detect
uv run rago-sync detect --email   # also send the HTML report by email
```

### `status`

Print the current `status.json` as a colour-coded table.

```bash
uv run rago-sync status
```

### `sync`

Fix non-compliant entries. Requires manual trigger (writes to disk, opens issues).

```bash
uv run rago-sync sync                        # sync all non-compliant entries
uv run rago-sync sync --entry tutorials/inference/lm-invoker
```

What sync does per state:

| State | Action |
|---|---|
| `MISSING` / `TEMPLATE_MISSING` | Creates the full 7-file cookbook entry from the Gitbook page |
| `CONTENT_DRIFT` | Overwrites the `.py` script from the Gitbook code block |
| `VERSION_STALE` | Updates `pyproject.toml` constraint, runs `uv lock` + `uv sync`, verifies |
| `GITBOOK_DRIFT` | Opens a GitHub issue (deduplicates — one issue per entry) |
| `NOT_RUNNABLE` | Retries `uv run` to check if the entry now passes |

### `sync-all`

Initial full sync — runs detect then syncs everything in priority order. Use for bootstrapping.

```bash
uv run rago-sync sync-all
```

### `verify`

Run `uv run` on cookbook entries to check runnability without modifying anything.

```bash
uv run rago-sync verify                  # verify only non-compliant entries
uv run rago-sync verify --all            # verify every tracked entry
```

---

## Entry states

| State | Meaning |
|---|---|
| `COMPLIANT` | Entry exists, matches Gitbook, runs cleanly |
| `MISSING` | No cookbook entry exists for a Gitbook page |
| `TEMPLATE_MISSING` | Entry exists but is missing required files |
| `GITBOOK_DRIFT` | Gitbook code references an API removed from gl-sdk main |
| `CONTENT_DRIFT` | Cookbook script has diverged from Gitbook |
| `VERSION_STALE` | Package constraint is behind the latest published version |
| `NOT_RUNNABLE` | Entry exists and is up-to-date but `uv run` fails |
| `PENDING_REVIEW` | A PR is open for this entry — detect is paused until merged/closed |

---

## Running tests

```bash
uv run pytest tests/ -v
```

---

## Triggering via Claude Code CLI

If you use Claude Code, you can trigger rago-sync with natural language or slash commands instead of typing CLI commands directly. Install the included skills:

```bash
cp -r skills/sync-cookbook ~/.claude/skills/
cp -r skills/rag-o-doc-sync-orchestrator ~/.claude/skills/
```

Then in Claude Code:

```
/sync-cookbook detect
/sync-cookbook sync --entry tutorials/inference/lm_invoker
run detect
what's drifted?
sync everything
```

See [`skills/README.md`](skills/README.md) for full installation and usage.

---

## Project layout

```
rago_sync/
  cli.py              # Typer CLI entry point
  config.py           # Paths and constants
  state.py            # StateManager + EntryStatus dataclass
  auth.py             # Token refresh
  inspector/          # Read-only checks (gap, drift, versions, api_drift)
  syncer/             # Write actions (cookbook_updater, migration, lock_manager)
  verifier/           # uv run verification loop
  reporter/           # HTML report + GitHub issue creation + email
skills/
  sync-cookbook/      # Claude Code skill (LLM bridge to CLI)
  rag-o-doc-sync-orchestrator/  # Full flow orchestrator skill
```
