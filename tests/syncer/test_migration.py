import pytest
from rago_sync.syncer.migration import parse_breaking_changes, classify_version_bump

SAMPLE_GUIDE = """
## LM Invoker

1. `OpenAICompatibleLMInvoker` is removed. Use `OpenAILMInvoker` instead.
2. `Reasoning` class is renamed to `Thinking`.

## Output Parser

1. The output parser modules under `gllm_inference.output_parser` are removed.
"""

def test_parse_removed_symbols():
    changes = parse_breaking_changes(SAMPLE_GUIDE)
    symbols = [c["symbol"] for c in changes]
    assert "OpenAICompatibleLMInvoker" in symbols

def test_parse_renamed_symbols():
    changes = parse_breaking_changes(SAMPLE_GUIDE)
    renamed = [c for c in changes if "renamed" in c["change"]]
    assert any(c["symbol"] == "Reasoning" for c in renamed)

def test_all_parsed_changes_are_breaking():
    changes = parse_breaking_changes(SAMPLE_GUIDE)
    assert all(c["breaking"] is True for c in changes)

def test_classify_breaking_when_symbol_in_code():
    cookbook_code = "from gllm_inference.schema import Reasoning\noutput.reasoning"
    result = classify_version_bump("gllm-inference", ">=0.5.0,<0.6.0", "0.6.1",
                                    cookbook_code, guide_content=SAMPLE_GUIDE)
    assert result["breaking"] is True
    assert len(result["changes"]) > 0

def test_classify_not_breaking_when_symbol_absent():
    cookbook_code = "from gllm_inference.lm_invoker import OpenAILMInvoker"
    result = classify_version_bump("gllm-inference", ">=0.5.0,<0.6.0", "0.6.1",
                                    cookbook_code, guide_content=SAMPLE_GUIDE)
    assert result["breaking"] is False

def test_classify_no_guide():
    result = classify_version_bump("gllm-core", ">=0.4.0,<0.5.0", "0.5.0",
                                    "from gllm_core import X", guide_content=None)
    assert result["breaking"] is False
