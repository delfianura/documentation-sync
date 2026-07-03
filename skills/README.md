# Claude Code Skills

These skills let you trigger rago-sync via Claude Code CLI using natural language or slash commands, instead of typing `uv run rago-sync` directly.

## How it works

```
You (natural language or /slash-command)
          ↓
Claude Code reads the skill (SKILL.md)
          ↓
Claude runs: uv run rago-sync <command>
          ↓
rago-sync Python CLI does the actual work
```

The skills are thin bridges — all logic is in the Python CLI. Skills just map intent to the right command.

---

## Installation

Copy the skill directories into your Claude Code skills folder:

```bash
cp -r skills/sync-cookbook ~/.claude/skills/
cp -r skills/gitbook-update ~/.claude/skills/
cp -r skills/gitbook-check-for-update ~/.claude/skills/
cp -r skills/rag-o-doc-sync-orchestrator ~/.claude/skills/
```

Then verify Claude Code picks them up:

```bash
claude /skills   # should list all four skills above
```

Paths are environment-overridable (see `rago_sync/config.py`), so this works on any machine, not just the original author's:

```bash
export RAGO_SYNC_GL_SDK_REPO=/path/to/gl-sdk
export RAGO_SYNC_COOKBOOK_REPO=/path/to/gen-ai-sdk-cookbook
```

---

## Skills

### `sync-cookbook` — day-to-day trigger

Use this for all normal operations: detect, sync, verify, status.

**Slash command:**
```
/sync-cookbook detect
/sync-cookbook sync
/sync-cookbook sync --entry tutorials/inference/lm_invoker
/sync-cookbook verify --all
/sync-cookbook status
```

**Natural language (Claude picks up the skill automatically):**
```
run detect
what's drifted?
sync everything
sync tutorials/inference/lm_invoker
verify all entries
show status
```

### `gitbook-update` / `gitbook-check-for-update` — GitBook side only

`gitbook-check-for-update` is read-only gap analysis (PR/branch/commit or full audit). `gitbook-update` does the actual edits: branches off `docs/gitbook-sync` in a worktree, edits `gitbook/**` only, and opens a PR back to `docs/gitbook-sync`.

### `rag-o-doc-sync-orchestrator` — entry point, asks scope + mode

Use this when you're not sure which of the above to run, or the request spans both GitBook and Cookbook. It asks two questions before doing anything:

1. **Scope**: GitBook / Cookbook / **both** (default)
2. **Mode**: routine drift check (discovery-first, via `detect`/`gitbook-check-for-update`) / **ad-hoc** update for a named PR (skips discovery, edits directly)

```
"update docs and cookbook for gl-sdk PR #5171"   → scope=both, mode=ad-hoc (PR named)
"what's out of sync with gitbook?"                → scope=gitbook, mode=routine (no PR named)
"sync everything"                                 → scope=both, mode=routine
```

---

## Skill directory layout

```
skills/
  sync-cookbook/
    SKILL.md                          ← skill definition (install this)
    references/
      gitbook-mcp-patterns.md         ← how gitbook MCP calls are structured
      verification_failure_patterns.md ← common uv run failure patterns
    scripts/
      cookbook_sync.py                ← legacy reference script (pre-CLI era)
  rag-o-doc-sync-orchestrator/
    SKILL.md                          ← skill definition (install this)
    references/
      sync-flow.md                    ← full flow documentation
```

---

## Cron (no skill needed)

The weekly detect + email runs automatically via Hermes cron — no LLM involved:

```bash
# Hermes cron job: rago-sync-weekly (Monday 9am)
cd /home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync
uv run rago-sync detect --email
```

`sync` is always manual. Never runs from cron.
