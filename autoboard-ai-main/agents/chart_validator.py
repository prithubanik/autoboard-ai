from typing import Any, Dict, List
import time

from state import AnalysisState


class ChartValidatorNode:
    def validate_spec(
        self,
        spec: Dict[str, Any],
        registry: Dict[str, Any],
        rules: Dict[str, Any],
    ) -> Dict[str, Any]:
        banned_suffixes = tuple(rules.get("banned_suffixes", []))
        cols = spec.get("columns", [])
        errors: List[str] = []

        for col in cols:
            if col not in registry:
                errors.append(f"Unknown column: {col}")
                continue

            if banned_suffixes and col.endswith(banned_suffixes):
                errors.append(f"Banned helper column selected: {col}")

            if registry[col].get("banned"):
                errors.append(f"Column marked banned: {col}")

            if not registry[col].get("safe_for_charting", True):
                errors.append(f"Unsafe for charting: {col}")

        approved = len(errors) == 0

        return {
            "chart_family": spec.get("chart_family"),
            "columns": cols,
            "approved": approved,
            "errors": errors,
        }

    def execute(self, state: AnalysisState) -> AnalysisState:
        print("🛡️ [Chart Validator]: ENTER execute() at t=0.00s", flush=True)

        chart_plan = state.get("chart_plan", [])
        current_chart_index = state.get("current_chart_index", 0)
        registry = state.get("feature_registry", {})
        rules = state.get("business_rules", {})

        if not chart_plan:
            return {
                "execution_error": "No chart plan available for validation.",
                "retry_count": state.get("retry_count", 0) + 1,
            }

        if current_chart_index >= len(chart_plan):
            return {"execution_error": None}

        current_spec = chart_plan[current_chart_index]
        result = self.validate_spec(current_spec, registry, rules)

        history = list(state.get("chart_validation_results", []))
        history.append(result)

        if not result["approved"]:
            error_msg = "; ".join(result["errors"])
            return {
                "current_chart_spec": current_spec,
                "chart_validation_results": history,
                "execution_error": error_msg,
                "retry_count": state.get("retry_count", 0) + 1,
            }

        return {
            "current_chart_spec": current_spec,
            "chart_validation_results": history,
            "execution_error": None,
        }