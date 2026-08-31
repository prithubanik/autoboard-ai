import json
import os
import shutil
import uuid

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from graph import build_analyst_graph, executor_node


app = FastAPI(title="Autonomous Multimodal Analyst API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("artifacts/charts", exist_ok=True)
app.mount("/artifacts", StaticFiles(directory="artifacts"), name="artifacts")


@app.post("/api/v1/analyze/stream")
async def analyze_dataset_stream(file: UploadFile = File(...)):
    filepath = f"data/{file.filename}"
    os.makedirs("data", exist_ok=True)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    def event_generator():
        workflow = build_analyst_graph()
        session_id = uuid.uuid4().hex

        initial_state = {
            "raw_data_path": filepath,
            "target_business_question": "Perform automated exploratory analysis and flag anomalies.",
            "cleaned_table_name": "",
            "diagnostics_table_name": "",
            "dataset_name": os.path.basename(filepath),
            "dataset_fingerprint": "",
            "run_id": "",
            "session_id": session_id,

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
            "current_chart_spec": None,
            "chart_validation_results": [],

            "report_findings": [],
            "final_report_markdown": None,

            "current_code": None,
            "code_history": [],
            "execution_error": None,

            "rendered_image_path": None,
            "rendered_json_path": None,
            "visual_critique": None,
            "artifact_warning": None,

            "retry_count": 0,
            "current_chart_index": 0,
            "skipped_chart_indices": [],
            "chart_failure_log": [],
            "prior_chart_summaries": [],

            "final_ui_blocks": [],
            "plots_generated_count": 0,
            "target_plots_count": 6,

            "cache_hit": False,
            "use_persistent_memory": False,
        }

        config = {"configurable": {"thread_id": session_id}}
        latest_state = dict(initial_state)

        try:
            for event in workflow.stream(initial_state, config=config):
                for node_name, state_update in event.items():
                    latest_state.update(state_update)

                    messages = {
                        "memory_router": "Memory router accepted the request.",
                        "recall": "Recall node loaded prior dataset and run memory.",
                        "data_cleaner": "Data profiler and cleaner completed dataset understanding.",
                        "insight_planner": "Insight planner ranked chart candidates using recalled context.",
                        "chart_validator": "Chart validator checked the current chart specification.",
                        "chart_builder": "Template chart builder prepared executable visualization code.",
                        "sandbox_executor": (
                            "Sandbox executed chart code successfully."
                            if not state_update.get("execution_error")
                            else "Sandbox execution failed. Retrying chart generation."
                        ),
                        "report_writer": "Report writer compiled the executive summary.",
                        "memory_retain": "Retain node persisted run memory and chart outcomes.",
                        "reflection_node": "Reflection node synthesized reusable memory notes.",
                    }

                    msg = messages.get(node_name, f"Agent {node_name} completed its task.")
                    yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"

                    blocks = state_update.get("final_ui_blocks", [])
                    if blocks:
                        yield f"data: {json.dumps({'type': 'partial_blocks', 'blocks': blocks})}\n\n"

                    if state_update.get("artifact_warning"):
                        yield f"data: {json.dumps({'type': 'warning', 'message': state_update.get('artifact_warning')})}\n\n"

            final_state = latest_state
            final_payload = {
                "type": "complete",
                "report_blocks": final_state.get("final_ui_blocks", []),
                "final_report_markdown": final_state.get("final_report_markdown"),
                "reflection_summary": final_state.get("reflection_summary"),
                "memory_write_status": final_state.get("memory_write_status"),
                "chart_failure_log": final_state.get("chart_failure_log", []),
            }
            yield f"data: {json.dumps(final_payload)}\n\n"

        finally:
            executor_node.shutdown()

    return StreamingResponse(event_generator(), media_type="text/event-stream")