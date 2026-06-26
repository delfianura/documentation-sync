from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from rago_sync.cli import app


runner = CliRunner()


def test_status_empty(tmp_status_file, monkeypatch):
    monkeypatch.setattr("rago_sync.cli.STATUS_FILE", tmp_status_file)
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 0
    assert "No entries" in result.output


def test_detect_dry_run(tmp_status_file, monkeypatch):
    monkeypatch.setattr("rago_sync.cli.STATUS_FILE", tmp_status_file)
    monkeypatch.setattr("rago_sync.cli.run_detect", MagicMock(return_value={}))
    monkeypatch.setattr("rago_sync.cli.run_report", MagicMock())
    result = runner.invoke(app, ["detect"])
    assert result.exit_code == 0


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ["detect", "sync", "sync-all", "verify", "status"]:
        assert cmd in result.output
