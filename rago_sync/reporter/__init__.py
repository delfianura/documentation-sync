from ..state import StateManager, EntryState
from .html import save_report
from .email_sender import send_report
from .github_issues import create_issue


def run_report(state_manager: StateManager, send_email: bool = False) -> None:
    """Generate HTML report, optionally email it, create issues for new drifts."""
    report_path = save_report(state_manager)
    print(f"Report saved to {report_path}")

    if send_email:
        html = report_path.read_text()
        ok = send_report(html)
        print("Email sent." if ok else "Email failed.")

    _create_issues_for_new_drifts(state_manager)


def _create_issues_for_new_drifts(state_manager: StateManager) -> None:
    for entry_path, status in state_manager.all_entries().items():
        if status.issues:
            continue  # already has an issue
        if status.state in (EntryState.GITBOOK_DRIFT, EntryState.MISSING, EntryState.NOT_RUNNABLE):
            url = create_issue(
                title=f"[RAGO Sync] {status.state}: {entry_path}",
                body=_issue_body(entry_path, status),
                labels=["rago-sync", status.state.lower().replace("_", "-")],
            )
            if url:
                issue_num = int(url.rstrip("/").split("/")[-1])
                status.issues.append(issue_num)
                state_manager.set(entry_path, status)


def _issue_body(entry_path: str, status) -> str:
    return f"""## What's wrong

**State**: `{status.state}`
**Entry**: `{entry_path}`
**Last checked**: {status.last_checked}

## How to fix

Run `rago-sync sync --entry {entry_path}` to attempt auto-fix.

For GITBOOK_DRIFT: check the migration guide and open a PR to `docs/gitbook-sync`.
For MISSING: a new cookbook entry needs to be created.
For NOT_RUNNABLE: the script fails — check the linked debug output.
"""
