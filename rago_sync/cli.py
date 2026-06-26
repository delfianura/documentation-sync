from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from .config import STATUS_FILE
from .state import StateManager, EntryState
from .auth import require_auth
from .inspector import run_detect
from .reporter import run_report
from .syncer import sync_entry

app = typer.Typer(help="RAGO Sync — cookbook/gitbook drift detector and syncer")
console = Console()

STATE_STYLE = {
    EntryState.COMPLIANT: "green",
    EntryState.MISSING: "red",
    EntryState.TEMPLATE_MISSING: "yellow",
    EntryState.GITBOOK_DRIFT: "red",
    EntryState.CONTENT_DRIFT: "yellow",
    EntryState.VERSION_STALE: "blue",
    EntryState.NOT_RUNNABLE: "red",
    EntryState.PENDING_REVIEW: "magenta",
}


@app.command()
def detect(email: bool = typer.Option(False, "--email", help="Send email report")):
    """Run all inspector checks. Read-only. Writes status.json and report.html."""
    rprint("[bold]Running RAGO detect...[/bold]")
    state_manager = StateManager(path=STATUS_FILE)
    results = run_detect(state_manager)
    for path, status in results.items():
        state_manager.set(path, status)
    state_manager.save()
    run_report(state_manager, send_email=email)
    _print_summary(state_manager)


@app.command()
def sync(
    entry: Annotated[Optional[str], typer.Option("--entry", help="Sync specific entry path")] = None,
):
    """Sync drifted entries. Opens PRs and creates issues. MANUAL TRIGGER ONLY."""
    require_auth()
    state_manager = StateManager(path=STATUS_FILE)
    entries = state_manager.all_entries()

    targets = {entry: entries[entry]} if entry else {
        k: v for k, v in entries.items()
        if v.state != EntryState.COMPLIANT and not v.skip_detect
    }

    for path, status in targets.items():
        rprint(f"[bold]Syncing:[/bold] {path} ({status.state})")
        new_state = sync_entry(path, state_manager)
        rprint(f"  → {new_state}")

    state_manager.save()


@app.command(name="sync-all")
def sync_all():
    """Initial full sync: detect then sync all non-compliant entries."""
    require_auth()
    rprint("[bold]Running sync-all (initial full sync)...[/bold]")
    state_manager = StateManager(path=STATUS_FILE)
    results = run_detect(state_manager)
    for path, status in results.items():
        state_manager.set(path, status)
    state_manager.save()

    priority_order = [
        EntryState.MISSING, EntryState.TEMPLATE_MISSING, EntryState.GITBOOK_DRIFT,
        EntryState.CONTENT_DRIFT, EntryState.VERSION_STALE, EntryState.NOT_RUNNABLE,
    ]
    entries = state_manager.all_entries()
    for target_state in priority_order:
        batch = {k: v for k, v in entries.items() if v.state == target_state and not v.skip_detect}
        for path in batch:
            rprint(f"  Syncing [{target_state}]: {path}")
            sync_entry(path, state_manager)

    state_manager.save()
    run_report(state_manager, send_email=False)
    _print_summary(state_manager)


@app.command()
def verify(all_entries: bool = typer.Option(False, "--all")):
    """Run uv run on cookbook entries to check runnability."""
    require_auth()
    from .verifier.runner import verify_entry
    state_manager = StateManager(path=STATUS_FILE)
    entries = state_manager.all_entries()
    targets = list(entries.keys()) if all_entries else [
        k for k, v in entries.items() if v.state != EntryState.COMPLIANT
    ]
    for path in targets:
        rprint(f"Verifying: {path}")
        result = verify_entry(path)
        symbol = "[green]PASS[/green]" if result.passed else "[red]FAIL[/red]"
        rprint(f"  {symbol} (iterations: {result.iterations})")


@app.command()
def status():
    """Print current status.json in a human-readable table."""
    state_manager = StateManager(path=STATUS_FILE)
    entries = state_manager.all_entries()
    if not entries:
        rprint("No entries tracked yet. Run [bold]rago-sync detect[/bold] first.")
        return
    table = Table("Entry Path", "State", "Last Checked")
    for path, s in sorted(entries.items()):
        style = STATE_STYLE.get(s.state, "white")
        table.add_row(path, s.state, s.last_checked, style=style)
    console.print(table)


def _print_summary(state_manager: StateManager) -> None:
    counts: dict[str, int] = {}
    for s in state_manager.all_entries().values():
        counts[s.state] = counts.get(s.state, 0) + 1
    rprint("\n[bold]Summary:[/bold]")
    for state, n in sorted(counts.items()):
        style = STATE_STYLE.get(state, "white")
        rprint(f"  [{style}]{state}[/{style}]: {n}")
