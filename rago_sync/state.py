import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import STATUS_FILE


class EntryState:
    COMPLIANT = "COMPLIANT"
    MISSING = "MISSING"
    TEMPLATE_MISSING = "TEMPLATE_MISSING"
    GITBOOK_DRIFT = "GITBOOK_DRIFT"
    CONTENT_DRIFT = "CONTENT_DRIFT"
    VERSION_STALE = "VERSION_STALE"
    NOT_RUNNABLE = "NOT_RUNNABLE"
    PENDING_REVIEW = "PENDING_REVIEW"


@dataclass
class EntryStatus:
    state: str
    last_checked: str
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    pr_opened_at: Optional[str] = None
    skip_detect: bool = False
    alerted_at: Optional[str] = None
    source: Optional[str] = None
    pinned: Optional[str] = None
    latest: Optional[str] = None
    breaking: Optional[bool] = None
    issues: list = field(default_factory=list)
    package: str = ""


class StateManager:
    def __init__(self, path: Path = STATUS_FILE):
        self.path = path
        self._data = self._load()

    def _load(self) -> dict:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {"last_detect": None, "entries": {}}

    def get(self, entry_path: str) -> Optional[EntryStatus]:
        raw = self._data["entries"].get(entry_path)
        if raw is None:
            return None
        return EntryStatus(**{k: v for k, v in raw.items()
                               if k in EntryStatus.__dataclass_fields__})

    def set(self, entry_path: str, status: EntryStatus) -> None:
        self._data["entries"][entry_path] = asdict(status)

    def all_entries(self) -> dict[str, EntryStatus]:
        return {k: EntryStatus(**{f: v for f, v in val.items()
                                   if f in EntryStatus.__dataclass_fields__})
                for k, val in self._data["entries"].items()}

    def pending_review_entries(self) -> dict[str, EntryStatus]:
        return {k: v for k, v in self.all_entries().items() if v.skip_detect}

    def save(self) -> None:
        self._data["last_detect"] = datetime.now(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2))
