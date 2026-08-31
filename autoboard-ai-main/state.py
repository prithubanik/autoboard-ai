import operator
from typing import TypedDict, List, Dict, Any, Optional, Annotated

# Max number of past chart-generation script versions to keep in state.
# Trimming happens INSIDE the reducer below, so no node ever needs to
# manually slice code_history (that was the source of the doubling bug).
CODE_HISTORY_CAP = 5


def _append_and_cap_code_history(
    existing: Optional[List[str]], new: Optional[List[str]]
) -> List[str]:
    """Additive reducer for code_history that also caps its length.

    IMPORTANT: nodes must only ever return the NEW code snippet(s) for this
    key (e.g. {"code_history": [new_code]}), never the full accumulated
    history. If a node returns the full existing list, this reducer will
    concatenate it onto itself and the state will grow without bound,
    eventually stalling the LangGraph checkpointer.
    """
    combined = (existing or []) + (new or [])
    return combined[-CODE_HISTORY_CAP:]


class AnalysisState(TypedDict, total=False):
    raw_data_path: str
    target_business_question: str
    cleaned_table_name: str
    diagnostics_table_name: str
    dataset_name: str
    dataset_fingerprint: str
    run_id: str
    session_id: str

    data_profile_summary: str
    feature_metadata: Dict[str, Any]
    feature_registry: Dict[str, Any]
    business_rules: Dict[str, Any]
    dataset_preview: List[Dict[str, Any]]
    schema_info: List[Dict[str, Any]]
    numeric_summary: Dict[str, Any]
    categorical_summary: Dict[str, Any]
    correlation_findings: List[Dict[str, Any]]
    cleaning_log: List[str]

    memory_context: Dict[str, Any]
    retrieved_memories: List[Dict[str, Any]]
    retrieved_chart_patterns: List[Dict[str, Any]]
    retrieved_business_definitions: List[Dict[str, Any]]
    prior_run_summaries: List[Dict[str, Any]]
    analysis_memory_hits: List[Dict[str, Any]]

    reflection_summary: Optional[str]
    reflection_updates: List[Dict[str, Any]]
    memory_write_status: Optional[str]

    insight_candidates: List[Dict[str, Any]]
    ranked_chart_plan: List[Dict[str, Any]]
    chart_plan: List[Dict[str, Any]]
    current_chart_spec: Dict[str, Any]
    chart_validation_results: List[Dict[str, Any]]

    # NOTE: report_findings is populated incrementally, ONE chart at a
    # time, by the visual critic on approval. It uses an additive reducer
    # just like final_ui_blocks/code_history: nodes must ONLY return the
    # newly created finding(s), never the whole accumulated list.
    report_findings: Annotated[List[Dict[str, Any]], operator.add]
    final_report_markdown: Optional[str]

    current_code: Optional[str]
    code_history: Annotated[List[str], _append_and_cap_code_history]
    execution_error: Optional[str]

    # NOTE: base64/JSON blobs removed from state to prevent checkpointer bloat.
    # Only lightweight file paths are carried through the graph now.
    rendered_image_path: Optional[str]
    rendered_json_path: Optional[str]
    artifact_warning: Optional[str]
    visual_critique: Optional[str]

    retry_count: int
    current_chart_index: int
    skipped_chart_indices: List[int]
    chart_failure_log: List[Dict[str, Any]]
    prior_chart_summaries: List[str]

    final_ui_blocks: Annotated[List[Dict[str, Any]], operator.add]
    plots_generated_count: int
    target_plots_count: int
    cache_hit: Optional[bool]
    use_persistent_memory: Optional[bool]
    user_edit_request: Optional[str]