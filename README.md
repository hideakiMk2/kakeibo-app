# 家計簿アプリ（Streamlit）
Streamlit と SQLite を用いた勉強目的のシンプルな家計簿アプリです。  
日々の支出・収入を記録し、月次集計やカテゴリ別の可視化を行えます。
---
# 起動方法
起動方法（Docker）\
※ すべて kakeibo-app/ 直下で実行

1) ビルド \
```bash
docker build -t kakeibo-app .
```
2) アプリ起動 \
```bash
docker run --rm -p 8501:8501 \
  -v "$(pwd)/data:/app/data" \
  kakeibo-app
```
ブラウザ：\
http://localhost:8501

3) コンテナに入る（任意）\
```bash
docker run --rm -it \
  -v "$(pwd):/app" \
  kakeibo-app \
  bash
```
4) （コンテナ内で）Streamlit起動\
```bash
uv run -- streamlit run src/app/main.py \
  --server.address=0.0.0.0 \
  --server.port=8501
```

## 機能
### 基本
- 日付単位での収入・支出の記録
- 品目・カテゴリの管理
- 取引一覧表示
- 月次合計の表示

### 拡張（予定含む）
- カテゴリ別グラフ表示
- 月別推移グラフ
- 月予算設定と警告表示
- 総残高表示
- カレンダー風表示
---
## 技術構成
- Python 3.13.11
- Streamlit（UIフレームワーク）
- SQLite（組み込みデータベース）
- uv（Python依存・環境管理）
- Docker（実行環境の統一）