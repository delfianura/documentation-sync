import pytest
from rago_sync.inspector.drift import (
    extract_code_blocks, normalize_code, similarity_score,
    classify_drift
)

def test_extract_code_blocks():
    md = "```python\nfrom gllm_core import Component\n```"
    blocks = extract_code_blocks(md)
    assert len(blocks) == 1
    assert "from gllm_core import Component" in blocks[0]

def test_extract_no_blocks():
    assert extract_code_blocks("No code here") == []

def test_normalize_strips_comments():
    code = "# this is a comment\nfrom gllm_core import X"
    assert "# this" not in normalize_code(code)
    assert "from gllm_core import X" in normalize_code(code)

def test_similarity_same_imports():
    code = "from gllm_inference.lm_invoker import OpenAILMInvoker\nresult = invoker.invoke()"
    score = similarity_score(code, code)
    assert score >= 85

def test_similarity_different_structure():
    a = "from gllm_inference.lm_invoker import OpenAILMInvoker\ninvoker.invoke()"
    b = "import os\nos.environ['KEY'] = 'val'"
    score = similarity_score(a, b)
    assert score < 85

def test_classify_exact_match():
    code = "from gllm_core import Component"
    result = classify_drift(code, code)
    assert result == "COMPLIANT"

def test_classify_empty_gitbook():
    result = classify_drift("", "from gllm_core import X")
    assert result == "NO_GITBOOK_CODE"

def test_classify_low_similarity():
    gb = "from gllm_inference.lm_invoker import OpenAILMInvoker\nawait invoker.invoke(msg)"
    cb = "import os\nprint(os.environ.get('KEY'))"
    result = classify_drift(gb, cb)
    assert result == "CONTENT_DRIFT"

def test_classify_high_similarity_needs_llm():
    base = "from gllm_inference.lm_invoker import OpenAILMInvoker\nawait invoker.invoke(msg)"
    # same imports, same calls, minor rename
    variant = "from gllm_inference.lm_invoker import OpenAILMInvoker\nawait invoker.invoke(message)"
    result = classify_drift(base, variant)
    assert result in ("COMPLIANT", "NEEDS_LLM_JUDGE")
