# UI Table / Wrap Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 表形式問題を表として正しく表示し、長い選択肢テキストが見切れないようにする。

**Architecture:** `app.py` に UI 専用の小さなヘルパー関数を追加し、通常問題と表形式問題の描画を分岐する。長文の可読性は Streamlit 用 CSS を最小追加して改善し、`parser.py` の既存責務は増やさない。

**Tech Stack:** Python 3.12, Streamlit, pytest, Ruff

---

### Task 1: 表形式問題の表示テストを追加

**Files:**
- Modify: `tests/test_app.py`

**Step 1: Write the failing test**

追加内容:
- 表ヘッダと選択肢行から Markdown テーブルを再構築できるテスト
- 表形式問題ではラジオラベルを短い形式にできるテスト

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app.py -v`
Expected: 新規テストが FAIL

**Step 3: Write minimal implementation**

対象:
- `src/quiz_app/app.py`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_app.py src/quiz_app/app.py
git commit -m "feat: render table-based quiz questions"
```

### Task 2: 長文選択肢の折り返しテストを追加

**Files:**
- Modify: `tests/test_app.py`

**Step 1: Write the failing test**

追加内容:
- 折り返し CSS 文字列に `white-space: normal` 相当が含まれるテスト

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app.py -v`
Expected: 新規テストが FAIL

**Step 3: Write minimal implementation**

対象:
- `src/quiz_app/app.py`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_app.py src/quiz_app/app.py
git commit -m "fix: wrap long radio option labels"
```

### Task 3: 全体検証

**Files:**
- Verify only

**Step 1: Run linter**

Run: `uv run ruff check src/ tests/`
Expected: All checks passed

**Step 2: Run formatter check**

Run: `uv run ruff format --check src/ tests/`
Expected: already formatted

**Step 3: Run full test suite**

Run: `uv run pytest`
Expected: 全テスト PASS

**Step 4: Commit**

```bash
git add Improvement_plan.md docs/plans/2026-03-09-ui-table-wrap-fixes.md src/quiz_app/app.py tests/test_app.py
git commit -m "fix: improve quiz option readability and table rendering"
```
