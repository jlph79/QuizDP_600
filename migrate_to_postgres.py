import sqlite3
import psycopg2
import json
import os
import base64
from database import DB_URL, insert_questions_and_case_studies, setup_database, insert_image

SQLITE_DB_PATH = "quiz_app.db"
JSON_PATH = os.path.join("DP-600_Resources", "DP600_QuestionsAnswersV3.json")
IMAGES_DIR = os.path.join("DP-600_Resources", "")

def migrate_data():
    # Connect to SQLite database
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL database
    pg_conn = psycopg2.connect(DB_URL)
    pg_cursor = pg_conn.cursor()

    try:
        # Set up the database schema
        setup_database()

        # Migrate users table
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        for user in users:
            try:
                pg_cursor.execute("INSERT INTO users (id, username, password) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING", user)
                pg_conn.commit()
            except Exception as e:
                print(f"Error inserting user {user[0]}: {str(e)}")
                pg_conn.rollback()

        # Get existing user IDs from PostgreSQL
        pg_cursor.execute("SELECT id FROM users")
        existing_user_ids = set(row[0] for row in pg_cursor.fetchall())

        # Migrate user_config table
        sqlite_cursor.execute("SELECT * FROM user_config")
        configs = sqlite_cursor.fetchall()
        for config in configs:
            if config[0] in existing_user_ids:
                try:
                    pg_cursor.execute("INSERT INTO user_config (user_id, header_font_size, body_font_size, answer_font_size, choice_font_size, exam_duration, exam_questions) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING", config)
                    pg_conn.commit()
                except Exception as e:
                    print(f"Error inserting user_config for user_id {config[0]}: {str(e)}")
                    pg_conn.rollback()
            else:
                print(f"Skipping user_config for user_id {config[0]} as it doesn't exist in users table")

        # Migrate user_progress table
        sqlite_cursor.execute("SELECT * FROM user_progress")
        progress = sqlite_cursor.fetchall()
        for prog in progress:
            if prog[0] in existing_user_ids:
                try:
                    pg_cursor.execute("INSERT INTO user_progress (user_id, current_index, score, user_answers, mode, practiced_questions, incorrect_answers, review_list, algorithm_performance) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (user_id, mode) DO NOTHING", prog)
                    pg_conn.commit()
                except Exception as e:
                    print(f"Error inserting user_progress for user_id {prog[0]}: {str(e)}")
                    pg_conn.rollback()
            else:
                print(f"Skipping user_progress for user_id {prog[0]} as it doesn't exist in users table")

        # Migrate exam_sessions table
        sqlite_cursor.execute("SELECT * FROM exam_sessions")
        sessions = sqlite_cursor.fetchall()
        for session in sessions:
            if session[1] in existing_user_ids:
                try:
                    # Convert is_completed to boolean
                    is_completed = bool(session[6])
                    modified_session = session[:6] + (is_completed,) + session[7:]
                    pg_cursor.execute("INSERT INTO exam_sessions (id, user_id, start_time, end_time, score, total_questions, is_completed, practiced_questions, incorrect_answers, review_list, algorithm_performance) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING", modified_session)
                    pg_conn.commit()
                except Exception as e:
                    print(f"Error inserting exam_session for user_id {session[1]}: {str(e)}")
                    pg_conn.rollback()
            else:
                print(f"Skipping exam_session for user_id {session[1]} as it doesn't exist in users table")

        # Migrate temp_tokens table
        sqlite_cursor.execute("SELECT * FROM temp_tokens")
        tokens = sqlite_cursor.fetchall()
        for token in tokens:
            if token[1] in existing_user_ids:
                try:
                    pg_cursor.execute("INSERT INTO temp_tokens (id, user_id, token, expiration) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING", token)
                    pg_conn.commit()
                except Exception as e:
                    print(f"Error inserting temp_token for user_id {token[1]}: {str(e)}")
                    pg_conn.rollback()
            else:
                print(f"Skipping temp_token for user_id {token[1]} as it doesn't exist in users table")

        # Migrate questions and case studies from JSON file
        with open(JSON_PATH, 'r') as file:
            data = json.load(file)
        
        questions = data['questions']
        case_studies = data['case_studies']
        
        # Sort questions by their ID (assuming ID is a string like '#1', '#2', etc.)
        questions.sort(key=lambda q: int(q['id'].replace('#', '')))
        
        # Update question IDs to be integers
        for i, question in enumerate(questions, start=1):
            question['id'] = i  # Change this line to store as integer
        
        insert_questions_and_case_studies(questions, case_studies)

        # Migrate images
        for filename in os.listdir(IMAGES_DIR):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                with open(os.path.join(IMAGES_DIR, filename), 'rb') as img_file:
                    img_data = img_file.read()
                    insert_image(filename, img_data)

        print("Data migration completed successfully.")
    except Exception as e:
        print(f"An error occurred during migration: {str(e)}")
    finally:
        # Close connections
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate_data()