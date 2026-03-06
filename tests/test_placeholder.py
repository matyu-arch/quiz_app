"""プレースホルダテスト。pytest動作確認用。"""

from quiz_app.parser import Choice, Question


def test_choice_creation() -> None:
    """Choiceデータクラスが正しく生成されることを確認する。"""
    choice = Choice(number=1, text="テスト選択肢")
    assert choice.number == 1
    assert choice.text == "テスト選択肢"


def test_question_creation() -> None:
    """Questionデータクラスが正しく生成されることを確認する。"""
    question = Question(
        number=1,
        text="テスト問題",
        choices=[
            Choice(number=1, text="選択肢1"),
            Choice(number=2, text="選択肢2"),
        ],
        correct_number=1,
        explanation="テスト解説",
    )
    assert question.number == 1
    assert len(question.choices) == 2
    assert question.correct_number == 1
