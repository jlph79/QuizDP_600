import json
import random
import sqlite3
from datetime import datetime
from typing import List, Dict, Union, Optional, Set
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
        self.practiced_questions: Dict[str, int] = {}  # Question ID to practice count
        self.incorrect_answers: Set[str] = set()
        self.review_list: Set[str] = set()
        self.algorithm_performance: Dict[str, int] = {
            'total_questions_presented': 0,
            'unique_questions_presented': 0,
            'questions_until_full_coverage': 0
        }

    def start_exam(self, config):
        selected_questions = self._select_questions(config.exam_questions)
        self.questions = selected_questions
        self.exam_session = ExamSession(
            user_id=self.user_id,
            start_time=datetime.now(),
            end_time=None,
            score=0,
            total_questions=len(self.questions),
            is_completed=False,
            practiced_questions=json.dumps(self.practiced_questions),
            incorrect_answers=list(self.incorrect_answers),
            review_list=list(self.review_list)
        )
        self.exam_session.save()

    def _select_questions(self, num_questions: int) -> List[Question]:
        all_questions = set(self.questions)
        unpracticed_questions = all_questions - set(self.practiced_questions.keys())
        least_practiced_questions = sorted(self.practiced_questions.items(), key=lambda x: x[1])
        
        selected = []
        
        # Prioritize unpracticed questions (50%)
        unpracticed_count = min(int(num_questions * 0.5), len(unpracticed_questions))
        selected.extend(random.sample(list(unpracticed_questions), unpracticed_count))
        
        # Add least practiced questions (30%)
        least_practiced_count = min(int(num_questions * 0.3), len(least_practiced_questions))
        selected.extend([self.get_question_by_id(q[0]) for q in least_practiced_questions[:least_practiced_count]])
        
        # Add incorrect questions (10%)
        incorrect_questions = all_questions.intersection(self.incorrect_answers)
        incorrect_count = min(int(num_questions * 0.1), len(incorrect_questions))
        selected.extend(random.sample(list(incorrect_questions), incorrect_count))
        
        # Add review questions (10%)
        review_questions = all_questions.intersection(self.review_list)
        review_count = min(int(num_questions * 0.1), len(review_questions))
        selected.extend(random.sample(list(review_questions), review_count))
        
        # Fill the rest with random questions
        remaining_count = num_questions - len(selected)
        remaining_questions = list(all_questions - set(selected))
        selected.extend(random.sample(remaining_questions, remaining_count))
        
        # Update algorithm performance metrics
        self.algorithm_performance['total_questions_presented'] += len(selected)
        self.algorithm_performance['unique_questions_presented'] = len(set(self.practiced_questions.keys()).union(set(q.id for q in selected)))
        if len(set(self.practiced_questions.keys()).union(set(q.id for q in selected))) == len(all_questions):
            self.algorithm_performance['questions_until_full_coverage'] = self.algorithm_performance['total_questions_presented']
        
        return selected

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

    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        for question in self.questions:
            if question.id == question_id:
                return question
        return None

    def check_answer(self, user_answers: Union[List[str], None]) -> bool:
        current_question = self.get_current_question()
        is_correct = False
        if current_question.type == "multiple-choice":
            correct_answers = set(current_question.correct_answers)
            user_answer_set = set(ans[0] for ans in user_answers) if user_answers else set()
            is_correct = user_answer_set == correct_answers
        
        if is_correct:
            self.score += 1
            if current_question.id in self.incorrect_answers:
                self.incorrect_answers.remove(current_question.id)
        else:
            self.incorrect_answers.add(current_question.id)
        
        self.practiced_questions[current_question.id] = self.practiced_questions.get(current_question.id, 0) + 1
        self.user_answers[current_question.id] = user_answers
        self.save_progress()
        return is_correct

    def go_to_question(self, index: int):
        if 0 <= index < len(self.questions):
            self.current_index = index
            self.save_progress()

    def mark_for_review(self, question_id: str):
        self.review_list.add(question_id)
        self.save_progress()

    def remove_from_review(self, question_id: str):
        if question_id in self.review_list:
            self.review_list.remove(question_id)
            self.save_progress()

    def save_progress(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_progress 
                (user_id, current_index, score, user_answers, mode, practiced_questions, incorrect_answers, review_list, algorithm_performance) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.user_id, self.current_index, self.score, json.dumps(self.user_answers), self.mode,
                  json.dumps(self.practiced_questions), json.dumps(list(self.incorrect_answers)),
                  json.dumps(list(self.review_list)), json.dumps(self.algorithm_performance)))

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
                    quiz.practiced_questions = json.loads(progress[5]) if progress[5] else {}
                    quiz.incorrect_answers = set(json.loads(progress[6])) if progress[6] else set()
                    quiz.review_list = set(json.loads(progress[7])) if progress[7] else set()
                    quiz.algorithm_performance = json.loads(progress[8]) if progress[8] else {
                        'total_questions_presented': 0,
                        'unique_questions_presented': 0,
                        'questions_until_full_coverage': 0
                    }
                except json.JSONDecodeError:
                    quiz.user_answers = {}
                    quiz.practiced_questions = {}
                    quiz.incorrect_answers = set()
                    quiz.review_list = set()
                    quiz.algorithm_performance = {
                        'total_questions_presented': 0,
                        'unique_questions_presented': 0,
                        'questions_until_full_coverage': 0
                    }
        return quiz

    def reset_tracking(self):
        self.practiced_questions = {}
        self.incorrect_answers = set()
        self.review_list = set()
        self.algorithm_performance = {
            'total_questions_presented': 0,
            'unique_questions_presented': 0,
            'questions_until_full_coverage': 0
        }
        self.save_progress()

    def get_algorithm_performance(self):
        return self.algorithm_performance