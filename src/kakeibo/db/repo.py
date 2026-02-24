from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple

# repo.py: .../src/kakeibo/db/repo.py
# project root: .../kakeibo-app
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "data" / "kakeibo.sqlite3"


def _ensure_data_dir() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create table if missing.
    Keep backward-compatibility: if existing DB lacks 'memo', add it.
    """
    create_sql = """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,                -- YYYY-MM-DD
        amount INTEGER NOT NULL CHECK(amount >= 0),
        category TEXT NOT NULL,
        item TEXT NOT NULL,
        memo TEXT NOT NULL DEFAULT ''
    );
    """
    with get_conn() as conn:
        conn.execute(create_sql)

        # Backward-compatible migration: add memo if missing
        cols = conn.execute("PRAGMA table_info(transactions);").fetchall()
        col_names = {c[1] for c in cols}  # c[1] = column name
        if "memo" not in col_names:
            conn.execute("ALTER TABLE transactions ADD COLUMN memo TEXT NOT NULL DEFAULT ''")

        conn.commit()


def insert_expense(date: str, amount: int, category: str, item: str, memo: str = "") -> None:
    if not date or not isinstance(date, str):
        raise ValueError("date must be 'YYYY-MM-DD'")
    if not isinstance(amount, int) or amount < 0:
        raise ValueError("amount must be a non-negative int")
    if not category.strip():
        raise ValueError("category must be non-empty")
    if not item.strip():
        raise ValueError("item must be non-empty")

    sql = """
    INSERT INTO transactions (date, amount, category, item, memo)
    VALUES (?, ?, ?, ?, ?)
    """
    with get_conn() as conn:
        conn.execute(
            sql,
            (
                date.strip(),
                amount,
                category.strip(),
                item.strip(),
                (memo or "").strip(),
            ),
        )
        conn.commit()


def _month_range(year_month: str) -> Tuple[str, str]:
    """
    'YYYY-MM' -> [start, end)
    """
    if len(year_month) != 7 or year_month[4] != "-":
        raise ValueError("year_month must be 'YYYY-MM'")
    y = int(year_month[:4])
    m = int(year_month[5:7])
    if not (1 <= m <= 12):
        raise ValueError("month must be 01..12")

    start = f"{y:04d}-{m:02d}-01"
    end = f"{y + 1:04d}-01-01" if m == 12 else f"{y:04d}-{m + 1:02d}-01"
    return start, end


def fetch_month(year_month: str) -> List[Dict[str, Any]]:
    start, end = _month_range(year_month)
    sql = """
    SELECT id, date, amount, category, item, memo
    FROM transactions
    WHERE date >= ? AND date < ?
    ORDER BY date DESC, id DESC
    """
    with get_conn() as conn:
        rows = conn.execute(sql, (start, end)).fetchall()

    # Return EN keys (stable)
    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": int(r["id"]),
                "date": r["date"],
                "amount": int(r["amount"]),
                "category": r["category"],
                "item": r["item"],
                "memo": r["memo"],
            }
        )
    return out


def sum_month(year_month: str) -> int:
    start, end = _month_range(year_month)
    sql = """
    SELECT COALESCE(SUM(amount), 0) AS total
    FROM transactions
    WHERE date >= ? AND date < ?
    """
    with get_conn() as conn:
        row = conn.execute(sql, (start, end)).fetchone()
    return int(row["total"]) if row is not None else 0


def sum_by_category(year_month: str) -> List[Dict[str, Any]]:
    start, end = _month_range(year_month)
    sql = """
    SELECT category, SUM(amount) AS total
    FROM transactions
    WHERE date >= ? AND date < ?
    GROUP BY category
    ORDER BY total DESC, category ASC
    """
    with get_conn() as conn:
        rows = conn.execute(sql, (start, end)).fetchall()

    # Return EN keys (stable)
    return [{"category": r["category"], "total": int(r["total"])} for r in rows]


def delete_transaction(tx_id: int) -> None:
    if not isinstance(tx_id, int) or tx_id <= 0:
        raise ValueError("tx_id must be a positive int")
    sql = "DELETE FROM transactions WHERE id = ?"
    with get_conn() as conn:
        conn.execute(sql, (tx_id,))
        conn.commit()