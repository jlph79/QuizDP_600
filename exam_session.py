import sqlite3
import json
from datetime import datetime
from database import DB_PATH

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
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO exam_sessions 
                (user_id, start_time, end_time, score, total_questions, is_completed, practiced_questions, incorrect_answers, review_list)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.user_id, self.start_time, self.end_time, self.score, self.total_questions, self.is_completed,
                  json.dumps(self.practiced_questions), json.dumps(self.incorrect_answers), json.dumps(self.review_list)))
            self.id = cursor.lastrowid
            return self.id

    @classmethod
    def load(cls, session_id):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM exam_sessions WHERE id = ?', (session_id,))
            data = cursor.fetchone()
            if data:
                return cls(
                    user_id=data[1],
                    start_time=data[2],
                    end_time=data[3],
                    score=data[4],
                    total_questions=data[5],
                    is_completed=data[6],
                    practiced_questions=json.loads(data[7]),
                    incorrect_answers=json.loads(data[8]),
                    review_list=json.loads(data[9]),
                    id=data[0]
                )
        return None

    def update(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE exam_sessions 
                SET end_time = ?, score = ?, is_completed = ?, practiced_questions = ?, incorrect_answers = ?, review_list = ?
                WHERE id = ?
            ''', (self.end_time, self.score, self.is_completed, json.dumps(self.practiced_questions),
                  json.dumps(self.incorrect_answers), json.dumps(self.review_list), self.id))