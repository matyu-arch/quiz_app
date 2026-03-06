"""app モジュールの RED テスト。"""

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP_TIMEOUT = 60


@dataclass(frozen=True)
class DummyChoice:
    """テスト用の選択肢を表すデータ。"""

    number: int
    text: str


@dataclass(frozen=True)
class DummyQuestion:
    """テスト用の問題を表すデータ。"""

    number: int
    text: str
    choices: tuple[DummyChoice, ...]
    correct_number: int
    explanation: str


def _make_questions(count: int) -> list[DummyQuestion]:
    """テスト用のダミー問題一覧を生成する。"""
    return [
        DummyQuestion(
            number=index,
            text=f"Q{index}",
            choices=(
                DummyChoice(number=1, text="A"),
                DummyChoice(number=2, text="B"),
                DummyChoice(number=3, text="C"),
            ),
            correct_number=1,
            explanation=f"E{index}",
        )
        for index in range(1, count + 1)
    ]


def _fake_quiz_files() -> dict[str, tuple[Path, Path]]:
    """テスト用のダミーファイルペアを返す。"""
    return {
        "test-01": (Path("md/1Q.md"), Path("md/1A.md")),
    }


def _patches():
    """テスト用の共通モックコンテキストを返す。"""
    return (
        patch(
            "quiz_app.app._discover_quiz_files",
            return_value=_fake_quiz_files(),
        ),
        patch(
            "quiz_app.app.load_quiz_data",
            return_value=_make_questions(2),
        ),
    )


def _click_button(app: AppTest, label: str) -> None:
    """指定ラベルのボタンをクリックして再描画する。"""
    for button in app.button:
        if button.label == label:
            button.click().run(timeout=APP_TIMEOUT)
            return
    labels = [b.label for b in app.button]
    msg = f"'{label}' not found. Available: {labels}"
    raise AssertionError(msg)


def _has_text(app: AppTest, expected_text: str) -> bool:
    """画面上の主要テキスト要素に期待文字列が含まれるか確認する。"""
    for elements in [app.title, app.header, app.subheader, app.markdown, app.text]:
        if any(expected_text in element.value for element in elements):
            return True
    return False


def _create_quiz_app():
    """テスト用のアプリを起動してクイズ開始まで進める。"""
    from quiz_app.engine import QuizEngine

    questions = _make_questions(2)
    engine = QuizEngine()
    engine.start_quiz(questions=questions, is_random=False, limit=None)

    p1, p2 = _patches()
    with p1, p2:
        app = AppTest.from_file("src/quiz_app/app.py")
        app.session_state["engine"] = engine
        app.session_state["page"] = "quiz"
        app.session_state["is_answered"] = False
        app.session_state["last_question"] = None
        app.session_state["last_is_correct"] = None
        app.run(timeout=APP_TIMEOUT)

    return app


def test_app_initial_screen_displays_title_and_start_button() -> None:
    """初期画面にタイトルとクイズ開始ボタンが表示されることを確認する。"""
    p1, p2 = _patches()
    with p1, p2:
        app = AppTest.from_file("src/quiz_app/app.py")
        app.run(timeout=APP_TIMEOUT)
        assert app.title[0].value == "一級建築士 クイズアプリ"
        assert any(button.label == "クイズ開始" for button in app.button)


def test_app_clicking_start_sets_engine_and_switches_page() -> None:
    """開始ボタンクリックでエンジン生成と画面遷移が行われることを確認する。"""
    p1, p2 = _patches()
    with p1, p2:
        app = AppTest.from_file("src/quiz_app/app.py")
        app.run(timeout=APP_TIMEOUT)
        assert "engine" not in app.session_state
        _click_button(app, "クイズ開始")
        assert "engine" in app.session_state
        assert app.session_state.page == "quiz"


def test_app_play_screen_displays_question_and_choices() -> None:
    """プレイ画面で問題と選択肢が表示されることを確認する。"""
    app = _create_quiz_app()

    assert _has_text(app, "Q1")
    assert len(app.radio) == 1
    assert app.radio[0].options == ["A", "B", "C"]


def test_app_play_screen_shows_explanation_after_answer() -> None:
    """解答後に解説と次の問題ボタンが表示されることを確認する。"""
    app = _create_quiz_app()

    app.radio[0].set_value("A")
    _click_button(app, "解答する")

    assert _has_text(app, "E1")
    assert any(button.label == "次の問題へ" for button in app.button)


def test_app_result_screen_displays_score_and_mistakes() -> None:
    """全問終了後にスコアと復習内容が表示されることを確認する。"""
    from quiz_app.engine import QuizEngine

    questions = _make_questions(2)
    engine = QuizEngine()
    engine.start_quiz(questions=questions, is_random=False, limit=None)

    # 問題1: 正解, 問題2: 不正解
    engine.submit_answer(1)  # correct
    engine.submit_answer(2)  # wrong

    p1, p2 = _patches()
    with p1, p2:
        app = AppTest.from_file("src/quiz_app/app.py")
        app.session_state["engine"] = engine
        app.session_state["page"] = "result"
        app.session_state["is_answered"] = False
        app.session_state["last_question"] = None
        app.session_state["last_is_correct"] = None
        app.run(timeout=APP_TIMEOUT)

    assert _has_text(app, "結果発表") or _has_text(app, "最終スコア")
    assert _has_text(app, "スコア: 1 / 2")
    assert _has_text(app, "Q2")
    assert _has_text(app, "E2")
    assert any(
        button.label in {"ホームに戻る", "再スタート"} for button in app.button
    )
