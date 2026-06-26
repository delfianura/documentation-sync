from rago_sync.inspector.versions import is_stale


def test_stale_when_latest_exceeds_upper_bound():
    # constraint says <0.6.0, latest is 0.6.1
    assert is_stale(">=0.5.0,<0.6.0", "0.6.1") is True


def test_not_stale_when_latest_within_bound():
    assert is_stale(">=0.5.0,<0.6.0", "0.5.163") is False


def test_not_stale_when_no_upper_bound():
    assert is_stale(">=0.5.0", "1.0.0") is False


def test_stale_when_latest_major_jump():
    assert is_stale(">=0.4.0,<0.5.0", "0.5.0") is True
