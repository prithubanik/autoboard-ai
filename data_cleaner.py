import os
import json
import duckdb
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, List
from state import AnalysisState


class SeniorDataCleanerNode:
    def __init__(self, duckdb_path: str = "data/analytics_engine.duckdb"):
        self.db_path = duckdb_path
        os.makedirs("data", exist_ok=True)

    def _load_file(self, raw_path: str) -> pd.DataFrame:
        ext = os.path.splitext(raw_path)[1].lower()
        if ext in [".xlsx", ".xls"]:
            return pd.read_excel(raw_path)
        return pd.read_csv(raw_path)

    def _safe_impute_and_transform(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        df = df.copy()
        metadata = {
            "transformations": [],
            "skewed_features": [],
            "outlier_flags": []
        }

        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        for col in num_cols:
            null_count = int(df[col].isnull().sum())
            if null_count > 0:
                median_val = df[col].median()
                df[f"{col}_clean"] = df[col].fillna(median_val)
                df[f"{col}_was_null"] = df[col].isnull().astype(int)
                metadata["transformations"].append(
                    f"Imputed {null_count} nulls in '{col}' with median {round(float(median_val), 2)} into '{col}_clean'."
                )
            else:
                df[f"{col}_clean"] = df[col]

        for col in num_cols:
            series = df[col].dropna()
            if len(series) < 5:
                continue
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            if iqr == 0:
                continue
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            outliers = int(((df[col] < lower) | (df[col] > upper)).sum())
            if outliers > 0:
                df[f"{col}_is_outlier"] = ((df[col] < lower) | (df[col] > upper)).astype(int)
                metadata["outlier_flags"].append(f"Flagged {outliers} IQR outliers in '{col}'.")

        object_cols = df.select_dtypes(include=["object"]).columns.tolist()
        candidate_name_tokens = ("date", "time", "month", "day", "year", "timestamp")

        for col in object_cols:
            name_lc = col.lower()
            sample = df[col].dropna().astype(str).head(25)

            looks_like_date_name = any(token in name_lc for token in candidate_name_tokens)
            looks_like_date_value = (
                sample.str.contains(
                    r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$|^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$",
                    regex=True
                ).mean() >= 0.5
                if len(sample) else False
            )

            if not (looks_like_date_name or looks_like_date_value):
                continue

            try:
                parsed = pd.to_datetime(df[col], errors="coerce")
                if parsed.notna().sum() > max(10, int(0.4 * len(df))):
                    df[col] = parsed
                    df[f"{col}_month"] = df[col].dt.to_period("M").astype(str)
                    metadata["transformations"].append(
                        f"Parsed '{col}' as datetime and generated '{col}_month'."
                    )
            except Exception:
                pass

        return df, metadata

    def _build_feature_registry(self, df: pd.DataFrame) -> Dict[str, Any]:
        helper_suffixes = ("_clean", "_was_null", "_is_outlier", "_month", "_log")
        registry: Dict[str, Any] = {}

        for col in df.columns:
            dtype = df[col].dtype
            non_null = int(df[col].notna().sum())
            null_rate = float(df[col].isna().mean()) if len(df) else 0.0
            cardinality = int(df[col].nunique(dropna=True))
            is_helper = any(col.endswith(suffix) for suffix in helper_suffixes)
            name_lc = str(col).lower()
            is_datetime_like = (
                pd.api.types.is_datetime64_any_dtype(dtype)
                or col.endswith("_month")
                or any(token in name_lc for token in ("date", "time", "month", "day", "year", "timestamp"))
            )

            if is_helper:
                role = "helper"
                safe_for_charting = False
                banned = True
            elif is_datetime_like:
                role = "datetime"
                safe_for_charting = True
                banned = False
            elif pd.api.types.is_numeric_dtype(dtype):
                is_identifier_like = any(token in str(col).lower() for token in ("id", "code", "zip", "rank", "flag", "index"))
                role = "category" if is_identifier_like and cardinality <= 12 else "metric"
                safe_for_charting = True
                banned = False
            else:
                role = "category"
                safe_for_charting = cardinality <= 25
                banned = False

            registry[col] = {
                "role": role,
                "safe_for_charting": safe_for_charting,
                "banned": banned,
                "dtype": str(dtype),
                "null_rate": round(null_rate, 4),
                "cardinality": cardinality,
                "non_null": non_null,
            }

        return registry

    def _build_schema_info(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        rows = []
        for col in df.columns:
            rows.append({
                "column": col,
                "dtype": str(df[col].dtype),
                "non_null": int(df[col].notna().sum()),
                "nulls": int(df[col].isna().sum()),
                "unique": int(df[col].nunique(dropna=True))
            })
        return rows

    def _build_numeric_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        result = {}
        excluded_suffixes = ("_clean", "_was_null", "_is_outlier", "_month", "_log")
        num_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns.tolist()
            if not any(c.endswith(suffix) for suffix in excluded_suffixes)
        ]
        for col in num_cols[:20]:
            series = df[col].dropna()
            if series.empty:
                continue
            result[col] = {
                "count": int(series.count()),
                "mean": round(float(series.mean()), 3),
                "median": round(float(series.median()), 3),
                "std": round(float(series.std()), 3) if series.count() > 1 else 0.0,
                "min": round(float(series.min()), 3),
                "max": round(float(series.max()), 3),
                "q1": round(float(series.quantile(0.25)), 3),
                "q3": round(float(series.quantile(0.75)), 3),
            }
        return result

    def _build_categorical_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        result = {}
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        for col in cat_cols[:15]:
            vc = df[col].astype(str).fillna("NA").value_counts(dropna=False).head(8)
            result[col] = [{"label": str(idx), "count": int(val)} for idx, val in vc.items()]
        return result

    def _build_correlation_findings(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        excluded_suffixes = ("_clean", "_was_null", "_is_outlier", "_month", "_log")
        num_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns.tolist()
            if not any(c.endswith(suffix) for suffix in excluded_suffixes)
        ]
        findings = []
        if len(num_cols) < 2:
            return findings

        corr = df[num_cols].corr(numeric_only=True)
        seen = set()

        for col1 in corr.columns:
            for col2 in corr.columns:
                if col1 == col2:
                    continue
                key = tuple(sorted((col1, col2)))
                if key in seen:
                    continue
                seen.add(key)
                value = corr.loc[col1, col2]
                if pd.isna(value):
                    continue
                if abs(value) >= 0.45:
                    findings.append({
                        "feature_x": col1,
                        "feature_y": col2,
                        "correlation": round(float(value), 3),
                        "direction": "positive" if value > 0 else "negative"
                    })

        findings = sorted(findings, key=lambda x: abs(x["correlation"]), reverse=True)
        return findings[:10]

    def _choose_datetime_columns(self, df: pd.DataFrame) -> List[str]:
        return [c for c in df.columns if str(df[c].dtype).startswith("datetime64") or c.endswith("_month")]

    def _build_chart_plan(self, df: pd.DataFrame, correlation_findings: List[Dict[str, Any]], target_count: int) -> List[Dict[str, Any]]:
        chart_plan = []
        excluded_suffixes = ("_clean", "_was_null", "_is_outlier", "_month", "_log")

        num_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns.tolist()
            if not any(c.endswith(suffix) for suffix in excluded_suffixes)
        ]
        cat_cols = [
            c for c in df.select_dtypes(include=["object", "category"]).columns.tolist()
            if not any(c.endswith(suffix) for suffix in excluded_suffixes)
            and df[c].nunique(dropna=True) <= 12
        ]
        dt_cols = [
            c for c in self._choose_datetime_columns(df)
            if not any(c.endswith(suffix) for suffix in excluded_suffixes)
        ]

        main_metric = num_cols[0] if num_cols else None

        if len(num_cols) >= 3:
            chart_plan.append({
                "angle_id": 1,
                "chart_family": "correlation_heatmap",
                "business_question": "Which core numeric features move together and indicate business drivers?",
                "columns": num_cols[:10]
            })

        if dt_cols and main_metric:
            chart_plan.append({
                "angle_id": 2,
                "chart_family": "time_series_line",
                "business_question": f"How does {main_metric} change over time?",
                "columns": [dt_cols[0], main_metric]
            })

        if cat_cols and main_metric:
            chart_plan.append({
                "angle_id": 3,
                "chart_family": "grouped_bar",
                "business_question": f"How does {main_metric} vary across {cat_cols[0]}?",
                "columns": [cat_cols[0], main_metric]
            })

        if cat_cols and main_metric and df[cat_cols[0]].nunique(dropna=True) <= 6:
            chart_plan.append({
                "angle_id": 4,
                "chart_family": "donut_share",
                "business_question": f"What share does each {cat_cols[0]} category contribute to {main_metric}?",
                "columns": [cat_cols[0], main_metric]
            })

        for finding in correlation_findings[:3]:
            chart_plan.append({
                "angle_id": len(chart_plan) + 1,
                "chart_family": "scatter_trend",
                "business_question": f"What relationship exists between {finding['feature_x']} and {finding['feature_y']}?",
                "columns": [finding["feature_x"], finding["feature_y"]]
            })

        if len(num_cols) >= 1:
            chart_plan.append({
                "angle_id": len(chart_plan) + 1,
                "chart_family": "box_outliers",
                "business_question": f"Where are outliers and spread concentrated in {num_cols[0]}?",
                "columns": [num_cols[0]]
            })

        if len(num_cols) >= 2 and cat_cols:
            chart_plan.append({
                "angle_id": len(chart_plan) + 1,
                "chart_family": "stacked_bar",
                "business_question": f"How do {num_cols[0]} and {num_cols[1]} compare across {cat_cols[0]}?",
                "columns": [cat_cols[0], num_cols[0], num_cols[1]]
            })

        deduped = []
        seen = set()
        for spec in chart_plan:
            key = (spec["chart_family"], tuple(spec["columns"]))
            if key not in seen:
                seen.add(key)
                deduped.append(spec)

        return deduped[:target_count]

    def _build_initial_ui_blocks(
        self,
        df: pd.DataFrame,
        schema_info: List[Dict[str, Any]],
        numeric_summary: Dict[str, Any],
        categorical_summary: Dict[str, Any],
        cleaning_log: List[str],
        correlation_findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        row_count = len(df)
        col_count = len(df.columns)
        num_count = len(df.select_dtypes(include=[np.number]).columns)
        cat_count = len(df.select_dtypes(include=["object", "category"]).columns)

        preview_rows = df.head(5).replace({np.nan: None}).to_dict(orient="records")

        top_correlations = correlation_findings[:5]
        top_corr_lines = [
            f"- {item['feature_x']} vs {item['feature_y']}: {item['correlation']} ({item['direction']})"
            for item in top_correlations
        ] or ["- No strong numeric correlations detected."]

        cleaning_lines = [f"- {line}" for line in cleaning_log] or ["- No major cleaning transforms were required."]

        overview_md = "\n".join([
            "### Dataset Understanding",
            f"- Rows: {row_count}",
            f"- Columns: {col_count}",
            f"- Numeric fields: {num_count}",
            f"- Categorical fields: {cat_count}",
            "",
            "### Cleaning Actions",
            *cleaning_lines,
            "",
            "### Key Correlation Signals",
            *top_corr_lines
        ])

        metric_block = {
            "id": "block-dataset-snapshot",
            "type": "MetricGridBlock",
            "title": "Dataset Snapshot",
            "metrics": [
                {"label": "Rows", "value": f"{row_count:,}"},
                {"label": "Columns", "value": f"{col_count:,}"},
                {"label": "Numeric Fields", "value": f"{num_count:,}"},
                {"label": "Categorical Fields", "value": f"{cat_count:,}"},
            ]
        }

        preview_block = {
            "id": "block-data-preview",
            "type": "MarkdownBlock",
            "title": "Data Preview",
            "content": "First 5 rows loaded successfully."
        }

        schema_block = {
            "id": "block-schema-overview",
            "type": "MarkdownBlock",
            "title": "Schema Overview",
            "content": f"Detected {len(schema_info)} fields. Initial profiling completed for schema, numeric summaries, categories, and correlations."
        }

        detail_block = {
            "id": "block-data-understanding",
            "type": "MarkdownBlock",
            "title": "Data Understanding",
            "content": overview_md
        }

        preview_data_block = {
            "id": "block-preview-json",
            "type": "DataFrameBlock",
            "title": "Preview Records",
            "rows": preview_rows
        }

        return [metric_block, preview_block, schema_block, detail_block, preview_data_block]

    def execute(self, state: AnalysisState) -> Dict[str, Any]:
        print("Senior Data Cleaner: Performing business-grade data understanding...")

        raw_path = state.get("raw_data_path", "data/data.csv")
        target_plots_count = state.get("target_plots_count", 7)

        if not os.path.exists(raw_path):
            return {
                "execution_error": f"Input file not found: {raw_path}",
                "retry_count": state.get("retry_count", 0) + 1,
            }

        df = self._load_file(raw_path)
        cleaned_df, metadata = self._safe_impute_and_transform(df)

        with duckdb.connect(self.db_path) as con:
            con.execute("CREATE OR REPLACE TABLE cleaned_analytics_base AS SELECT * FROM cleaned_df")

        feature_registry = self._build_feature_registry(cleaned_df)
        schema_info = self._build_schema_info(cleaned_df)
        numeric_summary = self._build_numeric_summary(cleaned_df)
        categorical_summary = self._build_categorical_summary(cleaned_df)
        correlation_findings = self._build_correlation_findings(cleaned_df)
        cleaning_log = metadata.get("transformations", []) + metadata.get("outlier_flags", [])

        chart_plan = self._build_chart_plan(cleaned_df, correlation_findings, target_plots_count)

        profile_summary = {
            "row_count": len(cleaned_df),
            "column_count": len(cleaned_df.columns),
            "columns": list(cleaned_df.columns),
            "top_numeric_fields": list(numeric_summary.keys())[:10],
            "top_categorical_fields": list(categorical_summary.keys())[:10],
            "correlation_findings": correlation_findings[:5],
            "chart_plan": chart_plan,
            "feature_registry": feature_registry,
        }

        return {
            "cleaned_table_name": "cleaned_analytics_base",
            "data_profile_summary": json.dumps(profile_summary, indent=2),
            "feature_metadata": metadata,
            "feature_registry": feature_registry,
            "business_rules": {
                "banned_suffixes": ["_clean", "_was_null", "_is_outlier", "_month", "_log"],
                "prefer_story_charts": ["time_series_line", "grouped_bar", "donut_share", "stacked_bar"],
            },
            "dataset_preview": cleaned_df.head(5).replace({np.nan: None}).to_dict(orient="records"),
            "schema_info": schema_info,
            "numeric_summary": numeric_summary,
            "categorical_summary": categorical_summary,
            "cleaning_log": cleaning_log,
            "correlation_findings": correlation_findings,
            "chart_plan": chart_plan,
            "final_ui_blocks": self._build_initial_ui_blocks(
                cleaned_df, schema_info, numeric_summary, categorical_summary, cleaning_log, correlation_findings
            ),
            "retry_count": 0,
        }