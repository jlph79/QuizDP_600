import json
import random
import sqlite3
from datetime import datetime
from typing import List, Dict, Union, Optional
from database import DB_PATH
from question import Question
from case_study import CaseStudy
from exam_session import ExamSession

class Quiz:
    def __init__(self, questions: List[Question], case_studies: Dict[str, CaseStudy], user_id: int, mode: str = "study"):
        self.questions: List[Question] = questions
        self.case_studies: Dict[str, CaseStudy] = case_studies
        self.user_id: int = user_id
        self.mode: str = mode
        self.current_index: int = 0
        self.score: int = 0
        self.user_answers: Dict[str, Union[List[str], None]] = {}
        self.exam_session: Optional[ExamSession] = None

    def start_exam(self, config):
        self.questions = random.sample(self.questions, config.exam_questions)
        self.exam_session = ExamSession(
            user_id=self.user_id,
            start_time=datetime.now(),
            end_time=None,
            score=0,
            total_questions=len(self.questions),
            is_completed=False
        )
        self.exam_session.save()

    def pause_exam(self):
        if self.exam_session:
            self.exam_session.end_time = datetime.now()
            self.exam_session.update()

    def resume_exam(self):
        if self.exam_session:
            self.exam_session.end_time = None
            self.exam_session.update()

    def finish_exam(self):
        if self.exam_session:
            self.exam_session.end_time = datetime.now()
            self.exam_session.score = self.score
            self.exam_session.is_completed = True
            self.exam_session.update()

    def get_current_question(self) -> Question:
        return self.questions[self.current_index]

    def check_answer(self, user_answers: Union[List[str], None]) -> bool:
        current_question = self.get_current_question()
        is_correct = False
        if current_question.type == "multiple-choice":
            correct_answers = set(current_question.correct_answers)
            user_answer_set = set(ans[0] for ans in user_answers) if user_answers else set()
            is_correct = user_answer_set == correct_answers
        
        if is_correct:
            self.score += 1
        self.user_answers[current_question.id] = user_answers
        self.save_progress()
        return is_correct

    def go_to_question(self, index: int):
        if 0 <= index < len(self.questions):
            self.current_index = index
            self.save_progress()

    def save_progress(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_progress 
                (user_id, current_index, score, user_answers, mode) 
                VALUES (?, ?, ?, ?, ?)
            ''', (self.user_id, self.current_index, self.score, json.dumps(self.user_answers), self.mode))

    @classmethod
    def load_progress(cls, questions, case_studies, user_id, mode):
        quiz = cls(questions, case_studies, user_id, mode)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_progress WHERE user_id = ? AND mode = ?', (user_id, mode))
            progress = cursor.fetchone()
            if progress:
                quiz.current_index = int(progress[2]) if progress[2] and not isinstance(progress[2], dict) else 0
                if progress[3] and isinstance(progress[3], str):
                    try:
                        quiz.score = len(json.loads(progress[3]))
                    except json.JSONDecodeError:
                        quiz.score = 0
                else:
                    quiz.score = int(progress[3]) if progress[3] else 0
                try:
                    quiz.user_answers = json.loads(progress[4]) if progress[4] else {}
                except json.JSONDecodeError:
                    quiz.user_answers = {}
        return quiz