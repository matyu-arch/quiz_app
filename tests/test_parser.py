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


def test_parse_questions_handles_choices_without_dash_prefix() -> None:
    """実データ形式 (`- ` プレフィックスなし) の選択肢もパースできることを確認する。"""
    md_text = """\
### \N{FULLWIDTH LATIN CAPITAL LETTER N}o.1
次の記述のうち、誤っているものはどれか。
1. 選択肢Aの内容です。
2. 選択肢Bの内容です。
3. 選択肢Cの内容です。
4. 選択肢Dの内容です。
""".strip()

    questions = parse_questions(md_text)

    assert len(questions) == 1

    question = questions[0]
    assert question.number == 1
    assert question.text == "次の記述のうち、誤っているものはどれか。"
    assert len(question.choices) == 4
    assert question.choices == (
        Choice(number=1, text="選択肢Aの内容です。"),
        Choice(number=2, text="選択肢Bの内容です。"),
        Choice(number=3, text="選択肢Cの内容です。"),
        Choice(number=4, text="選択肢Dの内容です。"),
    )


def test_parse_questions_table_format():
    """表形式で記述された選択肢が正しく抽出されること。"""
    md_text = """### No.1
表形式の選択肢テスト

| 選択肢 | 建築物の部分 |
|---|---|
| 1 | 木造 |
| 2 | 鉄骨 |
"""
    questions = parse_questions(md_text)
    assert len(questions) == 1

    q = questions[0]
    assert q.number == 1
    assert "表形式の選択肢テスト\n\n| 選択肢 | 建築物の部分 |\n|---|---|" in q.text
    assert len(q.choices) == 2
    assert q.choices[0] == Choice(number=1, text="木造")
    assert q.choices[1] == Choice(number=2, text="鉄骨")


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


def test_merge_answers_extracts_answer_number_from_real_data_style() -> None:
    """実データの「正解の選択肢は **4** です。」形式を抽出できることを確認する。"""
    questions = [
        Question(
            number=1,
            text="問題文",
            choices=[
                Choice(number=1, text="A"),
                Choice(number=2, text="B"),
                Choice(number=3, text="C"),
                Choice(number=4, text="D"),
            ],
            correct_number=0,
            explanation="",
        )
    ]
    a_md_text = """\
### No.1
正解の選択肢は **4** です。

以下に詳細な解説を示します。
""".strip()

    merged_questions = merge_answers(questions, a_md_text)

    assert merged_questions[0].correct_number == 4
    assert "以下に詳細な解説を示します。" in merged_questions[0].explanation


def test_load_quiz_data_raises_parse_error_when_answer_number_is_missing(
    tmp_path: Path,
) -> None:
    """正解番号を抽出できない解答データは QuizParseError にする。"""
    q_file_path = tmp_path / "valid_q.md"
    a_file_path = tmp_path / "invalid_answer_missing.md"

    q_file_path.write_text(
        """\
### No.1
問題文

1. A
2. B
3. C
4. D
""",
        encoding="utf-8",
    )
    a_file_path.write_text(
        """\
### No.1
このブロックには正解番号が含まれていません。
""",
        encoding="utf-8",
    )

    with pytest.raises(QuizParseError, match="正解番号"):
        load_quiz_data(str(q_file_path), str(a_file_path))


def test_load_quiz_data_raises_parse_error_when_answer_number_is_not_in_choices(
    tmp_path: Path,
) -> None:
    """選択肢に存在しない正解番号は QuizParseError にする。"""
    q_file_path = tmp_path / "valid_q.md"
    a_file_path = tmp_path / "invalid_answer_out_of_range.md"

    q_file_path.write_text(
        """\
### No.1
問題文

1. A
2. B
3. C
4. D
""",
        encoding="utf-8",
    )
    a_file_path.write_text(
        """\
### No.1
**正解: 9**
""",
        encoding="utf-8",
    )

    with pytest.raises(QuizParseError, match="存在しません"):
        load_quiz_data(str(q_file_path), str(a_file_path))


def test_merge_answers_extracts_answer_number_after_correct_marker() -> None:
    """【正解】見出しの次に来る太字選択肢から正解番号を抽出できることを確認する。"""
    questions = [
        Question(
            number=1,
            text="問題文",
            choices=[
                Choice(number=1, text="A"),
                Choice(number=2, text="B"),
                Choice(number=3, text="C"),
                Choice(number=4, text="D"),
            ],
            correct_number=0,
            explanation="",
        )
    ]
    a_md_text = """\
### No.1
**【正解】**
**4. D**(誤っている記述)

### 詳細な解説
解説本文
""".strip()

    merged_questions = merge_answers(questions, a_md_text)

    assert merged_questions[0].correct_number == 4
    assert merged_questions[0].explanation == "解説本文"


def test_merge_answers_extracts_fullwidth_number_inside_quotes() -> None:
    """「4」のように引用符付きの全角数字でも正解番号を抽出できることを確認する。"""
    questions = [
        Question(
            number=1,
            text="問題文",
            choices=[
                Choice(number=1, text="A"),
                Choice(number=2, text="B"),
                Choice(number=3, text="C"),
                Choice(number=4, text="D"),
            ],
            correct_number=0,
            explanation="",
        )
    ]
    a_md_text = """\
### No.1
**正解は「\N{FULLWIDTH DIGIT FOUR}」です。**

解説本文
""".strip()

    merged_questions = merge_answers(questions, a_md_text)

    assert merged_questions[0].correct_number == 4
    assert merged_questions[0].explanation == "解説本文"


def test_merge_answers_extracts_number_from_bracketed_bold_answer() -> None:
    """【 1 】形式の太字回答から正解番号を抽出できることを確認する。"""
    questions = [
        Question(
            number=1,
            text="問題文",
            choices=[
                Choice(number=1, text="A"),
                Choice(number=2, text="B"),
            ],
            correct_number=0,
            explanation="",
        )
    ]
    a_md_text = """\
### No.1
**【 1 】** が正解です。

解説本文
""".strip()

    merged_questions = merge_answers(questions, a_md_text)

    assert merged_questions[0].correct_number == 1


def test_merge_answers_extracts_number_from_incorrect_statement_style() -> None:
    """「誤っている選択肢は **1** です」形式を抽出できることを確認する。"""
    questions = [
        Question(
            number=1,
            text="問題文",
            choices=[
                Choice(number=1, text="A"),
                Choice(number=2, text="B"),
            ],
            correct_number=0,
            explanation="",
        )
    ]
    a_md_text = """\
### No.1
誤っている選択肢は **1** です。

解説本文
""".strip()

    merged_questions = merge_answers(questions, a_md_text)

    assert merged_questions[0].correct_number == 1


def test_merge_answers_extracts_number_from_explanation_line_marked_correct() -> None:
    """解説中の「5. ...(正解)」形式から正解番号を抽出できることを確認する。"""
    questions = [
        Question(
            number=1,
            text="問題文",
            choices=[Choice(number=index, text=str(index)) for index in range(1, 6)],
            correct_number=0,
            explanation="",
        )
    ]
    a_md_text = """\
### No.1
### 【解説】
*   **5. 建築できない(正解)**
解説本文
""".strip()

    merged_questions = merge_answers(questions, a_md_text)

    assert merged_questions[0].correct_number == 5


def test_merge_answers_keeps_first_valid_answer_when_duplicate_headers_exist() -> None:
    """同一問題番号が重複した場合は先に得られた有効な答えを優先する。"""
    questions = [
        Question(
            number=1,
            text="問題文",
            choices=[
                Choice(number=1, text="A"),
                Choice(number=2, text="B"),
            ],
            correct_number=0,
            explanation="",
        )
    ]
    a_md_text = """\
### No.1
**正解:2**

最初の解説

### No.1
答えが欠けた重複ブロック
""".strip()

    merged_questions = merge_answers(questions, a_md_text)

    assert merged_questions[0].correct_number == 2
    assert "最初の解説" in merged_questions[0].explanation
