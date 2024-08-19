from database import get_connection

class Config:
    def __init__(self, user_id, header_font_size=24, body_font_size=16, answer_font_size=18, choice_font_size=16, exam_duration=180, exam_questions=65):
        self.user_id = user_id
        self.header_font_size = header_font_size
        self.body_font_size = body_font_size
        self.answer_font_size = answer_font_size
        self.choice_font_size = choice_font_size
        self.exam_duration = exam_duration
        self.exam_questions = exam_questions

    def save(self, user_id=None):
        if user_id is not None:
            self.user_id = user_id
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO user_config 
                    (user_id, header_font_size, body_font_size, answer_font_size, choice_font_size, exam_duration, exam_questions) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE
                    SET header_font_size = EXCLUDED.header_font_size,
                        body_font_size = EXCLUDED.body_font_size,
                        answer_font_size = EXCLUDED.answer_font_size,
                        choice_font_size = EXCLUDED.choice_font_size,
                        exam_duration = EXCLUDED.exam_duration,
                        exam_questions = EXCLUDED.exam_questions
                ''', (self.user_id, self.header_font_size, self.body_font_size, self.answer_font_size, self.choice_font_size, self.exam_duration, self.exam_questions))

    @classmethod
    def load(cls, user_id):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM user_config WHERE user_id = %s', (user_id,))
                row = cursor.fetchone()
        
        if row:
            config = cls(user_id)
            if isinstance(row, dict):
                config.header_font_size = row['header_font_size']
                config.body_font_size = row['body_font_size']
                config.answer_font_size = row['answer_font_size']
                config.choice_font_size = row['choice_font_size']
                config.exam_duration = row['exam_duration']
                config.exam_questions = row['exam_questions']
            else:
                config.header_font_size, config.body_font_size, config.answer_font_size, config.choice_font_size, config.exam_duration, config.exam_questions = row[1:]
            return config
        else:
            return cls(user_id)  # Return default config if not found

    def update(self, header_font_size=None, body_font_size=None, answer_font_size=None, choice_font_size=None, exam_duration=None, exam_questions=None):
        if header_font_size is not None:
            self.header_font_size = header_font_size
        if body_font_size is not None:
            self.body_font_size = body_font_size
        if answer_font_size is not None:
            self.answer_font_size = answer_font_size
        if choice_font_size is not None:
            self.choice_font_size = choice_font_size
        if exam_duration is not None:
            self.exam_duration = exam_duration
        if exam_questions is not None:
            self.exam_questions = exam_questions
        self.save()