from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = ROOT_DIR / "data" / "qa_runs.sqlite3"


@dataclass
class SavedRun:
    run_id: int
    stored_at: str
    db_path: str


def get_db_path() -> Path:
    override = os.getenv("QA_RUNS_DB_PATH")
    return Path(override) if override else DEFAULT_DB_PATH


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
    connection.commit()


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

    return SavedRun(run_id=run_id, stored_at=stored_at, db_path=str(db_path))
