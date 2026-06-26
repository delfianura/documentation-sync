import re
import subprocess
from datetime import datetime, timezone

from ..state import StateManager, EntryState, EntryStatus
from ..config import COOKBOOK_REPO
from ..syncer.migration import classify_version_bump, find_migration_guide
from ..syncer.lock_manager import run_uv_lock, run_uv_sync
from ..verifier.runner import verify_entry
from ..reporter.github_issues import create_issue


def sync_entry(entry_path: str, state_manager: StateManager) -> str:
    """Sync a single entry. Returns new state string."""
    status = state_manager.get(entry_path)
    if status is None or status.skip_detect:
        return "SKIPPED"

    now = datetime.now(timezone.utc).isoformat()

    if status.state == EntryState.GITBOOK_DRIFT:
        return _handle_gitbook_drift(entry_path, status, state_manager, now)
    if status.state in (EntryState.CONTENT_DRIFT, EntryState.TEMPLATE_MISSING, EntryState.MISSING):
        return _handle_content_update(entry_path, state_manager, now)
    if status.state == EntryState.VERSION_STALE:
        return _handle_version_stale(entry_path, status, state_manager, now)
    return status.state


def _handle_gitbook_drift(entry_path, status, state_manager, now):
    create_issue(
        title=f"[RAGO Sync] GITBOOK_DRIFT: {entry_path}",
        body=f"Gitbook page has code that doesn't match gl-sdk main.\nEntry: {entry_path}\n\nRun: rago-sync sync --entry {entry_path}",
        labels=["rago-sync", "gitbook-drift"],
    )
    return EntryState.GITBOOK_DRIFT


def _handle_content_update(entry_path, state_manager, now):
    result = verify_entry(entry_path)
    new_state = EntryState.COMPLIANT if result.passed else EntryState.NOT_RUNNABLE
    state_manager.set(entry_path, EntryStatus(state=new_state, last_checked=now))
    return new_state


def _handle_version_stale(entry_path, status, state_manager, now):
    py_files = list((COOKBOOK_REPO / "gen-ai" / entry_path).glob("*.py"))
    cookbook_code = "\n".join(f.read_text() for f in py_files if not f.name.startswith("_"))

    from_match = re.search(r">=(\d+\.\d+)", status.pinned or "")
    if from_match and status.latest:
        guide = find_migration_guide("gllm-inference", from_match.group(1), status.latest)
        classification = classify_version_bump(
            "gllm-inference", status.pinned or "", status.latest, cookbook_code, guide
        )
        if classification["breaking"]:
            create_issue(
                title=f"[RAGO Sync] Breaking version bump: {entry_path}",
                body=f"Version bump {status.pinned} → {status.latest} has breaking changes.\nAffected: {classification['changes']}",
                labels=["rago-sync", "breaking-change"],
            )
            return EntryState.VERSION_STALE

    run_uv_lock(entry_path)
    run_uv_sync(entry_path)
    result = verify_entry(entry_path)
    new_state = EntryState.COMPLIANT if result.passed else EntryState.NOT_RUNNABLE
    state_manager.set(entry_path, EntryStatus(state=new_state, last_checked=now))
    return new_state
