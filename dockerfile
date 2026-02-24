FROM python:3.13-slim

WORKDIR /app

# uv をインストール
RUN pip install --no-cache-dir uv

# 依存定義を先にコピー（キャッシュ効かせる）
COPY pyproject.toml uv.lock ./

# 依存インストール（uvが .venv を作成）
RUN uv sync --frozen

# アプリ全体をコピー
COPY . .

# Streamlitのポート
EXPOSE 8501

# コンテナ内でStreamlit起動（外部公開）
CMD ["uv", "run", "--", "streamlit", "run", "app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]