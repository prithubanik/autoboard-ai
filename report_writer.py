from typing import Any, Dict, List

from state import AnalysisState


class ReportWriterNode:
    def _build_overall_story(self, state: AnalysisState) -> str:
        findings = state.get("report_findings", [])
        approved_count = len(findings)
        skipped_count = len(state.get("chart_failure_log", []))
        row_count = None
        column_count = None

        profile_raw = state.get("data_profile_summary", "") or ""
        try:
            import json
            profile = json.loads(profile_raw)
            row_count = profile.get("row_count")
            column_count = profile.get("column_count")
        except Exception:
            pass

        parts = []
        if row_count and column_count:
            parts.append(
                f"This dataset contains {row_count:,} rows and {column_count:,} columns, so the analysis focuses on the strongest generic business drivers, behavior patterns, and segment differences."
            )
        else:
            parts.append(
                "This dataset was analyzed to identify the strongest drivers, behavior patterns, and segment differences."
            )

        if approved_count > 0:
            parts.append(
                f"Across {approved_count} approved charts, the story points to a small set of linked themes: one or two numeric drivers move together, one category explains variation in behavior, and another signal appears weak or secondary."
            )
        else:
            parts.append(
                "No charts were approved, so the analysis could not establish a reliable story from the visuals."
            )

        if skipped_count > 0:
            parts.append(
                f"Some chart candidates were skipped after retries, which suggests the system avoided weak or misleading visuals instead of forcing them into the report."
            )

        return " ".join(parts)

    def _build_data_insights(self, state: AnalysisState) -> List[str]:
        insights: List[str] = []
        numeric_summary = state.get("numeric_summary", {})
        categorical_summary = state.get("categorical_summary", {})
        cleaning_log = state.get("cleaning_log", [])

        if numeric_summary:
            top_metric = max(numeric_summary.items(), key=lambda kv: kv[1].get("mean", 0), default=None)
            if top_metric:
                name, values = top_metric
                insights.append(
                    f"{name} is the largest numeric field on average, with a mean of {values.get('mean', 0)} and a range from {values.get('min', 0)} to {values.get('max', 0)}."
                )

        if categorical_summary:
            top_category = max(
                categorical_summary.items(),
                key=lambda kv: sum(item.get("count", 0) for item in kv[1]),
                default=None,
            )
            if top_category:
                name, values = top_category
                total_points = sum(item.get("count", 0) for item in values)
                insights.append(
                    f"{name} is the most populated categorical field with {total_points} observations across its leading values."
                )

        if cleaning_log:
            insights.append("Data quality notes: " + "; ".join(cleaning_log[:3]))

        if not insights:
            insights.append("The dataset appears structurally usable and ready for interpretation.")

        return insights[:5]

    def _build_chart_narrative(self, findings: List[Dict[str, Any]]) -> List[str]:
        narrative = []
        for idx, item in enumerate(findings, start=1):
            chart_family = item.get("chart_family", "chart")
            question = item.get("business_question") or "What does this chart reveal?"
            takeaway = item.get("takeaway") or "This chart surfaces a meaningful pattern."
            columns = item.get("columns", [])
            cols_text = ", ".join(columns) if columns else "the selected fields"

            narrative.append(f"### Chart {idx}: {chart_family.replace('_', ' ').title()}")
            narrative.append(f"**Business question:** {question}")
            narrative.append(f"**What the chart shows:** {takeaway}")
            narrative.append(
                f"**Why it matters:** This pattern comes from {cols_text}, so the decision implication is tied directly to how those variables behave together."
            )
            narrative.append("")

        if not narrative:
            narrative.append("No approved charts were generated for this run.")

        return narrative

    def _build_recommendation(self, state: AnalysisState) -> str:
        findings = state.get("report_findings", [])
        if not findings:
            return (
                "Recommendation: rerun the analysis with a different chart plan or cleaner input data, "
                "because the current run did not produce enough approved visuals to support a confident business decision."
            )

        chart_families = [item.get("chart_family", "") for item in findings]
        if any(cf == "scatter_trend" for cf in chart_families) and any(cf in {"grouped_bar", "stacked_bar", "correlation_heatmap"} for cf in chart_families):
            return (
                "Recommendation: use the strongest numeric drivers and the most informative category splits as the core decision signals, "
                "then monitor the weaker secondary signals only as supporting context."
            )

        return (
            "Recommendation: focus on the strongest approved drivers and refine any skipped angles only after tightening the business question or chart logic."
        )

    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        print("📝 [Report Writer]: Writing story-driven executive summary...")

        findings = state.get("report_findings", [])
        failure_log = state.get("chart_failure_log", [])
        glossary = state.get("retrieved_business_definitions", [])
        prior_runs = state.get("prior_run_summaries", [])
        cleaning_log = state.get("cleaning_log", [])

        overall_story = self._build_overall_story(state)
        data_insights = self._build_data_insights(state)
        chart_narrative = self._build_chart_narrative(findings)
        recommendation = self._build_recommendation(state)

        lines: List[str] = []
        lines.extend([
            "# Executive Brief",
            "",
            f"Dataset: {state.get('dataset_name', 'unknown_dataset')}",
            f"Prior runs recalled: {len(prior_runs)}",
            f"Charts approved: {len(findings)} | Charts skipped after max retries: {len(failure_log)}",
            "",
            "## Executive story",
            overall_story,
            "",
            "## 1) Data insights",
        ])
        lines.extend([f"- {item}" for item in data_insights])

        lines.extend(["", "## 2) Chart narrative"])
        lines.extend(chart_narrative)

        if failure_log:
            lines.extend(["", "## 3) Skipped angles"])
            for item in failure_log:
                chart_family = item.get("chart_family", "unknown")
                question = item.get("business_question", "")
                reason = item.get("reason", "Unknown failure.")
                lines.append(f"- {chart_family}: {question} — skipped because {reason}")

        if cleaning_log:
            lines.extend(["", "## 4) Data quality notes"])
            lines.extend([f"- {item}" for item in cleaning_log[:5]])

        if glossary:
            lines.extend(["", "## 5) Business context"])
            for item in glossary[:5]:
                lines.append(f"- {item.get('key')}: {item.get('definition')}")

        lines.extend(["", "## Final recommendation", recommendation])

        final_report_markdown = "\n".join(lines)

        return {
            "final_report_markdown": final_report_markdown,
            "final_ui_blocks": [{
                "id": "block-final-report",
                "type": "MarkdownBlock",
                "title": "Executive Report",
                "content": final_report_markdown,
            }],
        }