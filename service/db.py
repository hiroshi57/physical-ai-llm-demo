"""永続化層(SQLite, 標準ライブラリ). 実行履歴保存. テナント分離."""
from __future__ import annotations

import json
import sqlite3
from typing import Dict, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    instruction TEXT NOT NULL,
    safe INTEGER NOT NULL,
    replanned INTEGER NOT NULL,
    attempts INTEGER NOT NULL,
    delivered TEXT NOT NULL,
    plan TEXT NOT NULL,
    grid TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class ServiceDB:
    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def save_run(self, tenant_id: str, instruction: str, safe: bool, replanned: bool,
                 attempts: int, delivered: List[str], plan: List[str], grid: str,
                 created_at: str) -> int:
        cur = self.conn.execute(
            "INSERT INTO runs(tenant_id, instruction, safe, replanned, attempts, delivered, "
            "plan, grid, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (tenant_id, instruction, 1 if safe else 0, 1 if replanned else 0, attempts,
             json.dumps(delivered, ensure_ascii=False), json.dumps(plan, ensure_ascii=False),
             grid, created_at))
        self.conn.commit()
        return cur.lastrowid

    def get_run(self, tenant_id: str, run_id: int) -> Optional[Dict]:
        r = self.conn.execute(
            "SELECT * FROM runs WHERE id=? AND tenant_id=?", (run_id, tenant_id)).fetchone()
        if not r:
            return None
        return {"id": r["id"], "instruction": r["instruction"], "safe": bool(r["safe"]),
                "replanned": bool(r["replanned"]), "attempts": r["attempts"],
                "delivered": json.loads(r["delivered"]), "plan": json.loads(r["plan"]),
                "grid": r["grid"], "created_at": r["created_at"]}

    def history(self, tenant_id: str) -> List[Dict]:
        rows = self.conn.execute(
            "SELECT id, instruction, safe, delivered, created_at FROM runs WHERE tenant_id=? "
            "ORDER BY id DESC", (tenant_id,)).fetchall()
        return [{"id": r["id"], "instruction": r["instruction"], "safe": bool(r["safe"]),
                 "delivered": json.loads(r["delivered"]), "created_at": r["created_at"]} for r in rows]

    def close(self) -> None:
        self.conn.close()
