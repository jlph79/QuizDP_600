import sqlite3
from database import DB_PATH

class Config:
    def __init__(self):
        self.header_font_size = 24
        self.body_font_size = 16
        self.answer_font_size = 18
        self.choice_font_size = 16
        self.exam_duration = 120
        self.exam_questions = 50

    def save(self, user_id):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_config 
                (user_id, header_font_size, body_font_size, answer_font_size, choice_font_size, exam_duration, exam_questions) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, self.header_font_size, self.body_font_size, self.answer_font_size, self.choice_font_size, self.exam_duration, self.exam_questions))

    @classmethod
    def load(cls, user_id):
        config = cls()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM user_config WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                config.header_font_size, config.body_font_size, config.answer_font_size, config.choice_font_size, config.exam_duration, config.exam_questions = row[1:]
        return config