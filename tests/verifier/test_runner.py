import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from rago_sync.verifier.runner import VerifyResult, _parse_failure_category

def test_verify_result_pass():
    r = VerifyResult(passed=True, output="Hello", iterations=1)
    assert r.passed is True

def test_verify_result_fail():
    r = VerifyResult(passed=False, output="Traceback...", iterations=3, error="ImportError")
    assert r.passed is False
    assert r.iterations == 3

def test_parse_import_error():
    output = "Traceback...\nImportError: cannot import name 'OldClass'"
    assert _parse_failure_category(output) == "IMPORT_ERROR"

def test_parse_auth_error():
    output = "AuthenticationError: 401 Unauthorized"
    assert _parse_failure_category(output) == "AUTH_ERROR"

def test_parse_module_not_found():
    output = "ModuleNotFoundError: No module named 'gllm_inference'"
    assert _parse_failure_category(output) == "MODULE_NOT_FOUND"

def test_parse_generic_error():
    output = "Something went wrong"
    assert _parse_failure_category(output) == "UNKNOWN"
