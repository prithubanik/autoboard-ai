import base64
import json
import os
import re
import uuid
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from state import AnalysisState


class VisualCriticNode:
    """Vision QA gate for generic datasets.

    The model should decide:
    - status: is the chart visually valid?
    - question_satisfied: does it answer the assigned business question?

    If the vision endpoint fails, do NOT discard the chart automatically.
    Return a fallback response so the graph can continue using the chart
    code / chart takeaway instead of hard-failing the whole angle.
    """

    def __init__(
        self,
        model_name: str = "gemma4:31b-cloud",
        base_url: str = "http://localhost:11434",
    ):
        self.llm = ChatOllama(model=model_name, base_url=base_url, format="json")

        self.system_prompt = """
        You are a Senior Lead Data Scientist and Visual Critic.
        Inspect the rendered chart and return valid JSON only.

        Return this schema:
        {
          "status": "APPROVED" | "REJECTED",
          "question_satisfied": true | false,
          "primary_takeaway": "string",
          "anomaly_detected": "string or null",
          "rejection_reason": "string or null",
          "target_retry_node": "chart_architect" | "data_cleaner" | null
        }

        Rules:
        - Be forgiving on minor aesthetics.
        - status = REJECTED only if the chart is empty, unreadable, or broken.
        - question_satisfied = false if the chart does not answer the business_question.
        - Keep the critique generic and dataset-agnostic.
        - Never return markdown.
        - Never return explanations outside JSON.
        """

    def _build_rejection(self, reason: str, target_retry_node: str = "chart_architect") -> Dict[str, Any]:
        return {
            "status": "REJECTED",
            "question_satisfied": False,
            "primary_takeaway": "",
            "anomaly_detected": None,
            "rejection_reason": reason,
            "target_retry_node": target_retry_node,
        }

    def _parse_llm_json(self, response_content: str) -> Dict[str, Any]:
        try:
            parsed = json.loads(response_content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", response_content, re.DOTALL)
            if not match:
                return self._build_rejection("Vision critic returned non-JSON output.")
            try:
                parsed = json.loads(match.group(0))
            except json.JSONDecodeError:
                return self._build_rejection("Vision critic returned invalid JSON.")

        if not isinstance(parsed, dict):
            return self._build_rejection("Vision critic returned malformed response.")

        status = parsed.get("status")
        if status not in {"APPROVED", "REJECTED"}:
            return self._build_rejection("Vision critic returned invalid status.")

        parsed.setdefault("question_satisfied", status == "APPROVED")
        parsed.setdefault("primary_takeaway", "")
        parsed.setdefault("anomaly_detected", None)
        parsed.setdefault("rejection_reason", None)
        parsed.setdefault("target_retry_node", None)
        return parsed

    def _verdict_label(self, critique: Dict[str, Any]) -> str:
        if critique.get("status") == "REJECTED":
            return "REJECTED"
        if not critique.get("question_satisfied", True):
            return "MISMATCHED"
        return "APPROVED"

    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        print("👁️ [Visual Critic]: Reviewing rendered chart against business question...")

        image_path = state.get("rendered_image_path")
        json_path = state.get("rendered_json_path")
        approved_count = state.get("plots_generated_count", 0)
        chart_spec = state.get("current_chart_spec", {}) or {}

        if not image_path or not os.path.exists(image_path):
            return {
                "visual_critique": "REJECTED: No PNG chart image available for visual review.",
                "retry_count": state.get("retry_count", 0) + 1,
            }

        try:
            with open(image_path, "rb") as f:
                image_base64 = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            return {
                "visual_critique": f"REJECTED: Failed to read image -> {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1,
            }

        plotly_json = None
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    plotly_json = f.read()
            except Exception:
                pass

        business_question = chart_spec.get("business_question", "Analyze the data")
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": (
                            "Evaluate this chart against the business question and chart specification.\n"
                            f"BUSINESS QUESTION: {business_question}\n"
                            f"CHART SPEC: {chart_spec}"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    },
                ]
            ),
        ]

        try:
            raw_response = self.llm.invoke(messages)
            raw_content = raw_response.content if hasattr(raw_response, "content") else str(raw_response)
            critique = self._parse_llm_json(raw_content)
        except Exception as e:
            # Fallback: do not hard-fail the entire chart if the vision server is down.
            return {
                "visual_critique": f"MISMATCHED: Vision call failed -> {str(e)}",
                "retry_count": state.get("retry_count", 0) + 1,
            }

        verdict = self._verdict_label(critique)

        if verdict in ("REJECTED", "MISMATCHED"):
            reason = critique.get("rejection_reason") or "Chart did not satisfy the evaluation criteria."
            target = critique.get("target_retry_node", "chart_architect")
            return {
                "visual_critique": f"{verdict}: {reason} (Route to {target})",
                "retry_count": state.get("retry_count", 0) + 1,
            }

        session_id = state.get("session_id", "session")
        unique_suffix = uuid.uuid4().hex[:8]
        takeaway = critique.get("primary_takeaway", "")

        new_blocks: List[Dict[str, Any]] = [
            {
                "id": f"{session_id}-block-viz-{approved_count}",
                "render_key": f"{session_id}-plotly-{approved_count}-{unique_suffix}",
                "type": "VisualizationBlock",
                "title": f"Analysis Angle #{approved_count + 1}",
                "image_path": image_path,
                "plotly_json": plotly_json,
                "takeaway": takeaway,
                "business_question": business_question,
            }
        ]

        if critique.get("anomaly_detected"):
            new_blocks.append(
                {
                    "id": f"{session_id}-block-anomaly-{approved_count}",
                    "render_key": f"{session_id}-anomaly-{approved_count}-{unique_suffix}",
                    "type": "AnomalyCalloutBlock",
                    "severity": "high",
                    "title": "Outlier / Anomaly Signal",
                    "content": critique["anomaly_detected"],
                }
            )

        new_finding: Dict[str, Any] = {
            "angle_id": chart_spec.get("angle_id", approved_count + 1),
            "chart_family": chart_spec.get("chart_family", "unknown"),
            "columns": chart_spec.get("columns", []),
            "business_question": business_question,
            "takeaway": takeaway,
            "question_satisfied": True,
            "anomaly_detected": critique.get("anomaly_detected"),
            "image_path": image_path,
        }

        return {
            "final_ui_blocks": new_blocks,
            "report_findings": [new_finding],
            "prior_chart_summaries": [takeaway],
            "visual_critique": None,
            "execution_error": None,
            "retry_count": 0,
        }