import sqlite3
from datetime import datetime
from database import DB_PATH

class ExamSession:
    def __init__(self, user_id, start_time, end_time, score, total_questions, is_completed, id=None):
        self.id = id
        self.user_id = user_id
        self.start_time = start_time
        self.end_time = end_time
        self.score = score
        self.total_questions = total_questions
        self.is_completed = is_completed

    def save(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO exam_sessions 
                (user_id, start_time, end_time, score, total_questions, is_completed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.user_id, self.start_time, self.end_time, self.score, self.total_questions, self.is_completed))
            self.id = cursor.lastrowid
            return self.id

    @classmethod
    def load(cls, session_id):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM exam_sessions WHERE id = ?', (session_id,))
            data = cursor.fetchone()
            if data:
                return cls(*data[1:], id=data[0])
        return None

    def update(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE exam_sessions 
                SET end_time = ?, score = ?, is_completed = ?
                WHERE id = ?
            ''', (self.end_time, self.score, self.is_completed, self.id))