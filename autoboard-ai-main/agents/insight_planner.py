import json
import re
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from state import AnalysisState


class InsightPlannerNode:
    def __init__(self, model_name: str = "gemma4:31b-cloud", base_url: str = "http://localhost:11434"):
        self.llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            format="json",
            client_kwargs={"timeout": 60.0}
        )

        self.system_prompt = """
        You are a Lead Data Storyteller and Executive Analyst.
        Your job is to inspect the dataset profile and design a strategic plan of 3 to 5 charts that tell a clear, generic business story.

        IMPORTANT:
        - Keep the language domain-agnostic. Do NOT assume the dataset is about finance, credit cards, retail, healthcare, or any other specific industry.
        - Use field names from the dataset, but describe them in broad business terms like customer segment, outcome driver, behavior signal, capacity signal, usage pattern, or performance metric.
        - Build a story that works for any tabular dataset.

        Available Chart Families:
        - time_series_line (Needs a date/time column + numeric metric)
        - grouped_bar (Needs a category + numeric metric)
        - stacked_bar (Needs 2 categories + numeric metric)
        - scatter_trend (Needs 2 numeric metrics to show relationship)
        - correlation_heatmap (Needs 4 to 8 maximum numeric columns)
        - box_outliers (Needs a category + numeric metric to show spread)
        - donut_share (Needs a category + numeric metric for percentage share)

        STRICT RULES FOR YOUR STORY:
        1. VARY THE CHARTS: Never use the same chart_family more than once.
        2. DATA-DRIVEN SCATTERS: For scatter_trend, use a pair from the strongest correlation list.
        3. BE LOGICAL: Never plot ID columns, primary keys, names, or row numbers.
        4. Return ONLY valid JSON matching this schema:
        {
          "chart_plan": [
            {
              "angle_id": 1,
              "chart_family": "scatter_trend",
              "business_question": "What is the relationship between two important numeric signals?",
              "columns": ["ColumnA", "ColumnB"]
            }
          ]
        }
        """

    def _parse_llm_json(self, response_content: str) -> Dict[str, Any]:
        try:
            return json.loads(response_content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", response_content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return {"chart_plan": []}

    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        print("🧠 [Insight Planner]: Designing a generic storytelling chart plan...", flush=True)

        schema = state.get("schema_info", [])
        numeric_summary = state.get("numeric_summary", {})
        correlations = state.get("correlation_findings", [])

        schema_text_lines = []
        valid_charting_cols = []

        for col in schema:
            if isinstance(col, dict):
                name = col.get("name") or col.get("column_name") or col.get("column") or "Unknown_Column"
                ctype = col.get("type") or col.get("dtype") or "Unknown_Type"
            else:
                name = str(col)
                ctype = "Unknown"

            name_lower = name.lower()
            if name_lower.endswith("id") or name_lower == "id" or "index" in name_lower or name_lower.endswith("_key"):
                continue

            schema_text_lines.append(f"- {name} (Type: {ctype})")
            valid_charting_cols.append(name)

        schema_text = "\n".join(schema_text_lines)

        corr_text_lines = ["Strongest Correlations (Use these for scatter_trend):"]
        if correlations:
            for c in correlations[:5]:
                corr_text_lines.append(
                    f"- {c.get('feature_x', 'Unknown')} & {c.get('feature_y', 'Unknown')} (Score: {c.get('correlation', 0)})"
                )
        else:
            corr_text_lines.append("- No strong numeric correlations found in this dataset.")
        corr_text = "\n".join(corr_text_lines)

        safe_kpis = [c for c in list(numeric_summary.keys()) if c in valid_charting_cols][:10]
        numeric_text = f"Key numeric signals available: {safe_kpis}"

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=f"Here is the dataset profile. Design the storytelling chart plan.\n\nSCHEMA:\n{schema_text}\n\n{corr_text}\n\nNUMERIC SUMMARY:\n{numeric_text}"
            ),
        ]

        try:
            raw_response = self.llm.invoke(messages)
            content = raw_response.content if hasattr(raw_response, "content") else str(raw_response)
            parsed_plan = self._parse_llm_json(content)
            chart_plan = parsed_plan.get("chart_plan", [])
        except Exception as e:
            print(f"⚠️ [Insight Planner]: LLM failed, falling back to empty plan -> {e}")
            chart_plan = []

        if not chart_plan:
            print("⚠️ [Insight Planner]: Generating fallback plan...")
            fallback_cols = valid_charting_cols[:2] if len(valid_charting_cols) >= 2 else ["Unknown1", "Unknown2"]
            chart_plan = [
                {
                    "angle_id": 1,
                    "chart_family": "grouped_bar",
                    "business_question": "What is the baseline distribution across the most important category?",
                    "columns": fallback_cols
                }
            ]

        print(f"✅ [Insight Planner]: Master plan created with {len(chart_plan)} unique storytelling angles!", flush=True)

        return {
            "chart_plan": chart_plan,
            "insight_candidates": chart_plan,
            "current_chart_index": 0,
            "plots_generated_count": 0,
        }