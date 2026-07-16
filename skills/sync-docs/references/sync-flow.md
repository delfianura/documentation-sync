# RAG-O Documentation Sync Flow - Complete Reference

Documents the end-to-end flow from weekly detection through GitBook update to Cookbook sync.

## Flow Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WEEKLY CRON (Friday 1 PM)                        │
│  rag-o-weekly-sync-check skill                                      │
│  → Detects GitBook drift + Cookbook gaps                            │
│  → Sends HTML email report                                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    HUMAN REVIEW                                     │
│  • Read email, identify priority items                              │
│  • Decide: GitBook only? Cookbook only? Full sync?                 │
│  • Assign to PR authors (from email)                               │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│              GITBOOK UPDATE (gitbook-update workflow)              │
│  /run rag-o-doc-sync-orchestrator --mode=gitbook                   │
│                                                                      │
│  For each selected item:                                           │
│  1. Run gitbook-update workflow (PR/Branch mode)                   │
│  2. Workflow creates docs branch, applies changes per rules        │
│  3. Creates PR to docs/gitbook-sync                                │
│  4. HUMAN GATE: Review PR, approve/merge                           │
│  5. On merge: docs/gitbook-sync updated                            │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│              COOKBOOK SYNC (sync-cookbook skill)                   │
│  /run rag-o-doc-sync-orchestrator --mode=cookbook                  │
│  (or --mode=full for sequential)                                   │
│                                                                      │
│  Phase 1: Inventory - GitBook pages → Cookbook gaps                │
│  Phase 2-9: Create/update entries, run tests, verify               │
│  Phase 7c: If cookbook reveals GitBook code wrong → fix both       │
│  Phase 10: Commit cookbook changes                                 │
│                                                                      │
│  HUMAN GATE: Test failures → fix or skip entry                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Human Gates (Required)

| Gate | Trigger | Decision | Who |
|------|---------|----------|-----|
| GitBook PR Review | PR created to `docs/gitbook-sync` | Approve / Request changes | You / assigned author |
| Cookbook Test Failure | `uv run script.py` fails | Fix code / Update GitBook / Skip entry | You / assigned author |
| Version Mismatch | Cookbook pins old gllm-* version | Update pin / Wait for release | You |

## GitBook Update Workflow (gitbook-update)

Located at `$GL_SDK_DEV_DIR/.ai/workflows/gitbook-update.md`

**Section-type routing:**
- Tutorials → `.ai/rules/gitbook-update-tutorials.md`
- How-to Guides → `.ai/rules/gitbook-update-how-to-guides.md`
- Resources → `.ai/rules/gitbook-update-resources.md`

**Key rules:**
- Docs branch created FROM `docs/gitbook-sync` (never from feature branch)
- Only `gitbook/**` files modified
- Conventional commits: `docs(gllm-<lib>): <description>`
- PR base: `docs/gitbook-sync` (NOT `main`)
- Reuse existing PR if same head branch exists

## Cookbook Sync (sync-cookbook skill)

Located at `~/.hermes/skills/sync-cookbook/SKILL.md`

**Entry creation (7 files minimum):**
```
gen-ai/<category>/<subcategory>/<entry_name>/
├── .env.example
├── .python-version (3.12)
├── pyproject.toml (with gllm-* deps, uv internal index)
├── uv.lock
├── setup.sh / setup.bat
├── README.md (with expected output)
└── <script_name>.py (runnable, async main, load_dotenv)
```

**Version constraints (use these ranges):**
| Package | Constraint |
|---------|------------|
| gllm-core | `>=0.4.0,<0.5.0` |
| gllm-inference | `>=0.5.0,<0.6.0` |
| gllm-datastore | `>=0.5.0,<0.6.0` |
| gllm-retrieval | `>=0.5.0,<0.6.0` |
| gllm-generation | `>=0.5.0,<0.6.0` |
| gllm-pipeline | `>=0.4.0,<0.5.0` |
| python-dotenv | `>=1.0.0,<2.0.0` |

**Extras mapping:**
- `OpenAILMInvoker` → `gllm-inference[openai]`
- `ChromaDataStore` → `gllm-datastore[chroma]`
- `SQLDataStore` → `gllm-datastore[sql]`, `gllm-retrieval[sql]`

## Repository Paths

```bash
GL_SDK_REPO=$GL_SDK_REPO
COOKBOOK_REPO=$COOKBOOK_DIR
GITBOOK_BRANCH=origin/docs/gitbook-sync
```

## Commands Cheat Sheet

```bash
# Check cron status
hermes cron list

# Run detection manually
python3 ~/.hermes/skills/devops/rag-o-weekly-sync-check/scripts/generate_report.py

# Run orchestrator (GitBook only)
/run rag-o-doc-sync-orchestrator --mode=gitbook

# Run orchestrator (Cookbook only)
/run rag-o-doc-sync-orchestrator --mode=cookbook

# Run orchestrator (Full sequential)
/run rag-o-doc-sync-orchestrator --mode=full

# View open docs PRs
gh pr list --repo gdplabs/gl-sdk --base docs/gitbook-sync --state open

# Sync gl-sdk gitbook-sync branch
cd $GL_SDK_REPO && git checkout docs/gitbook-sync && git pull origin docs/gitbook-sync
```

## Common Pitfalls

1. **Order matters**: GitBook must be updated FIRST, then Cookbook. Cookbook content mirrors GitBook examples.
2. **Human review is mandatory** for GitBook PRs - cannot auto-merge.
3. **Cookbook tests use real APIs** - need valid API keys in `.env` (OPENAI_API_KEY, etc.)
4. **Version ranges not exact pins** - Cookbook entries must use `>=x.y,<x.z` format.
5. **UV auth required** - `UV_INDEX_GEN_AI_INTERNAL_PASSWORD=$(gcloud auth print-access-token)` before any `uv` command.
6. **Token expiry** - gcloud token expires; refresh every ~10 cookbook entries during batch runs.