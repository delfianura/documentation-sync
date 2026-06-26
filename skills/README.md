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
# sync-cookbook (main skill — use this for day-to-day operations)
cp -r skills/sync-cookbook ~/.claude/skills/

# rag-o-doc-sync-orchestrator (full flow orchestrator)
cp -r skills/rag-o-doc-sync-orchestrator ~/.claude/skills/
```

Then verify Claude Code picks them up:

```bash
claude /skills   # should list sync-cookbook and rag-o-doc-sync-orchestrator
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

### `rag-o-doc-sync-orchestrator` — full flow

Use after receiving the weekly email report to orchestrate the full GitBook → Cookbook sync cycle.

```
/rag-o-doc-sync-orchestrator --mode=cookbook   # cookbook sync only
/rag-o-doc-sync-orchestrator --mode=full        # gitbook update + cookbook sync
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
