---
name: rag-o-doc-sync-orchestrator
description: Orchestrates the full RAG-O documentation sync flow - GitBook update with human review, then Cookbook sync. Use after weekly cron report identifies drift.
---

# RAG-O Documentation Sync Orchestrator

Ties together the weekly detection -> human review -> GitBook update -> Cookbook sync flow.

> **Architecture note (2026-06-26):** Cookbook sync is now backed by the rago-sync Python CLI (`uv run rago-sync`). The `sync-cookbook` skill is the LLM bridge to that CLI. Do NOT reimplement cookbook sync logic here — delegate to the CLI via the `sync-cookbook` skill.

## Flow

```
Weekly Cron Report (Friday 1 PM)
         |
         v
Human reviews email, identifies priority items
         |
         v
Run: /run rag-o-doc-sync-orchestrator --mode=full
         |
         +---> GitBook Updates (gitbook-update workflow)
         |       |
         |       v
         |   Human reviews PRs on docs/gitbook-sync
         |       |
         |       v
         |   Merge approved PRs to docs/gitbook-sync
         |
         +---> Cookbook Sync (sync-cookbook skill)
                 |
                 v
             Auto-verify runnable
                 |
                 v
             Commit cookbook changes
```

## Modes

### Mode 1: GitBook Only (`--mode=gitbook`)
Run `gitbook-update` workflow for specific PRs/components from the weekly report.

```bash
# Interactive: shows report items, lets you select which to update
rag-o-doc-sync-orchestrator --mode=gitbook
```

### Mode 2: Cookbook Only (`--mode=cookbook`)
Run `sync-cookbook` skill to sync Cookbook with current GitBook state.

```bash
rag-o-doc-sync-orchestrator --mode=cookbook
```

### Mode 3: Full Sync (`--mode=full`)
Sequential: GitBook updates -> wait for review/merge -> Cookbook sync.

```bash
rag-o-doc-sync-orchestrator --mode=full
```

## Usage

```bash
# From Hermes CLI
/run rag-o-doc-sync-orchestrator --mode=full

# Or with specific items from report
/run rag-o-doc-sync-orchestrator --mode=gitbook --items="gllm-inference:OpenAILMInvoker,gllm-pipeline:ComponentStep"
```

## Integration Points

| Step | Tool/Skill | Trigger |
|------|------------|---------|
| Detect | rag-o-weekly-sync-check (cron) | Friday 1 PM auto |
| GitBook Update | gitbook-update workflow | Human trigger via orchestrator |
| Human Review | GitHub PR on docs/gitbook-sync | Manual |
| Cookbook Sync | sync-cookbook skill | Auto after GitBook merge (or manual) |

## Configuration

```json
{
  "gl_sdk_repo": "/home/delfia-n-a-putri/Documents/Work/GEN_AI/gl-sdk",
  "cookbook_repo": "/home/delfia-n-a-putri/Documents/Work/GEN_AI/gen-ai-sdk-cookbook",
  "gitbook_branch": "docs/gitbook-sync",
  "auto_cookbook_after_gitbook": true
}
```

## Workflow Details

### GitBook Update Phase

For each selected item from weekly report:
1. Run `gitbook-update` workflow in PR/Branch mode
2. Workflow creates docs branch, applies changes per section-type rules
3. Creates PR to `docs/gitbook-sync`
4. Human reviews PR (required gate)
5. On approval, merge to `docs/gitbook-sync`

### Cookbook Sync Phase

After GitBook changes merged, invoke the `sync-cookbook` skill which delegates to the rago-sync CLI:

```bash
cd /home/delfia-n-a-putri/Documents/Work/GEN_AI/Automation/rago-sync
uv run rago-sync detect        # see what's drifted
uv run rago-sync sync          # fix all drifted entries
```

The CLI handles: gap detection, entry creation (7-file structure), script overwrite, version constraint update, verify loop, issue creation, and state persistence. No manual steps needed.

## Human Gates

| Gate | Decision | Who |
|------|----------|-----|
| GitBook PR review | Approve/Request changes | You / assigned author |
| Cookbook test failures | Fix/skip entry | You / assigned author |
| Version mismatch resolution | Update pin/skip | You |

## References

- `references/sync-flow.md` — Complete flow documentation with commands and pitfalls