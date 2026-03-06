"""engine モジュールの RED テスト。"""

import random

import pytest

from quiz_app.engine import QuizEngine
from quiz_app.parser import Choice, Question


def _make_questions(count: int) -> list[Question]:
    """テスト用の Question 一覧を生成する。"""
    return [
        Question(
            number=index,
            text=f"問題 {index}",
            choices=[
                Choice(number=1, text="選択肢1"),
                Choice(number=2, text="選択肢2"),
                Choice(number=3, text="選択肢3"),
            ],
            correct_number=1,
            explanation=f"解説 {index}",
        )
        for index in range(1, count + 1)
    ]


def test_quiz_engine_start_quiz_initializes_questions_and_current_index() -> None:
    """正常な初期化で問題一覧と現在位置が初期状態になることを確認する。"""
    questions = _make_questions(3)
    engine = QuizEngine()

    engine.start_quiz(questions=questions, is_random=False, limit=None)

    assert engine.questions == questions
    assert engine.current_index == 0


def test_quiz_engine_start_quiz_applies_limit() -> None:
    """limit 指定時に保持される問題数が制限されることを確認する。"""
    questions = _make_questions(10)
    engine = QuizEngine()

    engine.start_quiz(questions=questions, is_random=False, limit=5)

    assert len(engine.questions) == 5
    assert [question.number for question in engine.questions] == [1, 2, 3, 4, 5]


def test_quiz_engine_start_quiz_shuffles_questions_when_random_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """is_random=True のときに問題順がシャッフルされることを確認する。"""
    questions = _make_questions(10)
    engine = QuizEngine()

    def fake_shuffle(items: list[Question]) -> None:
        """テスト用に並び順を反転させる。"""
        items.reverse()

    monkeypatch.setattr(random, "shuffle", fake_shuffle)

    engine.start_quiz(questions=questions, is_random=True, limit=None)

    assert [question.number for question in engine.questions] == [
        10,
        9,
        8,
        7,
        6,
        5,
        4,
        3,
        2,
        1,
    ]
    assert [question.number for question in questions] == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
    ]


def test_get_current_question_returns_question_and_raises_after_end() -> None:
    """現在の問題取得と全問終了後の例外送出を確認する。"""
    questions = _make_questions(2)
    engine = QuizEngine()

    engine.start_quiz(questions=questions, is_random=False, limit=None)

    assert engine.get_current_question() == questions[0]

    engine.current_index = len(engine.questions)

    with pytest.raises(IndexError):
        engine.get_current_question()


def test_submit_answer_returns_true_and_advances_on_correct_answer() -> None:
    """正解送信時に True を返し、現在位置が進むことを確認する。"""
    questions = _make_questions(2)
    engine = QuizEngine()

    engine.start_quiz(questions=questions, is_random=False, limit=None)

    result = engine.submit_answer(choice_number=1)

    assert result is True
    assert engine.current_index == 1


def test_submit_answer_records_mistake_and_advances_on_wrong_answer() -> None:
    """不正解送信時に False を返し、間違えた問題を記録することを確認する。"""
    questions = _make_questions(2)
    engine = QuizEngine()

    engine.start_quiz(questions=questions, is_random=False, limit=None)

    result = engine.submit_answer(choice_number=2)

    assert result is False
    assert engine.current_index == 1
    assert len(engine.mistakes) == 1
    assert engine.mistakes[0].number == 1


def test_quiz_engine_get_results_returns_score_and_mistakes() -> None:
    """クイズ終了後に正答数と間違えた問題一覧を取得できることを確認する。"""
    questions = _make_questions(3)
    engine = QuizEngine()

    engine.start_quiz(questions=questions, is_random=False, limit=None)
    engine.submit_answer(choice_number=1)
    engine.submit_answer(choice_number=2)
    engine.submit_answer(choice_number=1)

    score, mistakes = engine.get_results()

    assert score == 2
    assert len(mistakes) == 1
    assert mistakes[0].number == 2
