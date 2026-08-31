from typing import Any, Dict, List

from .memory_store import MemoryStore
from state import AnalysisState


class RetainNode:
    def __init__(self, db_path: str = "database/agent_memory.sqlite"):
        self.store = MemoryStore(db_path=db_path)

    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        persistent_mode = bool(state.get("use_persistent_memory", False))
        if not persistent_mode:
            print("💾 [Retain Node]: Ephemeral session mode enabled; no database write.")
            return {"memory_write_status": "skipped:ephemeral_session"}

        print("💾 [Retain Node]: Persisting dataset profile, run findings, and chart outcomes...")
        dataset_fingerprint = state.get("dataset_fingerprint", "")
        if not dataset_fingerprint:
            return {"memory_write_status": "skipped:no_dataset_fingerprint"}

        dataset_name = state.get("dataset_name", "unknown_dataset")
        schema_info = state.get("schema_info", [])
        feature_registry = state.get("feature_registry", {})
        profile_summary = state.get("data_profile_summary", "")

        self.store.upsert_dataset(
            dataset_fingerprint,
            dataset_name,
            schema_info,
            feature_registry,
            profile_summary,
        )

        run_id = state.get("run_id", "")
        report_markdown = state.get("final_report_markdown", "") or ""
        reflection_summary = state.get("reflection_summary", "") or ""
        findings = state.get("report_findings", [])
        chart_plan = state.get("chart_plan", [])
        failure_log = state.get("chart_failure_log", [])

        self.store.insert_run(
            run_id=run_id,
            dataset_fingerprint=dataset_fingerprint,
            question=state.get("target_business_question", "Analyze dataset"),
            report_markdown=report_markdown,
            reflection_summary=reflection_summary,
            findings=findings,
            chart_plan=chart_plan,
        )

        chart_results: List[Dict[str, Any]] = []

        for item in findings:
            chart_results.append(
                {
                    "chart_family": item.get("chart_family"),
                    "columns": item.get("columns", []),
                    "business_question": item.get("business_question"),
                    "approved": True,
                    "notes": "approved_via_visual_critic",
                }
            )

        for item in state.get("chart_validation_results", []):
            if not item.get("approved", True):
                chart_results.append(
                    {
                        "chart_family": item.get("chart_family"),
                        "columns": item.get("columns", []),
                        "business_question": "",
                        "approved": False,
                        "notes": " | ".join(item.get("errors", [])),
                    }
                )

        for item in failure_log:
            chart_results.append(
                {
                    "chart_family": item.get("chart_family"),
                    "columns": item.get("columns", []),
                    "business_question": item.get("business_question", ""),
                    "approved": False,
                    "notes": f"skipped_after_max_retries: {item.get('reason', 'unknown')}",
                }
            )

        self.store.insert_chart_outcomes(run_id, dataset_fingerprint, chart_results)

        for item in failure_log:
            self.store.insert_failure_pattern(
                dataset_fingerprint=dataset_fingerprint,
                chart_family=item.get("chart_family", "unknown"),
                error_text=item.get("reason", ""),
            )

        return {"memory_write_status": "ok"}