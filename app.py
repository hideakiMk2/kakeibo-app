from __future__ import annotations
import datetime as dt
import streamlit as st
from db import init_db, insert_expense, fetch_month, sum_month, sum_by_category, delete_transaction

# 初期化
st.set_page_config(page_title="家計簿アプリ", layout="wide")
init_db()  # テーブルが無ければ作成（存在すれば何もしない）初期化しないとSQLがエラーを吐くらしい

# ユーティリティ
def ym_of(date: dt.date) -> str:
    """date -> 'YYYY-MM'"""
    return f"{date.year:04d}-{date.month:02d}"

# UI
st.title("家計簿アプリ")

# サイドバー：表示月の選択　
# 現状streamlitだとyyyy.mm.ddまで表示されてしまうので違和感。
# できればyyyy.mmと表示したい
with st.sidebar:
    st.header("表示")
    today = dt.date.today()
    selected_month_date = st.date_input("表示する月", value=today)
    year_month = ym_of(selected_month_date)
    st.caption(f"現在の表示月: {year_month}")

# メイン：入力 + 集計 + 一覧
left, right = st.columns([1, 2], gap="large")

# 左：入力フォーム
with left:
    st.subheader("支出を追加")

    # 入力 UI
    date_val = st.date_input("日付", value=today)
    amount_val = st.number_input("金額（円）", min_value=0, step=100, value=0)
    item_val = st.text_input("品目", value="")

    # カテゴリは最初は固定候補（後でDB化してもOK）
    category_val = st.selectbox(
        "カテゴリ",
        options=["食費", "日用品", "交通", "娯楽", "家賃", "光熱費", "通信", "医療", "その他"],
        index=0,
    )

    memo = st.text_input("メモ（任意）", value="")

    # 追加ボタン
        # 追加ボタン
    if st.button("追加", type="primary", use_container_width=True):
        item_clean = item_val.strip()
        memo_clean = memo.strip()

        if item_clean == "":
            st.error("品目が空です。入力してください。")
        else:
            if amount_val == 0:
                st.warning("金額が0円です。0円として登録します。")

            insert_expense(
                date_val.isoformat(),
                int(amount_val),
                category_val,
                item_clean,
                memo_clean,
            )
            st.success("追加しました。")
            st.rerun()

    st.divider()

# 右：集計＋一覧

with right:
    st.subheader("集計")

    total = sum_month(year_month)
    by_cat = sum_by_category(year_month)

    c1, c2 = st.columns(2)
    with c1:
        st.metric("当月支出合計（円）", f"{total:,}")
    with c2:
        st.metric("カテゴリ数", f"{len(by_cat)}")

    st.write("カテゴリ別合計")
    if by_cat:
        st.dataframe(by_cat, use_container_width=True, hide_index=True)
    else:
        st.info("この月のデータがまだありません。")

    st.divider()

    st.subheader("当月の記録一覧")

rows = fetch_month(year_month)
if not rows:
    st.info("この月の記録はまだありません。左から追加してください。")
else:
    st.caption("間違えた行の「🗑️」を押すとDBから消えます。")

    h1, h2, h3, h4, h5, h6, h7 = st.columns([1.2, 1.2, 1.2, 1.6, 2.6, 1.0, 0.8])
    h1.markdown("**日付**")
    h2.markdown("**金額**")
    h3.markdown("**カテゴリ**")
    h4.markdown("**品目**")
    h5.markdown("**メモ**")
    h6.markdown("**ID**")
    h7.markdown("**削除**")

    # 1件ずつ表示して削除ボタンを付ける
    for r in rows:
        col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 1.2, 1.2, 1.6, 2.6, 1.0, 0.8])

        col1.write(r["date"])
        col2.write(f'{r["amount"]:,} 円')
        col3.write(r["category"])
        col4.write(r["item"])
        col5.write(r.get("memo", ""))         
        col6.write(f'ID: {r["id"]}')          # デバッグ用にIDも表示してみる

        if col7.button("🗑️", key=f"del_{r['id']}", help="削除"):
            delete_transaction(int(r["id"]))
            st.success(f"削除しました（ID={r['id']}）")
            st.rerun()