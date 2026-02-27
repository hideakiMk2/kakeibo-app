-- 支出/収入を統一管理
CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,                 -- ISO: YYYY-MM-DD (or YYYY-MM-DD HH:MM)
  type TEXT NOT NULL CHECK(type IN ('expense','income')),
  amount INTEGER NOT NULL CHECK(amount >= 0),
  category TEXT,
  item TEXT,
  memo TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);

-- 残高スナップショット（手入力で残高を記録）
CREATE TABLE IF NOT EXISTS balance_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  balance INTEGER NOT NULL,
  memo TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_balance_date ON balance_snapshots(date);