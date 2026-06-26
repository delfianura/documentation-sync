from datetime import datetime
from pathlib import Path

from ..state import StateManager, EntryState
from ..config import REPORT_FILE

STATE_COLOR = {
    EntryState.COMPLIANT: "#22c55e",
    EntryState.MISSING: "#ef4444",
    EntryState.TEMPLATE_MISSING: "#f97316",
    EntryState.GITBOOK_DRIFT: "#ef4444",
    EntryState.CONTENT_DRIFT: "#f59e0b",
    EntryState.VERSION_STALE: "#3b82f6",
    EntryState.NOT_RUNNABLE: "#dc2626",
    EntryState.PENDING_REVIEW: "#8b5cf6",
}


def generate_report(state_manager: StateManager) -> str:
    entries = state_manager.all_entries()
    rows = ""
    for path, status in sorted(entries.items()):
        color = STATE_COLOR.get(status.state, "#6b7280")
        stale_note = f" ({status.pinned} → {status.latest})" if status.latest else ""
        rows += (
            f"<tr><td>{path}</td>"
            f"<td style='color:{color};font-weight:bold'>{status.state}{stale_note}</td>"
            f"<td>{status.last_checked}</td></tr>\n"
        )

    counts: dict[str, int] = {}
    for s in entries.values():
        counts[s.state] = counts.get(s.state, 0) + 1

    summary = " | ".join(f"{s}: {n}" for s, n in sorted(counts.items()))
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>RAGO Sync Report</title>
<style>body{{font-family:monospace;padding:20px}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#f3f4f6}}</style></head>
<body>
<h1>RAGO Sync Report</h1>
<p>Generated: {datetime.utcnow().isoformat()}Z</p>
<p><strong>Summary:</strong> {summary}</p>
<table><tr><th>Entry Path</th><th>State</th><th>Last Checked</th></tr>
{rows}
</table></body></html>"""


def save_report(state_manager: StateManager) -> Path:
    html = generate_report(state_manager)
    REPORT_FILE.write_text(html)
    return REPORT_FILE
