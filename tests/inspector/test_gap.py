import pytest
from rago_sync.inspector.gap import gitbook_to_cookbook_path, find_best_cookbook_match, has_gllm_imports


# --- gitbook_to_cookbook_path tests (backward compat) ---

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


# --- find_best_cookbook_match tests ---

COOKBOOK_ENTRIES = {
    "how-to-guides/build_end_to_end_rag_pipeline/001_your_first_rag_pipeline",
    "how-to-guides/build_end_to_end_rag_pipeline/002_dynamic_step",
    "how-to-guides/build_end_to_end_rag_pipeline/003_implement_semantic_routing",
    "how-to-guides/build_end_to_end_rag_pipeline/004_adding_document_references",
    "how-to-guides/build_end_to_end_rag_pipeline/005_simple_guardrail",
    "how-to-guides/build_end_to_end_rag_pipeline/006_query_transformation",
    "how-to-guides/build_end_to_end_rag_pipeline/007_multimodal_input_handling",
    "how-to-guides/build_end_to_end_rag_pipeline/008_caching",
    "how-to-guides/build_end_to_end_rag_pipeline/009_parallel_pipeline_processing",
    "how-to-guides/build_end_to_end_rag_pipeline/010_pipeline_step_exclusion",
    "how-to-guides/build_end_to_end_rag_pipeline/011_subgraphs",
    "how-to-guides/build_end_to_end_rag_pipeline/012_rag_with_dynamic_models",
    "how-to-guides/build_end_to_end_rag_pipeline/013_synthesize_responses_from_multiple_retrievers",
    "how-to-guides/build_multimodal_rag_pipeline/001_simple_image_rag_pipeline",
    "how-to-guides/build_multimodal_rag_pipeline/002_contextual_image_captioning",
    "how-to-guides/build_multimodal_rag_pipeline/003_intelligent_image_routing",
    "how-to-guides/build_multimodal_rag_pipeline/004_image_input_handling",
    "how-to-guides/build_multimodal_rag_pipeline/005_simple_video_rag_pipeline",
    "how-to-guides/build_multimodal_rag_pipeline/006_long_video_rag_pipeline",
    "how-to-guides/execute_a_pipeline",
    "how-to-guides/human_in_the_loop",
    "how-to-guides/pausing_flow_for_debugging",
    "how-to-guides/run_pipeline_on_a_server",
    "how-to-guides/trace_your_pipeline",
    "how-to-guides/utilize_language_model_request_processor/001_extend_lm_capabilities_with_tools",
    "how-to-guides/utilize_language_model_request_processor/002_produce_consistent_output_from_lm",
    "how-to-guides/utilize_language_model_request_processor/003_stream_lm_output",
    "tutorials/core/component",
    "tutorials/core/dynamic_component",
    "tutorials/core/event_emitter",
    "tutorials/core/logger_manager",
    "tutorials/core/tool",
    "tutorials/data_store/query_filter",
    "tutorials/data_store/cache",
    "tutorials/data_store/encryption",
    "tutorials/data_store/key_value_store",
    "tutorials/data_store/basic_crud_and_methods",
    "tutorials/inference/catalog",
    "tutorials/inference/component",
    "tutorials/inference/em_invoker",
    "tutorials/inference/lm_invoker/batch_invocation",
    "tutorials/inference/lm_invoker/client_lifecycle_management",
    "tutorials/inference/lm_invoker/code_interpreter",
    "tutorials/inference/lm_invoker/context_management",
    "tutorials/inference/lm_invoker/custom_processing_hooks",
    "tutorials/inference/lm_invoker/data_store_management",
    "tutorials/inference/lm_invoker/file_management",
    "tutorials/inference/lm_invoker/image_generation",
    "tutorials/inference/lm_invoker/input_transformer",
    "tutorials/inference/lm_invoker/mcp_connector",
    "tutorials/inference/lm_invoker/mcp_server",
    "tutorials/inference/lm_invoker/output_transformer",
    "tutorials/inference/lm_invoker/prompt_operations",
    "tutorials/inference/lm_invoker/skills",
    "tutorials/inference/lm_invoker/web_search",
    "tutorials/inference/lm_request_processor",
    "tutorials/inference/prompt_builder",
    "tutorials/inference/realtime_session",
    "tutorials/inference/schema",
    "tutorials/generation/context_enricher",
    "tutorials/generation/deep_researcher",
    "tutorials/generation/relevance_filter",
    "tutorials/generation/repacker",
    "tutorials/generation/response_synthesizer",
    "tutorials/orchestration/pipeline",
    "tutorials/retrieval/chunk_processor",
    "tutorials/retrieval/query_transformer",
    "tutorials/retrieval/reranker",
    "tutorials/retrieval/retrieval_parameter_extractor",
}

def test_matches_guide_with_numeric_prefix():
    match = find_best_cookbook_match(
        "guides/build-end-to-end-rag-pipeline/your-first-rag-pipeline.md",
        COOKBOOK_ENTRIES,
    )
    assert match == "how-to-guides/build_end_to_end_rag_pipeline/001_your_first_rag_pipeline"

def test_matches_guide_without_numeric_prefix():
    match = find_best_cookbook_match(
        "guides/execute-a-pipeline.md",
        COOKBOOK_ENTRIES,
    )
    assert match == "how-to-guides/execute_a_pipeline"

def test_matches_tutorial():
    match = find_best_cookbook_match(
        "tutorials/core/component.md",
        COOKBOOK_ENTRIES,
    )
    assert match == "tutorials/core/component"

def test_matches_lm_invoker_subpage():
    match = find_best_cookbook_match(
        "tutorials/inference/lm-invoker/batch-invocation.md",
        COOKBOOK_ENTRIES,
    )
    assert match == "tutorials/inference/lm_invoker/batch_invocation"

def test_matches_produce_consistent_output():
    match = find_best_cookbook_match(
        "guides/utilize-language-model-request-processor/produce-consistent-output-from-lm.md",
        COOKBOOK_ENTRIES,
    )
    assert match == "how-to-guides/utilize_language_model_request_processor/002_produce_consistent_output_from_lm"

def test_returns_none_when_no_match():
    match = find_best_cookbook_match(
        "guides/introduction-to-rag.md",
        COOKBOOK_ENTRIES,
    )
    assert match is None

def test_returns_none_for_unmatched_last_segment():
    match = find_best_cookbook_match(
        "tutorials/core/retry.md",
        COOKBOOK_ENTRIES,
    )
    assert match is None
