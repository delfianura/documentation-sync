# Verification Failure Patterns

Common failure categories when running `uv run` on cookbook entries.

## Package Registry Auth (401)

```
Failed to fetch: https://glsdk.gdplabs.id/gen-ai-internal/...
HTTP status client error (401 Unauthorized)
```

**Fix**: Set UV auth env vars before running:
```bash
export UV_INDEX_GEN_AI_INTERNAL_USERNAME=oauth2accesstoken
export UV_INDEX_GEN_AI_INTERNAL_PASSWORD="$(gcloud auth print-access-token)"
```

Tokens expire in ~1hr. For long runs, refresh between batches.

## Missing API Keys

Entries using live LLM invokers need real API keys:

| Provider | Env var | Used by |
|---|---|---|
| OpenAI | `OPENAI_API_KEY` | `OpenAILMInvoker`, `OpenAIEMInvoker` |
| Anthropic | `ANTHROPIC_API_KEY` | `AnthropicLMInvoker` |
| Google | `GOOGLE_API_KEY` | `GoogleLMInvoker`, `GoogleEMInvoker` |

Some entries use `load_dotenv()` — copy `.env.example` to `.env` and fill values.

## Missing Package Extras

```
ImportError: cannot import name 'OpenAILMInvoker' from 'gllm_inference.lm_invoker'
```

| Import | Extra |
|---|---|
| `OpenAILMInvoker`, `OpenAIEMInvoker`, `OpenAIRealtimeSession` | `gllm-inference[openai]` |
| `GoogleLMInvoker`, `GoogleEMInvoker` | `gllm-inference[google]` |
| `AnthropicLMInvoker` | `gllm-inference[anthropic]` |
| `ChromaDataStore` | `gllm-datastore[chroma]` |

## Entries That Pass Without API Keys

These consistently pass because they don't invoke live LLMs:

| Path | Reason |
|---|---|
| `tutorials/inference/prompt_builder` | PromptBuilder only |
| `tutorials/inference/catalog` | Catalog, no LLM calls |
| `tutorials/core/dynamic_component` | Core component only |
| `tutorials/core/event_emitter` | Core event emitter |
| `tutorials/core/logger_manager` | Core logger |
| `tutorials/core/tool` | Core tool |
| `tutorials/retrieval/chunk_processor` | Dedup only, no LLM |

## `RuntimeWarning: coroutine 'main' was never awaited`

GitBook often shows `async def main()` snippets where the body uses `asyncio.run(...)` internally. If you copy that pattern verbatim and call `main()` from `if __name__ == "__main__"` without `asyncio.run(main())`, Python emits this warning and the function body does not execute.

**Fix**:
- If the function body only calls `asyncio.run(...)` → change it to `def main()` and call it directly.
- Otherwise → keep `async def main()` and use `if __name__ == "__main__": asyncio.run(main())`.

Check for this immediately after creating a new script from a GitBook snippet; `uv run` stderr will contain the warning.
