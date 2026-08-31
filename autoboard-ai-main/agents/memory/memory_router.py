from typing import Any, Dict

from state import AnalysisState


class MemoryRouterNode:
    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        print("🧭 [Memory Router]: Entry router active. Delegating to recall path.")
        return {"cache_hit": False}