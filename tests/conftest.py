import json
import os
import sys

import pytest

from rago_sync.state import EntryState, EntryStatus, StateManager

# ── Isolate test environment from host PYTHONPATH pollution ──
# Hermes agent sets PYTHONPATH to its own venv, which has an incompatible
# click version. This ensures tests run against the project's own deps.
os.environ.pop("PYTHONPATH", None)
for _key in list(sys.path):
    if ".hermes/hermes-agent" in _key:
        sys.path.remove(_key)


@pytest.fixture
def tmp_status_file(tmp_path, monkeypatch):
    status_file = tmp_path / "status.json"
    status_file.write_text(json.dumps({"last_detect": None, "entries": {}}))
    monkeypatch.setattr("rago_sync.config.STATUS_FILE", status_file)
    monkeypatch.setattr("rago_sync.state.STATUS_FILE", status_file)
    return status_file


@pytest.fixture
def mock_state_manager(tmp_status_file):
    return StateManager(path=tmp_status_file)


@pytest.fixture
def sample_entry_status():
    return EntryStatus(
        state=EntryState.CONTENT_DRIFT,
        last_checked="2026-06-26T10:00:00Z",
    )