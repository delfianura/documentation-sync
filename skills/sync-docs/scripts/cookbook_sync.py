#!/usr/bin/env python3
"""
Cookbook ↔ GitBook Sync Agent
Comprehensive synchronization between GL SDK GitBook documentation and gen-ai-sdk-cookbook repository.

Usage:
    python cookbook_sync.py              # Full sync with verification (needs auth + API keys)
    python cookbook_sync.py --audit      # Audit only, no verification
    python cookbook_sync.py --no-email   # Skip email notification
    python cookbook_sync.py --no-telegram # Skip Telegram notification
"""

import json
import os
import subprocess
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict, field

# ============================================================================
# CONFIGURATION
# ============================================================================

COOKBOOK_REPO_PATH = Path("$COOKBOOK_DIR")
REPORT_OUTPUT_PATH = Path("./cookbook_sync_report.json")
HTML_REPORT_PATH = Path("./cookbook_sync_report.html")

EMAIL_CONFIG_PATH = Path("$EMAIL_CONFIG_PATH")

# GitBook pages with runnable Python examples (discovered via MCP)
GITBOOK_PAGES: Dict[str, Dict[str, Any]] = {
    # Inference tutorials
    "lm-invoker-basic": {
        "title": "LM Invoker Basic Usage",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_basic_usage",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["basic_invoke", "streaming", "message_roles", "multimodal", "structured_output", "tool_calling", "thinking", "output_analytics", "retry_timeout", "build_lm_invoker"],
    },
    "lm-invoker-skills": {
        "title": "Skills",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker/skills",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_skills",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["create_skill", "list_skills", "retrieve_skill", "skill_versions", "use_skill"],
    },
    "lm-invoker-web-search": {
        "title": "Web Search",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker/web-search",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_web_search",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["web_search_basic"],
    },
    "lm-invoker-file-management": {
        "title": "File Management",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker/file-management",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_file_management",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["file_upload", "file_list"],
    },
    "lm-invoker-data-store-management": {
        "title": "Data Store Management",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker/data-store-management",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_data_store_management",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["builtin_rag"],
    },
    "lm-invoker-context-management": {
        "title": "Context Management",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker/context-management",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_context_management",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["context_estimation"],
    },
    "lm-invoker-prompt-operations": {
        "title": "Prompt Operations",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker/prompt-operations",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_prompt_operations",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["prompt_templates"],
    },
    "lm-invoker-batch-invocation": {
        "title": "Batch Invocation",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker/batch-invocation",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_batch_invocation",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["batch_invoke"],
    },
    "lm-invoker-input-transformer": {
        "title": "Input Transformer",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker/input-transformer",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_input_transformer",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["input_transformation"],
    },
    "lm-invoker-output-transformer": {
        "title": "Output Transformer",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker/output-transformer",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_output_transformer",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["output_transformation"],
    },
    "lm-invoker-model-switching": {
        "title": "Model Switching",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker/model-switching",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_model_switching",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["model_switching"],
    },
    "lm-invoker-with-system-prompt": {
        "title": "With System Prompt",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-invoker/with-system-prompt",
        "cookbook_path": "gen-ai/tutorials/inference/lm_invoker/lm_invoker_with_system_prompt",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["system_prompt"],
    },
    "em-invoker": {
        "title": "EM Invoker",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/em-invoker",
        "cookbook_path": "gen-ai/tutorials/inference/em_invoker",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["em_invoker_basic"],
    },
    "lm-request-processor-streaming": {
        "title": "LM Request Processor Streaming",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-request-processor/streaming",
        "cookbook_path": "gen-ai/tutorials/inference/lm_request_processor/lm_request_processor_streaming",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["streaming_lmrp"],
    },
    "lm-request-processor-structured-output": {
        "title": "LM Request Processor Structured Output",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-request-processor/structured-output",
        "cookbook_path": "gen-ai/tutorials/inference/lm_request_processor/lm_request_processor_structured_output",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["json_output", "response_schema"],
    },
    "lm-request-processor-tool-calling": {
        "title": "LM Request Processor Tool Calling",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/lm-request-processor/tool-calling",
        "cookbook_path": "gen-ai/tutorials/inference/lm_request_processor/lm_request_processor_tool_calling",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["tool_calling_lmrp"],
    },
    "prompt-builder": {
        "title": "Prompt Builder",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/prompt-builder",
        "cookbook_path": "gen-ai/tutorials/inference/prompt_builder",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["prompt_builder"],
    },
    "realtime-session": {
        "title": "Realtime Session",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/realtime-session",
        "cookbook_path": "gen-ai/tutorials/inference/realtime_session",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["text_only", "text_audio", "tool_calling", "integration"],
    },
    "catalog": {
        "title": "Catalog",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/inference/catalog",
        "cookbook_path": "gen-ai/tutorials/inference/catalog",
        "category": "tutorials",
        "package": "gllm-inference",
        "examples": ["catalog_usage"],
    },

    # Data Store tutorials
    "data-store-quickstart": {
        "title": "Data Store Quickstart",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/data-store",
        "cookbook_path": "gen-ai/tutorials/data_store/quickstart",
        "category": "tutorials",
        "package": "gllm-datastore",
        "examples": ["basic_usage", "fulltext_vector"],
    },
    "data-store-query-filter": {
        "title": "Query Filter",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/data-store/query-filter",
        "cookbook_path": "gen-ai/tutorials/data_store/query_filter",
        "category": "tutorials",
        "package": "gllm-datastore",
        "examples": ["metadata_filter", "combining_conditions", "nested_logic", "reusable_filters", "dict_filters", "query_options", "fuzzy_filter"],
    },
    "data-store-build": {
        "title": "Build a Data Store from Configuration",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/data-store/build-data-store",
        "cookbook_path": "gen-ai/tutorials/data_store/build_data_store",
        "category": "tutorials",
        "package": "gllm-datastore",
        "examples": ["config_driven"],
    },
    "data-store-batching": {
        "title": "Batching",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/data-store/batching",
        "cookbook_path": "gen-ai/tutorials/data_store/batching",
        "category": "tutorials",
        "package": "gllm-datastore",
        "examples": ["auto_batching", "manual_batching"],
    },
    "data-store-encryption": {
        "title": "Encryption",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/data-store/encryption",
        "cookbook_path": "gen-ai/tutorials/data_store/encryption",
        "category": "tutorials",
        "package": "gllm-datastore",
        "examples": ["field_encryption"],
    },
    "data-store-cache": {
        "title": "Data Store as Cache",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/data-store/cache",
        "cookbook_path": "gen-ai/tutorials/data_store/cache",
        "category": "tutorials",
        "package": "gllm-datastore",
        "examples": ["cache_decorator", "cache_manual"],
    },
    "vector-data-store-legacy": {
        "title": "Vector Data Store (Legacy)",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/data-store/legacy/vector-data-store",
        "cookbook_path": "gen-ai/tutorials/data_store/legacy_vector_data_store",
        "category": "tutorials",
        "package": "gllm-datastore",
        "examples": ["quickstart"],
    },
    "data-store-hybrid": {
        "title": "Hybrid Search",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/data-store/hybrid-search",
        "cookbook_path": "gen-ai/tutorials/data_store/hybrid_search",
        "category": "tutorials",
        "package": "gllm-datastore",
        "examples": ["hybrid_search"],
    },

    # Retrieval tutorials
    "retriever": {
        "title": "Retriever",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/retrieval/retriever",
        "cookbook_path": "gen-ai/tutorials/retrieval/retriever",
        "category": "tutorials",
        "package": "gllm-retrieval",
        "examples": ["vector_retriever", "hybrid_retriever"],
    },
    "query-transformer": {
        "title": "Query Transformer",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/retrieval/query-transformer",
        "cookbook_path": "gen-ai/tutorials/retrieval/query_transformer",
        "category": "tutorials",
        "package": "gllm-retrieval",
        "examples": ["one_to_one_transformer", "json_extractor"],
    },
    "reranker": {
        "title": "Reranker",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/retrieval/reranker",
        "cookbook_path": "gen-ai/tutorials/retrieval/reranker",
        "category": "tutorials",
        "package": "gllm-retrieval",
        "examples": ["jina_reranker", "similarity_reranker", "pipeline_integration"],
    },
    "chunk-processor": {
        "title": "Chunk Processor",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/retrieval/chunk-processor",
        "cookbook_path": "gen-ai/tutorials/retrieval/chunk_processor",
        "category": "tutorials",
        "package": "gllm-retrieval",
        "examples": ["dedupe_processor"],
    },
    "retrieval-parameter-extractor": {
        "title": "Retrieval Parameter Extractor",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/retrieval/retrieval-parameter-extractor",
        "cookbook_path": "gen-ai/tutorials/retrieval/retrieval_parameter_extractor",
        "category": "tutorials",
        "package": "gllm-retrieval",
        "examples": ["lm_based_extractor"],
    },

    # Generation tutorials
    "response-synthesizer": {
        "title": "Response Synthesizer",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/generation/response-synthesizer",
        "cookbook_path": "gen-ai/tutorials/generation/response_synthesizer",
        "category": "tutorials",
        "package": "gllm-generation",
        "examples": ["stuff_strategy", "map_reduce", "refine", "static_list"],
    },
    "repacker": {
        "title": "Repacker",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/generation/repacker",
        "cookbook_path": "gen-ai/tutorials/generation/repacker",
        "category": "tutorials",
        "package": "gllm-generation",
        "examples": ["repacker_basic"],
    },
    "context-enricher": {
        "title": "Context Enricher",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/generation/context-enricher",
        "cookbook_path": "gen-ai/tutorials/generation/context_enricher",
        "category": "tutorials",
        "package": "gllm-generation",
        "examples": ["context_enricher_basic"],
    },
    "relevance-filter": {
        "title": "Relevance Filter",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/generation/relevance-filter",
        "cookbook_path": "gen-ai/tutorials/generation/relevance_filter",
        "category": "tutorials",
        "package": "gllm-generation",
        "examples": ["relevance_filter_basic"],
    },
    "reference-formatter": {
        "title": "Reference Formatter",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/generation/reference-formatter",
        "cookbook_path": "gen-ai/tutorials/generation/reference_formatter",
        "category": "tutorials",
        "package": "gllm-generation",
        "examples": ["reference_formatter_basic"],
    },
    "compressor": {
        "title": "Compressor",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/generation/compressor",
        "cookbook_path": "gen-ai/tutorials/generation/compressor",
        "category": "tutorials",
        "package": "gllm-generation",
        "examples": ["compressor_basic"],
    },
    "deep-researcher": {
        "title": "Deep Researcher",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/generation/deep-researcher",
        "cookbook_path": "gen-ai/tutorials/generation/deep_researcher",
        "category": "tutorials",
        "package": "gllm-generation",
        "examples": ["deep_researcher_basic"],
    },

    # Core tutorials
    "core-component": {
        "title": "Component",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/core/component",
        "cookbook_path": "gen-ai/tutorials/core/component",
        "category": "tutorials",
        "package": "gllm-core",
        "examples": ["component_basic"],
    },
    "core-dynamic-component": {
        "title": "Dynamic Component",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/core/dynamic-component",
        "cookbook_path": "gen-ai/tutorials/core/dynamic_component",
        "category": "tutorials",
        "package": "gllm-core",
        "examples": ["dynamic_component_basic"],
    },
    "core-event-emitter": {
        "title": "Event Emitter",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/core/event-emitter",
        "cookbook_path": "gen-ai/tutorials/core/event_emitter",
        "category": "tutorials",
        "package": "gllm-core",
        "examples": ["event_emitter_basic", "streaming"],
    },
    "core-logger-manager": {
        "title": "Logger Manager",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/core/logger-manager",
        "cookbook_path": "gen-ai/tutorials/core/logger_manager",
        "category": "tutorials",
        "package": "gllm-core",
        "examples": ["logger_manager_basic"],
    },
    "core-tool": {
        "title": "Tool",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/core/tool",
        "cookbook_path": "gen-ai/tutorials/core/tool",
        "category": "tutorials",
        "package": "gllm-core",
        "examples": ["tool_quickstart", "tool_decorator", "langchain_adapter", "google_adk_adapter"],
    },

    # Orchestration tutorials
    "orchestration-basic-concepts": {
        "title": "Basic Concepts",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/orchestration/basic-concepts",
        "cookbook_path": "gen-ai/tutorials/orchestration/basic_concepts",
        "category": "tutorials",
        "package": "gllm-pipeline",
        "examples": ["basic_concepts"],
    },
    "orchestration-state": {
        "title": "State",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/orchestration/state",
        "cookbook_path": "gen-ai/tutorials/orchestration/state",
        "category": "tutorials",
        "package": "gllm-pipeline",
        "examples": ["state_basic", "rag_state"],
    },
    "orchestration-steps": {
        "title": "Steps",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/orchestration/steps",
        "cookbook_path": "gen-ai/tutorials/orchestration/steps",
        "category": "tutorials",
        "package": "gllm-pipeline",
        "examples": ["step_types"],
    },
    "orchestration-pipeline": {
        "title": "Pipeline",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/orchestration/pipeline",
        "cookbook_path": "gen-ai/tutorials/orchestration/pipeline",
        "category": "tutorials",
        "package": "gllm-pipeline",
        "examples": ["pipeline_basic", "pipe_operator", "subgraph", "input_output_schema", "debug_state"],
    },
    "orchestration-routing": {
        "title": "Routing",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/orchestration/routing",
        "cookbook_path": "gen-ai/tutorials/orchestration/routing",
        "category": "tutorials",
        "package": "gllm-pipeline",
        "examples": ["semantic_router"],
    },

    # Evaluation tutorials (from working cookbook)
    "evals-getting-started": {
        "title": "Getting Started with Evaluations",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/evaluations/getting-started",
        "cookbook_path": "gen-ai/tutorials/evaluations/getting_started",
        "category": "tutorials",
        "package": "gllm-evals",
        "examples": ["getting_started"],
    },
    "evals-tutorials-custom-evaluator": {
        "title": "Custom Evaluator Tutorial",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/evaluations/tutorials/custom-evaluator-tutorial",
        "cookbook_path": "gen-ai/tutorials/evaluations/tutorials/custom_evaluator_tutorial",
        "category": "tutorials",
        "package": "gllm-evals",
        "examples": ["custom_evaluator"],
    },
    "evals-evaluator-standard": {
        "title": "Standard Evaluator",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/evaluations/evaluator/example-evaluator-standard",
        "cookbook_path": "gen-ai/tutorials/evaluations/evaluator/example_evaluator_standard",
        "category": "tutorials",
        "package": "gllm-evals",
        "examples": ["standard_evaluator"],
    },
    "evals-composite-evaluator": {
        "title": "Composite Evaluator",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/evaluations/evaluator/composite-evaluator",
        "cookbook_path": "gen-ai/tutorials/evaluations/evaluator/composite_evaluator",
        "category": "tutorials",
        "package": "gllm-evals",
        "examples": ["composite_evaluator"],
    },
    "evals-classical-retrieval": {
        "title": "Classical Retrieval Evaluator",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/evaluations/evaluator/classical-retrieval-evaluator",
        "cookbook_path": "gen-ai/tutorials/evaluations/evaluator/classical_retrieval_evaluator",
        "category": "tutorials",
        "package": "gllm-evals",
        "examples": ["classical_retrieval"],
    },
    "evals-lm-based-retrieval": {
        "title": "LM Based Retrieval Evaluator",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/evaluations/evaluator/lm-based-retrieval-evaluator",
        "cookbook_path": "gen-ai/tutorials/evaluations/evaluator/lm_based_retrieval_evaluator",
        "category": "tutorials",
        "package": "gllm-evals",
        "examples": ["lm_based_retrieval"],
    },
    "evals-geval-generation": {
        "title": "GEval Generation Evaluator",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/evaluations/evaluator/geval-generation-evaluator",
        "cookbook_path": "gen-ai/tutorials/evaluations/evaluator/geval_generation_evaluator",
        "category": "tutorials",
        "package": "gllm-evals",
        "examples": ["single_evaluation", "batch_evaluation"],
    },
    "evals-metrics-aggregator": {
        "title": "Metrics Aggregator",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/evaluations/evaluator/metrics-aggregator",
        "cookbook_path": "gen-ai/tutorials/evaluations/evaluator/metrics_aggregator",
        "category": "tutorials",
        "package": "gllm-evals",
        "examples": ["metrics_aggregator"],
    },
    "evals-query-transformer": {
        "title": "Query Transformer Evaluator",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/evaluations/evaluator/query-transformer-evaluator",
        "cookbook_path": "gen-ai/tutorials/evaluations/evaluator/query_transformer_evaluator",
        "category": "tutorials",
        "package": "gllm-evals",
        "examples": ["query_transformer_evaluator"],
    },
    "evals-summarization": {
        "title": "Summarization Evaluator",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/evaluations/evaluator/summarization-evaluator",
        "cookbook_path": "gen-ai/tutorials/evaluations/evaluator/summarization_evaluator",
        "category": "tutorials",
        "package": "gllm-evals",
        "examples": ["summarization_evaluator"],
    },
    "evals-create-custom": {
        "title": "Create Custom Evaluator",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/tutorials/evaluations/evaluator/create-custom-evaluator",
        "cookbook_path": "gen-ai/tutorials/evaluations/evaluator/create_custom_evaluator",
        "category": "tutorials",
        "package": "gllm-evals",
        "examples": ["create_custom_evaluator"],
    },

    # How-to guides - Build End-to-End RAG Pipeline
    "your-first-rag-pipeline": {
        "title": "Your First RAG Pipeline",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/your-first-rag-pipeline",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/001_your_first_rag_pipeline",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["pipeline_basic"],
    },
    "dynamic-step": {
        "title": "Dynamic Step",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/dynamic-step",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/002_dynamic_step",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["dynamic_step"],
    },
    "implement-semantic-routing": {
        "title": "Implement Semantic Routing",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/implement-semantic-routing",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/003_implement_semantic_routing",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["semantic_routing"],
    },
    "adding-document-references": {
        "title": "Adding Document References",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/adding-document-references",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/004_adding_document_references",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["document_references"],
    },
    "simple-guardrail": {
        "title": "Simple Guardrail",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/simple-guardrail",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/005_simple_guardrail",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["guardrail"],
    },
    "query-transformation": {
        "title": "Query Transformation",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/query-transformation",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/006_query_transformation",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["query_transformation"],
    },
    "multimodal-input-handling": {
        "title": "Multimodal Input Handling",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/multimodal-input-handling",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/007_multimodal_input_handling",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["multimodal_input"],
    },
    "caching": {
        "title": "Caching",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/caching",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/008_caching",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["caching"],
    },
    "parallel-pipeline-processing": {
        "title": "Parallel Pipeline Processing",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/parallel-pipeline-processing",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/009_parallel_pipeline_processing",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["parallel_processing"],
    },
    "pipeline-step-exclusion": {
        "title": "Pipeline Step Exclusion",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/pipeline-step-exclusion",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/010_pipeline_step_exclusion",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["step_exclusion"],
    },
    "subgraphs": {
        "title": "Subgraphs",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/subgraphs",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/011_subgraphs",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["subgraphs"],
    },
    "rag-with-dynamic-models": {
        "title": "RAG with Dynamic Models",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/build-end-to-end-rag-pipeline/rag-with-dynamic-models",
        "cookbook_path": "gen-ai/how-to-guides/build_end_to_end_rag_pipeline/012_rag_with_dynamic_models",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["dynamic_models"],
    },

    # Other how-to guides
    "run-pipeline-on-a-server": {
        "title": "Run Pipeline on a Server",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/run-pipeline-on-a-server",
        "cookbook_path": "gen-ai/how-to-guides/run_pipeline_on_a_server",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["server_deployment"],
    },
    "human-in-the-loop": {
        "title": "Human in the Loop",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/human-in-the-loop",
        "cookbook_path": "gen-ai/how-to-guides/human_in_the_loop",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["human_in_loop"],
    },
    "pausing-flow-for-debugging": {
        "title": "Pausing Flow for Debugging",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/pausing-flow-for-debugging",
        "cookbook_path": "gen-ai/how-to-guides/pausing_flow_for_debugging",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["debugging"],
    },
    "trace-your-pipeline": {
        "title": "Trace Your Pipeline",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/trace-your-pipeline",
        "cookbook_path": "gen-ai/how-to-guides/trace_your_pipeline",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["tracing"],
    },
    "execute-a-pipeline": {
        "title": "Execute a Pipeline",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/execute-a-pipeline",
        "cookbook_path": "gen-ai/how-to-guides/execute_a_pipeline",
        "category": "how-to-guides",
        "package": "gllm-pipeline",
        "examples": ["execute_pipeline"],
    },
    "index-your-data": {
        "title": "Index Your Data with Vector Data Store",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/index-your-data-with-vector-data-store",
        "cookbook_path": "gen-ai/how-to-guides/index_your_data",
        "category": "how-to-guides",
        "package": "gllm-datastore",
        "examples": ["csv_indexing", "chunk_indexing"],
    },
    "utilize-lm-request-processor-1": {
        "title": "Extend LM Capabilities with Tools",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/utilize-language-model-request-processor/extend-lm-capabilities-with-tools",
        "cookbook_path": "gen-ai/how-to-guides/utilize_language_model_request_processor/001_extend_lm_capabilities_with_tools",
        "category": "how-to-guides",
        "package": "gllm-inference",
        "examples": ["tools_extension"],
    },
    "utilize-lm-request-processor-2": {
        "title": "Produce Consistent Output from LM",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/utilize-language-model-request-processor/produce-consistent-output-from-lm",
        "cookbook_path": "gen-ai/how-to-guides/utilize_language_model_request_processor/002_produce_consistent_output_from_lm",
        "category": "how-to-guides",
        "package": "gllm-inference",
        "examples": ["consistent_output"],
    },
    "utilize-lm-request-processor-3": {
        "title": "Stream LM Output",
        "url": "https://gdplabs.gitbook.io/sdk/gen-ai-sdk/guides/utilize-language-model-request-processor/stream-lm-output",
        "cookbook_path": "gen-ai/how-to-guides/utilize_language_model_request_processor/003_stream_lm_output",
        "category": "how-to-guides",
        "package": "gllm-inference",
        "examples": ["stream_output"],
    },

    # Deep Research
    "deep-research-pipeline": {
        "title": "Deep Research Pipeline",
        "url": "https://gdplabs.gitbook.io/sdk/gl-deep-researcher/guides/compose-a-deep-research-flow/deep-research-pipeline",
        "cookbook_path": "deep-research",
        "category": "deep-research",
        "package": "gl-deep-researcher",
        "examples": ["01_a_deep_research_quickstart_openai", "01_b_deep_research_quickstart_google", "01_c_deep_research_quickstart_perplexity", "01_d_deep_research_quickstart_parallel", "01_e_deep_research_quickstart_glodr", "02_deep_research_custom_prompt"],
    },
    "deep-research-with-routing": {
        "title": "Deep Research in a Pipeline with Routing",
        "url": "https://gdplabs.gitbook.io/sdk/gl-deep-researcher/guides/deep-research-in-a-pipeline-with-routing",
        "cookbook_path": "deep-research",
        "category": "deep-research",
        "package": "gl-deep-researcher",
        "examples": ["deep_research_routing"],
    },
    "deep-research-google-drive": {
        "title": "Deep Research Pipeline with Google Drive Connector",
        "url": "https://gdplabs.gitbook.io/sdk/gl-deep-researcher/guides/deep-research-pipeline-with-google-drive-connector",
        "cookbook_path": "deep-research",
        "category": "deep-research",
        "package": "gl-deep-researcher",
        "examples": ["google_drive_connector"],
    },
    "hybrid-deep-researcher": {
        "title": "Hybrid Deep Researcher Pipeline",
        "url": "https://gdplabs.gitbook.io/sdk/gl-deep-researcher/guides/hybrid-deep-researcher-pipeline",
        "cookbook_path": "deep-research",
        "category": "deep-research",
        "package": "gl-deep-researcher",
        "examples": ["hybrid_deep_researcher"],
    },
}

REQUIRED_COOKBOOK_FILES = [
    ".env.example",
    ".python-version",
    "pyproject.toml",
    "uv.lock",
    "setup.sh",
    "setup.bat",
    "README.md",
]

PACKAGE_DEPENDENCIES = {
    "gllm-core": "gllm-core>=0.4.0,<0.5.0",
    "gllm-inference": "gllm-inference>=0.5.0,<0.6.0",
    "gllm-datastore": "gllm-datastore>=0.5.0,<0.6.0",
    "gllm-retrieval": "gllm-retrieval>=0.5.0,<0.6.0",
    "gllm-generation": "gllm-generation>=0.5.0,<0.6.0",
    "gllm-pipeline": "gllm-pipeline>=0.4.0,<0.5.0",
    "gllm-evals": "gllm-evals>=0.5.0,<0.6.0",
    "gl-deep-researcher": "gl-deep-researcher>=0.1.0,<0.2.0",
}

PACKAGE_EXTRAS = {
    "openai": "[openai]",
    "google": "[google]",
    "anthropic": "[anthropic]",
    "chroma": "[chroma]",
    "sql": "[sql]",
}

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CookbookEntry:
    path: str
    title: str
    category: str
    has_readme: bool = False
    has_code: bool = False
    has_all_required_files: bool = False
    missing_files: List[str] = field(default_factory=list)
    code_files: List[str] = field(default_factory=list)
    last_verified: Optional[str] = None
    verification_status: str = "unknown"  # PASS, FAIL, SKIPPED, UNKNOWN
    verification_error: Optional[str] = None
    gitbook_url: Optional[str] = None
    gitbook_page_id: Optional[str] = None

@dataclass
class SyncReport:
    generated_at: str
    summary: Dict[str, int]
    synced_entries: List[Dict[str, Any]]
    missing_in_cookbook: List[Dict[str, Any]]
    missing_in_gitbook: List[Dict[str, Any]]
    outdated_entries: List[Dict[str, Any]]
    verification_results: List[Dict[str, Any]]
    action_items: List[str]
    emails_sent: List[Dict[str, Any]] = field(default_factory=list)
    telegram_sent: List[Dict[str, Any]] = field(default_factory=list)
    commits_created: List[Dict[str, Any]] = field(default_factory=list)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def run_command(cmd: str, cwd: Optional[Path] = None, timeout: int = 120) -> tuple[int, str, str]:
    """Run a shell command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return -1, "", str(e)

# ============================================================================
# SCANNING FUNCTIONS
# ============================================================================

def scan_cookbook_directory(repo_path: Path) -> Dict[str, CookbookEntry]:
    """Scan the cookbook repository for all entries."""
    entries = {}

    # Scan how-to-guides
    htg_path = repo_path / "gen-ai" / "how-to-guides"
    if htg_path.exists():
        for readme in htg_path.rglob("README.md"):
            rel_path = readme.parent.relative_to(repo_path)
            entry_path = str(rel_path)
            code_files = list(readme.parent.glob("*.py"))
            required_files = []
            for req in REQUIRED_COOKBOOK_FILES:
                if not (readme.parent / req).exists():
                    required_files.append(req)

            entries[entry_path] = CookbookEntry(
                path=entry_path,
                title=readme.parent.name.replace("_", " ").title(),
                category="how-to-guides",
                has_readme=True,
                has_code=len(code_files) > 0,
                has_all_required_files=len(required_files) == 0,
                missing_files=required_files,
                code_files=[f.name for f in code_files],
            )

    # Scan tutorials
    tut_path = repo_path / "gen-ai" / "tutorials"
    if tut_path.exists():
        for readme in tut_path.rglob("README.md"):
            rel_path = readme.parent.relative_to(repo_path)
            entry_path = str(rel_path)
            if entry_path in entries:
                continue
            code_files = list(readme.parent.glob("*.py"))
            required_files = []
            for req in REQUIRED_COOKBOOK_FILES:
                if not (readme.parent / req).exists():
                    required_files.append(req)

            entries[entry_path] = CookbookEntry(
                path=entry_path,
                title=readme.parent.name.replace("_", " ").title(),
                category="tutorials",
                has_readme=True,
                has_code=len(code_files) > 0,
                has_all_required_files=len(required_files) == 0,
                missing_files=required_files,
                code_files=[f.name for f in code_files],
            )

    # Scan deep-research
    dr_path = repo_path / "deep-research"
    if dr_path.exists():
        code_files = list(dr_path.glob("*.py"))
        required_files = []
        for req in REQUIRED_COOKBOOK_FILES:
            if not (dr_path / req).exists():
                required_files.append(req)

        entries["deep-research"] = CookbookEntry(
            path="deep-research",
            title="Deep Research",
            category="deep-research",
            has_readme=(dr_path / "README.md").exists(),
            has_code=len(code_files) > 0,
            has_all_required_files=len(required_files) == 0,
            missing_files=required_files,
            code_files=[f.name for f in code_files],
        )

    print(f"Scanned {len(entries)} cookbook entries")
    return entries


def map_gitbook_to_cookbook(gitbook_pages: Dict, cookbook_entries: Dict[str, CookbookEntry]) -> tuple[List, List, List]:
    """Map GitBook pages to cookbook entries and find gaps."""
    synced = []
    missing_in_cookbook = []
    missing_in_gitbook = []

    # Pages that should have cookbook entries (have runnable Python examples)
    for page_id, page_info in gitbook_pages.items():
        cookbook_path = page_info.get("cookbook_path")
        if not cookbook_path:
            continue

        entry = cookbook_entries.get(cookbook_path)
        if entry:
            # Exists in cookbook
            synced.append({
                "page_id": page_id,
                "title": page_info["title"],
                "cookbook_path": cookbook_path,
                "has_code": entry.has_code,
                "has_all_required_files": entry.has_all_required_files,
                "missing_files": entry.missing_files,
                "code_files": entry.code_files,
                "url": page_info["url"],
                "category": page_info["category"],
            })
        else:
            # Missing in cookbook
            missing_in_cookbook.append({
                "page_id": page_id,
                "title": page_info["title"],
                "expected_path": cookbook_path,
                "url": page_info["url"],
                "category": page_info["category"],
                "package": page_info.get("package"),
                "examples": page_info.get("examples", []),
            })

    # Cookbook entries not documented in GitBook
    gitbook_paths = {p.get("cookbook_path", "") for p in gitbook_pages.values() if p.get("cookbook_path")}
    for entry_path, entry in cookbook_entries.items():
        found = False
        for gb_path in gitbook_paths:
            if entry_path == gb_path or entry_path.startswith(gb_path + "/"):
                found = True
                break
        if not found:
            missing_in_gitbook.append({
                "path": entry_path,
                "title": entry.title,
                "has_readme": entry.has_readme,
                "has_code": entry.has_code,
                "category": entry.category,
            })

    return synced, missing_in_cookbook, missing_in_gitbook


# ============================================================================
# VERIFICATION FUNCTIONS
# ============================================================================

async def verify_cookbook_entry(entry_path: str, repo_path: Path) -> Dict[str, Any]:
    """Verify a cookbook entry by running its Python scripts."""
    full_path = repo_path / entry_path
    if not full_path.exists():
        return {
            "path": entry_path,
            "status": "FAIL",
            "error": "Directory does not exist",
            "exit_code": -1,
        }

    # Find Python files to run
    py_files = list(full_path.glob("*.py"))
    if not py_files:
        return {
            "path": entry_path,
            "status": "SKIPPED",
            "error": "No Python files to run",
            "exit_code": 0,
        }

    # Set up UV auth
    env = os.environ.copy()
    env["UV_INDEX_GEN_AI_INTERNAL_USERNAME"] = "oauth2accesstoken"
    # Note: In real usage, we'd get the token from gcloud
    # For now, we'll try without it (will fail if deps not cached)

    results = []
    overall_status = "PASS"

    for py_file in py_files:
        # Run with uv
        cmd = f"uv run {py_file.name}"
        exit_code, stdout, stderr = run_command(cmd, cwd=full_path, timeout=180)

        status = "PASS" if exit_code == 0 else "FAIL"
        if status == "FAIL":
            overall_status = "FAIL"

        results.append({
            "script": py_file.name,
            "status": status,
            "exit_code": exit_code,
            "stdout": stdout[:2000] if stdout else "",
            "stderr": stderr[:2000] if stderr else "",
        })

    return {
        "path": entry_path,
        "status": overall_status,
        "scripts": results,
        "error": None if overall_status == "PASS" else "One or more scripts failed",
    }


# ============================================================================
# EMAIL NOTIFICATION
# ============================================================================

def send_email_notification(report: SyncReport, action_type: str = "sync_report") -> bool:
    """Send email notification with sync report."""
    try:
        with open(EMAIL_CONFIG_PATH) as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"Failed to load email config: {e}")
        return False

    app_password = cfg.get("app_password", "") or os.environ.get("GMAIL_APP_PASSWORD", "")
    if not app_password:
        print("No app password configured for email")
        return False

    import smtplib
    import ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    summary = report.summary
    status = "SUCCESS" if summary["missing_in_cookbook"] == 0 and summary["outdated_entries"] == 0 else "PARTIAL" if summary["synced_entries"] > 0 else "FAILED"

    subject = f"[Cookbook Sync] {status}: {action_type} - {datetime.now().strftime('%Y-%m-%d')}"

    # Build HTML report
    html = build_html_email(report, status)
    plain = build_plain_email(report, status)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["sender"]
    msg["To"] = ", ".join(cfg["recipients"])
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(cfg["sender"], app_password)
            server.send_message(msg)
        print(f"Email sent successfully to {msg['To']}")

        report.emails_sent.append({
            "recipient": cfg["recipients"][0],
            "subject": subject,
            "status": "sent",
            "sent_at": datetime.now().isoformat(),
        })
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        report.emails_sent.append({
            "recipient": cfg["recipients"][0],
            "subject": subject,
            "status": "failed",
            "error": str(e),
            "sent_at": datetime.now().isoformat(),
        })
        return False


def build_html_email(report: SyncReport, status: str) -> str:
    """Build HTML email content."""
    summary = report.summary

    status_colors = {"SUCCESS": "#28a745", "PARTIAL": "#ffc107", "FAILED": "#dc3545"}
    status_color = status_colors.get(status, "#6c757d")

    synced_html = ""
    for item in report.synced_entries[:20]:
        code_status = "✓" if item.get("has_code") else "✗"
        files_status = "✓" if item.get("has_all_required_files") else "✗"
        synced_html += f"""
        <tr>
          <td style="padding: 8px; border-bottom: 1px solid #eee;">{item['title']}</td>
          <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{code_status}</td>
          <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{files_status}</td>
          <td style="padding: 8px; border-bottom: 1px solid #eee;"><a href="{item['url']}" style="color: #4361ee;">View</a></td>
        </tr>"""

    missing_cookbook_html = ""
    for item in report.missing_in_cookbook[:15]:
        missing_cookbook_html += f"""
        <tr>
          <td style="padding: 8px; border-bottom: 1px solid #eee;">{item['title']}</td>
          <td style="padding: 8px; border-bottom: 1px solid #eee; font-family: monospace; font-size: 12px;">{item['expected_path']}</td>
          <td style="padding: 8px; border-bottom: 1px solid #eee;"><a href="{item['url']}" style="color: #4361ee;">View</a></td>
        </tr>"""

    action_items_html = ""
    for i, item in enumerate(report.action_items, 1):
        action_items_html += f"<li style='margin-bottom: 8px;'><strong>Action {i}:</strong> {item}</li>"

    missing_section = ""
    if report.missing_in_cookbook:
        missing_section = f"""
<h2>⚠ Missing in Cookbook ({summary['missing_in_cookbook']})</h2>
<p style="font-size: 13px; color: #6c757d;">These GitBook pages lack corresponding cookbook code examples.</p>
<table><thead><tr><th>Page Title</th><th>Expected Path</th><th>Link</th></tr></thead><tbody>{missing_cookbook_html}</tbody></table>"""

    html = f"""<html>
<head>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #1a1a2e; }}
    h1 {{ color: #1a1a2e; margin-bottom: 8px; }}
    h2 {{ color: #333; margin-top: 24px; margin-bottom: 12px; font-size: 18px; border-bottom: 2px solid #4361ee; padding-bottom: 8px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }}
    th {{ background: #f8f9fa; padding: 10px; text-align: left; font-weight: 600; border-bottom: 2px solid #dee2e6; }}
    td {{ padding: 8px; }}
    .stats {{ display: flex; gap: 16px; margin: 20px 0; flex-wrap: wrap; }}
    .stat-box {{ background: #f8f9fa; border-radius: 8px; padding: 16px; text-align: center; min-width: 120px; flex: 1; }}
    .stat-number {{ font-size: 28px; font-weight: bold; color: #4361ee; }}
    .stat-label {{ font-size: 12px; color: #6c757d; margin-top: 4px; }}
    .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; color: white; background: {status_color}; }}
    ul {{ padding-left: 20px; }}
    .footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
  </style>
</head>
<body>
<div style="border-bottom: 3px solid #4361ee; padding-bottom: 16px; margin-bottom: 24px;">
  <h1 style="margin: 0;">📚 Cookbook ↔ GitBook Sync Report</h1>
  <p style="margin: 8px 0 0; color: #6c757d; font-size: 13px;">Generated: {report.generated_at}</p>
  <div style="margin-top: 12px;"><span class="status-badge">{status}</span></div>
</div>

<div class="stats">
  <div class="stat-box"><div class="stat-number" style="color: #28a745;">{summary['synced_entries']}</div><div class="stat-label">Synced Entries</div></div>
  <div class="stat-box"><div class="stat-number {'gap-high' if summary['missing_in_cookbook'] > 0 else 'gap-low'}">{summary['missing_in_cookbook']}</div><div class="stat-label">Missing in Cookbook</div></div>
  <div class="stat-box"><div class="stat-number {'gap-medium' if summary['missing_in_gitbook'] > 0 else 'gap-low'}">{summary['missing_in_gitbook']}</div><div class="stat-label">Missing in GitBook</div></div>
  <div class="stat-box"><div class="stat-number {'gap-high' if summary['outdated_entries'] > 0 else 'gap-low'}">{summary['outdated_entries']}</div><div class="stat-label">Outdated</div></div>
  <div class="stat-box"><div class="stat-number" style="color: #4361ee;">{summary['verified_working']}</div><div class="stat-label">Verified Working</div></div>
  <div class="stat-box"><div class="stat-number" style="color: #dc3545;">{summary['failed_verification']}</div><div class="stat-label">Failed Verification</div></div>
</div>

<h2>✅ Synced Entries ({summary['synced_entries']})</h2>
<table><thead><tr><th>Guide Title</th><th style="text-align: center;">Code</th><th style="text-align: center;">Files</th><th>Link</th></tr></thead><tbody>{synced_html}</tbody></table>

{missing_section}

<h2>📋 Action Items</h2>
<ul>{action_items_html}</ul>

<h2>🔗 Resources</h2>
<ul>
  <li><strong>Cookbook Repository:</strong> <a href="https://github.com/gdplabs/gen-ai-sdk-cookbook" style="color: #4361ee;">https://github.com/gdplabs/gen-ai-sdk-cookbook</a></li>
  <li><strong>GitBook Documentation:</strong> <a href="https://gdplabs.gitbook.io/sdk" style="color: #4361ee;">https://gdplabs.gitbook.io/sdk</a></li>
</ul>

<div class="footer">
  <p><strong>Report generated by:</strong> Cookbook ↔ GitBook Sync Workflow</p>
  <p>This is an automated report. Please review the action items and create PRs as needed.</p>
</div>
</body></html>"""
    return html


def build_plain_email(report: SyncReport, status: str) -> str:
    """Build plain text email content."""
    summary = report.summary
    lines = [
        f"Cookbook ↔ GitBook Sync Report",
        f"Generated: {report.generated_at}",
        f"Status: {status}",
        "",
        "Summary:",
        f"- Synced Entries: {summary['synced_entries']}",
        f"- Missing in Cookbook: {summary['missing_in_cookbook']}",
        f"- Missing in GitBook: {summary['missing_in_gitbook']}",
        f"- Outdated: {summary['outdated_entries']}",
        f"- Verified Working: {summary['verified_working']}",
        f"- Failed Verification: {summary['failed_verification']}",
        "",
        "Action Items:",
    ]
    for item in report.action_items:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "Resources:",
        "- Cookbook Repository: https://github.com/gdplabs/gen-ai-sdk-cookbook",
        "- GitBook Documentation: https://gdplabs.gitbook.io/sdk",
    ])
    return "\n".join(lines)


# ============================================================================
# TELEGRAM NOTIFICATION
# ============================================================================

def send_telegram_notification(report: SyncReport) -> bool:
    """Send Telegram notification with sync summary."""
    # Try to get bot token and chat ID from environment or config
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("Telegram bot token or chat ID not configured, skipping Telegram notification")
        # Try loading from a config file
        telegram_config_path = Path.home() / ".config" / "telegram" / "config.json"
        if telegram_config_path.exists():
            try:
                with open(telegram_config_path) as f:
                    cfg = json.load(f)
                    bot_token = cfg.get("bot_token")
                    chat_id = cfg.get("chat_id")
            except Exception:
                pass

    if not bot_token or not chat_id:
        report.telegram_sent.append({
            "status": "skipped",
            "reason": "Not configured",
            "sent_at": datetime.now().isoformat(),
        })
        return False

    import requests

    summary = report.summary
    status = "SUCCESS" if summary["missing_in_cookbook"] == 0 and summary["outdated_entries"] == 0 else "PARTIAL" if summary["synced_entries"] > 0 else "FAILED"

    emoji = {"SUCCESS": "✅", "PARTIAL": "⚠️", "FAILED": "❌"}.get(status, "📊")

    message = f"""{emoji} <b>Cookbook Sync {status}</b>

📊 <b>Summary:</b>
• Synced: {summary['synced_entries']}
• Missing in Cookbook: {summary['missing_in_cookbook']}
• Missing in GitBook: {summary['missing_in_gitbook']}
• Outdated: {summary['outdated_entries']}
• Verified Working: {summary['verified_working']}
• Failed: {summary['failed_verification']}

📋 <b>Top Actions:</b>"""

    for item in report.action_items[:3]:
        message += f"\n• {item}"

    if len(report.action_items) > 3:
        message += f"\n• ... and {len(report.action_items) - 3} more"

    message += f"\n\n🔗 <a href='https://github.com/gdplabs/gen-ai-sdk-cookbook'>View Cookbook</a> | <a href='https://gdplabs.gitbook.io/sdk'>View GitBook</a>"

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10,
        )

        if response.status_code == 200:
            print("Telegram notification sent successfully")
            report.telegram_sent.append({
                "status": "sent",
                "message_id": response.json().get("result", {}).get("message_id"),
                "sent_at": datetime.now().isoformat(),
            })
            return True
        else:
            print(f"Telegram notification failed: {response.text}")
            report.telegram_sent.append({
                "status": "failed",
                "error": response.text,
                "sent_at": datetime.now().isoformat(),
            })
            return False
    except Exception as e:
        print(f"Failed to send Telegram notification: {e}")
        report.telegram_sent.append({
            "status": "failed",
            "error": str(e),
            "sent_at": datetime.now().isoformat(),
        })
        return False


# ============================================================================
# MAIN SYNC FUNCTION
# ============================================================================

async def run_sync(verify: bool = True) -> SyncReport:
    """Run the complete sync workflow."""
    print("=" * 60)
    print("Cookbook ↔ GitBook Sync Agent")
    print("=" * 60)

    # Scan cookbook
    print("\n[1/5] Scanning cookbook repository...")
    cookbook_entries = scan_cookbook_directory(COOKBOOK_REPO_PATH)

    # Map GitBook to cookbook
    print("\n[2/5] Mapping GitBook pages to cookbook entries...")
    synced, missing_in_cookbook, missing_in_gitbook = map_gitbook_to_cookbook(GITBOOK_PAGES, cookbook_entries)

    # Verify cookbook entries
    verification_results = []
    if verify:
        print("\n[3/5] Verifying cookbook entries (running examples)...")
        for entry in synced:
            if entry.get("has_code"):
                print(f"  Verifying: {entry['cookbook_path']}")
                result = await verify_cookbook_entry(entry["cookbook_path"], COOKBOOK_REPO_PATH)
                result["title"] = entry["title"]
                result["url"] = entry["url"]
                verification_results.append(result)
            else:
                verification_results.append({
                    "path": entry["cookbook_path"],
                    "title": entry["title"],
                    "url": entry["url"],
                    "status": "SKIPPED",
                    "error": "No code files",
                })
    else:
        print("\n[3/5] Skipping verification (audit mode)")
        for entry in synced:
            verification_results.append({
                "path": entry["cookbook_path"],
                "title": entry["title"],
                "url": entry["url"],
                "status": "UNKNOWN",
                "error": "Verification skipped",
            })

    # Count verification results
    verified_working = sum(1 for r in verification_results if r["status"] == "PASS")
    failed_verification = sum(1 for r in verification_results if r["status"] == "FAIL")

    # Build action items
    action_items = []
    if missing_in_cookbook:
        action_items.append(f"Create {len(missing_in_cookbook)} missing cookbook entries from GitBook guides")
    if missing_in_gitbook:
        action_items.append(f"Document {len(missing_in_gitbook)} cookbook entries in GitBook")
    if failed_verification > 0:
        action_items.append(f"Fix {failed_verification} cookbook entries that failed verification")
    if not action_items:
        action_items.append("All entries are in sync - no action needed")

    # Build report
    report = SyncReport(
        generated_at=datetime.now().isoformat(),
        summary={
            "total_gitbook_pages": len(GITBOOK_PAGES),
            "total_cookbook_entries": len(cookbook_entries),
            "synced_entries": len(synced),
            "missing_in_cookbook": len(missing_in_cookbook),
            "missing_in_gitbook": len(missing_in_gitbook),
            "outdated_entries": 0,  # Would need drift detection
            "verified_working": verified_working,
            "failed_verification": failed_verification,
        },
        synced_entries=synced,
        missing_in_cookbook=missing_in_cookbook,
        missing_in_gitbook=missing_in_gitbook,
        outdated_entries=[],
        verification_results=verification_results,
        action_items=action_items,
    )

    # Send notifications
    print("\n[4/5] Sending email notification...")
    send_email_notification(report, "sync_complete")

    print("\n[5/5] Sending Telegram notification...")
    send_telegram_notification(report)

    # Save report
    print("\nSaving report...")
    with open(REPORT_OUTPUT_PATH, "w") as f:
        json.dump(asdict(report), f, indent=2)

    # Save HTML report
    html = build_html_email(report, "SUCCESS" if report.summary["missing_in_cookbook"] == 0 else "PARTIAL")
    with open(HTML_REPORT_PATH, "w") as f:
        f.write(html)

    print(f"\nReport saved to: {REPORT_OUTPUT_PATH}")
    print(f"HTML report saved to: {HTML_REPORT_PATH}")

    return report


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Cookbook ↔ GitBook Sync Agent")
    parser.add_argument("--audit", action="store_true", help="Run in audit mode (no verification)")
    parser.add_argument("--no-email", action="store_true", help="Skip email notification")
    parser.add_argument("--no-telegram", action="store_true", help="Skip Telegram notification")
    args = parser.parse_args()

    # Run sync
    report = asyncio.run(run_sync(verify=not args.audit))

    # Print summary
    print("\n" + "=" * 60)
    print("SYNC SUMMARY")
    print("=" * 60)
    print(f"GitBook Pages: {report.summary['total_gitbook_pages']}")
    print(f"Cookbook Entries: {report.summary['total_cookbook_entries']}")
    print(f"Synced: {report.summary['synced_entries']}")
    print(f"Missing in Cookbook: {report.summary['missing_in_cookbook']}")
    print(f"Missing in GitBook: {report.summary['missing_in_gitbook']}")
    print(f"Verified Working: {report.summary['verified_working']}")
    print(f"Failed Verification: {report.summary['failed_verification']}")
    print("\nAction Items:")
    for item in report.action_items:
        print(f"  - {item}")
    print(f"\nEmails Sent: {len(report.emails_sent)}")
    print(f"Telegram Sent: {len(report.telegram_sent)}")


if __name__ == "__main__":
    main()