import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import json
import base64
import logging
import os 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load the database URL from an environment variable
PASSWORD = os.getenv("PASSWORD")
if PASSWORD is None:
    raise ValueError("PASSWORD environment variable not set.")
DB_URL = f"postgresql://postgres:{PASSWORD}@viaduct.proxy.rlwy.net:20628/railway"

if DB_URL is None:
    raise ValueError("DATABASE_URL environment variable not set.")
    
def get_connection():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def setup_database():
    logger.info("Connecting to the cloud PostgreSQL database...")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Check if questions table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'questions'
                )
            """)
            questions_exist = cursor.fetchone()['exists']

            if not questions_exist:
                logger.warning("Questions table does not exist. Creating it now...")
                create_questions_table(cursor)
            else:
                logger.info("Questions table already exists.")

            # Check for exam_sessions table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'exam_sessions'
                )
            """)
            exam_sessions_exist = cursor.fetchone()['exists']

            if not exam_sessions_exist:
                logger.warning("exam_sessions table does not exist. Creating it now...")
                create_exam_sessions_table(cursor)
            else:
                logger.info("exam_sessions table exists.")

            # Check for user_progress table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_progress'
                )
            """)
            user_progress_exist = cursor.fetchone()['exists']

            if not user_progress_exist:
                logger.warning("user_progress table does not exist. Creating it now...")
                create_user_progress_table(cursor)
            else:
                logger.info("user_progress table exists.")
                # Check if current_exam_questions column exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = 'user_progress' AND column_name = 'current_exam_questions'
                    )
                """)
                current_exam_questions_exist = cursor.fetchone()['exists']

                if not current_exam_questions_exist:
                    logger.warning("current_exam_questions column does not exist in user_progress table. Adding it now...")
                    add_current_exam_questions_column(cursor)
                else:
                    logger.info("current_exam_questions column already exists in user_progress table.")

            # Check for quiz_states table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'quiz_states'
                )
            """)
            quiz_states_exist = cursor.fetchone()['exists']

            if not quiz_states_exist:
                logger.warning("quiz_states table does not exist. Creating it now...")
                create_quiz_states_table(cursor)
            else:
                logger.info("quiz_states table exists.")

def create_questions_table(cursor):
    cursor.execute('''
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY,
            case_study_id TEXT,
            question_context TEXT,
            question_text TEXT NOT NULL,
            question_type TEXT NOT NULL,
            choices JSONB,
            correct_answers JSONB,
            correct_answers_community JSONB,
            images JSONB
        )
    ''')
    logger.info("questions table created successfully.")

def create_exam_sessions_table(cursor):
    cursor.execute('''
        CREATE TABLE exam_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            score INTEGER,
            total_questions INTEGER,
            is_completed BOOLEAN,
            practiced_questions JSONB,
            incorrect_answers JSONB,
            review_list JSONB
        )
    ''')
    logger.info("exam_sessions table created successfully.")

def create_user_progress_table(cursor):
    cursor.execute('''
        CREATE TABLE user_progress (
            user_id INTEGER NOT NULL,
            mode TEXT NOT NULL,
            current_index INTEGER,
            score INTEGER,
            user_answers JSONB,
            practiced_questions JSONB,
            incorrect_answers JSONB,
            review_list JSONB,
            algorithm_performance JSONB,
            current_exam_questions JSONB,
            PRIMARY KEY (user_id, mode)
        )
    ''')
    logger.info("user_progress table created successfully.")

def create_quiz_states_table(cursor):
    cursor.execute('''
        CREATE TABLE quiz_states (
            token TEXT PRIMARY KEY,
            state JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    logger.info("quiz_states table created successfully.")

def add_current_exam_questions_column(cursor):
    cursor.execute('''
        ALTER TABLE user_progress
        ADD COLUMN current_exam_questions JSONB
    ''')
    logger.info("current_exam_questions column added to user_progress table successfully.")

def insert_questions_and_case_studies(questions, case_studies):
    logger.info(f"Inserting {len(questions)} questions and {len(case_studies)} case studies...")
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Insert questions
            for question in questions:
                try:
                    cursor.execute('''
                        INSERT INTO questions 
                        (id, case_study_id, question_context, question_text, question_type, choices, correct_answers, correct_answers_community, images)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE
                        SET case_study_id = EXCLUDED.case_study_id,
                            question_context = EXCLUDED.question_context,
                            question_text = EXCLUDED.question_text,
                            question_type = EXCLUDED.question_type,
                            choices = EXCLUDED.choices,
                            correct_answers = EXCLUDED.correct_answers,
                            correct_answers_community = EXCLUDED.correct_answers_community,
                            images = EXCLUDED.images
                    ''', (
                        int(question['id']),
                        question.get('case_study_id'),
                        question.get('question_context'),
                        question['question_text'],
                        question['question_type'],
                        json.dumps(question['choices']),
                        json.dumps(question['correct_answers']),
                        json.dumps(question.get('correct_answers_community', [])),
                        json.dumps(question.get('images', []))
                    ))
                    conn.commit()  # Commit after each successful insert
                except Exception as e:
                    conn.rollback()  # Rollback the transaction for this question
                    logger.error(f"Error inserting question {question['id']}: {str(e)}")
                    logger.error(f"Question data: {question}")

            # Insert case studies
            for case_study in case_studies:
                try:
                    title = case_study.get('title')
                    if not title:
                        title = f"Case Study: {case_study['id']}"  # Generate a title if it's missing
                    
                    cursor.execute('''
                        INSERT INTO case_studies 
                        (id, title, overview, existing_environment, requirements)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE
                        SET title = EXCLUDED.title,
                            overview = EXCLUDED.overview,
                            existing_environment = EXCLUDED.existing_environment,
                            requirements = EXCLUDED.requirements
                    ''', (
                        case_study['id'],
                        title,
                        case_study.get('overview'),
                        json.dumps(case_study.get('existing_environment', {})),
                        json.dumps(case_study.get('requirements', {}))
                    ))
                    conn.commit()  # Commit after each successful insert
                except Exception as e:
                    conn.rollback()  # Rollback the transaction for this case study
                    logger.error(f"Error inserting case study {case_study.get('id', 'Unknown ID')}: {str(e)}")
                    logger.error(f"Case study data: {case_study}")
    logger.info("Insertion of questions and case studies complete.")

def insert_image(filename, image_data):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute('''
                    INSERT INTO images (filename, data)
                    VALUES (%s, %s)
                    ON CONFLICT (filename) DO UPDATE
                    SET data = EXCLUDED.data
                ''', (filename, psycopg2.Binary(image_data)))
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Error inserting image {filename}: {str(e)}")

# This function will be called from main.py
if __name__ == "__main__":
    setup_database()