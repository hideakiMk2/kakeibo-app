from __future__ import annotations

import datetime as dt
import streamlit as st

from kakeibo.db.repo import (
    init_db,
    insert_expense,
    fetch_month,
    sum_month,
    sum_by_category,
    delete_transaction,
)

st.set_page_config(page_title="Kakeibo", layout="wide")
init_db()

def ym_of(d: dt.date) -> str:
    return f"{d.year:04d}-{d.month:02d}"

st.title("Kakeibo")

# ここで「表示月」を選ぶ（集計と一覧に反映）
with st.sidebar:
    st.header("View")
    base = dt.date.today()
    selected = st.date_input("Month", value=base)
    year_month = ym_of(selected)

# 上：入力（横並びでコンパクトに）
st.subheader("Entry")
c1, c2, c3, c4, c5 = st.columns([1.2, 1.0, 1.2, 1.6, 1.4])
with c1:
    date_val = st.date_input("Date", value=dt.date.today())
with c2:
    amount_val = st.number_input("Amount (JPY)", min_value=0, step=100, value=0)
with c3:
    category_val = st.selectbox(
        "Category",
        options=["Food", "Daily", "Transport", "Leisure", "Rent", "Utilities", "Internet", "Medical", "Other"],
        index=0,
    )
with c4:
    item_val = st.text_input("Item", value="")
with c5:
    memo_val = st.text_input("Memo", value="")

if st.button("Add", type="primary", width="stretch"):
    item_clean = item_val.strip()
    if item_clean == "":
        st.error("Item is empty.")
    else:
        insert_expense(
            date=date_val.isoformat(),
            amount=int(amount_val),
            category=category_val,
            item=item_clean,
            memo=memo_val.strip(),
        )
        st.success("Added.")
        st.rerun()

st.divider()

# 中央：集計
st.subheader(f"Summary ({year_month})")
total = sum_month(year_month)
by_cat = sum_by_category(year_month)

m1, m2 = st.columns(2)
m1.metric("Total (JPY)", f"{total:,}")
m2.metric("Categories", f"{len(by_cat)}")

if by_cat:
    st.dataframe(by_cat, width="stretch", hide_index=True)
else:
    st.info("No data for this month.")

st.divider()

# 下：一覧（削除つき）
st.subheader("Records")
rows = fetch_month(year_month)

if not rows:
    st.info("No records for this month.")
else:
    h1, h2, h3, h4, h5, h6, h7 = st.columns([1.2, 1.2, 1.2, 1.6, 2.6, 1.0, 0.8])
    h1.markdown("**Date**")
    h2.markdown("**Amount**")
    h3.markdown("**Category**")
    h4.markdown("**Item**")
    h5.markdown("**Memo**")
    h6.markdown("**ID**")
    h7.markdown("**Del**")

    for r in rows:
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 1.2, 1.2, 1.6, 2.6, 1.0, 0.8])
        col1.write(r["date"])
        col2.write(f'{r["amount"]:,} JPY')
        col3.write(r["category"])
        col4.write(r["item"])
        col5.write(r.get("memo", ""))
        col6.write(f'ID: {r["id"]}')

        if col7.button("🗑️", key=f"del_{r['id']}"):
            delete_transaction(int(r["id"]))
            st.success(f"Deleted (ID={r['id']})")
            st.rerun()