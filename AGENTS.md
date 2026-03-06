# AGENTS.md — quiz-app プロジェクトルール

## アーキテクチャ制約
- `parser.py` と `engine.py` は Streamlit に依存してはならない
- UI ロジックは `app.py` に限定する
- データクラスには `dataclasses` を使用する

## TDD 方針
- 新機能は必ずテストを先に書く（テスト先行開発）
- `parser.py` と `engine.py` のテストカバレッジを最優先する
- テストファイルは `tests/` ディレクトリに配置する

## コーディング標準
- すべての関数・クラスに日本語 docstring を付与する
- 型ヒント（type hints）を必須とする
- `ruff check` と `ruff format` をパスするコードのみをコミットする

## ファイル構成
```
src/quiz_app/   # アプリケーションコード
tests/          # テストコード
md/             # マークダウンデータ（Q/Aファイル）
```

## コマンド
```bash
uv run ruff check src/ tests/   # リント
uv run ruff format src/ tests/  # フォーマット
uv run pytest                    # テスト実行
```
