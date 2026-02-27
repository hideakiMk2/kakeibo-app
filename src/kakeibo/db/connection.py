from pathlib import Path
import sqlite3

# connection.py: src/kakeibo/db/connection.py
DB_PATH = Path(__file__).resolve().parents[3] / "data" / "kakeibo.sqlite3"
# parents[0]=db, [1]=kakeibo, [2]=src, [3]=project root

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con