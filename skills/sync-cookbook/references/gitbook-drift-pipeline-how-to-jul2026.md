# GITBOOK_DRIFT — pipeline orchestration how-to pages (Jul 2026) — RESOLVED

Pages affected: `guides/execute-a-pipeline`, `guides/debug-a-pipeline`,
`guides/human-in-the-loop`, `guides/pausing-flow-for-debugging`.

## Docs commits that originally introduced the drift (docs/gitbook-sync)

- `c5334a4d0` **GitBook: Update content** (most recent on docs/gitbook-sync at time of drift)
- `d860d7250` docs(gllm-pipeline): add interrupted and resumable pipeline lifecycle into HITL guide (#4696)
- `15c55eb0` docs(gllm-pipeline): Add tutorial for observability and debugging features (#4444)

## Status at time of original report — RESOLVED as of HEAD 70e6e3903

All APIs documented in these pages are confirmed present on
`$GL_SDK_REPO` (`origin/master` HEAD `70e6e3903`
and `docs/gitbook-sync` HEAD `ddedf2813` at time of resolution). Earlier false-alarm was
caused by inspecting a stale checkout (`~/gl-sdk`) that pointed at a different `Pipeline`
implementation.

| Method/page | Confirmed | Location |
|---|---|---|
| `Pipeline.enable_debug_tracing()` | ✅ | `pipeline.py` L490 |
| `Pipeline.disable_debug_tracing()` | ✅ | `pipeline.py` L511 |
| `Pipeline.invoke(..., include_outputs_from={...})` | ✅ | `pipeline.py` L528 |
| `Pipeline.get_state(thread_id)` | ✅ | `pipeline.py` L762 |
| `Pipeline.get_state_history(thread_id, ...)` | ✅ | `pipeline.py` L883 |
| `Pipeline.update_state(thread_id, values, as_node)` | ✅ | `pipeline.py` L786 |
| `Pipeline.resume(thread_id, value)` | ✅ | `pipeline.py` L822 |
| `Pipeline.fork_from(thread_id, checkpoint_id, values, ...)` | ✅ | `pipeline.py` L589 |

Execution entry-point docs:
- `debug-a-pipeline` uses `asyncio.run(pipeline.invoke(...))` inline — fine.
- `human-in-the-loop` §7 uses `asyncio.run(email_pipeline_lifecycle())` at module top level — fine.

## Verify before reporting GITBOOK_DRIFT

The pre-flight `gitbook.check-for-update` workflow is a **gate, not the decider**. GREEN
means "proceed"; only RED means stop and open an issue in `GDP-ADMIN/gl-sdk`. The actual
decision to sync is governed by `rago-sync detect` and `status.json`.

## Pitfall: stale checkout false alarm

Never inspect `~/gl-sdk` for gl-sdk API surface checks. That checkout lags behind
`$GL_SDK_REPO` by many commits. Always use:

```bash
cd $GL_SDK_REPO
grep -nE "^\\s+def (enable_debug_tracing|disable_debug_tracing|invoke|get_state\\b|get_state_history|update_state|resume|fork_from)\\b" \\
  libs/gllm-pipeline/gllm_pipeline/pipeline/pipeline.py
```

## Cookbook drift at time of resolution (rago-sync detect ↔ CSV)

| Entry | status.json | CSV | Authoritative action |
|---|---|---|---|
| `how-to-guides/execute_a_pipeline` | absent | CONTENT_DRIFT | Fix `context=` -> `config=`, re-run detect |
| `how-to-guides/debug_a_pipeline` | MISSING | missing_in_cookbook | Bootstrap from GitBook |
| `how-to-guides/human_in_the_loop` | CONTENT_DRIFT | CONTENT_DRIFT | `rago-sync sync --entry` |
| `how-to-guides/pausing_flow_for_debugging` | CONTENT_DRIFT | CONTENT_DRIFT | `rago-sync sync --entry` |

## Corrective owner / follow-up

`GDP-ADMIN/gl-sdk` — back-port already done. No action needed on the gl-sdk side.
Cookbook update is pending Advisor direction. If any of these pages regress, re-run the
grep command above before reopening a `GITBOOK_DRIFT` issue; `main` may have advanced.
