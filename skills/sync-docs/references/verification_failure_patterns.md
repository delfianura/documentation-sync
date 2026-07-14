# Verification Failure Patterns Reference

Documented from the 2026-06-12 comprehensive sync run (65 entries verified).

## Summary Statistics

| Status | Count | Percentage |
|--------|-------|------------|
| PASS | 6 | 9% |
| FAIL | 59 | 91% |
| SKIPPED | 0 | 0% |

## Root Cause Analysis

### 1. Package Registry Authentication (401 Unauthorized) — ~45% of failures

**Error Pattern:**
```
Failed to download and build `gllm-inference==0.6.40`
Failed to fetch: `https://glsdk.gdplabs.id/gen-ai-internal/gllm-inference/gllm_inference-0.6.40.tar.gz`
HTTP status client error (401 Unauthorized) for url
```

**Root Cause:** `uv` cannot access the private PyPI index at `https://glsdk.gdplabs.id/gen-ai-internal/simple/` without valid authentication.

**Fix:**
```bash
export UV_INDEX_GEN_AI_INTERNAL_USERNAME=oauth2accesstoken
export UV_INDEX_GEN_AI_INTERNAL_PASSWORD="$(gcloud auth print-access-token)"
```

**Why it happens:** The gcloud access token expires (~1 hour). In batch verification runs, tokens expire mid-run.

**Prevention:** Refresh token every 10 entries or use a service account with longer-lived tokens.

---

### 2. Missing LLM API Keys — ~25% of failures

**Error Pattern:**
```
raise OpenAIError("The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable")
```

**Root Cause:** Examples using live LLM invokers (`OpenAILMInvoker`, `AnthropicLMInvoker`, `GoogleLMInvoker`, `GoogleRealtimeSession`, `OpenAIRealtimeSession`) require real API keys.

**Required Keys:**
| Provider | Environment Variable | Used By |
|----------|---------------------|---------|
| OpenAI | `OPENAI_API_KEY` | `OpenAILMInvoker`, `OpenAIEMInvoker`, `OpenAIRealtimeSession` |
| Anthropic | `ANTHROPIC_API_KEY` | `AnthropicLMInvoker` |
| Google | `GOOGLE_API_KEY` | `GoogleLMInvoker`, `GoogleEMInvoker`, `GoogleRealtimeSession` |

**Fix:** Set all required keys in `.env` before verification:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."
```

**Note:** Some examples use `load_dotenv()` to load from `.env` file - copy `.env.example` to `.env` and fill in values.

---

### 3. Missing Required Files — ~15% of failures

**Required File Set (7 files):**
1. `.env.example` — Documents required environment variables
2. `.python-version` — Pins Python version (3.12)
3. `pyproject.toml` — Project metadata and dependencies
4. `uv.lock` — Lock file for reproducible builds
5. `setup.sh` — Unix/Linux/macOS setup script
6. `setup.bat` — Windows setup script
7. `README.md` — Documentation with expected output

**Common Missing Files by Entry Type:**
| Entry Type | Frequently Missing |
|------------|-------------------|
| Evaluation tutorials | `.python-version`, `uv.lock`, `setup.sh`, `setup.bat` |
| Realtime sessions | `.python-version`, `setup.sh`, `setup.bat` |
| LM Request Processor | `.env.example`, `.python-version`, `setup.sh`, `setup.bat` |
| Deep Research | `.python-version` |

---

### 4. Python Version Mismatch — ~8% of failures

**Error Pattern:**
```
Using CPython 3.13.12 interpreter at: /usr/bin/python3.13
Creating virtual environment at: .venv
```

**Root Cause:** Some entries have `.python-version` set to `3.12` but the system default is 3.13. uv picks 3.13 if available, causing potential incompatibility with packages pinned to 3.12.

**Fix:** Explicitly set:
```
# .python-version
3.12

# pyproject.toml
[project]
requires-python = ">=3.11,<3.14"
```

---

### 5. Missing Package Extras — ~5% of failures

**Error Pattern:**
```
ImportError: cannot import name 'OpenAILMInvoker' from 'gllm_inference.lm_invoker'
```

**Root Cause:** Using `OpenAILMInvoker` requires the `[openai]` extra dependency.

**Fix:** In `pyproject.toml`:
```toml
dependencies = [
    "gllm-inference[openai]>=0.5.0,<0.6.0",
]
```

**Extra Mapping:**
| Import | Required Extra |
|--------|---------------|
| `OpenAILMInvoker`, `OpenAIEMInvoker`, `OpenAIRealtimeSession`, `OpenAIChatCompletionsLMInvoker` | `[openai]` |
| `GoogleLMInvoker`, `GoogleEMInvoker`, `GoogleRealtimeSession` | `[google]` |
| `AnthropicLMInvoker` | `[anthropic]` |
| `ChromaDataStore` | `[chroma]` (on `gllm-datastore`) |
| `SQLDataStore` | `[sql]` (on `gllm-datastore` and `gllm-retrieval`) |

---

### 6. Dependency Conflict Workarounds — Verified Patterns

**Pattern 1: Pipeline + Inference version conflict**
```toml
# If gllm-pipeline>=0.4.0,<0.5.0 conflicts with gllm-inference version:
gllm-core>=0.4.0,<0.5.0
gllm-inference>=0.6.0,<0.7.0
gllm-pipeline>=0.5.0,<0.6.0
```

**Pattern 2: Use explicit `@main` decorator instead of legacy `_run`**
```python
# Avoids runtime warning
from gllm_core.schema import Component, main

class MyComponent(Component):
    @main
    async def process(self, input: str) -> str:
        return input.upper()
```

**Pattern 3: Defensive exclusion manager**
```python
exclusions = getattr(pipeline, "_exclusions", None)
if exclusions:
    current = exclusions.get_current_exclusions()
```

**Pattern 4: Use `context` parameter for runtime values (not `config`)**
```python
# Correct
result = await pipeline.invoke(state, context={"top_k": 5, "debug": True})

# Deprecated (causes warnings)
result = await pipeline.invoke(state, config={"top_k": 5, "debug": True})
```

**Pattern 5: Replace `transform` with explicit `Component` + `step` when input mapping fails**
```python
# If transform(input_map=["state_key"]) fails:
class MyComponent(Component):
    @main
    async def process(self, state_key: str) -> str:
        ...

step(MyComponent(), input_map={"state_key": "state_key"}, output_state="result")
```

---

## Verified Working Entries (No Auth/API Keys Required)

These entries passed verification consistently:

| Path | Category | Reason |
|------|----------|--------|
| `gen-ai/tutorials/inference/prompt_builder` | tutorials | No LLM invoker - uses PromptBuilder only |
| `gen-ai/tutorials/inference/catalog` | tutorials | Uses catalog but doesn't invoke LLMs |
| `gen-ai/tutorials/core/dynamic_component` | tutorials | Core component only |
| `gen-ai/tutorials/core/event_emitter` | tutorials | Core event emitter only |
| `gen-ai/tutorials/core/logger_manager` | tutorials | Core logger only |
| `gen-ai/tutorials/core/tool` | tutorials | Core tool only |

**Pattern:** Entries that DON'T invoke live LLMs pass verification. Entities requiring real LLM calls fail in environments without API keys.

---

## Recommendations for CI/CD

1. **Always run Phase 0 auth before verification:**
   ```bash
   export UV_INDEX_GEN_AI_INTERNAL_USERNAME=oauth2accesstoken
   export UV_INDEX_GEN_AI_INTERNAL_PASSWORD="$(gcloud auth print-access-token)"
   ```

2. **Set all LLM API keys in CI environment:**
   ```yaml
   env:
     OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
     ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
     GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
   ```

3. **Verify entries without LLM calls first** (they pass without API keys)

4. **Batch verification in groups of 10** with token refresh between groups

5. **Use install cache** to avoid re-downloading packages:
   ```bash
   uv cache dir  # Check cache location
   ```

6. **Generate lock files once** and commit them - don't regenerate in CI

---

### 7. Copied-verbatim GitBook pseudocode → NameError at runtime — found via PR #78 review

**Error Pattern:** GitBook illustrative snippets sometimes reference a variable (`vector_datastore`, `data_store`, `document_store`, `chunk_store`) that the page never defines — it's showing "assume you already have a store" pseudocode. `sync` copies the code block verbatim, so the cookbook script inherits the undefined name and raises `NameError` the moment it runs.

**Root Cause:** Verification classified these as `❌ Pseudocode` internally, but nothing blocked the PR from being opened with those entries included — the internal "Notes" column admitted the failure instead of gating on it.

**Fix / Gate:** Treat "fails with NameError due to undefined variable" as a hard verification failure, distinct from `NOT_RUNNABLE` (missing credentials, which is expected per pattern #4 above). Do not open a PR containing an entry that hits this — either construct a concrete stub (e.g. in-memory `ChromaDataStore`) so the script actually runs, or exclude the entry from the PR and file a follow-up issue instead of shipping it with a known-broken note.

---

### 8. Import path drift on sync — found via PR #78 review

**Error Pattern:** A reviewer suggested `from gllm_inference.em_invoker import OpenAIEMInvoker` in place of what the sync produced — the generated import didn't match the submodule convention already used by sibling entries.

**Fix:** Before committing a synced/hand-edited entry, grep sibling entries in the same category for the accepted import form of the same class and match it, rather than trusting whatever GitBook's snippet or the sync script produced verbatim.

---

### 9. Removing `load_dotenv()`/env loading without checking dependents — found via PR #78 review

**Error Pattern:** `reranker.py` had `load_dotenv()` removed during the docstring/cleanup pass, but the entry still uses `OpenAIEMInvoker` (needs `OPENAI_API_KEY`) and `pyproject.toml` still declares `python-dotenv`. Result: local `.env`-based dev breaks silently. Separately, `filter_extractor.py` (a new entry) never had `load_dotenv()`/`python-dotenv` added at all despite needing an API key.

**Fix:** Whenever an entry uses any LLM/EM invoker requiring an API key, verify as a pair: (a) `load_dotenv()` is called, and (b) `python-dotenv` is declared in that entry's `pyproject.toml`. Don't drop one side during unrelated edits (docstring passes, version bumps) without checking the other.

---

### 10. Undocumented "should we call `release_resources()`?" pattern

A reviewer asked whether invokers should always have `release_resources()` called after use — there's currently no documented answer either way in this skill. Before the next sync touching invoker-using entries, check the convention actually used across the cookbook (grep for `release_resources` usage) and either apply it consistently or record here why it's not needed, so this doesn't get asked PR after PR.

---

## Known Outdated GitBook Pages (Need Sync)

As of 2026-06-12, these GitBook pages have cookbook entries that may be outdated:
- `lm-invoker-web-search` — Web search API changed
- `lm-invoker-skills` — Skills API is Anthropic-specific, beta
- `realtime-session` — Uses older `gllm-inference==0.5.x` series

Run drift detection by comparing GitBook code blocks against cookbook scripts.