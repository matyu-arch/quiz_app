# Page Title Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** ページ上の表示タイトルだけを `法規クイズアプリ` に変更する。

**Architecture:** Streamlit UI 層の `st.title(...)` に表示文言が直接定義されているため、その 1 箇所のみを変更する。回帰防止として UI テストの期待値を先に更新し、失敗を確認してから実装を変える。

**Tech Stack:** Python, Streamlit, pytest, ruff

---

### Task 1: ページタイトル文字列の更新

**Files:**
- Modify: `tests/test_app.py`
- Modify: `src/quiz_app/app.py`

**Step 1: Write the failing test**

- `tests/test_app.py` の初期画面テストで期待タイトルを `法規クイズアプリ` に変更する。

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app.py::test_app_initial_screen_displays_title_and_start_button -v`

Expected: FAIL with old title `一級建築士 クイズアプリ`

**Step 3: Write minimal implementation**

- `src/quiz_app/app.py` の `st.title(...)` を `法規クイズアプリ` に変更する。

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app.py::test_app_initial_screen_displays_title_and_start_button -v`

Expected: PASS

**Step 5: Verify the change**

Run:

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run pytest
```
