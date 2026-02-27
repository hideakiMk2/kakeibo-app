import streamlit as st
from datetime import date

from kakeibo.db import repo

st.set_page_config(page_title="残高と収入", layout="wide")
repo.init_db()

st.title("残高と収入")

# ---- 残高推定 ----
st.subheader("現在残高")
bal = repo.estimate_current_balance()

c1, c2, c3, c4 = st.columns(4)
c1.metric("基準日", str(bal["base_date"]))
c2.metric("基準残高", f"{bal['base_balance']:,} 円")
c3.metric("基準日以降の収入", f"{bal['income_since_base']:,} 円")
c4.metric("基準日以降の支出", f"{bal['expense_since_base']:,} 円")

st.metric("残高", f"{bal['current_balance']:,} 円")

st.divider()

# ---- 残高を管理 ----
st.subheader("残高を記録")
col1, col2, col3 = st.columns(3)
with col1:
    d = st.date_input("記録日", value=date.today(), key="snap_date")
with col2:
    b = st.number_input("残高（円）", value=0, step=1000, min_value=0, key="snap_balance")
with col3:
    memo = st.text_input("メモ（任意）", value="", key="snap_memo")

if st.button("残高を記録"):
    repo.add_balance_snapshot(date=d.isoformat(), balance=int(b), memo=memo)
    st.success("記録しました")

st.subheader("残高管理履歴")
snap_rows = repo.list_balance_snapshots(limit=50)
if snap_rows:
    st.dataframe([dict(r) for r in snap_rows], use_container_width=True)

    del_sid = st.number_input("削除するID", min_value=0, step=1, value=0, key="del_snap")
    if st.button("削除"):
        if del_sid > 0:
            repo.delete_balance_snapshot(int(del_sid))
            st.success("削除しました（再読み込みしてください）")
else:
    st.info("残高管理履歴がありません")

st.divider()

# ---- 収入入力 ----
st.subheader("収入入力")
colA, colB, colC = st.columns(3)

with colA:
    inc_date = st.date_input("日付", value=date.today(), key="inc_date")
with colB:
    inc_amount = st.number_input("金額", min_value=0, step=1000, value=0, key="inc_amount")
with colC:
    inc_category = st.text_input("カテゴリ（例：給料/副業/返金）", value="給料", key="inc_category")

inc_item = st.text_input("品目（例：2月分給与）", value="", key="inc_item")
inc_memo = st.text_input("メモ", value="", key="inc_memo")

if st.button("収入を追加"):
    repo.add_income(
        date=inc_date.isoformat(),
        amount=int(inc_amount),
        category=inc_category,
        item=inc_item,
        memo=inc_memo,
    )
    st.success("収入を追加しました")

st.subheader("月別一覧（収入）")
y = st.number_input("年", min_value=2000, max_value=2100, value=date.today().year, step=1, key="inc_y")
m = st.number_input("月", min_value=1, max_value=12, value=date.today().month, step=1, key="inc_m")

inc_rows = repo.list_transactions_by_month(int(y), int(m), tx_type="income")
if inc_rows:
    st.dataframe([dict(r) for r in inc_rows], use_container_width=True)

    del_id = st.number_input("削除する収入ID", min_value=0, step=1, value=0, key="del_income")
    if st.button("収入を削除"):
        if del_id > 0:
            repo.delete_transaction(int(del_id))
            st.success("削除しました（再読み込みしてください）")
else:
    st.info("収入データがありません")