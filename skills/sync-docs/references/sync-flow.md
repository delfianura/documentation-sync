# RAGO Documentation Sync Flow — Background Reference

Documents the end-to-end flow from weekly detection through GitBook update to Cookbook sync.
This is background context only — the actual logic lives in the `rago-sync` CLI and the
`sync-docs` / `gitbook-update` / `gitbook-check-for-update` skills.

## Flow Overview

```
              WEEKLY CRON (Friday 1 PM)
              rago-sync detect --email
              → Detects GitBook drift + Cookbook gaps
              → Sends HTML email report
                          │
                          ▼
              HUMAN REVIEW
              • Read email, identify priority items
              • Decide: GitBook only? Cookbook only? Full sync?
              • Assign to PR authors (from email)
                          │
                          ▼
              GITBOOK UPDATE (gitbook-update skill)
              For each selected item:
              1. Run gitbook-update (PR/Branch mode)
              2. Creates docs branch, applies changes per rules
              3. Creates PR to docs/gitbook-sync
              4. HUMAN GATE: Review PR, approve/merge
              5. On merge: docs/gitbook-sync updated
                          │
                          ▼
              COOKBOOK SYNC (sync-cookbook skill)
              cd $RAGO_SYNC_DIR && uv run rago-sync sync

              Phase 1: Inventory - GitBook pages → Cookbook gaps
              Phase 2-9: Create/update entries, run tests, verify
              Phase 10: Commit cookbook changes

              HUMAN GATE: Test failures → fix or skip entry
```

## Human Gates (Required)

| Gate | Trigger | Decision | Who |
|------|---------|----------|-----|
| GitBook PR Review | PR created to `docs/gitbook-sync` | Approve / Request changes | You / assigned author |
| Cookbook Test Failure | `uv run script.py` fails | Fix code / Update GitBook / Skip entry | You / assigned author |
| Version Mismatch | Cookbook pins old gllm-* version | Update pin / Wait for release | You |

## GitBook Update Workflow

Located at `$GL_SDK_REPO/.ai/workflows/gitbook-update.md`

**Section-type routing:**
- Tutorials → `.ai/rules/gitbook-update-tutorials.md`
- How-to Guides → `.ai/rules/gitbook-update-how-to-guides.md`
- Resources → `.ai/rules/gitbook-update-resources.md`

**Key rules:**
- Docs branch created FROM `docs/gitbook-sync` (never from feature branch)
- Only `gitbook/**` files modified
- Conventional commits: `docs(gllm-<lib>): <description>`
- PR base: `docs/gitbook-sync` (NOT `main`)

## Cookbook Sync

Skill: `sync-cookbook` (see `$RAGO_SYNC_DIR/skills/sync-cookbook/SKILL.md`)

**Entry creation (7 files minimum):**
```
gen-ai/<category>/<subcategory>/<entry_name>/
├── .env.example
├── .python-version
├── pyproject.toml (with gllm-* deps, uv internal index)
├── uv.lock
├── setup.sh / setup.bat
├── README.md (with expected output)
└── <script_name>.py (runnable, async main, load_dotenv)
```

**Version constraints:** Always use `>=x.y,<x.z` ranges. Check the latest published
versions with:
```bash
uv pip index versions gllm-core --extra-index-url "$REGISTRY_URL" 2>&1 | head -3
```

## Commands Cheat Sheet

```bash
# Run detection manually
cd $RAGO_SYNC_DIR && uv run rago-sync detect --email

# Sync cookbook entries
cd $RAGO_SYNC_DIR && uv run rago-sync sync
cd $RAGO_SYNC_DIR && uv run rago-sync sync --entry tutorials/inference/lm_invoker

# Verify cookbook entries
cd $RAGO_SYNC_DIR && uv run rago-sync verify --all

# View open docs PRs
gh pr list --repo gdplabs/gl-sdk --base docs/gitbook-sync --state open

# Sync gl-sdk gitbook-sync branch
cd $GL_SDK_REPO && git checkout docs/gitbook-sync && git pull origin docs/gitbook-sync
```

## Common Pitfalls

1. **Order matters**: GitBook must be updated FIRST, then Cookbook. Cookbook content mirrors GitBook examples.
2. **Human review is mandatory** for GitBook PRs — cannot auto-merge.
3. **Cookbook tests use real APIs** — need valid API keys in `.env` (OPENAI_API_KEY, etc.)
4. **Version ranges not exact pins** — Cookbook entries must use `>=x.y,<x.z` format.
5. **UV auth required** — `UV_INDEX_GEN_AI_INTERNAL_PASSWORD=$(gcloud auth print-access-token)` before any `uv` command.
6. **Token expiry** — gcloud token expires; refresh every ~10 cookbook entries during batch runs.