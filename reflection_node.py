from typing import Any, Dict, List

from state import AnalysisState


class ReflectionNode:
    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        print("🔎 [Reflection Node]: Consolidating reusable memory summary...")
        findings = state.get("report_findings", [])
        prior_runs = state.get("prior_run_summaries", [])
        chart_plan = state.get("chart_plan", [])
        failure_log = state.get("chart_failure_log", [])

        lines: List[str] = []
        lines.append(f"Dataset: {state.get('dataset_name', 'unknown_dataset')}")
        lines.append(f"Approved charts this run: {len(findings)}")
        lines.append(f"Skipped charts this run: {len(failure_log)}")
        if findings:
            top = findings[:3]
            lines.append(
                "Top chart families: "
                + ", ".join(sorted({x.get("chart_family", "unknown") for x in top}))
            )
        if chart_plan:
            lines.append(
                "Planned analytical angles: "
                + ", ".join(x.get("chart_family", "unknown") for x in chart_plan[:5])
            )
        if failure_log:
            lines.append(
                "Chart families to avoid repeating without changes: "
                + ", ".join(sorted({x.get("chart_family", "unknown") for x in failure_log}))
            )
        if prior_runs:
            lines.append(f"Prior related runs recalled: {len(prior_runs)}")
        if state.get("cleaning_log"):
            lines.append(
                "Key cleaning actions: "
                + " | ".join(state.get("cleaning_log", [])[:3])
            )

        reflection_summary = "\n".join(lines)
        updates = [
            {
                "dataset_fingerprint": state.get("dataset_fingerprint"),
                "run_id": state.get("run_id"),
                "summary": reflection_summary,
            }
        ]

        return {
            "reflection_summary": reflection_summary,
            "reflection_updates": updates,
            "final_ui_blocks": [
                {
                    "id": "block-reflection-summary",
                    "type": "MarkdownBlock",
                    "title": "Memory Reflection",
                    "content": reflection_summary,
                }
            ],
        }