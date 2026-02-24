from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple

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
    sql = """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        amount INTEGER NOT NULL CHECK(amount >= 0),
        category TEXT NOT NULL,
        item TEXT NOT NULL,
        memo TEXT NOT NULL DEFAULT ''
    );
    """
    with get_conn() as conn:
        conn.execute(sql)
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

    memo = (memo or "").strip()

    sql = """
    INSERT INTO transactions (date, amount, category, item, memo)
    VALUES (?, ?, ?, ?, ?)
    """
    with get_conn() as conn:
        conn.execute(sql, (date, amount, category.strip(), item.strip(), memo))
        conn.commit()


def _month_range(year_month: str) -> Tuple[str, str]:
    if len(year_month) != 7 or year_month[4] != "-":
        raise ValueError("year_month must be 'YYYY-MM'")
    y = int(year_month[:4])
    m = int(year_month[5:7])
    if not (1 <= m <= 12):
        raise ValueError("month must be 01..12")

    start = f"{y:04d}-{m:02d}-01"
    end = f"{y + 1:04d}-01-01" if m == 12 else f"{y:04d}-{m + 1:02d}-01"
    return start, end


# ★ここで日本語キーに変換
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

    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": int(r["id"]),
                "日付": r["date"],
                "金額": int(r["amount"]),
                "カテゴリー": r["category"],
                "品物": r["item"],
                "メモ": r["memo"],
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


# ★カテゴリ集計も日本語キー
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

    return [{"カテゴリー": r["category"], "合計": int(r["total"])} for r in rows]


def delete_transaction(tx_id: int) -> None:
    if not isinstance(tx_id, int) or tx_id <= 0:
        raise ValueError("tx_id must be a positive int")
    sql = "DELETE FROM transactions WHERE id = ?"
    with get_conn() as conn:
        conn.execute(sql, (tx_id,))
        conn.commit()