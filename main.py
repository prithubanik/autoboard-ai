# main.py
import faulthandler
import signal
import sys
import threading

from graph import build_analyst_graph, executor_node
from state import AnalysisState

# Dump all thread stacks automatically if execution stalls
faulthandler.enable()

if sys.platform != "win32":
    # On Linux/macOS: kill -SIGUSR1 <pid> dumps stack traces without killing the process
    faulthandler.register(signal.SIGUSR1, all_threads=True)
else:
    # On Windows: auto-dump stack traces to a file if nothing progresses for 60s
    faulthandler.dump_traceback_later(60, repeat=True, exit=False,
                                       file=open("hang_trace.log", "w"))


def run_autonomous_analyst(csv_file_path: str, thread_id: str = "session_001"):
    app = build_analyst_graph()

    initial_state: AnalysisState = {
        "raw_data_path": csv_file_path,
        "target_business_question": "Perform automated exploratory analysis and flag anomalies.",
        "cleaned_table_name": "",
        "diagnostics_table_name": "",
        "dataset_name": "",
        "dataset_fingerprint": "",
        "run_id": "",
        "session_id": thread_id,
        "data_profile_summary": "",
        "feature_metadata": {},
        "feature_registry": {},
        "business_rules": {},
        "dataset_preview": [],
        "schema_info": [],
        "numeric_summary": {},
        "categorical_summary": {},
        "correlation_findings": [],
        "cleaning_log": [],
        "memory_context": {},
        "retrieved_memories": [],
        "retrieved_chart_patterns": [],
        "retrieved_business_definitions": [],
        "prior_run_summaries": [],
        "analysis_memory_hits": [],
        "reflection_summary": None,
        "reflection_updates": [],
        "memory_write_status": None,
        "insight_candidates": [],
        "ranked_chart_plan": [],
        "chart_plan": [],
        "current_chart_spec": {},
        "chart_validation_results": [],
        "report_findings": [],
        "final_report_markdown": None,
        "current_code": None,
        "code_history": [],
        "execution_error": None,
        "rendered_image_path": None,
        "rendered_json_path": None,
        "artifact_warning": None,
        "visual_critique": None,
        "retry_count": 0,
        "current_chart_index": 0,
        "skipped_chart_indices": [],
        "chart_failure_log": [],
        "prior_chart_summaries": [],
        "final_ui_blocks": [],
        "plots_generated_count": 0,
        "target_plots_count": 10,
        "cache_hit": False,
        "use_persistent_memory": False,
    }

    config = {"configurable": {"thread_id": thread_id, "recursion_limit": 100}}

    try:
        final_state = app.invoke(initial_state, config=config)
        return final_state.get("final_ui_blocks", [])
    finally:
        executor_node.shutdown()