import hashlib
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List


class MemoryStore:
    def __init__(self, db_path: str = "database/agent_memory.sqlite"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS datasets (
                    dataset_fingerprint TEXT PRIMARY KEY,
                    dataset_name TEXT,
                    first_seen_at TEXT,
                    last_seen_at TEXT,
                    schema_json TEXT,
                    feature_registry_json TEXT,
                    profile_summary_json TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_runs (
                    run_id TEXT PRIMARY KEY,
                    dataset_fingerprint TEXT,
                    created_at TEXT,
                    question TEXT,
                    report_markdown TEXT,
                    reflection_summary TEXT,
                    findings_json TEXT,
                    chart_plan_json TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chart_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT,
                    dataset_fingerprint TEXT,
                    chart_family TEXT,
                    columns_json TEXT,
                    business_question TEXT,
                    approved INTEGER,
                    notes TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS business_glossary (
                    key TEXT PRIMARY KEY,
                    definition TEXT,
                    metadata_json TEXT
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS failure_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_fingerprint TEXT,
                    chart_family TEXT,
                    error_text TEXT,
                    created_at TEXT
                )
                """
            )
            conn.commit()

    def fingerprint_file(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def upsert_dataset(
        self,
        dataset_fingerprint: str,
        dataset_name: str,
        schema: List[Dict[str, Any]],
        feature_registry: Dict[str, Any],
        profile_summary: str,
    ):
        now = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO datasets (
                    dataset_fingerprint, dataset_name, first_seen_at, last_seen_at,
                    schema_json, feature_registry_json, profile_summary_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(dataset_fingerprint) DO UPDATE SET
                    last_seen_at=excluded.last_seen_at,
                    dataset_name=excluded.dataset_name,
                    schema_json=excluded.schema_json,
                    feature_registry_json=excluded.feature_registry_json,
                    profile_summary_json=excluded.profile_summary_json
                """,
                (
                    dataset_fingerprint,
                    dataset_name,
                    now,
                    now,
                    json.dumps(schema),
                    json.dumps(feature_registry),
                    profile_summary,
                ),
            )
            conn.commit()

    def insert_run(
        self,
        run_id: str,
        dataset_fingerprint: str,
        question: str,
        report_markdown: str,
        reflection_summary: str,
        findings: List[Dict[str, Any]],
        chart_plan: List[Dict[str, Any]],
    ):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO analysis_runs (
                    run_id, dataset_fingerprint, created_at, question,
                    report_markdown, reflection_summary, findings_json, chart_plan_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    dataset_fingerprint,
                    datetime.utcnow().isoformat(),
                    question,
                    report_markdown,
                    reflection_summary,
                    json.dumps(findings),
                    json.dumps(chart_plan),
                ),
            )
            conn.commit()

    def insert_chart_outcomes(
        self,
        run_id: str,
        dataset_fingerprint: str,
        items: List[Dict[str, Any]],
    ):
        with self._connect() as conn:
            for item in items:
                conn.execute(
                    """
                    INSERT INTO chart_outcomes (
                        run_id, dataset_fingerprint, chart_family, columns_json,
                        business_question, approved, notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        dataset_fingerprint,
                        item.get("chart_family"),
                        json.dumps(item.get("columns", [])),
                        item.get("business_question"),
                        int(bool(item.get("approved", True))),
                        item.get("notes", ""),
                    ),
                )
            conn.commit()

    def insert_failure_pattern(
        self,
        dataset_fingerprint: str,
        chart_family: str,
        error_text: str,
    ):
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO failure_patterns (
                    dataset_fingerprint, chart_family, error_text, created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    dataset_fingerprint,
                    chart_family,
                    error_text,
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()

    def get_dataset_context(self, dataset_fingerprint: str) -> Dict[str, Any]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT dataset_name, schema_json, feature_registry_json, profile_summary_json
                FROM datasets
                WHERE dataset_fingerprint = ?
                """,
                (dataset_fingerprint,),
            )
            row = cur.fetchone()
            if not row:
                return {}
            return {
                "dataset_name": row[0],
                "schema_info": json.loads(row[1]) if row[1] else [],
                "feature_registry": json.loads(row[2]) if row[2] else {},
                "profile_summary": row[3],
            }

    def get_recent_runs(
        self,
        dataset_fingerprint: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT run_id, created_at, question, reflection_summary, findings_json, chart_plan_json
                FROM analysis_runs
                WHERE dataset_fingerprint = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (dataset_fingerprint, limit),
            )
            rows = cur.fetchall()
            return [
                {
                    "run_id": r[0],
                    "created_at": r[1],
                    "question": r[2],
                    "reflection_summary": r[3],
                    "findings": json.loads(r[4]) if r[4] else [],
                    "chart_plan": json.loads(r[5]) if r[5] else [],
                }
                for r in rows
            ]

    def get_chart_patterns(
        self,
        dataset_fingerprint: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT chart_family, columns_json, business_question, approved, notes
                FROM chart_outcomes
                WHERE dataset_fingerprint = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (dataset_fingerprint, limit),
            )
            rows = cur.fetchall()
            return [
                {
                    "chart_family": r[0],
                    "columns": json.loads(r[1]) if r[1] else [],
                    "business_question": r[2],
                    "approved": bool(r[3]),
                    "notes": r[4],
                }
                for r in rows
            ]

    def get_glossary(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT key, definition, metadata_json FROM business_glossary ORDER BY key LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
            return [
                {
                    "key": r[0],
                    "definition": r[1],
                    "metadata": json.loads(r[2]) if r[2] else {},
                }
                for r in rows
            ]