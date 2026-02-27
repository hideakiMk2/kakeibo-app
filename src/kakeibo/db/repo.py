from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional, Literal

from kakeibo.db.connection import get_connection


TxType = Literal["expense", "income"]


def _read_schema() -> str:
    schema_path = Path(__file__).with_name("schema.sql")
    return schema_path.read_text(encoding="utf-8")


def init_db() -> None:
    """Create tables if not exist."""
    with get_connection() as con:
        con.executescript(_read_schema())
        con.commit()


# ---------- Transactions (expense/income) ----------

def add_transaction(
    date: str,
    tx_type: TxType,
    amount: int,
    category: str = "",
    item: str = "",
    memo: str = "",
) -> None:
    init_db()
    with get_connection() as con:
        con.execute(
            """
            INSERT INTO transactions(date, type, amount, category, item, memo)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (date, tx_type, amount, category, item, memo),
        )
        con.commit()


def add_expense(date: str, amount: int, category: str, item: str, memo: str = "") -> None:
    add_transaction(date=date, tx_type="expense", amount=amount, category=category, item=item, memo=memo)


def add_income(date: str, amount: int, category: str, item: str, memo: str = "") -> None:
    # category/itemは「収入区分（給料/副業/返金）」等に使える
    add_transaction(date=date, tx_type="income", amount=amount, category=category, item=item, memo=memo)


def delete_transaction(tx_id: int) -> None:
    init_db()
    with get_connection() as con:
        con.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        con.commit()


def list_transactions_by_month(year: int, month: int, tx_type: Optional[TxType] = None) -> list[sqlite3.Row]:
    init_db()
    start = f"{year:04d}-{month:02d}-01"
    # 翌月1日
    if month == 12:
        end = f"{year+1:04d}-01-01"
    else:
        end = f"{year:04d}-{month+1:02d}-01"

    q = """
        SELECT id, date, type, amount, category, item, memo
        FROM transactions
        WHERE date >= ? AND date < ?
    """
    params: list[object] = [start, end]
    if tx_type:
        q += " AND type = ?"
        params.append(tx_type)

    q += " ORDER BY date DESC, id DESC"

    with get_connection() as con:
        cur = con.execute(q, params)
        return cur.fetchall()


def monthly_summary(year: int, month: int) -> dict[str, int]:
    init_db()
    start = f"{year:04d}-{month:02d}-01"
    if month == 12:
        end = f"{year+1:04d}-01-01"
    else:
        end = f"{year:04d}-{month+1:02d}-01"

    with get_connection() as con:
        exp = con.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS s
            FROM transactions
            WHERE date >= ? AND date < ? AND type = 'expense'
            """,
            (start, end),
        ).fetchone()["s"]
        inc = con.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS s
            FROM transactions
            WHERE date >= ? AND date < ? AND type = 'income'
            """,
            (start, end),
        ).fetchone()["s"]

    net = int(inc) - int(exp)
    return {"income": int(inc), "expense": int(exp), "net": net}


def category_summary_for_expenses(year: int, month: int) -> list[sqlite3.Row]:
    """既存のカテゴリ別集計（支出用）。必要ならincomeも同様に作れる。"""
    init_db()
    start = f"{year:04d}-{month:02d}-01"
    if month == 12:
        end = f"{year+1:04d}-01-01"
    else:
        end = f"{year:04d}-{month+1:02d}-01"

    with get_connection() as con:
        cur = con.execute(
            """
            SELECT category, COALESCE(SUM(amount),0) AS total
            FROM transactions
            WHERE date >= ? AND date < ? AND type = 'expense'
            GROUP BY category
            ORDER BY total DESC
            """,
            (start, end),
        )
        return cur.fetchall()


# ---------- Balance snapshots ----------

def add_balance_snapshot(date: str, balance: int, memo: str = "") -> None:
    init_db()
    with get_connection() as con:
        con.execute(
            """
            INSERT INTO balance_snapshots(date, balance, memo)
            VALUES (?, ?, ?)
            """,
            (date, balance, memo),
        )
        con.commit()


def list_balance_snapshots(limit: int = 50) -> list[sqlite3.Row]:
    init_db()
    with get_connection() as con:
        cur = con.execute(
            """
            SELECT id, date, balance, memo
            FROM balance_snapshots
            ORDER BY date DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cur.fetchall()


def delete_balance_snapshot(snapshot_id: int) -> None:
    init_db()
    with get_connection() as con:
        con.execute("DELETE FROM balance_snapshots WHERE id = ?", (snapshot_id,))
        con.commit()


def estimate_current_balance() -> dict[str, int | str]:
    """
    最新スナップショット以降の取引を反映した推定残高を返す。
    snapshotが無い場合は base=0 とする。
    """
    init_db()
    with get_connection() as con:
        snap = con.execute(
            """
            SELECT date, balance
            FROM balance_snapshots
            ORDER BY date DESC, id DESC
            LIMIT 1
            """
        ).fetchone()

        if snap:
            base_date = snap["date"]
            base_balance = int(snap["balance"])
        else:
            base_date = "0000-01-01"
            base_balance = 0

        inc = con.execute(
            """
            SELECT COALESCE(SUM(amount),0) AS s
            FROM transactions
            WHERE date > ? AND type='income'
            """,
            (base_date,),
        ).fetchone()["s"]

        exp = con.execute(
            """
            SELECT COALESCE(SUM(amount),0) AS s
            FROM transactions
            WHERE date > ? AND type='expense'
            """,
            (base_date,),
        ).fetchone()["s"]

    current = base_balance + int(inc) - int(exp)
    return {
        "base_date": base_date,
        "base_balance": base_balance,
        "income_since_base": int(inc),
        "expense_since_base": int(exp),
        "current_balance": int(current),
    }