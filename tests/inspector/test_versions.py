from unittest.mock import MagicMock, patch

from rago_sync.inspector.versions import get_latest_version, is_stale


def test_get_latest_version_parses_simple_index_html():
    # `uv pip index versions` was removed in uv 0.9.17 ("unrecognized subcommand
    # 'index'"), so get_latest_version now parses the PEP 503 simple index HTML
    # directly. Verify it picks the highest version, not just the last listed.
    html = """
    <a href="gllm_inference-0.6.77.tar.gz">gllm_inference-0.6.77.tar.gz</a>
    <a href="gllm_inference-0.6.9.tar.gz">gllm_inference-0.6.9.tar.gz</a>
    <a href="gllm_inference-0.6.90.tar.gz">gllm_inference-0.6.90.tar.gz</a>
    """
    mock_resp = MagicMock()
    mock_resp.read.return_value = html.encode()
    mock_resp.__enter__.return_value = mock_resp
    with patch("rago_sync.inspector.versions.refresh_token", return_value=True), \
         patch.dict("os.environ", {"UV_INDEX_GEN_AI_INTERNAL_PASSWORD": "tok"}), \
         patch("urllib.request.urlopen", return_value=mock_resp):
        assert get_latest_version("gllm-inference") == "0.6.90"


def test_get_latest_version_returns_none_without_auth():
    with patch("rago_sync.inspector.versions.refresh_token", return_value=False):
        assert get_latest_version("gllm-inference") is None


def test_stale_when_latest_exceeds_upper_bound():
    # constraint says <0.6.0, latest is 0.6.1
    assert is_stale(">=0.5.0,<0.6.0", "0.6.1") is True


def test_not_stale_when_latest_within_bound():
    assert is_stale(">=0.5.0,<0.6.0", "0.5.163") is False


def test_not_stale_when_no_upper_bound():
    assert is_stale(">=0.5.0", "1.0.0") is False


def test_stale_when_latest_major_jump():
    assert is_stale(">=0.4.0,<0.5.0", "0.5.0") is True
