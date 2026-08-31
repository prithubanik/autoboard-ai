import time
from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from state import AnalysisState
from agents.memory_router import MemoryRouterNode
from agents.memory.memory_recall import RecallNode
from agents.data_cleaner import SeniorDataCleanerNode
from agents.insight_planner import InsightPlannerNode
from agents.chart_validator import ChartValidatorNode
from agents.chart_architect import ChartArchitectNode
from agents.sandbox_executor import SandboxExecutorNode
from agents.chart_editor import ChartEditorNode
from agents.chart_progress import ChartProgressNode
from agents.chart_skip import ChartSkipNode
from agents.report_writer import ReportWriterNode
from agents.memory.memory_retain import RetainNode
from agents.reflection_node import ReflectionNode
from agents.visual_critic import VisualCriticNode


class TimedMemorySaver(MemorySaver):
    """Drop-in MemorySaver that logs slow checkpoint writes."""

    def put(self, config, checkpoint, metadata, new_versions):
        start = time.time()
        result = super().put(config, checkpoint, metadata, new_versions)
        elapsed = time.time() - start
        if elapsed > 1:
            print(f"⚠️ [Checkpointer]: put() took {elapsed:.1f}s — state likely bloated.", flush=True)
        return result


memory_router_node = MemoryRouterNode()
recall_node = RecallNode(db_path="database/agent_memory.sqlite")
data_cleaner_node = SeniorDataCleanerNode()
insight_planner_node = InsightPlannerNode()
chart_validator_node = ChartValidatorNode()
chart_architect_node = ChartArchitectNode()
sandbox_executor_node = SandboxExecutorNode()
chart_editor_node = ChartEditorNode()
chart_progress_node = ChartProgressNode()
chart_skip_node = ChartSkipNode()
report_writer_node = ReportWriterNode()
retain_node = RetainNode(db_path="database/agent_memory.sqlite")
reflection_node = ReflectionNode()
visual_critic_node = VisualCriticNode()


def route_after_validator(state: AnalysisState) -> Literal["chart_builder", "report_writer"]:
    current = state.get("current_chart_index", 0)
    plan = state.get("chart_plan", [])
    if current >= len(plan):
        return "report_writer"
    return "chart_builder"


def route_after_execution(state: AnalysisState) -> Literal["chart_builder", "visual_critic", "chart_skip"]:
    if state.get("execution_error"):
        if state.get("retry_count", 0) >= 3:
            return "chart_skip"
        return "chart_builder"
    return "visual_critic"


def route_after_critic(state: AnalysisState) -> Literal["chart_builder", "chart_progress", "chart_skip"]:
    critique = state.get("visual_critique", "") or ""
    is_genuinely_wrong = critique.startswith("REJECTED") or critique.startswith("MISMATCHED")
    if is_genuinely_wrong:
        if state.get("retry_count", 0) >= 3:
            return "chart_skip"
        return "chart_builder"
    return "chart_progress"


def route_after_progress(state: AnalysisState) -> Literal["chart_validator", "report_writer"]:
    current = state.get("current_chart_index", 0)
    plan = state.get("chart_plan", [])
    if current >= len(plan):
        return "report_writer"
    return "chart_validator"


def build_analyst_graph():
    workflow = StateGraph(AnalysisState)

    workflow.add_node("memory_router", memory_router_node.execute)
    workflow.add_node("recall", recall_node.execute)
    workflow.add_node("data_cleaner", data_cleaner_node.execute)
    workflow.add_node("insight_planner", insight_planner_node.execute)
    workflow.add_node("chart_validator", chart_validator_node.execute)
    workflow.add_node("chart_builder", chart_architect_node.execute)
    workflow.add_node("chart_editor", chart_editor_node.execute)
    workflow.add_node("sandbox_executor", sandbox_executor_node.execute)
    workflow.add_node("visual_critic", visual_critic_node.execute)
    workflow.add_node("chart_progress", chart_progress_node.execute)
    workflow.add_node("chart_skip", chart_skip_node.execute)
    workflow.add_node("report_writer", report_writer_node.execute)
    workflow.add_node("memory_retain", retain_node.execute)
    workflow.add_node("reflection_node", reflection_node.execute)

    workflow.set_entry_point("memory_router")

    workflow.add_edge("memory_router", "recall")
    workflow.add_edge("recall", "data_cleaner")
    workflow.add_edge("data_cleaner", "insight_planner")
    workflow.add_edge("insight_planner", "chart_validator")

    workflow.add_conditional_edges("chart_validator", route_after_validator)
    workflow.add_edge("chart_builder", "sandbox_executor")
    workflow.add_edge("chart_editor", "sandbox_executor")

    workflow.add_conditional_edges("sandbox_executor", route_after_execution)
    workflow.add_conditional_edges("visual_critic", route_after_critic)
    workflow.add_conditional_edges("chart_progress", route_after_progress)
    workflow.add_conditional_edges("chart_skip", route_after_progress)

    workflow.add_edge("report_writer", "memory_retain")
    workflow.add_edge("memory_retain", "reflection_node")
    workflow.add_edge("reflection_node", END)

    checkpointer = TimedMemorySaver()
    return workflow.compile(checkpointer=checkpointer)


executor_node = sandbox_executor_node