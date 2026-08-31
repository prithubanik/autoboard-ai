from typing import Any, Dict

from state import AnalysisState


class ChartSkipNode:
    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        print("⏭️ [Chart Skip]: Max retries reached, skipping this chart...", flush=True)

        current_index = state.get("current_chart_index", 0)
        chart_plan = state.get("chart_plan", [])
        spec = chart_plan[current_index] if current_index < len(chart_plan) else {}

        skipped = list(state.get("skipped_chart_indices", []))
        skipped.append(current_index)

        failure_log = list(state.get("chart_failure_log", []))
        failure_log.append(
            {
                "angle_id": spec.get("angle_id", current_index + 1),
                "chart_family": spec.get("chart_family", "unknown"),
                "columns": spec.get("columns", []),
                "business_question": spec.get("business_question", ""),
                "reason": (
                    state.get("visual_critique")
                    or state.get("execution_error")
                    or "Unknown failure after max retries."
                ),
            }
        )

        new_chart_index = current_index + 1
        print(f"⏭️ [Chart Skip]: current_chart_index={new_chart_index}", flush=True)

        return {
            "skipped_chart_indices": skipped,
            "chart_failure_log": failure_log,
            "current_chart_index": new_chart_index,
            "retry_count": 0,
            "execution_error": None,
            "visual_critique": None,
        }