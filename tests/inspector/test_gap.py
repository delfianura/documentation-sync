import pytest
from rago_sync.inspector.gap import gitbook_to_cookbook_path, has_gllm_imports

def test_tutorial_path_mapping():
    assert gitbook_to_cookbook_path("tutorials/inference/lm-invoker/README.md") == \
           "tutorials/inference/lm_invoker"

def test_guide_path_mapping():
    assert gitbook_to_cookbook_path("guides/build-end-to-end-rag-pipeline/your-first-rag-pipeline.md") == \
           "how-to-guides/build_end_to_end_rag_pipeline/your_first_rag_pipeline"

def test_hyphen_to_underscore():
    assert gitbook_to_cookbook_path("tutorials/data-store/query-filter.md") == \
           "tutorials/data_store/query_filter"

def test_has_gllm_imports_positive():
    content = "```python\nfrom gllm_inference.lm_invoker import OpenAILMInvoker\n```"
    assert has_gllm_imports(content) is True

def test_has_gllm_imports_negative():
    content = "```python\nimport os\n```"
    assert has_gllm_imports(content) is False
