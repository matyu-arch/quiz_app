"""UI層 (Streamlit フロントエンド)。

ユーザーインターフェースの描画と入力の受け付けを担当する。
parser.py と engine.py を呼び出す。
"""

import sys
from pathlib import Path

import streamlit as st


def _ensure_package_root() -> None:
    """現在の src ディレクトリを import path の先頭へ追加する。"""
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))


def _start_quiz() -> None:
    """問題データを読み込み、クイズを開始する。"""
    _ensure_package_root()
    from quiz_app.engine import QuizEngine
    from quiz_app.parser import load_quiz_data

    questions = load_quiz_data("dummy_q.md", "dummy_a.md")
    engine = QuizEngine()
    engine.start_quiz(questions=questions, is_random=False, limit=None)
    st.session_state["engine"] = engine
    st.session_state["page"] = "quiz"
    st.session_state["is_answered"] = False
    st.session_state["last_question"] = None
    st.session_state["last_is_correct"] = None
    st.rerun()


def _render_home() -> None:
    """ホーム画面を描画する。"""
    if "engine" not in st.session_state and st.button("クイズ開始"):
        _start_quiz()


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

    choice_map = {choice.text: choice.number for choice in current_question.choices}
    selected_choice = st.radio(
        "選択肢を選んでください",
        options=list(choice_map.keys()),
    )

    if st.button("解答する"):
        is_correct = engine.submit_answer(choice_map[selected_choice])
        st.session_state["is_answered"] = True
        st.session_state["last_question"] = current_question
        st.session_state["last_is_correct"] = is_correct
        st.rerun()


def _get_correct_choice_text(question: object) -> str:
    """問題オブジェクトから正解の選択肢テキストを取得する。"""
    for choice in getattr(question, "choices", ()):
        if choice.number == getattr(question, "correct_number", 0):
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
