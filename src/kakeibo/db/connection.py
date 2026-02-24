from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "kakeibo.sqlite3"

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con