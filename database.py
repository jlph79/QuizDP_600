import sqlite3

DB_PATH = "quiz_app.db"

def setup_database():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_config (
                user_id INTEGER PRIMARY KEY,
                header_font_size INTEGER,
                body_font_size INTEGER,
                answer_font_size INTEGER,
                exam_duration INTEGER,
                exam_questions INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id INTEGER,
                current_index INTEGER,
                score INTEGER,
                user_answers TEXT,
                mode TEXT,
                PRIMARY KEY (user_id, mode),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_sessions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                score INTEGER,
                total_questions INTEGER,
                is_completed BOOLEAN,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')