import re
import textwrap
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from state import AnalysisState


class ChartArchitectNode:
    def __init__(
        self,
        model_name: str = "gemma4:31b-cloud",
        base_url: str = "http://localhost:11434",
    ):
        self.llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            client_kwargs={"timeout": 60.0},
        )

        self.base_system_prompt = textwrap.dedent(
            """
            You are a Lead Data Visualization Architect and Senior Financial Analyst.

            Generate ONE clean Python script using Plotly Express (px) or Plotly Graph Objects (go)
            to visualize a specific analytical angle from a DuckDB database.

            DUCKDB ENVIRONMENT (VERY IMPORTANT):
            - DuckDB file path: data/analytics_engine.duckdb
            - The cleaned analysis table is called cleaned_analytics_base.
            - Do NOT invent other table names.

            SCRIPT STRUCTURE (STRICT):
            - Write a single flat script.
            - DO NOT define functions like generate_chart() or main().
            - DO NOT wrap the chart creation inside any function.
            - Define a single Plotly figure at top-level named `fig`.

            MANDATORY RULES:
            1. NEVER use pd.read_csv(). Always load from DuckDB.
            2. ALWAYS create a top-level `fig`.
            3. DO NOT manually save files.
            4. Return ONLY executable Python code inside ```python ... ``` fences.
            """
        )

    def _clean_llm_code_output(self, raw_output: str) -> str:
        pattern = r"```python\s*(.*?)```"
        match = re.search(pattern, raw_output, re.DOTALL | re.IGNORECASE)

        if match:
            clean_code = match.group(1).strip()
        else:
            clean_code = raw_output.replace("```python", "").replace("```", "").strip()

        for bad in [
            "showscale=True",
            "showscale = True",
            "showscale=True,",
            "showscale = True,",
        ]:
            clean_code = clean_code.replace(bad, "")

        bad_patterns = [
            "fig.write_image(",
            "fig.write_json(",
            "fig.write_html(",
            "json.dumps(fig.to_dict()",
            "json.dump(fig.to_dict()",
            "def generate_chart(",
            "def main(",
            "if __name__ == '__main__':",
            "if __name__ == \"__main__\":",
        ]
        for bad in bad_patterns:
            clean_code = re.sub(rf".*{re.escape(bad)}.*\n?", "", clean_code)

        enforced_save_logic = textwrap.dedent(
            """
            import os
            import sys

            os.makedirs("artifacts/scratchpad", exist_ok=True)

            _target_fig = None
            if 'fig' in locals():
                _target_fig = fig
            else:
                for _val in list(locals().values()):
                    if hasattr(_val, 'write_image') and hasattr(_val, 'write_json'):
                        _target_fig = _val
                        break

            if _target_fig is not None:
                try:
                    _target_fig.write_image("artifacts/scratchpad/latest_render.png")
                    _target_fig.write_json("artifacts/scratchpad/latest_render.json")
                except Exception as e:
                    print(f"Failed to save image. Ensure kaleido is installed. Error: {e}", file=sys.stderr)
                    sys.exit(1)
            else:
                print("Error: No Plotly figure object found. You must instantiate a chart.", file=sys.stderr)
                sys.exit(1)
            """
        )

        return clean_code + "\n" + enforced_save_logic

    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        current_count = state.get("plots_generated_count", 0)
        print(f"🎨 [Chart Architect]: Designing Chart #{current_count + 1}...")

        profile = state.get("data_profile_summary", "No summary provided.")
        table_name = state.get("cleaned_table_name", "cleaned_analytics_base")

        spec = state.get("current_chart_spec") or state.get("current_spec")
        if spec is None:
            chart_family = "generic_story_chart"
            business_question = "Tell a high-level story about the dataset."
            columns = []
        else:
            chart_family = spec.get("chart_family", "generic_story_chart")
            business_question = spec.get("business_question", "Tell a high-level story about the dataset.")
            columns = spec.get("columns", [])

        error_feedback = state.get("execution_error", None)
        critique_feedback = state.get("visual_critique", None)

        chart_directives = [
            "Chart #1: Use the chart_family and columns to show the core business relationship.",
            "Chart #2: Build an aggregated bar/line view that highlights top categories or trends.",
            "Chart #3: Focus on outliers or spread using boxplots, distributions, or bubble charts.",
        ]
        current_directive = chart_directives[min(current_count, len(chart_directives) - 1)]

        columns_str = ", ".join(map(str, columns)) if columns else "N/A"

        prompt_content = f"""
        DATASET PROFILE (JSON or text):
        {profile}

        DUCKDB CONNECTION SPEC:
        - File path: data/analytics_engine.duckdb
        - Cleaned table name: {table_name}
        - You MUST query this table.

        CURRENT CHART SPEC:
        - chart_family: {chart_family}
        - business_question: {business_question}
        - columns to use: {columns_str}

        TARGET VISUALIZATION DIRECTIVE:
        {current_directive}

        IMPLEMENTATION HINTS:
        - Connect with: import duckdb; con = duckdb.connect("data/analytics_engine.duckdb")
        - Load data with: df = con.execute(f"SELECT * FROM {table_name}").df()
        - Define `fig = ...` at top level.
        """

        if error_feedback:
            prompt_content += f"\n\n[PREVIOUS EXECUTION FAILED]: Fix this Python Error:\n{error_feedback}"

        if critique_feedback:
            prompt_content += f"\n\n[VISION CRITIC REJECTION]: Fix these visual issues:\n{critique_feedback}"

        messages = [
            SystemMessage(content=self.base_system_prompt),
            HumanMessage(content=prompt_content),
        ]

        raw_llm_response = self.llm.invoke(messages)
        raw_content = (
            raw_llm_response.content
            if hasattr(raw_llm_response, "content")
            else str(raw_llm_response)
        )

        executable_code = self._clean_llm_code_output(raw_content)

        return {
            "current_code": executable_code,
            "code_history": [executable_code],
            "execution_error": None,
        }