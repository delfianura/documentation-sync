# Data Store cookbook sync — gotchas

Condensed lessons from syncing `gen-ai/tutorials/data_store/` to GitBook
(2026-07-16, PR #92). Applies whenever you sync or author data_store cookbook
entries against the current GitBook pages.

## `gllm-datastore[chroma]` extra required even for non-Chroma entries

`gllm_datastore.__init__` eagerly imports `ChromaDataStore`, which triggers
`check_optional_packages("chromadb", extras="chroma")`. This fires at import
time for ANY `gllm_datastore.*` import — including `key_value_store` entries
that use `OpenBaoKeyValueStore` and never touch Chroma.

**Fix**: always pin `gllm-datastore[chroma]` (not bare `gllm-datastore`) in
`pyproject.toml` for every data_store entry, regardless of which backend the
script uses.

## Chroma backend-specific operators raise at runtime
GitBook documents some Query Filter / QueryOptions features as backend-dependent.
On Chroma (in-memory or persistent) these raise at runtime, so **DROP them from
runnable cookbook examples** — keep the example green:

- `F.fuzzy("metadata.field", ...)` on `store.fulltext.retrieve(filters=...)` →
  `ValueError: Unsupported filter operator 'fuzzy' for retrieve.`
- `QueryOptions(include_fields=[...])` →
  `ValueError: Unsupported query option 'include_fields' for retrieve.`

The fulltext/vector filter, `limit`, `offset`, and `order_by` paths all work on
Chroma. If a GitBook snippet uses a fuzzy/include_fields call, omit it from the
cookbook `.py` and note the backend-dependence in the PR description.

## Eviction manager import path
`gllm_datastore.cache.vector_cache.eviction_manager.__init__` does NOT re-export
`AsyncIOEvictionManager`. The leaf-module path is required:

```python
from gllm_datastore.cache.vector_cache.eviction_manager.asyncio_eviction_manager import (
    AsyncIOEvictionManager,
)
```

Same shape for `ttl_eviction_strategy` / `lru_eviction_strategy` — import from the
leaf module, not the package `__init__`. If you must keep imports short (ruff
E501), alias the module: `import ...asyncio_eviction_manager as _em` then
`AsyncIOEvictionManager = _em.AsyncIOEvictionManager`.

## Version pin compatibility (data_store entries)
Resolve the full set together — do not pin each package to "latest" in isolation:

- `gllm-datastore==0.5.94` requires `gllm-core>=0.3.36,<0.5.0` (OK with 0.4.37).
- `gllm-inference==0.6.98` requires `gllm-core>=0.4.21,<0.4.37` — **CONFLICTS**
  with `gllm-core==0.4.37.post1` (latest). `uv lock` fails:
  `your project's requirements are unsatisfiable`.
- `gllm-inference==0.6.95` requires `gllm-core>=0.4.21,<0.5.0` (OK with 0.4.37).

Working pin set for data_store entries (verified resolving):

```
gllm-core>=0.4.37,<0.5.0
gllm-inference[openai]>=0.6.95,<0.7.0
gllm-datastore[chroma]>=0.5.94,<0.6.0
```

Always run `uv lock` after editing any pin and read the error before committing.

## Ad-hoc verification note
`uv run` log output is wrapped by uv's formatter — multi-word strings split across
lines (e.g. `Closing asyncio eviction manager` → `Closing asyncio` / `eviction mana
ger`). When grepping `uv run` stdout/stderr for a signal, assert `returncode == 0`
and use broad substring matches, not exact multi-word literals.

## Cookbook restructure after GitBook page merge
When GitBook merges multiple subpages into one main page (e.g. data-store +
build-data-store + basic-crud-and-methods → single data-store page), the cookbook
must be restructured to mirror the new single-page layout:

1. Replace old multi-directory layout (`basic_crud_and_methods/` + `build_data_store/`)
   with a single `basic_usage/` directory.
2. Create one `.py` per GitBook section: `quickstart.py` → `#quick-start`,
   `capabilities.py` → `#using-the-store-end-to-end`, `builder.py` →
   `#build-a-data-store-from-configuration`.
3. Remove `supported_datastores/` (resource page, not a tutorial).
4. Add `legacy_data_store/` for any legacy pages still existing separately.
5. Update parent `README.md` with a table mapping each entry to its GitBook URL.