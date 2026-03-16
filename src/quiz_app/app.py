"""UI層 (Streamlit フロントエンド)。

ユーザーインターフェースの描画と入力の受け付けを担当する。
parser.py と engine.py を呼び出す。
"""

import sys
from pathlib import Path

# Streamlit 実行時のため、src ディレクトリを sys.path に追加する
src_dir = str(Path(__file__).resolve().parents[1])
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import streamlit as st  # noqa: E402

from quiz_app.engine import QuizEngine  # noqa: E402
from quiz_app.parser import Question, QuizParseError, load_quiz_data  # noqa: E402

MD_DIR = Path(__file__).resolve().parents[2] / "md"


def _build_radio_option_css() -> str:
    """長い選択肢を折り返して表示するための CSS を返す。"""
    return """
<style>
[data-baseweb="radio"] label {
    align-items: flex-start;
}
[data-baseweb="radio"] label,
[data-baseweb="radio"] label p,
[data-baseweb="radio"] label div,
.stMarkdown p,
.stMarkdown li {
    white-space: normal;
    word-break: break-word;
    overflow-wrap: anywhere;
}
</style>
"""


def _build_feedback_markup(is_correct: bool) -> str:
    """正誤に応じた強調表示用マークアップを返す。"""
    if is_correct:
        accent_color = "#16a34a"
        background_color = "rgba(22, 163, 74, 0.16)"
        message = "正解です。"
    else:
        accent_color = "#dc2626"
        background_color = "rgba(220, 38, 38, 0.16)"
        message = "不正解です。"

    return f"""
<div style="
    margin: 0.75rem 0;
    padding: 0.85rem 1rem;
    border-left: 0.4rem solid {accent_color};
    background: {background_color};
    border-radius: 0.5rem;
    font-weight: 700;
">
    {message}
</div>
"""


def _is_table_question(question: Question) -> bool:
    """問題文に Markdown テーブルが含まれるかを判定する。"""
    return any(line.strip().startswith("|") for line in question.text.splitlines())


def _build_question_body_and_table(question: Question) -> tuple[str, str | None]:
    """問題文を本文と表 Markdown に分けて返す。"""
    if not _is_table_question(question):
        return question.text, None

    text_lines = question.text.splitlines()
    body_lines: list[str] = []
    table_lines: list[str] = []

    for line in text_lines:
        stripped_line = line.strip()
        if stripped_line.startswith("|"):
            table_lines.append(stripped_line)
        else:
            body_lines.append(line)

    full_table_lines = list(table_lines)
    for choice in question.choices:
        full_table_lines.append(f"| {choice.number} | {choice.text} |")

    body = "\n".join(body_lines).strip()
    table_markdown = "\n".join(full_table_lines) if full_table_lines else None
    return body, table_markdown


def _build_choice_labels(question: Question) -> list[str]:
    """問題形式に応じた選択肢ラベル一覧を返す。"""
    if _is_table_question(question):
        return [f"選択肢 {choice.number}" for choice in question.choices]

    return [f"{choice.number}. {choice.text}" for choice in question.choices]


def _build_choice_display_lines(question: Question) -> list[str]:
    """表示用の選択肢文字列一覧を返す。"""
    if _is_table_question(question):
        return [f"選択肢 {choice.number}" for choice in question.choices]

    return [f"{choice.number}. {choice.text}" for choice in question.choices]


def _build_answer_review_lines(
    question: Question,
    selected_number: int | None,
) -> list[str]:
    """解答後に表示する正誤マーク付き選択肢一覧を返す。"""
    lines: list[str] = []

    for choice in question.choices:
        choice_label = f"{choice.number}. {choice.text}"
        prefix = ""
        if choice.number == question.correct_number:
            prefix = "✅ "
        elif selected_number is not None and choice.number == selected_number:
            prefix = "❌ "

        lines.append(f"{prefix}{choice_label}")

    return lines


def _discover_quiz_files() -> dict[str, tuple[Path, Path]]:
    """md/ ディレクトリから Q/A ファイルのペアを検出する。"""
    quiz_files: dict[str, tuple[Path, Path]] = {}
    for q_file in sorted(MD_DIR.glob("*Q.md")):
        stem = q_file.stem[:-1]  # "2Q" -> "2"
        a_file = q_file.with_name(f"{stem}A.md")
        if a_file.exists():
            quiz_files[f"第{stem}回"] = (q_file, a_file)
    return quiz_files


def _start_quiz(
    q_path: Path,
    a_path: Path,
    is_random: bool,
    limit: int | None,
) -> None:
    """問題データを読み込み、クイズを開始する。"""
    try:
        questions = load_quiz_data(str(q_path), str(a_path))
    except QuizParseError as exc:
        st.error(str(exc))
        return

    engine = QuizEngine()
    engine.start_quiz(questions=questions, is_random=is_random, limit=limit)
    st.session_state["engine"] = engine
    st.session_state["page"] = "quiz"
    st.session_state["is_answered"] = False
    st.session_state["last_question"] = None
    st.session_state["last_is_correct"] = None
    st.session_state["last_selected_number"] = None
    st.rerun()


def _render_home() -> None:
    """ホーム画面を描画する。"""
    quiz_files = _discover_quiz_files()

    if not quiz_files:
        st.warning("md/ ディレクトリにクイズファイルが見つかりません。")
        return

    selected_label = st.selectbox(
        "出題回を選択",
        options=list(quiz_files.keys()),
    )
    assert selected_label is not None
    q_path, a_path = quiz_files[selected_label]

    is_random = st.checkbox("ランダム出題", value=False)

    try:
        questions = load_quiz_data(str(q_path), str(a_path))
    except QuizParseError as exc:
        st.error(str(exc))
        return

    total_count = len(questions)

    limit_input = st.number_input(
        "出題数 (0 で全問)",
        min_value=0,
        max_value=total_count,
        value=0,
        step=1,
    )
    limit: int | None = int(limit_input) if limit_input > 0 else None

    if st.button("クイズ開始"):
        _start_quiz(q_path, a_path, is_random, limit)


def _render_play() -> None:
    """プレイ画面を描画する。"""
    engine = st.session_state["engine"]
    st.markdown(_build_radio_option_css(), unsafe_allow_html=True)

    if st.session_state.get("is_answered", False):
        answered_question = st.session_state.get("last_question")
        last_is_correct = st.session_state.get("last_is_correct", False)
        last_selected_number = st.session_state.get("last_selected_number")

        if answered_question is None:
            st.session_state["is_answered"] = False
            st.rerun()
            return

        answered_body, answered_table = _build_question_body_and_table(
            answered_question
        )
        st.markdown(f"### 第{answered_question.number}問")
        st.markdown(answered_body)
        if answered_table is not None:
            st.markdown(answered_table)

        st.markdown(_build_feedback_markup(last_is_correct), unsafe_allow_html=True)

        st.markdown("### 選択結果")
        for line in _build_answer_review_lines(
            answered_question,
            selected_number=last_selected_number,
        ):
            st.markdown(line)

        st.markdown(answered_question.explanation)

        if st.button("次の問題へ"):
            # 古い radio キーを session_state からクリア
            old_key = f"quiz_radio_{answered_question.number}"
            st.session_state.pop(old_key, None)

            st.session_state["is_answered"] = False
            st.session_state["last_question"] = None
            st.session_state["last_is_correct"] = None
            st.session_state["last_selected_number"] = None

            try:
                engine.get_current_question()
            except IndexError:
                st.session_state["page"] = "result"

            st.rerun()
        return

    try:
        current_question = engine.get_current_question()
    except IndexError:
        st.session_state["page"] = "result"
        st.rerun()
        return

    question_body, question_table = _build_question_body_and_table(current_question)
    st.markdown(f"### 第{current_question.number}問")
    st.markdown(question_body)
    if question_table is not None:
        st.markdown(question_table)

    st.markdown("選択肢を選んでください")
    display_lines = _build_choice_display_lines(current_question)
    for choice, display_line in zip(
        current_question.choices,
        display_lines,
        strict=True,
    ):
        st.markdown(display_line)
        if st.button(
            f"選択肢{choice.number}で解答",
            key=f"answer_button_{current_question.number}_{choice.number}",
        ):
            is_correct = engine.submit_answer(choice.number)
            st.session_state["is_answered"] = True
            st.session_state["last_question"] = current_question
            st.session_state["last_is_correct"] = is_correct
            st.session_state["last_selected_number"] = choice.number
            st.rerun()


def _get_correct_choice_text(question: Question) -> str:
    """問題オブジェクトから正解の選択肢テキストを取得する。"""
    for choice in question.choices:
        if choice.number == question.correct_number:
            return choice.text

    return ""


def _reset_to_home() -> None:
    """セッション状態を初期化してホームへ戻る。"""
    for key in [
        "engine",
        "page",
        "is_answered",
        "last_question",
        "last_is_correct",
        "last_selected_number",
    ]:
        st.session_state.pop(key, None)

    st.rerun()


def _render_result() -> None:
    """リザルト画面を描画する。"""
    engine = st.session_state["engine"]
    score, mistakes = engine.get_results()

    st.markdown("## 結果発表")
    st.markdown(f"スコア: {score} / {len(engine.questions)}")

    if mistakes:
        st.markdown("### 間違えた問題")
        for question in mistakes:
            st.markdown(f"#### 第{question.number}問")
            st.markdown(question.text)
            st.markdown(f"正解: {_get_correct_choice_text(question)}")
            st.markdown(question.explanation)
    else:
        st.markdown("間違えた問題はありません。")

    if st.button("ホームに戻る"):
        _reset_to_home()


def main() -> None:
    """アプリ全体を描画する。"""
    st.title("法規クイズアプリ")

    if "page" not in st.session_state:
        st.session_state["page"] = "home"

    if "engine" not in st.session_state:
        _render_home()
        return

    if st.session_state["page"] in {"quiz", "play"}:
        _render_play()
        return

    if st.session_state["page"] == "result":
        _render_result()
        return


if __name__ == "__main__":
    main()
