import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import json
import base64
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL = "postgresql://postgres:AkxzbtDGKXDcLzsSEPwEdgUVxiCRDwXj@viaduct.proxy.rlwy.net:20628/railway"

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