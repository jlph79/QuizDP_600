import psycopg2
from database import get_connection

def create_algorithm_performance_table():
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS algorithm_performance (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        total_questions_presented INTEGER NOT NULL,
                        unique_questions_presented INTEGER NOT NULL,
                        questions_until_full_coverage INTEGER NOT NULL,
                        timestamp TIMESTAMP NOT NULL
                    )
                ''')
        print("Algorithm performance table created successfully.")
    except psycopg2.Error as e:
        print(f"An error occurred while creating the algorithm_performance table: {e}")

if __name__ == "__main__":
    create_algorithm_performance_table()