# Choice Buttons Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `st.radio` を廃止し、各選択肢を個別 `markdown + button` で表示して長文の見切れを防ぐ。

**Architecture:** `app.py` のプレイ画面で選択肢ごとのブロックを順に描画し、ボタン押下時にその選択肢番号を直接 `submit_answer()` へ渡す。解答後レビュー表示は維持し、テストは新しい UI 操作に合わせて更新する。

**Tech Stack:** Python 3.12, Streamlit, pytest, Ruff

---

### Task 1: UI テストを個別ボタン方式へ更新

**Files:**
- Modify: `tests/test_app.py`

**Step 1: Write the failing test**

追加・更新内容:
- プレイ画面で `radio` ではなく選択肢用ボタンが並ぶことを確認
- ボタン押下で解答後画面へ遷移することを確認

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_app.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

対象:
- `src/quiz_app/app.py`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app.py -v`
Expected: PASS

### Task 2: app.py を個別選択肢ボタン方式へ変更

**Files:**
- Modify: `src/quiz_app/app.py`

**Step 1: Remove radio-based logic**

- `st.radio(...)`
- `selected_label`
- `choice_labels.index(...)`

**Step 2: Add choice rendering helper**

- 選択肢ごとに本文 Markdown と解答ボタンを表示する

**Step 3: Wire answer submission**

- クリックされた選択肢番号を `submit_answer()` へ渡す

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_app.py -v`
Expected: PASS

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
