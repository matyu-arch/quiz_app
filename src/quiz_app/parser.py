"""データ解析層 (Data Layer)。

Markdownファイルの読み込みと構造化データへの変換を担当する。
Streamlitには一切依存しない。
"""

import re
import unicodedata
from dataclasses import dataclass, field, replace
from pathlib import Path


class QuizParseError(Exception):
    """クイズ用Markdownの解析に失敗したことを表す例外。"""


@dataclass(frozen=True)
class Choice:
    """選択肢を表す不変データクラス。"""

    number: int
    text: str


@dataclass(frozen=True)
class Question:
    """問題を表す不変データクラス。"""

    number: int
    text: str
    choices: tuple[Choice, ...] = field(default_factory=tuple)
    correct_number: int = 0
    explanation: str = ""

    def __post_init__(self) -> None:
        """入力された選択肢を不変のタプルへ正規化する。"""
        object.__setattr__(self, "choices", tuple(self.choices))


QUESTION_HEADER_PATTERN = re.compile(
    r"^###\s*(?:No\.|\N{FULLWIDTH LATIN CAPITAL LETTER N}o\.|"
    r"\N{FULLWIDTH LATIN CAPITAL LETTER N}\N{FULLWIDTH LATIN CAPITAL LETTER O}\.)"
    r"\s*(?P<number>\d+)",
    re.MULTILINE,
)
CHOICE_PATTERN = re.compile(
    r"^(?:-\s*)?(?P<number>\d+)\.\s*(?P<text>.+?)\s*$", re.MULTILINE
)
TABLE_CHOICE_PATTERN = re.compile(
    r"^\|\s*(?:[^|\n]*\|\s*)?(?P<number>\d+)\s*\|(?P<text>.+?)\|\s*$", re.MULTILINE
)
MARKDOWN_HEADING_PATTERN = re.compile(r"^#{1,6}\s+.+$")
BRACKET_HEADING_PATTERN = re.compile(r"^〈.+〉$")
THEMATIC_BREAK_PATTERN = re.compile(r"^(?:---+|\*\*\*+|___+)\s*$")
NUMBER_CHARS_PATTERN = r"0-9\uFF10-\uFF19"
ANSWER_NUMBER_PATTERN = re.compile(
    rf"^.*(?:正解|正答)[^\n]*?(?:\N{{FULLWIDTH COLON}}|:|は)\s*"
    rf"[^{NUMBER_CHARS_PATTERN}\n]*?(?P<number>[{NUMBER_CHARS_PATTERN}]+)"
    rf"[^{NUMBER_CHARS_PATTERN}\n]*.*$",
    re.MULTILINE,
)
ANSWER_NUMBER_IN_BOLD_PATTERN = re.compile(
    rf"^.*(?:正解|正答)[^\n]*?\*\*(?P<number>[{NUMBER_CHARS_PATTERN}]+)\*\*.*$",
    re.MULTILINE,
)
ANSWER_STANDALONE_NUMBER_PATTERN = re.compile(
    rf"^\*\*\s*(?:【\s*)?(?:選択肢\s*)?(?P<number>[{NUMBER_CHARS_PATTERN}]+)"
    rf"(?:\s*】)?(?:\s*\.\s*.*)?\*\*(?:.*)$",
    re.MULTILINE,
)
ANSWER_NUMBER_IN_BRACKETS_PATTERN = re.compile(
    rf"^.*【\s*(?P<number>[{NUMBER_CHARS_PATTERN}]+)\s*】.*正解.*$",
    re.MULTILINE,
)
INCORRECT_ANSWER_NUMBER_PATTERN = re.compile(
    rf"^.*誤っている(?:記述|もの|選択肢)?[^\n]*?(?:は|が)\s*"
    rf"[^{NUMBER_CHARS_PATTERN}\n]*?(?P<number>[{NUMBER_CHARS_PATTERN}]+)"
    rf"[^{NUMBER_CHARS_PATTERN}\n]*.*$",
    re.MULTILINE,
)
ANSWER_NUMBER_IN_EXPLANATION_PATTERN = re.compile(
    rf"^(?:\*+\s*)?\*\*(?:選択肢\s*)?(?P<number>[{NUMBER_CHARS_PATTERN}]+)\."
    r".*正解.*$",
    re.MULTILINE,
)
ANSWER_MARKER_PATTERN = re.compile(
    r"\*\*【正解(?:の選択肢)?】\*\*|##\s*正解の選択肢",
    re.MULTILINE,
)
IGNORED_EXPLANATION_LINE_PATTERN = re.compile(
    r"^(?:---+|###\s*【解答と解説】|##\s*正解の選択肢|###\s*詳細な解説)\s*$"
)


def parse_questions(md_text: str) -> list[Question]:
    """問題用Markdown文字列を Question の一覧へ変換する。"""
    questions: list[Question] = []
    matches = list(QUESTION_HEADER_PATTERN.finditer(md_text))

    for index, match in enumerate(matches):
        block_start = match.end()
        is_last_question = index == len(matches) - 1
        block_end = len(md_text) if is_last_question else matches[index + 1].start()
        question_block = md_text[block_start:block_end].strip()
        questions.append(
            Question(
                number=int(match.group("number")),
                text=_extract_question_text(question_block),
                choices=_extract_choices(question_block),
                correct_number=0,
                explanation="",
            )
        )

    return questions


def merge_answers(questions: list[Question], a_md_text: str) -> list[Question]:
    """解答用Markdown文字列を Question の一覧へ結合する。"""
    answers_by_number = _parse_answer_blocks(a_md_text)
    merged_questions: list[Question] = []

    for question in questions:
        correct_number, explanation = answers_by_number.get(question.number, (0, ""))
        merged_questions.append(
            replace(
                question,
                correct_number=correct_number,
                explanation=explanation,
            )
        )

    return merged_questions


def load_quiz_data(q_file_path: str, a_file_path: str) -> list[Question]:
    """QファイルとAファイルを読み込み、解答付きの問題一覧を返す。"""
    q_md_text = Path(q_file_path).read_text(encoding="utf-8")
    a_md_text = Path(a_file_path).read_text(encoding="utf-8")

    try:
        questions = parse_questions(q_md_text)
        if not questions:
            raise QuizParseError("問題用Markdownの形式が不正です。")

        if not QUESTION_HEADER_PATTERN.search(a_md_text):
            raise QuizParseError("解答用Markdownの形式が不正です。")

        merged_questions = merge_answers(questions, a_md_text)
        if not merged_questions:
            raise QuizParseError("問題データを結合できませんでした。")

        _validate_merged_questions(merged_questions)
    except QuizParseError:
        raise
    except Exception as exc:
        raise QuizParseError("クイズデータの解析に失敗しました。") from exc

    return merged_questions


def _extract_question_text(question_block: str) -> str:
    """問題ブロックから問題文を抽出する。"""
    lines: list[str] = []

    for line in question_block.splitlines():
        if CHOICE_PATTERN.match(line.strip()):
            break
        if TABLE_CHOICE_PATTERN.match(line.strip()):
            break
        lines.append(line.strip())

    # 末尾の空行を削除してから結合
    while lines and not lines[-1]:
        lines.pop()

    return "\n".join(lines)


def _extract_choices(question_block: str) -> list[Choice]:
    """問題ブロックから選択肢一覧を抽出する。"""
    choices = _extract_standard_choices(question_block)
    if not choices:
        choices = [
            Choice(number=int(match.group("number")), text=match.group("text").strip())
            for match in TABLE_CHOICE_PATTERN.finditer(question_block)
        ]
    return choices


def _extract_standard_choices(question_block: str) -> list[Choice]:
    """通常形式で記述された選択肢を、折り返し行も含めて抽出する。"""
    choices: list[Choice] = []
    current_number: int | None = None
    current_lines: list[str] = []

    for raw_line in question_block.splitlines():
        stripped_line = raw_line.strip()
        if not stripped_line:
            if current_number is not None and current_lines and current_lines[-1] != "":
                current_lines.append("")
            continue

        choice_match = CHOICE_PATTERN.match(stripped_line)
        if choice_match is not None:
            if current_number is not None:
                choices.append(
                    Choice(
                        number=current_number,
                        text=_join_choice_lines(current_lines),
                    )
                )
            current_number = int(choice_match.group("number"))
            current_lines = [choice_match.group("text").strip()]
            continue

        if current_number is None:
            continue

        if TABLE_CHOICE_PATTERN.match(stripped_line):
            break
        if MARKDOWN_HEADING_PATTERN.match(stripped_line):
            break
        if BRACKET_HEADING_PATTERN.match(stripped_line):
            break
        if THEMATIC_BREAK_PATTERN.match(stripped_line):
            break

        current_lines.append(stripped_line)

    if current_number is not None:
        choices.append(
            Choice(number=current_number, text=_join_choice_lines(current_lines))
        )

    return choices


def _join_choice_lines(lines: list[str]) -> str:
    """選択肢本文の行一覧を空行込みで自然な改行へ整形する。"""
    normalized_lines = list(lines)
    while normalized_lines and not normalized_lines[-1]:
        normalized_lines.pop()

    return "\n".join(normalized_lines)


def _parse_answer_blocks(a_md_text: str) -> dict[int, tuple[int, str]]:
    """解答用Markdown文字列を問題番号ごとの正解番号と解説へ変換する。"""
    answers_by_number: dict[int, tuple[int, str]] = {}
    matches = list(QUESTION_HEADER_PATTERN.finditer(a_md_text))

    for index, match in enumerate(matches):
        block_start = match.end()
        is_last_question = index == len(matches) - 1
        block_end = len(a_md_text) if is_last_question else matches[index + 1].start()
        answer_block = a_md_text[block_start:block_end].strip()
        question_number = int(match.group("number"))
        extracted_answer = _extract_answer_data(answer_block)
        current_answer = answers_by_number.get(question_number)
        if current_answer is None or (
            current_answer[0] == 0 and extracted_answer[0] != 0
        ):
            answers_by_number[question_number] = extracted_answer

    return answers_by_number


def _extract_answer_data(answer_block: str) -> tuple[int, str]:
    """問題ごとの解答ブロックから正解番号と解説を抽出する。"""
    answer_number, explanation_start = _extract_answer_number(answer_block)
    explanation = _extract_explanation(answer_block, explanation_start)
    return answer_number, explanation


def _extract_answer_number(answer_block: str) -> tuple[int, int]:
    """解答ブロックから正解番号とその位置を抽出する。"""
    inline_match = ANSWER_NUMBER_PATTERN.search(answer_block)
    if inline_match is not None:
        return _to_halfwidth_number(inline_match.group("number")), inline_match.end()

    inline_bold_match = ANSWER_NUMBER_IN_BOLD_PATTERN.search(answer_block)
    if inline_bold_match is not None:
        return (
            _to_halfwidth_number(inline_bold_match.group("number")),
            inline_bold_match.end(),
        )

    bracket_match = ANSWER_NUMBER_IN_BRACKETS_PATTERN.search(answer_block)
    if bracket_match is not None:
        return _to_halfwidth_number(bracket_match.group("number")), bracket_match.end()

    incorrect_match = INCORRECT_ANSWER_NUMBER_PATTERN.search(answer_block)
    if incorrect_match is not None:
        return (
            _to_halfwidth_number(incorrect_match.group("number")),
            incorrect_match.end(),
        )

    explanation_match = ANSWER_NUMBER_IN_EXPLANATION_PATTERN.search(answer_block)
    if explanation_match is not None:
        return (
            _to_halfwidth_number(explanation_match.group("number")),
            explanation_match.end(),
        )

    marker_match = ANSWER_MARKER_PATTERN.search(answer_block)
    if marker_match is not None:
        number_match = ANSWER_STANDALONE_NUMBER_PATTERN.search(
            answer_block,
            marker_match.end(),
        )
        if number_match is not None:
            return (
                _to_halfwidth_number(number_match.group("number")),
                number_match.end(),
            )

    standalone_match = ANSWER_STANDALONE_NUMBER_PATTERN.search(answer_block)
    if standalone_match is not None:
        return (
            _to_halfwidth_number(standalone_match.group("number")),
            standalone_match.end(),
        )

    return 0, 0


def _extract_explanation(answer_block: str, explanation_start: int) -> str:
    """解答ブロックから解説本文を抽出する。"""
    explanation_lines: list[str] = []

    for line in answer_block[explanation_start:].splitlines():
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if IGNORED_EXPLANATION_LINE_PATTERN.match(stripped_line):
            continue
        explanation_lines.append(stripped_line)

    return "\n".join(explanation_lines)


def _to_halfwidth_number(number_text: str) -> int:
    """全角数字を半角数字へ正規化して整数へ変換する。"""
    return int(unicodedata.normalize("NFKC", number_text))


def _validate_merged_questions(questions: list[Question]) -> None:
    """結合済み問題一覧の整合性を検証する。"""
    for question in questions:
        if question.correct_number == 0:
            raise QuizParseError(
                f"問題番号 {question.number} の正解番号を抽出できませんでした。"
            )

        choice_numbers = {choice.number for choice in question.choices}
        if question.correct_number not in choice_numbers:
            raise QuizParseError(
                f"問題番号 {question.number} の正解番号 {question.correct_number} "
                "は選択肢内に存在しません。"
            )
