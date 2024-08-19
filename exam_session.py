import json
from datetime import datetime
from database import get_connection
import logging
import traceback

logger = logging.getLogger(__name__)

class ExamSession:
    def __init__(self, user_id, start_time, end_time, score, total_questions, is_completed, practiced_questions, incorrect_answers, review_list, id=None):
        self.id = id
        self.user_id = user_id
        self.start_time = start_time
        self.end_time = end_time
        self.score = score
        self.total_questions = total_questions
        self.is_completed = is_completed
        self.practiced_questions = practiced_questions
        self.incorrect_answers = incorrect_answers
        self.review_list = review_list

    def save(self):
        logger.info("Saving exam session")
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO exam_sessions 
                        (user_id, start_time, end_time, score, total_questions, is_completed, practiced_questions, incorrect_answers, review_list)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE
                        SET user_id = EXCLUDED.user_id,
                            start_time = EXCLUDED.start_time,
                            end_time = EXCLUDED.end_time,
                            score = EXCLUDED.score,
                            total_questions = EXCLUDED.total_questions,
                            is_completed = EXCLUDED.is_completed,
                            practiced_questions = EXCLUDED.practiced_questions,
                            incorrect_answers = EXCLUDED.incorrect_answers,
                            review_list = EXCLUDED.review_list
                        RETURNING id
                    ''', (self.user_id, self.start_time, self.end_time, self.score, self.total_questions, self.is_completed,
                          self.practiced_questions, json.dumps(self.incorrect_answers), json.dumps(self.review_list)))
                    self.id = cursor.fetchone()['id']
                    logger.info(f"Exam session saved with ID: {self.id}")
                    return self.id
        except Exception as e:
            logger.error(f"Error saving exam session: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    @classmethod
    def load(cls, session_id):
        logger.info(f"Loading exam session with ID: {session_id}")
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT * FROM exam_sessions WHERE id = %s', (session_id,))
                    data = cursor.fetchone()
                    if data:
                        logger.info("Exam session loaded successfully")
                        return cls(
                            user_id=data['user_id'],
                            start_time=data['start_time'],
                            end_time=data['end_time'],
                            score=data['score'],
                            total_questions=data['total_questions'],
                            is_completed=data['is_completed'],
                            practiced_questions=data['practiced_questions'],
                            incorrect_answers=json.loads(data['incorrect_answers']),
                            review_list=json.loads(data['review_list']),
                            id=data['id']
                        )
            logger.warning(f"No exam session found with ID: {session_id}")
            return None
        except Exception as e:
            logger.error(f"Error loading exam session: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def update(self):
        logger.info(f"Updating exam session with ID: {self.id}")
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        UPDATE exam_sessions 
                        SET end_time = %s, score = %s, is_completed = %s, practiced_questions = %s, incorrect_answers = %s, review_list = %s
                        WHERE id = %s
                    ''', (self.end_time, self.score, self.is_completed, self.practiced_questions,
                          json.dumps(self.incorrect_answers), json.dumps(self.review_list), self.id))
            logger.info("Exam session updated successfully")
        except Exception as e:
            logger.error(f"Error updating exam session: {str(e)}")
            logger.error(traceback.format_exc())
            raise