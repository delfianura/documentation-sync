# Claude Code Skills

These skills let you trigger rago-sync via Claude Code CLI using natural language or slash commands, instead of typing `uv run rago-sync` directly.

## How it works

```
You (natural language or /slash-command)
          ↓
Claude Code reads the skill (SKILL.md)
          ↓
Claude runs: uv run rago-sync <command>   (cookbook side)
    and/or edits gitbook/** in a worktree  (gitbook side)
          ↓
rago-sync Python CLI does the cookbook work
```

`sync-docs` is the thin bridge and entry point — all cookbook logic is in the Python CLI, all gitbook logic is in `gitbook-update`/`gitbook-check-for-update`. Skills just map intent to the right command.

---

## Installation

Copy the skill directories into your Claude Code skills folder:

```bash
cp -r skills/sync-cookbook ~/.claude/skills/
cp -r skills/sync-docs ~/.claude/skills/
cp -r skills/gitbook-update ~/.claude/skills/
cp -r skills/gitbook-check-for-update ~/.claude/skills/
```

Then verify Claude Code picks them up:

```bash
claude /skills   # should list sync-docs, gitbook-update, gitbook-check-for-update
```

Paths are environment-overridable (see `rago_sync/config.py`), so this works on any machine, not just the original author's:

```bash
export RAGO_SYNC_GL_SDK_REPO=/path/to/gl-sdk
export RAGO_SYNC_COOKBOOK_REPO=/path/to/gen-ai-sdk-cookbook
```

---

## Skills

### `sync-docs` — entry point, asks scope + mode

Use this for everything — day-to-day cookbook operations, GitBook-only requests, or anything spanning both. It asks two questions before doing anything (skipping either if the request already answers it):

1. **Scope**: GitBook / Cookbook / **both** (default)
2. **Mode**: routine drift check (discovery-first, via `detect`/`gitbook-check-for-update`) / **ad-hoc** update for a named PR (skips discovery, edits directly)

```
"update docs and cookbook for gl-sdk PR #5171"   → scope=both, mode=ad-hoc (PR named)
"what's out of sync with gitbook?"                → scope=gitbook, mode=routine (no PR named)
"sync everything"                                 → scope=both, mode=routine
"sync tutorials/inference/lm_invoker"              → scope=cookbook, direct rago-sync command
```

**Cookbook-only shortcuts** (bypass the scope/mode questions when you just want the raw CLI command):
```
/sync-docs detect
/sync-docs sync
/sync-docs sync --entry tutorials/inference/lm_invoker
/sync-docs verify --all
/sync-docs status
/sync-docs verify-coverage --ruff    # check codeblock-map.yaml against cookbook
```

### `gitbook-update` / `gitbook-check-for-update` — GitBook side only

`gitbook-check-for-update` is read-only gap analysis (PR/branch/commit or full audit). `gitbook-update` does the actual edits: branches off `docs/gitbook-sync` in a worktree, edits `gitbook/**` only, and opens a PR back to `docs/gitbook-sync`. `sync-docs` delegates to these for the GitBook side — you normally don't need to invoke them directly.

---

## Skill directory layout

```
skills/
  sync-docs/
    SKILL.md                          ← skill definition (install this)
    references/
      gitbook-mcp-patterns.md         ← how gitbook MCP calls are structured
      verification_failure_patterns.md ← common uv run failure patterns
      sync-flow.md                    ← background on the original cron-triggered flow
      codeblock-map.yaml              ← YAML map: GitBook page → code blocks → .py files
    scripts/
      cookbook_sync.py                ← legacy reference script (pre-CLI era)
      generate_map.py                 ← auto-generate codeblock-map.yaml from cookbook .py files
      verify_coverage.py              ← checks codeblock-map.yaml against cookbook files
  gitbook-update/
    SKILL.md
    rules/
      gitbook-update-tutorials.md
      gitbook-update-how-to-guides.md
      gitbook-update-resources.md
  gitbook-check-for-update/
    SKILL.md
```

---

## Cron (no skill needed)

The weekly detect + email runs automatically via Hermes cron — no LLM involved:

```bash
# Hermes cron job: rago-sync-weekly (Monday 9am)
cd $RAGO_SYNC_DIR
uv run rago-sync detect --email
```

`sync` is always manual. Never runs from cron.
