FROM python:3.13.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

# 依存定義と src を同時コピー（←重要）
COPY pyproject.toml uv.lock src ./ 

# 依存 + プロジェクト同期
RUN uv sync --frozen

# 残りのファイル
COPY . .

EXPOSE 8501
ENV PYTHONPATH=src

CMD ["uv", "run", "--", "streamlit", "run", "src/app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]