import streamlit as st
from datetime import date

from kakeibo.db import repo

st.set_page_config(page_title="家計簿", layout="wide")
repo.init_db()

st.title("家計簿（支出）")

# ---- 入力（支出） ----
st.subheader("支出入力")
col1, col2, col3 = st.columns(3)

with col1:
    d = st.date_input("日付", value=date.today())
with col2:
    amount = st.number_input("金額", min_value=0, step=100, value=0)
with col3:
    category = st.text_input("カテゴリ", value="")

item = st.text_input("品目", value="")
memo = st.text_input("メモ", value="")

if st.button("支出を追加"):
    repo.add_expense(date=d.isoformat(), amount=int(amount), category=category, item=item, memo=memo)
    st.success("追加しました")

st.divider()

# ---- 集計 / 一覧（月選択） ----
st.subheader("月別（支出・収入・差分）")

colA, colB = st.columns(2)
with colA:
    y = st.number_input("年", min_value=2000, max_value=2100, value=date.today().year, step=1)
with colB:
    m = st.number_input("月", min_value=1, max_value=12, value=date.today().month, step=1)

summary = repo.monthly_summary(int(y), int(m))
c1, c2, c3 = st.columns(3)
c1.metric("収入合計", f"{summary['income']:,} 円")
c2.metric("支出合計", f"{summary['expense']:,} 円")
c3.metric("差分", f"{summary['net']:,} 円")

st.subheader("カテゴリ別（支出）")
cat_rows = repo.category_summary_for_expenses(int(y), int(m))
if cat_rows:
    st.dataframe([dict(r) for r in cat_rows], use_container_width=True)
else:
    st.info("データがありません")

st.subheader("月別一覧（支出）")
rows = repo.list_transactions_by_month(int(y), int(m), tx_type="expense")
if rows:
    st.dataframe([dict(r) for r in rows], use_container_width=True)

    del_id = st.number_input("削除する支出ID", min_value=0, step=1, value=0)
    if st.button("支出を削除"):
        if del_id > 0:
            repo.delete_transaction(int(del_id))
            st.success("削除しました（再読み込みしてください）")
else:
    st.info("データがありません")