# Routing verification notes

## Hub + subdirectory boilerplate pattern
Some GitBook pages are hubs with variant subpages rather than single tutorial pages. Example: `tutorials/orchestration/routing/`.

- Parent entry needs standard boilerplate: `.env.example`, `.python-version`, `pyproject.toml`, `README.md`, `setup.bat`, `setup.sh`, `uv.lock`
- Each variant subdirectory also needs the same set, because users `cd` into it and run `setup.sh` / `uv run python <script>.py`
- Parent `README.md` should link to each subdirectory

## Working pyproject shape
```toml
[project]
name = "router-example"
version = "0.0.0"
description = "Router example"
requires-python = ">=3.11,<3.14"
readme = "README.md"
dependencies = [
  "gllm-pipeline[llmrouter]>=0.5.18,<0.6.0",
  "gllm-inference[openai]",
]

[[tool.uv.index]]
name = "gen-ai-internal"
url = "https://glsdk.gdplabs.id/gen-ai-internal/simple/"

[tool.uv.sources]
gllm-pipeline = { index = "gen-ai-internal" }
gllm-inference = { index = "gen-ai-internal" }
```

## Verified examples
- `rule-based-router/rule_based_router.py`
- `semantic-router/semantic_router_native.py`
- `similarity-based-router/semantic_router_native.py`
- `lm-based-router/lm_router.py`

All pass `ruff check --select E,W,F` and `py_compile`.

## Runtime verification evidence
- `rule-based-router`: `setup.sh` exit 0; `uv run` exit 0; prints `billing` / `tech_support` / `faq` routes
- `semantic-router`, `lm-based-router`, `similarity-based-router`: `setup.sh` exit 0; `uv run` exit 0 with unset `OPENAI_API_KEY`; prints skip notice instead of crashing

## blocker
`gllm_pipeline.router/__init__.py` eagerly imports `classifier_router`, which imports `gllm_pipeline.router.backend.llmrouter.classifier.mlp_adapter`, which imports `torch`. Minimal installs that omit `torch` therefore fail at import time for all router examples, including `RuleBasedRouter` and `SemanticRouter.native()`.

Observed:
```
ModuleNotFoundError: No module named 'torch'
```

`ruff check` and `py_compile` can still pass; runtime verification is blocked by package import side-effect, not by the cookbook script.

## GitBook API mismatch
GitBook still shows:
```python
credentials="<YOUR_OPENAI_API_KEY>"
```
Installed `gllm-pipeline v0.5.18` expects:
```python
credentials={"api_key": "<YOUR_OPENAI_API_KEY>"}
```

## Retry pattern that worked
After changing `pyproject.toml`, always remove subdirectory `.venv` and `uv.lock` before re-running `setup.sh`:
```bash
rm -rf .venv uv.lock
bash setup.sh
PYTHONPATH= uv run python <script>.py
```