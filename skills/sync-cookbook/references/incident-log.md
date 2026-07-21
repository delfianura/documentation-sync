# Incident log

Dated, PR-specific history behind the generalized rules in `SKILL.md`. Keep this file
append-only — each entry is evidence for a rule, not the rule itself. If a rule in
`SKILL.md` needs justification, link here; don't inline the story in the main skill body.

## Folder naming (prefixed slugs)

PR #75 created folders like `lm_invoker_basic_usage/` by prefixing the parent directory
name onto the section slug. PR #88 had to delete 11 such prefixed duplicates and rename
them to `basic_usage/`, `context_management/`, etc. Root cause: convention-based path
mapping guessed a slug instead of reading the GitBook section heading.

## Import simplification (PR #94 / #96 review)

- `Pipeline` → `from gllm_pipeline.pipeline import Pipeline` (not `...pipeline.pipeline`)
- `transform` and other step helpers → `from gllm_pipeline.steps import transform` (not
  `...steps._func`)
- Both have public re-exports in their `__init__.py`; prefer the shorter public path.

## data-store merge (PR #92)

Restructure pattern used when subpages were merged into `tutorials/data-store/README.md`:
1. Replaced the old multi-directory layout (`basic_crud_and_methods/` + `build_data_store/`)
   with a single `basic_usage/` directory.
2. Created one `.py` per GitBook section, not one per old entry directory:
   `quickstart.py` → `#quick-start`, `capabilities.py` → `#using-the-store-end-to-end`,
   `builder.py` → `#build-a-data-store-from-configuration`.
3. Removed `supported_datastores/` (a resource page, not a tutorial — cookbook only mirrors
   tutorial pages).
4. Added `legacy_data_store/` for legacy GitBook pages that still exist separately.
5. Updated the parent `README.md` with a table mapping each entry directory to its
   GitBook URL.
6. Committed the restructure as a single commit so renames stay readable in the diff.

## Cross-package compatibility resolver failure (data-store sync, PR #92)

`gllm-inference==0.6.98` required `gllm-core>=0.4.21,<0.4.37`, but the latest published
`gllm-core` at the time was `0.4.37.post1` — `uv lock` failed as unsatisfiable. Fix: drop
to `gllm-inference>=0.6.95,<0.7.0` (0.6.95 allows `gllm-core<0.5.0`) so it coexists with
`gllm-core>=0.4.37`. Lesson generalized in `SKILL.md` under "Cross-package compatibility":
always re-run `uv lock` after any pin edit and read the error — never assume "latest
= compatible".

## Cross-package import break (observed July 2026)

`gllm-pipeline==0.5.18` imported `parallel_gather` from `gllm_core.concurrency`, but the
latest published `gllm-core==0.4.24` at the time did not export that symbol. Every cookbook
script importing `gllm_pipeline.pipeline` or `gllm_pipeline.steps` failed with
`ImportError: cannot import name 'parallel_gather'` even though `ruff check` / `py_compile`
passed (the import is syntactically valid, just unresolvable at the installed versions).

Resolution: bumped the cookbook entry's floor pin (`gllm-core>=0.4.37,<0.5.0`), patched the
upstream package's own minimum in `libs/gllm-pipeline/pyproject.toml`, and opened a
`GDP-ADMIN/gl-sdk` PR titled `fix(gllm-pipeline): bump gllm-core minimum to >=0.4.37`. The
generalized guardrail (always probe installed cross-package imports post-sync) lives in
`SKILL.md`.

## GitBook router credential shape drift

At one point live GitBook routing pages showed `credentials="<YOUR_OPENAI_API_KEY>"` while
the installed `gllm-pipeline v0.5.18` `build_em_invoker` / `build_lm_request_processor`
expected a mapping (`credentials={"api_key": "<YOUR_OPENAI_API_KEY>"}`). Generalized rule:
when manually syncing, always ground the credential shape against the currently installed
package signature, not GitBook prose — GitBook can lag or lead the installed API in either
direction.

## `release_resources()` pattern origin

The `try/finally` + `release_resources()` convention for invokers matches gl-sdk PR #5319.

## Skill eval: pipeline tutorial recreation vs PR #94

A dry-run agent recreated `gen-ai/tutorials/orchestration/pipeline/` from scratch using only
`SKILL.md` + the live GitBook page (WebFetch, no GitBook MCP available), then diffed the
result against `gdplabs/gen-ai-sdk-cookbook` PR #94. Result: 14/14 files correctly
identified, ruff-clean, no over/under-generation — the trigger taxonomy and coverage-mapping
instructions work as intended. Two structural gaps found and fixed in `SKILL.md`:
1. No decision rule for intentionally-illustrative pseudocode blocks (e.g. `steps=[]`) vs.
   accidentally-incomplete fragments — added under "Code block marking →
   Deliberately-illustrative vs. accidentally-incomplete blocks".
2. Docstring shape was underspecified ("a reference link", no format) — every recreated file
   diverged from the PR's `References:\n    <url>` block + `main()` docstring convention.
   Pinned down under "Cookbook code conventions".
Version-pin lookup and `uv run`/`uv sync` verification could not be tested (no internal-index
gcloud credentials in the eval sandbox) — not a skill gap, just an environment limit.

## Pipeline how-to pages drift (resolved, July 2026)

Pages `execute-a-pipeline`, `debug-a-pipeline`, `human-in-the-loop`,
`pausing-flow-for-debugging` were flagged `GITBOOK_DRIFT` because `enable_debug_tracing`,
`disable_debug_tracing`, `include_outputs_from`, `get_state`, `get_state_history`,
`update_state`, `resume`, `fork_from`, and `context=` were documented before landing on
`main`. All landed on `docs/gitbook-sync` HEAD `61a407b04`; the four pages and three
cookbook scripts were re-verified GREEN. Full detail: `references/gitbook-drift-pipeline-how-to-jul2026.md`.
If these pages resurface as `GITBOOK_DRIFT`, re-run the API-grounding check before opening
a new issue — `main` may have advanced further since this record.
