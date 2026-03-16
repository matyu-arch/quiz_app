"""app モジュールの RED テスト。"""

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP_TIMEOUT = 60


def _build_app() -> AppTest:
    """テスト対象の Streamlit アプリを関数から生成する。"""

    def _run_app() -> None:
        """テスト実行時にアプリ本体を呼び出す。"""
        from quiz_app.app import main

        main()

    return AppTest.from_function(_run_app)


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


def _make_table_question() -> DummyQuestion:
    """表形式問題を表すダミー問題を生成する。"""
    return DummyQuestion(
        number=50,
        text=(
            "表形式問題です。\n\n"
            "| 選択肢 | 室の種類 | 柱のささえる床の数 |\n"
            "|---|---|---:|"
        ),
        choices=(
            DummyChoice(number=1, text="病院の病室 | 4"),
            DummyChoice(number=2, text="事務室 | 10"),
        ),
        correct_number=1,
        explanation="表形式の解説",
    )


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
        app = _build_app()
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
        app = _build_app()
        app.run(timeout=APP_TIMEOUT)
        assert app.title[0].value == "法規クイズアプリ"
        assert any(button.label == "クイズ開始" for button in app.button)


def test_app_clicking_start_sets_engine_and_switches_page() -> None:
    """開始ボタンクリックでエンジン生成と画面遷移が行われることを確認する。"""
    p1, p2 = _patches()
    with p1, p2:
        app = _build_app()
        app.run(timeout=APP_TIMEOUT)
        assert "engine" not in app.session_state
        _click_button(app, "クイズ開始")
        assert "engine" in app.session_state
        assert app.session_state.page == "quiz"


def test_app_play_screen_displays_question_and_choices() -> None:
    """プレイ画面で問題と個別の選択肢ボタンが表示されることを確認する。"""
    app = _create_quiz_app()

    assert _has_text(app, "Q1")
    assert _has_text(app, "1. A")
    assert _has_text(app, "2. B")
    assert _has_text(app, "3. C")
    assert any(button.label == "選択肢1で解答" for button in app.button)
    assert any(button.label == "選択肢2で解答" for button in app.button)
    assert any(button.label == "選択肢3で解答" for button in app.button)


def test_app_play_screen_shows_explanation_after_answer() -> None:
    """解答後に解説と次の問題ボタンが表示されることを確認する。"""
    app = _create_quiz_app()

    _click_button(app, "選択肢1で解答")

    assert _has_text(app, "Q1")
    assert _has_text(app, "E1")
    assert any(button.label == "次の問題へ" for button in app.button)


def test_app_answered_screen_shows_choice_review_for_correct_answer() -> None:
    """正解時は選んだ選択肢のみに ✅ が付くことを確認する。"""
    app = _create_quiz_app()

    _click_button(app, "選択肢1で解答")

    assert _has_text(app, "✅ 1. A")
    assert not _has_text(app, "❌ 1. A")
    assert not _has_text(app, "✅ 2. B")


def test_app_answered_screen_shows_choice_review_for_wrong_answer() -> None:
    """不正解時は選択肢に ❌、正解肢に ✅ が付くことを確認する。"""
    app = _create_quiz_app()

    _click_button(app, "選択肢2で解答")

    assert _has_text(app, "❌ 2. B")
    assert _has_text(app, "✅ 1. A")


def test_build_answer_review_lines_returns_marked_choices() -> None:
    """選択結果に応じたマーク付き選択肢一覧を生成できることを確認する。"""
    from quiz_app.app import _build_answer_review_lines

    question = _make_questions(1)[0]

    correct_lines = _build_answer_review_lines(question, selected_number=1)
    wrong_lines = _build_answer_review_lines(question, selected_number=2)

    assert correct_lines == ["✅ 1. A", "2. B", "3. C"]
    assert wrong_lines == ["✅ 1. A", "❌ 2. B", "3. C"]


def test_build_feedback_markup_returns_success_style_for_correct_answer() -> None:
    """正解時は緑系のマークアップを返すことを確認する。"""
    from quiz_app.app import _build_feedback_markup

    markup = _build_feedback_markup(True)

    assert "正解です。" in markup
    assert "#16a34a" in markup


def test_build_feedback_markup_returns_error_style_for_wrong_answer() -> None:
    """不正解時は赤系のマークアップを返すことを確認する。"""
    from quiz_app.app import _build_feedback_markup

    markup = _build_feedback_markup(False)

    assert "不正解です。" in markup
    assert "#dc2626" in markup


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
        app = _build_app()
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
    assert any(button.label in {"ホームに戻る", "再スタート"} for button in app.button)


def test_app_initial_screen_displays_parse_error_message() -> None:
    """問題データの解析失敗時に画面へエラーメッセージを表示する。"""
    from quiz_app.parser import QuizParseError

    with (
        patch(
            "quiz_app.app._discover_quiz_files",
            return_value=_fake_quiz_files(),
        ),
        patch(
            "quiz_app.app.load_quiz_data",
            side_effect=QuizParseError("正解番号を抽出できませんでした。"),
        ),
    ):
        app = _build_app()
        app.run(timeout=APP_TIMEOUT)

    assert any("正解番号を抽出できませんでした。" in error.value for error in app.error)


def test_importing_app_module_does_not_run_main() -> None:
    """モジュール import 時には main が自動実行されないことを確認する。"""
    sys.modules.pop("quiz_app.app", None)

    with patch("streamlit.title") as mocked_title:
        importlib.import_module("quiz_app.app")

    mocked_title.assert_not_called()


def test_build_choice_labels_returns_short_labels_for_table_question() -> None:
    """表形式問題では短いラジオラベルを返すことを確認する。"""
    from quiz_app.app import _build_choice_labels

    labels = _build_choice_labels(_make_table_question())

    assert labels == ["選択肢 1", "選択肢 2"]


def test_build_choice_labels_returns_text_labels_for_regular_question() -> None:
    """通常問題では番号付きの選択肢文をラベルに使うことを確認する。"""
    from quiz_app.app import _build_choice_labels

    question = _make_questions(1)[0]

    labels = _build_choice_labels(question)

    assert labels == ["1. A", "2. B", "3. C"]


def test_build_question_body_and_table_returns_table_markdown() -> None:
    """表形式問題から本文と表 Markdown を分離できることを確認する。"""
    from quiz_app.app import _build_question_body_and_table

    body, table_markdown = _build_question_body_and_table(_make_table_question())

    assert "表形式問題です。" in body
    assert table_markdown is not None
    assert "| 選択肢 | 室の種類 | 柱のささえる床の数 |" in table_markdown
    assert "| 1 | 病院の病室 | 4 |" in table_markdown
    assert "| 2 | 事務室 | 10 |" in table_markdown


def test_build_radio_option_css_enables_wrapping() -> None:
    """長文選択肢の折り返し用 CSS を返すことを確認する。"""
    from quiz_app.app import _build_radio_option_css

    css = _build_radio_option_css()

    assert "white-space: normal" in css
    assert "word-break: break-word" in css
    assert ".stMarkdown" in css
    assert '[data-baseweb="radio"]' in css
    assert "overflow-wrap: anywhere" in css
