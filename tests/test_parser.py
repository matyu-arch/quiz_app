"""parser モジュールの RED テスト。"""

from dataclasses import is_dataclass
from pathlib import Path

import pytest

from quiz_app.parser import (
    Choice,
    Question,
    QuizParseError,
    load_quiz_data,
    merge_answers,
    parse_questions,
)


def test_choice_dataclass_init() -> None:
    """Choice が number/text を保持して初期化されることを確認する。"""
    choice = Choice(number=1, text="選択肢A")

    assert is_dataclass(Choice)
    assert choice.number == 1
    assert choice.text == "選択肢A"


def test_question_dataclass_init() -> None:
    """Question が必要な属性を保持して初期化されることを確認する。"""
    question = Question(
        number=10,
        text="次のうち正しいものを選べ。",
        choices=[
            Choice(number=1, text="選択肢1"),
            Choice(number=2, text="選択肢2"),
            Choice(number=3, text="選択肢3"),
        ],
        correct_number=2,
        explanation="正解は2です。",
    )

    assert is_dataclass(Question)
    assert question.number == 10
    assert question.text == "次のうち正しいものを選べ。"
    assert [choice.number for choice in question.choices] == [1, 2, 3]
    assert question.correct_number == 2
    assert question.explanation == "正解は2です。"


def test_parse_questions_returns_question_list_from_markdown() -> None:
    """問題用Markdownから Question の一覧を生成できることを確認する。"""
    md_text = """
### No. 1
Pythonで可変長のデータ列を保持する代表的な型はどれですか。

- 1. list
- 2. int
- 3. float

### No. 2
次のうち、Webアプリのフレームワークをすべて選ぶ問題ではありません。最も適切なものを1つ選んでください。

- 1. Streamlit
- 2. FastAPI
- 3. Django
- 4. PostgreSQL
""".strip()

    questions = parse_questions(md_text)

    assert len(questions) == 2

    first_question = questions[0]
    assert isinstance(first_question, Question)
    assert first_question.number == 1
    assert (
        first_question.text
        == "Pythonで可変長のデータ列を保持する代表的な型はどれですか。"
    )
    assert len(first_question.choices) == 3
    assert first_question.choices == (
        Choice(number=1, text="list"),
        Choice(number=2, text="int"),
        Choice(number=3, text="float"),
    )
    assert first_question.correct_number == 0
    assert first_question.explanation == ""

    second_question = questions[1]
    assert isinstance(second_question, Question)
    assert second_question.number == 2
    assert (
        second_question.text
        == "次のうち、Webアプリのフレームワークをすべて選ぶ問題ではありません。"
        "最も適切なものを1つ選んでください。"
    )
    assert len(second_question.choices) == 4
    assert second_question.choices == (
        Choice(number=1, text="Streamlit"),
        Choice(number=2, text="FastAPI"),
        Choice(number=3, text="Django"),
        Choice(number=4, text="PostgreSQL"),
    )
    assert second_question.correct_number == 0
    assert second_question.explanation == ""


def test_merge_answers_returns_new_questions_with_answers_and_explanations() -> None:
    """解答用Markdownを Question 一覧へ結合して新しい一覧を返すことを確認する。"""
    questions = [
        Question(
            number=1,
            text="Pythonで可変長のデータ列を保持する代表的な型はどれですか。",
            choices=[
                Choice(number=1, text="tuple"),
                Choice(number=2, text="list"),
                Choice(number=3, text="int"),
            ],
            correct_number=0,
            explanation="",
        ),
        Question(
            number=2,
            text="次のうち誤っている記述を1つ選んでください。",
            choices=[
                Choice(number=1, text="StreamlitはPythonでUIを構築できる。"),
                Choice(number=2, text="FastAPIはWeb API構築に使える。"),
                Choice(number=3, text="DjangoはWebフレームワークである。"),
                Choice(number=4, text="PostgreSQLはPythonのWebフレームワークである。"),
            ],
            correct_number=0,
            explanation="",
        ),
    ]
    a_md_text = (
        "### \N{FULLWIDTH LATIN CAPITAL LETTER N}o. 1\n"
        "**正解\N{FULLWIDTH COLON}2**\n\n"
        "list は要素の追加や削除ができる可変長のシーケンスです。\n\n"
        "### \N{FULLWIDTH LATIN CAPITAL LETTER N}o. 2\n"
        "**正解\N{FULLWIDTH LEFT PARENTHESIS}誤っている記述"
        "\N{FULLWIDTH RIGHT PARENTHESIS}は 4 です。**\n\n"
        "PostgreSQL はリレーショナルデータベース管理システムであり、\n"
        "Webフレームワークではありません。"
    )

    merged_questions = merge_answers(questions, a_md_text)

    assert merged_questions is not questions
    assert len(merged_questions) == 2

    assert questions[0].correct_number == 0
    assert questions[0].explanation == ""
    assert questions[1].correct_number == 0
    assert questions[1].explanation == ""

    first_question = merged_questions[0]
    assert first_question is not questions[0]
    assert first_question.number == 1
    assert first_question.choices == questions[0].choices
    assert first_question.correct_number == 2
    assert (
        first_question.explanation
        == "list は要素の追加や削除ができる可変長のシーケンスです。"
    )

    second_question = merged_questions[1]
    assert second_question is not questions[1]
    assert second_question.number == 2
    assert second_question.choices == questions[1].choices
    assert second_question.correct_number == 4
    assert (
        second_question.explanation
        == "PostgreSQL はリレーショナルデータベース管理システムであり、\n"
        "Webフレームワークではありません。"
    )


def test_load_quiz_data_raises_file_not_found_for_missing_files() -> None:
    """存在しないファイルパスを渡すと FileNotFoundError が送出されることを確認する。"""
    with pytest.raises(FileNotFoundError):
        load_quiz_data("md/not_found_q.md", "md/not_found_a.md")


def test_load_quiz_data_raises_parse_error_for_invalid_markdown_format(
    tmp_path: Path,
) -> None:
    """見出しのない不正なMarkdownを渡すと QuizParseError が送出されることを確認する。"""
    q_file_path = tmp_path / "invalid_q.md"
    a_file_path = tmp_path / "invalid_a.md"

    q_file_path.write_text(
        "これは問題Markdownではありません。\n見出しも選択肢も含まれていません。\n",
        encoding="utf-8",
    )
    a_file_path.write_text(
        "これは解答Markdownではありません。\n正解番号も問題見出しもありません。\n",
        encoding="utf-8",
    )

    with pytest.raises(QuizParseError):
        load_quiz_data(str(q_file_path), str(a_file_path))
