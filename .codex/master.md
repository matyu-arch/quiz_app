# quiz-app マスタープロンプト

## プロジェクト概要
マークダウン形式の選択問題（Q）と解答・解説（A）を読み込み、ブラウザ上で学習できるインタラクティブなWebベースのクイズアプリケーション。

## 技術スタック
- **言語:** Python 3.12+
- **パッケージ管理:** uv
- **Webフレームワーク:** Streamlit
- **コンテナ:** Podman
- **リンター/フォーマッター:** Ruff
- **テスト:** pytest

## アーキテクチャ (3レイヤー)
1. **Data Layer (`parser.py`):** Markdownの解析。Streamlitに依存しない。
2. **Logic Layer (`engine.py`):** クイズの状態管理。UIに依存しない。
3. **UI Layer (`app.py`):** Streamlitフロントエンド。

## コーディング規約
- すべての関数・クラスに日本語 docstring を付与
- 型ヒントを必須とする
- Ruff の設定に従ったフォーマット（line-length = 88）
- インポート順序は isort 準拠

## 品質ゲート
コミット前に以下をすべてパスすること:
```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run pytest
```
