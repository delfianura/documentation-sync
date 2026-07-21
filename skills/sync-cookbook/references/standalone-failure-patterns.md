# Standalone cookbook script failure patterns

Collected from gllm-pipeline tutorial sync work. These are runtime/resolution failures that appear when a GitBook snippet is wrapped as a standalone `uv run` script.

## Broken `.venv` recovery

If runs fail on *every* new script with `ImportError` from unrelated packages (`anyio`, `mcp`, `pydantic`), the venv is likely corrupted by a previous interrupted install or UV index mismatch.

Fix:
```bash
rm -rf .venv
uv lock && uv sync
```

Do not debug the individual import chains; the symptom is venv contamination, not cookbook syntax.

## GitBook omissions that break standalone scripts

### 1. Missing or wrong `state_type`

GitBook snippets often omit `state_type` or pass `dict`. The resolver requires `TypedDict` or `BaseModel`.

Failure:
```
ValueError: Schema <class 'dict'> must be a TypedDict or Pydantic BaseModel. Got <class 'type'>.
```

Fix: add a minimal `TypedDict` with only the fields the block reads/writes.

### 2. Conditional/control-flow steps without a checkpointer

Steps such as `if_else`, `switch`, `toggle`, `no_op`, `guard`, `try_catch`, and `map_reduce` fail inside LangGraph when no checkpointer is present.

Failure:
```
RuntimeError: 'NoneType' object is not iterable
```
originating in `pipeline.py` event processing.

Fix: add `checkpointer=InMemorySaver()` to the Pipeline.

### 3. `goto` target resolution

`goto(target=...)` resolves target step names from state/config. If the state doesn't contain the key, it raises `KeyError`. Either pre-seed the target name in state or use a static string target.

### 4. `from gllm_pipeline.steps import X` not always exposed at package root

Some helpers live in submodules or need explicit imports from `gllm_pipeline.types` (`Group`, `Val`). Verify with:
```bash
PYTHONPATH= uv run python -c "from gllm_pipeline.steps import X; print('ok')"
```

## Decision rule for fragile pages

If more than ~30% of a page's code blocks require invisible runtime wiring and would ship as fragile wrappers, prefer:
1. Record the page as `reference-only` in `README.md`.
2. Open a follow-up issue/PR to add a runnable example once the upstream API stabilizes.
3. Do not add broken `.py` files to the cookbook just to satisfy coverage.

This preserves reviewer trust and keeps `uv run` meaningful as a verification signal.