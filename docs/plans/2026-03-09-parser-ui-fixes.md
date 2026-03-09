# Parser / UI Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 実データで発生している正解抽出漏れと UI エラー処理不足を修正し、壊れた問題を出題しないようにする。

**Architecture:** `parser.py` で正解抽出とデータ整合性検証を担い、`app.py` は `QuizParseError` を受けてユーザー向けメッセージを表示する。変更は最小差分に留め、既存の 3 層分離を維持する。

**Tech Stack:** Python 3.12, pytest, Streamlit, Ruff

---

### Task 1: parser の回帰テスト追加

**Files:**
- Modify: `tests/test_parser.py`

**Step 1: Write the failing test**

追加内容:
- `正解の選択肢は **4** です。` を抽出できるテスト
- 正解番号が抽出できない A ファイルで `QuizParseError` になるテスト
- 正解番号が選択肢外なら `QuizParseError` になるテスト

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_parser.py -v`
Expected: 新規テストが FAIL

**Step 3: Write minimal implementation**

対象:
- `src/quiz_app/parser.py`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_parser.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_parser.py src/quiz_app/parser.py
git commit -m "fix: improve parser answer extraction"
```

### Task 2: UI の解析エラー表示対応

**Files:**
- Modify: `tests/test_app.py`
- Modify: `src/quiz_app/app.py`

**Step 1: Write the failing test**

追加内容:
- `load_quiz_data()` が `QuizParseError` を送出したとき、画面に `st.error()` のメッセージが表示されるテスト

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app.py -v`
Expected: 新規テストが FAIL

**Step 3: Write minimal implementation**

対象:
- `_render_home()`
- `_start_quiz()`
- 必要ならエラーメッセージ整形用ヘルパー

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_app.py src/quiz_app/app.py
git commit -m "fix: handle quiz parse errors in ui"
```

### Task 3: import 副作用低減

**Files:**
- Modify: `src/quiz_app/app.py`
- Modify: `tests/test_app.py`（必要最小限）

**Step 1: Write the failing test**

追加内容:
- `main()` が無条件実行でなくても既存テスト方式で動作することを確認するテスト、または既存テスト調整

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app.py -v`
Expected: 必要なら FAIL

**Step 3: Write minimal implementation**

対象:
- `if __name__ == "__main__": main()`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_app.py src/quiz_app/app.py
git commit -m "refactor: guard streamlit entrypoint"
```

### Task 4: 全体検証

**Files:**
- Verify only

**Step 1: Run formatter/linter checks**

Run: `uv run ruff check src/ tests/`
Expected: All checks passed

**Step 2: Run full test suite**

Run: `uv run pytest`
Expected: 全テスト PASS

**Step 3: Spot-check real data**

Run: `uv run python -c "..."` または等価コマンド
Expected: `correct_number == 0` の問題が 0 件

**Step 4: Commit**

```bash
git add .
git commit -m "fix: validate quiz data and handle parse errors"
```
