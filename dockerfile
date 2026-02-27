FROM python:3.13.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

# 依存定義
COPY pyproject.toml uv.lock ./

# src を明示的に /app/src にコピー
COPY src/ ./src/

# ここで sync（プロジェクトの editable install が走る）
RUN uv sync --frozen

EXPOSE 8501

CMD ["uv", "run", "--", "streamlit", "run", "src/app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]