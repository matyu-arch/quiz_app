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
from quiz_app.parser import Question, load_quiz_data  # noqa: E402

MD_DIR = Path(__file__).resolve().parents[2] / "md"


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
    questions = load_quiz_data(str(q_path), str(a_path))
    engine = QuizEngine()
    engine.start_quiz(questions=questions, is_random=is_random, limit=limit)
    st.session_state["engine"] = engine
    st.session_state["page"] = "quiz"
    st.session_state["is_answered"] = False
    st.session_state["last_question"] = None
    st.session_state["last_is_correct"] = None
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

    questions = load_quiz_data(str(q_path), str(a_path))
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

    if st.session_state.get("is_answered", False):
        answered_question = st.session_state.get("last_question")
        last_is_correct = st.session_state.get("last_is_correct", False)

        if answered_question is None:
            st.session_state["is_answered"] = False
            st.rerun()
            return

        st.markdown(f"### 第{answered_question.number}問")
        st.markdown(answered_question.text)

        if last_is_correct:
            st.markdown("**正解です。**")
        else:
            st.markdown("**不正解です。**")

        st.markdown(answered_question.explanation)

        if st.button("次の問題へ"):
            # 古い radio キーを session_state からクリア
            old_key = f"quiz_radio_{answered_question.number}"
            st.session_state.pop(old_key, None)

            st.session_state["is_answered"] = False
            st.session_state["last_question"] = None
            st.session_state["last_is_correct"] = None

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

    st.markdown(f"### 第{current_question.number}問")
    st.markdown(current_question.text)

    choice_labels = [choice.text for choice in current_question.choices]
    choice_numbers = [choice.number for choice in current_question.choices]

    selected_label = st.radio(
        "選択肢を選んでください",
        options=choice_labels,
        key=f"quiz_radio_{current_question.number}",
    )

    selected_number = choice_numbers[choice_labels.index(selected_label)]

    if st.button("解答する"):
        is_correct = engine.submit_answer(selected_number)
        st.session_state["is_answered"] = True
        st.session_state["last_question"] = current_question
        st.session_state["last_is_correct"] = is_correct
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
    st.title("一級建築士 クイズアプリ")

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


main()
