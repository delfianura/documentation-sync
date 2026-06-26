import subprocess
from datetime import datetime, timezone

from ..state import EntryState, EntryStatus, StateManager
from ..config import PENDING_REVIEW_STALE_DAYS, AUTH_REFRESH_EVERY_N
from .gap import list_gitbook_pages, list_cookbook_entries, gitbook_to_cookbook_path, get_page_content, has_gllm_imports
from .template import check_template
from .drift import check_content_drift
from .api_drift import check_api_drift
from .versions import check_version_stale


def _poll_pr_state(pr_number: int) -> str:
    """Returns 'open', 'merged', or 'closed'."""
    result = subprocess.run(
        ["gh", "pr", "view", str(pr_number), "--json", "state,merged",
         "--jq", "[.state, (.merged | tostring)] | join(\",\")"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return "open"
    parts = result.stdout.strip().split(",")
    state, merged = parts[0], parts[1] if len(parts) > 1 else "false"
    if merged == "true":
        return "merged"
    return state.lower()


def run_detect(state_manager: StateManager) -> dict[str, EntryStatus]:
    """Run all inspector checks. Returns updated entry statuses."""
    now = datetime.now(timezone.utc).isoformat()
    results: dict[str, EntryStatus] = {}

    # Auth before version checks
    try:
        from ..auth import refresh_token
        refresh_token()
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("refresh_token failed: %s", exc)

    # Phase 1: handle PENDING_REVIEW entries
    for entry_path, status in state_manager.pending_review_entries().items():
        pr_state = _poll_pr_state(status.pr_number)
        if pr_state == "merged":
            results[entry_path] = EntryStatus(state=EntryState.COMPLIANT,
                                               last_checked=now)
        elif pr_state == "closed":
            results[entry_path] = EntryStatus(state=EntryState.GITBOOK_DRIFT,
                                               last_checked=now)
        else:
            # still open — check staleness
            opened = status.pr_opened_at or now
            age_days = (datetime.now(timezone.utc) - datetime.fromisoformat(opened)).days
            if age_days >= PENDING_REVIEW_STALE_DAYS:
                status.alerted_at = now
            results[entry_path] = status  # preserve as-is

    # Phase 2: gap detection
    gb_pages = list_gitbook_pages()
    cb_entries = set(list_cookbook_entries())
    counter = 0

    for gb_rel in gb_pages:
        content = get_page_content(gb_rel)
        if not has_gllm_imports(content):
            continue
        cookbook_path = gitbook_to_cookbook_path(gb_rel)
        if cookbook_path in results:
            continue  # already handled (PENDING_REVIEW)

        counter += 1
        if counter % AUTH_REFRESH_EVERY_N == 0:
            from ..auth import refresh_token
            refresh_token()

        if cookbook_path not in cb_entries:
            results[cookbook_path] = EntryStatus(state=EntryState.MISSING,
                                                  last_checked=now)
            continue

        # run checks cheapest first
        missing_files = check_template(cookbook_path)
        if missing_files:
            results[cookbook_path] = EntryStatus(state=EntryState.TEMPLATE_MISSING,
                                                  last_checked=now)
            continue

        api_missing = check_api_drift(content)
        if api_missing:
            results[cookbook_path] = EntryStatus(state=EntryState.GITBOOK_DRIFT,
                                                  last_checked=now)
            continue

        drift_result = check_content_drift(cookbook_path, content)
        if drift_result == "CONTENT_DRIFT":
            results[cookbook_path] = EntryStatus(state=EntryState.CONTENT_DRIFT,
                                                  last_checked=now)
            continue
        # NEEDS_LLM_JUDGE treated as COMPLIANT for MVP

        stale = check_version_stale(cookbook_path)
        if stale:
            pkg = next(iter(stale))
            results[cookbook_path] = EntryStatus(
                state=EntryState.VERSION_STALE,
                last_checked=now,
                pinned=stale[pkg]["constraint"],
                latest=stale[pkg]["latest"],
                package=pkg,
            )
            continue

        results[cookbook_path] = EntryStatus(state=EntryState.COMPLIANT,
                                              last_checked=now)

    return results
