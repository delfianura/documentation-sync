from pathlib import Path
import pytest
from rago_sync.inspector.template import check_template

REQUIRED = [".env.example", ".python-version", "pyproject.toml",
            "uv.lock", "setup.sh", "setup.bat", "README.md"]

@pytest.fixture
def complete_entry(tmp_path):
    entry = tmp_path / "gen-ai" / "tutorials" / "core" / "component"
    entry.mkdir(parents=True)
    for f in REQUIRED:
        (entry / f).write_text("")
    return tmp_path, "tutorials/core/component"

@pytest.fixture
def incomplete_entry(tmp_path):
    entry = tmp_path / "gen-ai" / "tutorials" / "core" / "component"
    entry.mkdir(parents=True)
    for f in REQUIRED[:3]:  # missing uv.lock, setup.sh, setup.bat, README.md
        (entry / f).write_text("")
    return tmp_path, "tutorials/core/component"

def test_complete_entry_returns_empty(complete_entry, monkeypatch):
    cookbook_root, entry_path = complete_entry
    monkeypatch.setattr("rago_sync.inspector.template.COOKBOOK_REPO",
                        cookbook_root)
    missing = check_template(entry_path)
    assert missing == []

def test_missing_files_detected(incomplete_entry, monkeypatch):
    cookbook_root, entry_path = incomplete_entry
    monkeypatch.setattr("rago_sync.inspector.template.COOKBOOK_REPO",
                        cookbook_root)
    missing = check_template(entry_path)
    assert "uv.lock" in missing
    assert "setup.sh" in missing

def test_nonexistent_entry_returns_all_required(tmp_path, monkeypatch):
    monkeypatch.setattr("rago_sync.inspector.template.COOKBOOK_REPO",
                        tmp_path)
    missing = check_template("tutorials/does/not/exist")
    assert set(missing) == set(REQUIRED)
