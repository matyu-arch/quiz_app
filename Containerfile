# ---- ステージ1: ビルド ----
FROM python:3.12-slim AS builder

# uv インストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 依存関係のインストール（キャッシュ最適化）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --all-groups --no-install-project

# ソースコードのコピー
COPY src/ ./src/

# ---- ステージ2: 実行 ----
FROM python:3.12-slim AS runtime

WORKDIR /app

# Antigravity Dev Containers のサーバー導入に必要なツールを追加
RUN apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates procps \
    && rm -rf /var/lib/apt/lists/*

# uv をランタイムにも同梱（開発時の pip install uv を不要化）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# ビルドステージから仮想環境とソースをコピー
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# マークダウンデータ用ディレクトリ
COPY md/ ./md/

# パスの設定
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

# Streamlit ポート公開
EXPOSE 8501

# Streamlit 起動
CMD ["streamlit", "run", "src/quiz_app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
