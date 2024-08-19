import json
import random
from datetime import datetime
from typing import List, Dict, Union, Optional, Set
from database import get_connection
from question import Question
from case_study import CaseStudy
from exam_session import ExamSession
import logging
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set logging level to DEBUG for more detailed logs

class Quiz:
    def __init__(self, questions: List[Question], case_studies: Dict[str, CaseStudy], user_id: int, mode: str = "study"):
        self.all_questions: List[Question] = questions
        self.study_questions: List[Question] = questions.copy()
        self.exam_practice_questions: List[Question] = []
        self.case_studies: Dict[str, CaseStudy] = case_studies
        self.user_id: int = user_id
        self.mode: str = mode
        self.current_index: int = 0
        self.score: int = 0
        self.user_answers: Dict[str, Union[List[str], None]] = {}
        self.exam_session: Optional[ExamSession] = None
        self.practiced_questions: Dict[str, int] = {}
        self.incorrect_answers: Set[str] = set()
        self.review_list: Set[str] = set()
        self.algorithm_performance: Dict[str, int] = {
            'total_questions_presented': 0,
            'unique_questions_presented': 0,
            'questions_until_full_coverage': 0
        }
        self.load_progress()
        self.set_mode(self.mode)  # Ensure correct initialization based on mode
        logger.info(f"Quiz initialized. Mode: {self.mode}, Current questions: {len(self.get_current_question_set())}")

    def start_exam(self, config):
        logger.info(f"Starting new exam with config: {config.__dict__}")
        self.set_mode("exam practice")
        num_questions = min(config.exam_questions, len(self.all_questions))
        logger.info(f"Selecting {num_questions} questions for the new exam")
        
        # Always select new questions for a new exam
        self.exam_practice_questions = self._select_questions(num_questions)
        
        if not self.exam_practice_questions:
            logger.error("No questions were selected for the exam")
            return False

        self.current_index = 0
        self.score = 0
        self.user_answers = {}

        self.exam_session = ExamSession(
            user_id=self.user_id,
            start_time=datetime.now(),
            end_time=None,
            score=0,
            total_questions=len(self.exam_practice_questions),
            is_completed=False,
            practiced_questions=json.dumps(self.practiced_questions),
            incorrect_answers=list(self.incorrect_answers),
            review_list=list(self.review_list)
        )
        self.exam_session.save()
        self.save_progress()
        logger.info(f"New exam started with {len(self.exam_practice_questions)} questions: {[q.id for q in self.exam_practice_questions]}")
        return True

    def _select_questions(self, num_questions: int) -> List[Question]:
        logger.info(f"Selecting {num_questions} new questions")
        all_questions = list(self.all_questions)
        logger.info(f"Total questions available: {len(all_questions)}")
        
        if not all_questions:
            logger.error("No questions available to select from")
            return []
        
        random.shuffle(all_questions)  # Shuffle the questions first
        
        # Calculate weights for each question
        weights = []
        for q in all_questions:
            practice_count = self.practiced_questions.get(q.id, 0)
            if practice_count == 0:
                # Significant boost for unpracticed questions
                weight = 10.0
            else:
                # Reduce weight for practiced questions, but maintain some chance
                weight = max(0.5, 1 - (practice_count * 0.1))
            
            weights.append(weight)
        
        logger.info(f"Weights calculated: {weights}")
        
        # Ensure weights are not all zero
        if all(w == 0 for w in weights):
            logger.warning("All weights are zero. Setting equal weights.")
            weights = [1] * len(all_questions)
        
        # Select questions based on weights
        selected = random.choices(all_questions, weights=weights, k=min(num_questions, len(all_questions)))
        
        # Update algorithm performance metrics
        self.algorithm_performance['total_questions_presented'] += len(selected)
        self.algorithm_performance['unique_questions_presented'] = len(set(self.practiced_questions.keys()).union(set(q.id for q in selected)))
        if len(set(self.practiced_questions.keys()).union(set(q.id for q in selected))) == len(all_questions):
            self.algorithm_performance['questions_until_full_coverage'] = self.algorithm_performance['total_questions_presented']
        
        logger.info(f"Algorithm performance after selection: {self.algorithm_performance}")
        logger.info(f"Selected {len(selected)} new questions: {[q.id for q in selected]}")
        return selected

    def pause_exam(self):
        if self.exam_session:
            self.exam_session.end_time = datetime.now()
            self.exam_session.update()
            self.save_progress()
            self.save_algorithm_performance()
            logger.info("Exam paused")

    def resume_exam(self):
        if self.exam_session:
            self.exam_session.end_time = None
            self.exam_session.update()
            logger.info("Exam resumed")

    def finish_exam(self):
        if self.exam_session:
            self.exam_session.end_time = datetime.now()
            self.exam_session.score = self.score
            self.exam_session.is_completed = True
            self.exam_session.update()
        self.save_progress()
        self.save_algorithm_performance()
        self.set_mode("study")
        logger.info(f"Exam finished. Final score: {self.score}")

    def get_current_question_set(self) -> List[Question]:
        return self.exam_practice_questions if self.mode == "exam practice" else self.study_questions

    def get_current_question(self) -> Optional[Question]:
        questions = self.get_current_question_set()
        if questions and 0 <= self.current_index < len(questions):
            return questions[self.current_index]
        logger.warning(f"No question found at index {self.current_index}. Total questions: {len(questions)}")
        return None

    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        for question in self.all_questions:
            if question.id == question_id:
                return question
        return None

    def check_answer(self, user_answers: Union[List[str], None]) -> bool:
        current_question = self.get_current_question()
        if not current_question:
            logger.error("No current question available to check answer")
            return False
        
        is_correct = current_question.check_answer(user_answers)
        
        if is_correct:
            self.score += 1
            if current_question.id in self.incorrect_answers:
                self.incorrect_answers.remove(current_question.id)
        else:
            self.incorrect_answers.add(current_question.id)
        
        self.practiced_questions[current_question.id] = self.practiced_questions.get(current_question.id, 0) + 1
        self.user_answers[current_question.id] = user_answers
        self.save_progress()
        self.save_algorithm_performance()
        logger.info(f"Answer checked for question {current_question.id}. Is correct: {is_correct}. Current score: {self.score}")
        return is_correct

    def go_to_question(self, index: int):
        questions = self.get_current_question_set()
        logger.info(f"Attempting to go to question at index {index}. Current mode: {self.mode}, Total questions: {len(questions)}")
        logger.info(f"Current questions: {[q.id for q in questions]}")
        if 0 <= index < len(questions):
            self.current_index = index
            self.save_progress()
            logger.info(f"Moved to question at index {index}")
        else:
            logger.error(f"Invalid question index: {index}")

    def mark_for_review(self, question_id: str):
        self.review_list.add(question_id)
        self.save_progress()
        logger.info(f"Question {question_id} marked for review")

    def remove_from_review(self, question_id: str):
        if question_id in self.review_list:
            self.review_list.remove(question_id)
            self.save_progress()
            logger.info(f"Question {question_id} removed from review")

    def save_progress(self):
        logger.info("Saving progress")
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO user_progress 
                        (user_id, current_index, score, user_answers, mode, practiced_questions, incorrect_answers, review_list, algorithm_performance, current_exam_questions) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id, mode) DO UPDATE
                        SET current_index = EXCLUDED.current_index,
                            score = EXCLUDED.score,
                            user_answers = EXCLUDED.user_answers,
                            practiced_questions = EXCLUDED.practiced_questions,
                            incorrect_answers = EXCLUDED.incorrect_answers,
                            review_list = EXCLUDED.review_list,
                            algorithm_performance = EXCLUDED.algorithm_performance,
                            current_exam_questions = EXCLUDED.current_exam_questions
                    ''', (self.user_id, self.current_index, self.score, json.dumps(self.user_answers), self.mode,
                          json.dumps(self.practiced_questions), json.dumps(list(self.incorrect_answers)),
                          json.dumps(list(self.review_list)), json.dumps(self.algorithm_performance),
                          json.dumps([q.id for q in self.exam_practice_questions])))
            logger.info(f"Progress saved successfully. Mode: {self.mode}, Current exam questions: {[q.id for q in self.exam_practice_questions]}")
        except Exception as e:
            logger.error(f"Error saving progress: {str(e)}")

    def load_progress(self):
        logger.info(f"Loading progress for user {self.user_id}")
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT * FROM user_progress WHERE user_id = %s', (self.user_id,))
                    progress = cursor.fetchone()
                    if progress:
                        self.mode = progress['mode']
                        self.current_index = progress['current_index'] if progress['current_index'] is not None else 0
                        self.score = progress['score'] if progress['score'] is not None else 0
                        
                        # Handle current_exam_questions
                        current_exam_question_ids = progress['current_exam_questions']
                        if isinstance(current_exam_question_ids, str):
                            try:
                                current_exam_question_ids = json.loads(current_exam_question_ids)
                            except json.JSONDecodeError:
                                logger.error(f"Failed to decode current_exam_questions: {current_exam_question_ids}")
                                current_exam_question_ids = []
                        elif isinstance(current_exam_question_ids, list):
                            pass  # It's already a list, no need to decode
                        else:
                            logger.warning(f"Unexpected type for current_exam_questions: {type(current_exam_question_ids)}")
                            current_exam_question_ids = []
                        
                        self.exam_practice_questions = [q for q in self.all_questions if q.id in current_exam_question_ids]
                        
                        # Load other fields
                        self.user_answers = json.loads(progress['user_answers']) if progress['user_answers'] else {}
                        self.practiced_questions = json.loads(progress['practiced_questions']) if progress['practiced_questions'] else {}
                        self.incorrect_answers = set(json.loads(progress['incorrect_answers'])) if progress['incorrect_answers'] else set()
                        self.review_list = set(json.loads(progress['review_list'])) if progress['review_list'] else set()
                        self.algorithm_performance = json.loads(progress['algorithm_performance']) if progress['algorithm_performance'] else {
                            'total_questions_presented': 0,
                            'unique_questions_presented': 0,
                            'questions_until_full_coverage': 0
                        }

                        logger.info(f"Progress loaded. Mode: {self.mode}, Questions: {len(self.get_current_question_set())}")
                    else:
                        logger.info("No progress data found, initializing with default values")
                        self.exam_practice_questions = []
                        self.user_answers = {}
                        self.practiced_questions = {}
                        self.incorrect_answers = set()
                        self.review_list = set()
                        self.algorithm_performance = {
                            'total_questions_presented': 0,
                            'unique_questions_presented': 0,
                            'questions_until_full_coverage': 0
                        }
            logger.info(f"Progress loading completed. Mode: {self.mode}, Current questions: {len(self.get_current_question_set())}")
        except Exception as e:
            logger.error(f"Error loading progress: {str(e)}")
            logger.error(traceback.format_exc())
            # Initialize with default values in case of error
            self.exam_practice_questions = []
            self.user_answers = {}
            self.practiced_questions = {}
            self.incorrect_answers = set()
            self.review_list = set()
            self.algorithm_performance = {
                'total_questions_presented': 0,
                'unique_questions_presented': 0,
                'questions_until_full_coverage': 0
            }

    def save_algorithm_performance(self):
        logger.info(f"Saving algorithm performance: {self.algorithm_performance}")
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO algorithm_performance 
                        (user_id, total_questions_presented, unique_questions_presented, questions_until_full_coverage, timestamp) 
                        VALUES (%s, %s, %s, %s, %s)
                    ''', (self.user_id, self.algorithm_performance['total_questions_presented'],
                          self.algorithm_performance['unique_questions_presented'],
                          self.algorithm_performance['questions_until_full_coverage'],
                          datetime.now()))
            logger.info("Algorithm performance saved successfully")
        except Exception as e:
            logger.error(f"Error saving algorithm performance: {str(e)}")

    def reset_tracking(self):
        logger.info("Resetting tracking")
        self.practiced_questions = {}
        self.incorrect_answers = set()
        self.review_list = set()
        self.algorithm_performance = {
            'total_questions_presented': 0,
            'unique_questions_presented': 0,
            'questions_until_full_coverage': 0
        }
        self.save_progress()
        self.save_algorithm_performance()
        logger.info("Tracking reset completed")

    def clear_exam_progress(self):
        logger.info("Clearing exam progress")
        self.exam_practice_questions = []
        self.current_index = 0
        self.score = 0
        self.user_answers = {}
        self.save_progress()
        logger.info("Exam progress cleared")

    def get_algorithm_performance(self):
        return self.algorithm_performance

    def get_total_questions(self):
        return len(self.get_current_question_set())

    def get_current_score(self):
        total_questions = self.get_total_questions()
        return f"{self.score}/{total_questions}"

    def set_mode(self, new_mode: str):
        logger.info(f"Setting mode from {self.mode} to {new_mode}")
        self.mode = new_mode
        if new_mode == "study":
            self.current_index = 0
        elif new_mode == "exam practice":
            if not self.exam_practice_questions:
                self.clear_exam_progress()
                # Select questions for exam practice mode
                num_questions = min(20, len(self.all_questions))  # Default to 20 questions or less if not enough questions
                self.exam_practice_questions = self._select_questions(num_questions)
            self.current_index = 0
        self.save_progress()
        logger.info(f"Mode set to {self.mode}, Current questions: {len(self.get_current_question_set())}")