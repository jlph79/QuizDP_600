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
                practiced_questions TEXT,
                incorrect_answers TEXT,
                review_list TEXT,
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
                practiced_questions TEXT,
                incorrect_answers TEXT,
                review_list TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

def migrate_database():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Check if columns exist in user_progress table
        cursor.execute("PRAGMA table_info(user_progress)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'practiced_questions' not in columns:
            cursor.execute("ALTER TABLE user_progress ADD COLUMN practiced_questions TEXT")
        if 'incorrect_answers' not in columns:
            cursor.execute("ALTER TABLE user_progress ADD COLUMN incorrect_answers TEXT")
        if 'review_list' not in columns:
            cursor.execute("ALTER TABLE user_progress ADD COLUMN review_list TEXT")
        
        # Check if columns exist in exam_sessions table
        cursor.execute("PRAGMA table_info(exam_sessions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'practiced_questions' not in columns:
            cursor.execute("ALTER TABLE exam_sessions ADD COLUMN practiced_questions TEXT")
        if 'incorrect_answers' not in columns:
            cursor.execute("ALTER TABLE exam_sessions ADD COLUMN incorrect_answers TEXT")
        if 'review_list' not in columns:
            cursor.execute("ALTER TABLE exam_sessions ADD COLUMN review_list TEXT")

# Call both functions
setup_database()
migrate_database()