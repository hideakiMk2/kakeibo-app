# 家計簿アプリ（Streamlit）
Streamlit と SQLite を用いた勉強目的のシンプルな家計簿アプリです。  
日々の支出・収入を記録し、月次集計やカテゴリ別の可視化を行えます。
---
# 起動方法
1) ビルドコマンド
docker build -t kakeibo-app .
2) コンテナを起動
docker run --rm -p 8501:8501 \
  -e PYTHONPATH=src \
  -v "$(pwd)/src/data:/app/src/data" \
  kakeibo-app
3) コンテナに入る(シェル)
docker run --rm -it \
  -e PYTHONPATH=src \
  -v "$(pwd):/app" \
  kakeibo-app \
  bash
4) Streamlitを起動
PYTHONPATH=src uv run -- streamlit run src/app/main.py

## 機能
### 基本
- 日付ごとの支出・収入の記録
- 品目・カテゴリ管理
- 一覧表示
- 月合計表示

### 拡張（予定含む）
- カテゴリ別グラフ表示
- 月別推移グラフ
- 月予算設定と警告表示
- 総残高表示
- カレンダー風表示
---
## 技術構成
- Python 3.13.11
- Streamlit
- SQLite