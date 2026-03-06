"""app モジュールの RED テスト。"""

from dataclasses import dataclass
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
            text=f"第{index}問の問題文です。",
            choices=(
                DummyChoice(number=1, text="選択肢1"),
                DummyChoice(number=2, text="選択肢2"),
                DummyChoice(number=3, text="選択肢3"),
            ),
            correct_number=1,
            explanation=f"第{index}問の解説です。",
        )
        for index in range(1, count + 1)
    ]


def _click_button(app: AppTest, label: str) -> None:
    """指定ラベルのボタンをクリックして再描画する。"""
    for button in app.button:
        if button.label == label:
            button.click().run(timeout=APP_TIMEOUT)
            return

    raise AssertionError(f"{label} ボタンが見つかりません。")


def _has_text(app: AppTest, expected_text: str) -> bool:
    """画面上の主要テキスト要素に期待文字列が含まれるか確認する。"""
    collections = [
        app.title,
        app.header,
        app.subheader,
        app.markdown,
        app.text,
    ]

    for elements in collections:
        if any(expected_text in element.value for element in elements):
            return True

    return False


def test_app_initial_screen_displays_title_and_start_button() -> None:
    """初期画面にタイトルとクイズ開始ボタンが表示されることを確認する。"""
    app = AppTest.from_file("src/quiz_app/app.py")

    app.run(timeout=APP_TIMEOUT)

    assert app.title[0].value == "一級建築士 クイズアプリ"
    assert app.button[0].label == "クイズ開始"


def test_app_clicking_start_sets_engine_and_switches_page() -> None:
    """開始ボタンクリックでエンジン生成と画面遷移が行われることを確認する。"""
    with patch(
        "quiz_app.parser.load_quiz_data",
        return_value=_make_questions(3),
    ):
        app = AppTest.from_file("src/quiz_app/app.py")

        app.run(timeout=APP_TIMEOUT)

        assert "engine" not in app.session_state

        app.button[0].click().run(timeout=APP_TIMEOUT)

        assert "engine" in app.session_state
        assert app.session_state.engine.__class__.__name__ == "QuizEngine"
        assert app.session_state.page == "quiz"


def test_app_play_screen_displays_question_and_explanation() -> None:
    """プレイ画面で問題、選択肢、解説、次へボタンが表示されることを確認する。"""
    with patch(
        "quiz_app.parser.load_quiz_data",
        return_value=_make_questions(2),
    ):
        app = AppTest.from_file("src/quiz_app/app.py")

        app.run(timeout=APP_TIMEOUT)
        _click_button(app, "クイズ開始")

        assert any("第1問の問題文です。" in element.value for element in app.markdown)
        assert len(app.radio) == 1
        assert app.radio[0].options == ["選択肢1", "選択肢2", "選択肢3"]

        app.radio[0].set_value("選択肢1")
        _click_button(app, "解答する")

        assert any("第1問の解説です。" in element.value for element in app.markdown)
        assert any(button.label == "次の問題へ" for button in app.button)


def test_app_result_screen_displays_score_and_mistakes() -> None:
    """全問終了後にリザルト画面でスコアと復習内容が表示されることを確認する。"""
    with patch(
        "quiz_app.parser.load_quiz_data",
        return_value=_make_questions(2),
    ):
        app = AppTest.from_file("src/quiz_app/app.py")

        app.run(timeout=APP_TIMEOUT)
        _click_button(app, "クイズ開始")

        app.radio[0].set_value("選択肢1")
        _click_button(app, "解答する")
        _click_button(app, "次の問題へ")

        app.radio[0].set_value("選択肢2")
        _click_button(app, "解答する")
        _click_button(app, "次の問題へ")

        assert _has_text(app, "結果発表") or _has_text(app, "最終スコア")
        assert _has_text(app, "スコア: 1 / 2")
        assert _has_text(app, "第2問の問題文です。")
        assert _has_text(app, "第2問の解説です。")
        assert any(
            button.label in {"ホームに戻る", "再スタート"} for button in app.button
        )
