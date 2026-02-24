from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

# DBファイルの保存先（プロジェクト直下の data/kakeibo.db）
DB_PATH = Path(__file__).resolve().parent / "data" / "kakeibo.db"


def _ensure_data_dir() -> None:
    """data/ ディレクトリが無ければ作成する"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    """
    DB接続を返す。
    row_factory を sqlite3.Row にしておくと、dict化しやすい。
    """
    _ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS transactions (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        date     TEXT    NOT NULL,
        amount   INTEGER NOT NULL CHECK(amount >= 0),
        category TEXT    NOT NULL,
        item     TEXT    NOT NULL
    );
    """
    with get_conn() as conn:
        conn.execute(sql)

        # 既存DBに memo 列を追加（無ければ）
        cols = conn.execute("PRAGMA table_info(transactions);").fetchall()
        col_names = {c[1] for c in cols}  # c[1] が列名
        if "memo" not in col_names:
            conn.execute("ALTER TABLE transactions ADD COLUMN memo TEXT NOT NULL DEFAULT ''")

        conn.commit()


def insert_expense(date: str, amount: int, category: str, item: str, memo: str = "") -> None:
    if not date or not isinstance(date, str):
        raise ValueError("date must be a non-empty string like 'YYYY-MM-DD'")
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
    """
    'YYYY-MM' → (start_date, end_date_exclusive)
    例: '2026-02' → ('2026-02-01', '2026-03-01')
    """
    if len(year_month) != 7 or year_month[4] != "-":
        raise ValueError("year_month must be 'YYYY-MM'")

    y = int(year_month[0:4])
    m = int(year_month[5:7])
    if not (1 <= m <= 12):
        raise ValueError("month must be 01..12")

    start = f"{y:04d}-{m:02d}-01"
    # 次月の1日
    if m == 12:
        end = f"{y + 1:04d}-01-01"
    else:
        end = f"{y:04d}-{m + 1:02d}-01"
    return start, end


def fetch_month(year_month: str) -> List[Dict[str, Any]]:
    """
    指定月の支出一覧を返す（新しい日付順）。
    戻り値は dict のリスト（Streamlitでそのまま st.dataframe に渡しやすい）。
    """
    start, end = _month_range(year_month)

    sql = """
    SELECT id, date, amount, category, item, memo
    FROM transactions
    WHERE date >= ? AND date < ?
    ORDER BY date DESC, id DESC
    """
    with get_conn() as conn:
        rows = conn.execute(sql, (start, end)).fetchall()
    return [dict(r) for r in rows]


def sum_month(year_month: str) -> int:
    """
    指定月の支出合計（円）を返す。
    データが無い場合は 0 を返す。
    """
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
    """
    指定月のカテゴリ別合計を返す（合計降順）。
    戻り値例:
      [{'category': '食費', 'total': 12000}, {'category': '交通', 'total': 3000}]
    """
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
    return [{"category": r["category"], "total": int(r["total"])} for r in rows]

def delete_transaction(tx_id: int) -> None:
    """
    id を指定して transactions から1件削除する
    """
    if not isinstance(tx_id, int) or tx_id <= 0:
        raise ValueError("tx_id must be a positive int")

    sql = "DELETE FROM transactions WHERE id = ?"
    with get_conn() as conn:
        conn.execute(sql, (tx_id,))
        conn.commit()
