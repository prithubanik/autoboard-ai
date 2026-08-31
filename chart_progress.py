from typing import Any, Dict

from state import AnalysisState


class ChartProgressNode:
    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        print("📈 [Chart Progress]: Advancing chart counters...", flush=True)

        new_plots_count = state.get("plots_generated_count", 0) + 1
        new_chart_index = state.get("current_chart_index", 0) + 1

        print(
            f"📈 [Chart Progress]: current_chart_index={new_chart_index}, "
            f"plots_generated_count={new_plots_count}",
            flush=True,
        )

        return {
            "plots_generated_count": new_plots_count,
            "current_chart_index": new_chart_index,
            "retry_count": 0,
            "execution_error": None,
            "visual_critique": None,
        }