"""ロジック・状態管理層 (Logic Layer)。

クイズの進行状態を管理する。UIへの表示方法は関知しない。
"""

import random

from quiz_app.parser import Question


class QuizEngine:
    """クイズの進行を管理するエンジン。

    問題の読み込み、シャッフル、出題数絞り込み、
    解答の記録、スコア計算を行う。
    """

    def __init__(self) -> None:
        """クイズの初期状態を作成する。"""
        self.questions: list[Question] = []
        self.mistakes: list[Question] = []
        self.current_index: int = 0
        self.score: int = 0

    def start_quiz(
        self,
        questions: list[Question],
        is_random: bool,
        limit: int | None,
    ) -> None:
        """問題一覧を読み込み、出題状態を初期化する。"""
        loaded_questions = list(questions)

        if is_random:
            random.shuffle(loaded_questions)

        if limit is not None:
            loaded_questions = loaded_questions[:limit]

        self.questions = loaded_questions
        self.mistakes = []
        self.current_index = 0
        self.score = 0

    def get_current_question(self) -> Question:
        """現在の問題を返す。"""
        if self.current_index >= len(self.questions):
            raise IndexError("すでに全問終了しています。")

        return self.questions[self.current_index]

    def submit_answer(self, choice_number: int) -> bool:
        """解答を送信して正誤判定し、次の問題へ進める。"""
        current_question = self.get_current_question()
        is_correct = current_question.correct_number == choice_number

        if is_correct:
            self.score += 1
        else:
            self.mistakes.append(current_question)

        self.current_index += 1
        return is_correct

    def get_results(self) -> tuple[int, list[Question]]:
        """現在のスコアと間違えた問題一覧を返す。"""
        return self.score, list(self.mistakes)
