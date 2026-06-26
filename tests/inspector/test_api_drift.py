from rago_sync.inspector.api_drift import extract_gllm_identifiers, is_stale_import


def test_extract_class_names():
    code = "from gllm_inference.lm_invoker import OpenAILMInvoker\ninvoker = OpenAILMInvoker('gpt-4')"
    ids = extract_gllm_identifiers(code)
    assert "OpenAILMInvoker" in ids


def test_extract_from_imports():
    code = "from gllm_core.schema import Component, main"
    ids = extract_gllm_identifiers(code)
    assert "Component" in ids
    assert "main" in ids


def test_is_stale_import_with_removed_class():
    removed_classes = {"OpenAICompatibleLMInvoker", "Reasoning"}
    assert is_stale_import("OpenAICompatibleLMInvoker", removed_classes) is True
    assert is_stale_import("OpenAILMInvoker", removed_classes) is False
