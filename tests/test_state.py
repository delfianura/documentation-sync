import json
from pathlib import Path
import pytest
from rago_sync.state import EntryState, EntryStatus, StateManager

@pytest.fixture
def tmp_state(tmp_path):
    status_file = tmp_path / "status.json"
    return StateManager(path=status_file)

def test_entry_state_constants():
    assert EntryState.COMPLIANT == "COMPLIANT"
    assert EntryState.MISSING == "MISSING"
    assert EntryState.PENDING_REVIEW == "PENDING_REVIEW"
    assert EntryState.GITBOOK_DRIFT == "GITBOOK_DRIFT"
    assert EntryState.CONTENT_DRIFT == "CONTENT_DRIFT"
    assert EntryState.VERSION_STALE == "VERSION_STALE"
    assert EntryState.NOT_RUNNABLE == "NOT_RUNNABLE"
    assert EntryState.TEMPLATE_MISSING == "TEMPLATE_MISSING"

def test_get_nonexistent_entry(tmp_state):
    assert tmp_state.get("some/path") is None

def test_set_and_get_entry(tmp_state):
    status = EntryStatus(state=EntryState.COMPLIANT, last_checked="2026-06-26T10:00:00Z")
    tmp_state.set("tutorials/core/component", status)
    result = tmp_state.get("tutorials/core/component")
    assert result.state == EntryState.COMPLIANT

def test_pending_review_entries(tmp_state):
    tmp_state.set("a/b", EntryStatus(state=EntryState.PENDING_REVIEW,
                                     last_checked="2026-06-26T10:00:00Z",
                                     skip_detect=True))
    tmp_state.set("c/d", EntryStatus(state=EntryState.COMPLIANT,
                                     last_checked="2026-06-26T10:00:00Z"))
    pending = tmp_state.pending_review_entries()
    assert "a/b" in pending
    assert "c/d" not in pending

def test_save_and_reload(tmp_path):
    path = tmp_path / "status.json"
    mgr = StateManager(path=path)
    mgr.set("x/y", EntryStatus(state=EntryState.VERSION_STALE, last_checked="2026-06-26T10:00:00Z",
                                 pinned="0.5.0", latest="0.6.1"))
    mgr.save()
    mgr2 = StateManager(path=path)
    result = mgr2.get("x/y")
    assert result.state == EntryState.VERSION_STALE
    assert result.pinned == "0.5.0"
    assert result.latest == "0.6.1"

def test_save_preserves_last_detect(tmp_path):
    path = tmp_path / "status.json"
    mgr = StateManager(path=path)
    mgr.save()
    data = json.loads(path.read_text())
    assert "last_detect" in data
    assert data["last_detect"] is not None
