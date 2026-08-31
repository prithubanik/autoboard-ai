import os
import uuid
from typing import Any, Dict

from .memory_store import MemoryStore
from state import AnalysisState


class RecallNode:
    def __init__(self, db_path: str = "database/agent_memory.sqlite"):
        self.store = MemoryStore(db_path=db_path)

    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        print("🧠 [Recall Node]: Retrieving prior dataset and analysis memory...")
        raw_path = state.get("raw_data_path", "")
        dataset_name = os.path.basename(raw_path) if raw_path else "unknown_dataset"
        dataset_fingerprint = (
            self.store.fingerprint_file(raw_path)
            if raw_path and os.path.exists(raw_path)
            else ""
        )
        run_id = state.get("run_id") or str(uuid.uuid4())

        persistent_mode = bool(state.get("use_persistent_memory", False))
        dataset_context = {}
        prior_runs = []
        chart_patterns = []
        glossary = []

        if persistent_mode and dataset_fingerprint:
            dataset_context = self.store.get_dataset_context(dataset_fingerprint) or {}
            prior_runs = self.store.get_recent_runs(dataset_fingerprint, limit=5) or []
            chart_patterns = self.store.get_chart_patterns(dataset_fingerprint, limit=10) or []
            glossary = self.store.get_glossary(limit=20) or []
        elif persistent_mode:
            glossary = self.store.get_glossary(limit=20) or []

        return {
            "dataset_name": dataset_name,
            "dataset_fingerprint": dataset_fingerprint,
            "run_id": run_id,
            "memory_context": {
                "dataset_context": dataset_context,
                "prior_runs": prior_runs,
                "chart_patterns": chart_patterns,
                "glossary": glossary,
            },
            "retrieved_memories": prior_runs,
            "retrieved_chart_patterns": chart_patterns,
            "retrieved_business_definitions": glossary,
            "prior_run_summaries": [
                {
                    "run_id": item.get("run_id"),
                    "question": item.get("question"),
                    "reflection_summary": item.get("reflection_summary"),
                }
                for item in prior_runs
            ],
            "analysis_memory_hits": prior_runs,
            "cache_hit": bool(dataset_context or prior_runs or chart_patterns or glossary) and persistent_mode,
        }