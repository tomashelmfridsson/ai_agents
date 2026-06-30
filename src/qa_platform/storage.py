from __future__ import annotations

import csv
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "qa_runs.sqlite3"
DEFAULT_LOG_DIR = ROOT_DIR / "data" / "run_logs"
DEFAULT_EXPORT_DIR = ROOT_DIR / "data" / "exports"


@dataclass
class SavedRun:
    run_id: int
    stored_at: str
    db_path: str
    log_path: str


@dataclass
class SavedEvaluationExport:
    csv_path: str
    row_count: int


def get_db_path() -> Path:
    override = os.getenv("QA_RUNS_DB_PATH")
    return Path(override) if override else DEFAULT_DB_PATH


def get_log_dir() -> Path:
    override = os.getenv("QA_RUNS_LOG_DIR")
    return Path(override) if override else DEFAULT_LOG_DIR


def get_export_dir() -> Path:
    override = os.getenv("QA_EXPORT_DIR")
    if override:
        return Path(override)
    return Path.home() / "Downloads"


def _slugify_title(title: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", (title or "").strip().lower())
    normalized = normalized.strip("-")
    return normalized or "scenario"


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS qa_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stored_at TEXT NOT NULL,
            title TEXT NOT NULL,
            source_requirements TEXT NOT NULL,
            iterations INTEGER NOT NULL,
            requirement_count INTEGER NOT NULL,
            design_count INTEGER NOT NULL,
            coverage_ratio REAL NOT NULL,
            approved INTEGER NOT NULL,
            finding_count INTEGER NOT NULL,
            improvement_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS run_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            evaluator_type TEXT NOT NULL,
            evaluator_name TEXT NOT NULL,
            evaluator_model TEXT NOT NULL,
            approved INTEGER,
            score REAL,
            dimensions_json TEXT NOT NULL,
            findings_json TEXT NOT NULL,
            notes TEXT NOT NULL,
            stored_at TEXT NOT NULL,
            FOREIGN KEY(run_id) REFERENCES qa_runs(id)
        )
        """
    )
    connection.commit()


def _normalize_agent_name(agent_name: str) -> str:
    normalized = (agent_name or "").strip().lower()
    if normalized.endswith(" agent"):
        normalized = normalized[: -len(" agent")]
    return normalized


def _build_agent_runtime_lookup(agent_configs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for config in agent_configs:
        lookup[_normalize_agent_name(str(config.get("agent_name", "")))] = config
    return lookup


def _group_stage_traces(stage_traces: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {}
    for trace in stage_traces:
        grouped.setdefault(int(trace.get("iteration", 0)), []).append(trace)
    return grouped


def build_run_log_text(
    payload: dict[str, Any],
    run_id: int,
    stored_at: str,
    db_path: str,
) -> str:
    review = payload.get("review", {})
    run_controls = payload.get("run_controls", {})
    agent_lookup = _build_agent_runtime_lookup(payload.get("agent_configs", []))
    lines = [
        f"Run ID: {run_id}",
        f"Stored at: {stored_at}",
        f"Database: {db_path}",
        f"Scenario: {payload.get('title', 'Untitled demo')}",
        f"Approved: {review.get('approved')}",
        f"Coverage ratio: {review.get('coverage_ratio')}",
        f"Backtracking rounds: {payload.get('iterations')}",
        f"Maximum rounds: {run_controls.get('max_rounds', payload.get('iterations', 0))}",
        f"Maximum feedback messages: {run_controls.get('max_feedback_messages', 0)}",
        f"Maximum feedback messages per agent pair: {run_controls.get('max_feedback_per_agent_pair', 0)}",
        "",
        "Source requirements:",
        str(payload.get("source_requirements", "")),
        "",
    ]
    agent_configs = payload.get("agent_configs", []) or []
    if agent_configs:
        lines.extend(["Configured agent runtime", ""])
        for config in agent_configs:
            lines.extend(
                [
                    str(config.get("agent_name", "")),
                    f"Execution mode: {config.get('execution_mode', '')}",
                    f"Timeout: {config.get('timeout_seconds', 60)} seconds",
                    f"Resolved model: {config.get('model_id', '') or 'deterministic implementation'}",
                    f"Directives: {config.get('directives', '') or 'No directives configured.'}",
                    "",
                ]
            )

    run_index = 1
    for cycle, traces in _group_stage_traces(payload.get("stage_traces", [])).items():
        lines.extend(
            [
                f"Backtracking round {cycle}",
                "Below is the full sequence of agent passes for this backtracking round, with explicit input, output, and routing context.",
                "",
            ]
        )
        for trace in traces:
            runtime_config = agent_lookup.get(_normalize_agent_name(str(trace.get("agent_name", ""))), {})
            execution_mode = runtime_config.get("execution_mode") or "Structured baseline"
            model_id = runtime_config.get("model_id") or "deterministic implementation"
            lines.extend(
                [
                    f"Run {run_index} • Cycle {trace.get('iteration')} • Stage {trace.get('stage_index')}",
                    str(trace.get("agent_name", "")),
                    f"Status: {trace.get('status', '')}",
                    f"Execution: {execution_mode} / {model_id}",
                    f"Timeout: {runtime_config.get('timeout_seconds', 60)} seconds",
                    f"Time: {int(trace.get('duration_ms', 0) or 0)} ms",
                    f"Configured directive: {runtime_config.get('directives', '') or 'No directives configured.'}",
                ]
            )
            agent_explanation = str(trace.get("agent_explanation", "") or "").strip()
            decision_explanation = str(trace.get("decision_explanation", "") or "").strip()
            if agent_explanation or decision_explanation:
                lines.append("How this agent works")
                if agent_explanation:
                    lines.append(agent_explanation)
                    lines.append("")
                if decision_explanation:
                    lines.append(decision_explanation)
                    lines.append("")
            input_summary = trace.get("input_summary", []) or []
            if input_summary:
                lines.append("Input")
                lines.append(str(input_summary[0]))
                if len(input_summary) > 1:
                    lines.append("")
                    lines.append("Show input details")
                    lines.extend(str(item) for item in input_summary[1:])
            reasoning_trace = trace.get("reasoning_trace", []) or []
            if reasoning_trace:
                lines.append("Reasoning trace")
                lines.append(str(reasoning_trace[0]))
                lines.append("")
                lines.append(f"Source: {trace.get('reasoning_source', 'structured_trace')}")
                if len(reasoning_trace) > 1:
                    lines.append("")
                    lines.append("Show reasoning details")
                    lines.extend(str(item) for item in reasoning_trace[1:])
            output_summary = trace.get("output_summary", []) or []
            if output_summary:
                lines.append("Output")
                lines.append(str(output_summary[0]))
                if len(output_summary) > 1:
                    lines.append("")
                    lines.append("Show output details")
                    lines.extend(str(item) for item in output_summary[1:])
            lines.append("")
            run_index += 1

    findings = review.get("findings", []) or []
    improvements = review.get("improvement_actions", []) or []
    lines.extend(
        [
            "Run summary",
            f"Findings: {len(findings)}",
            *[str(item) for item in findings],
            "",
            f"Improvement actions: {len(improvements)}",
            *[str(item) for item in improvements],
            "",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def save_run(payload: dict[str, Any]) -> SavedRun:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    stored_at = datetime.now(timezone.utc).isoformat()
    review = payload["review"]

    connection = sqlite3.connect(db_path)
    try:
        _ensure_schema(connection)
        cursor = connection.execute(
            """
            INSERT INTO qa_runs (
                stored_at,
                title,
                source_requirements,
                iterations,
                requirement_count,
                design_count,
                coverage_ratio,
                approved,
                finding_count,
                improvement_count,
                payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stored_at,
                payload["title"],
                payload["source_requirements"],
                payload["iterations"],
                len(payload["requirements"]),
                len(payload["test_designs"]),
                review["coverage_ratio"],
                1 if review["approved"] else 0,
                len(review["findings"]),
                len(review["improvement_actions"]),
                json.dumps(payload, ensure_ascii=False),
            ),
        )
        connection.commit()
        run_id = int(cursor.lastrowid)
    finally:
        connection.close()

    log_dir = get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    scenario_slug = _slugify_title(str(payload.get("title", "")))
    log_path = log_dir / f"{scenario_slug}-{timestamp}.txt"
    log_path.write_text(
        build_run_log_text(
            payload=payload,
            run_id=run_id,
            stored_at=stored_at,
            db_path=str(db_path),
        ),
        encoding="utf-8",
    )

    return SavedRun(run_id=run_id, stored_at=stored_at, db_path=str(db_path), log_path=str(log_path))


def save_run_evaluation(
    *,
    run_id: int,
    evaluator_type: str,
    evaluator_name: str,
    evaluator_model: str = "",
    approved: bool | None = None,
    score: float | None = None,
    dimensions: dict[str, Any] | None = None,
    findings: list[str] | None = None,
    notes: str = "",
) -> int:
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    stored_at = datetime.now(timezone.utc).isoformat()

    connection = sqlite3.connect(db_path)
    try:
        _ensure_schema(connection)
        cursor = connection.execute(
            """
            INSERT INTO run_evaluations (
                run_id,
                evaluator_type,
                evaluator_name,
                evaluator_model,
                approved,
                score,
                dimensions_json,
                findings_json,
                notes,
                stored_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                evaluator_type,
                evaluator_name,
                evaluator_model,
                None if approved is None else (1 if approved else 0),
                score,
                json.dumps(dimensions or {}, ensure_ascii=False),
                json.dumps(findings or [], ensure_ascii=False),
                notes or "",
                stored_at,
            ),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def export_run_evaluations_csv(run_id: int | None = None) -> SavedEvaluationExport:
    db_path = get_db_path()
    export_dir = get_export_dir()
    try:
        export_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        export_dir = DEFAULT_EXPORT_DIR
        export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target_name = f"run-evaluations-{run_id}-{timestamp}.csv" if run_id is not None else f"run-evaluations-all-{timestamp}.csv"
    csv_path = export_dir / target_name

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        _ensure_schema(connection)
        if run_id is None:
            run_rows = connection.execute(
                """
                SELECT id, stored_at, title, payload_json
                FROM qa_runs
                ORDER BY id
                """
            ).fetchall()
        else:
            run_rows = connection.execute(
                """
                SELECT id, stored_at, title, payload_json
                FROM qa_runs
                WHERE id = ?
                ORDER BY id
                """,
                (run_id,),
            ).fetchall()

        evaluation_rows = connection.execute(
            """
            SELECT
                id,
                run_id,
                evaluator_type,
                evaluator_name,
                evaluator_model,
                approved,
                score,
                dimensions_json,
                findings_json,
                notes,
                stored_at
            FROM run_evaluations
            ORDER BY run_id, id
            """
        ).fetchall()
    finally:
        connection.close()

    evaluations_by_run: dict[int, dict[str, sqlite3.Row]] = {}
    for row in evaluation_rows:
        evaluations_by_run.setdefault(int(row["run_id"]), {})[str(row["evaluator_type"])] = row

    fieldnames = [
        "run_id",
        "scenario_title",
        "run_stored_at",
        "source_requirements",
        "requirement_count",
        "test_case_count",
        "requirement_id",
        "requirement_text",
        "test_case_id",
        "test_case_title",
        "test_type",
        "steps_json",
        "expected_results_json",
        "oracle",
        "risks_json",
        "review_agent_approved",
        "review_agent_score",
        "review_agent_model",
        "review_agent_findings_json",
        "review_agent_notes",
        "human_approved",
        "human_score",
        "human_relevance",
        "human_completeness",
        "human_oracle_quality",
        "human_executability",
        "human_findings_json",
        "human_notes",
        "deepeval_approved",
        "deepeval_score",
        "deepeval_model",
        "deepeval_findings_json",
        "deepeval_notes",
    ]

    exported_rows: list[dict[str, Any]] = []
    for run_row in run_rows:
        payload = json.loads(str(run_row["payload_json"]))
        requirements = payload.get("requirements", []) or []
        test_designs = payload.get("test_designs", []) or []
        requirement_map = {
            str(item.get("requirement_id", "")): str(item.get("normalized_text", "") or item.get("original_text", ""))
            for item in requirements
        }
        run_evaluations = evaluations_by_run.get(int(run_row["id"]), {})
        review_eval = run_evaluations.get("review_agent")
        human_eval = run_evaluations.get("human")
        deepeval_eval = run_evaluations.get("deepeval")

        review_findings = json.loads(str(review_eval["findings_json"])) if review_eval else []
        human_findings = json.loads(str(human_eval["findings_json"])) if human_eval else []
        deepeval_findings = json.loads(str(deepeval_eval["findings_json"])) if deepeval_eval else []
        human_dimensions = json.loads(str(human_eval["dimensions_json"])) if human_eval else {}

        if not test_designs:
            test_designs = [{}]

        for test_case in test_designs:
            requirement_id = str(test_case.get("requirement_id", ""))
            exported_rows.append(
                {
                    "run_id": run_row["id"],
                    "scenario_title": run_row["title"],
                    "run_stored_at": run_row["stored_at"],
                    "source_requirements": payload.get("source_requirements", ""),
                    "requirement_count": len(requirements),
                    "test_case_count": len(payload.get("test_designs", []) or []),
                    "requirement_id": requirement_id,
                    "requirement_text": requirement_map.get(requirement_id, ""),
                    "test_case_id": test_case.get("test_case_id", ""),
                    "test_case_title": test_case.get("title", ""),
                    "test_type": test_case.get("test_type", ""),
                    "steps_json": json.dumps(test_case.get("steps", []) or [], ensure_ascii=False),
                    "expected_results_json": json.dumps(test_case.get("expected_results", []) or [], ensure_ascii=False),
                    "oracle": test_case.get("oracle", ""),
                    "risks_json": json.dumps(test_case.get("risks", []) or [], ensure_ascii=False),
                    "review_agent_approved": review_eval["approved"] if review_eval else "",
                    "review_agent_score": review_eval["score"] if review_eval else "",
                    "review_agent_model": review_eval["evaluator_model"] if review_eval else "",
                    "review_agent_findings_json": json.dumps(review_findings, ensure_ascii=False),
                    "review_agent_notes": review_eval["notes"] if review_eval else "",
                    "human_approved": human_eval["approved"] if human_eval else "",
                    "human_score": human_eval["score"] if human_eval else "",
                    "human_relevance": human_dimensions.get("relevance", ""),
                    "human_completeness": human_dimensions.get("completeness", ""),
                    "human_oracle_quality": human_dimensions.get("oracle_quality", ""),
                    "human_executability": human_dimensions.get("executability", ""),
                    "human_findings_json": json.dumps(human_findings, ensure_ascii=False),
                    "human_notes": human_eval["notes"] if human_eval else "",
                    "deepeval_approved": deepeval_eval["approved"] if deepeval_eval else "",
                    "deepeval_score": deepeval_eval["score"] if deepeval_eval else "",
                    "deepeval_model": deepeval_eval["evaluator_model"] if deepeval_eval else "",
                    "deepeval_findings_json": json.dumps(deepeval_findings, ensure_ascii=False),
                    "deepeval_notes": deepeval_eval["notes"] if deepeval_eval else "",
                }
            )

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in exported_rows:
            writer.writerow(row)

    return SavedEvaluationExport(csv_path=str(csv_path), row_count=len(exported_rows))
