import json
import streamlit as st
from database import get_connection
import secrets
import time
import logging
from psycopg2 import IntegrityError

logger = logging.getLogger(__name__)

class User:
    def __init__(self, username, password, user_id=None):
        self.username = username
        self.password = password  # In a real app, you'd hash this password
        self.user_id = user_id

    def save(self):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id', (self.username, self.password))
                result = cursor.fetchone()
                self.user_id = result['id'] if isinstance(result, dict) else result[0]
        return self.user_id

    @classmethod
    def authenticate(cls, username, password):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
                user_data = cursor.fetchone()
        if user_data:
            logger.info(f"User data retrieved: {user_data}")
            if isinstance(user_data, dict):
                return cls(username, password, user_id=user_data['id'])
            elif isinstance(user_data, (tuple, list)):
                return cls(username, password, user_id=user_data[0])
            else:
                logger.error(f"Unexpected user_data format: {type(user_data)}")
                return None
        logger.warning(f"Authentication failed for username: {username}")
        return None

    def get_practiced_questions(self, mode):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT practiced_questions FROM user_progress WHERE user_id = %s AND mode = %s', (self.user_id, mode))
                result = cursor.fetchone()
        return json.loads(result['practiced_questions']) if result and result['practiced_questions'] else []

    def get_incorrect_answers(self, mode):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT incorrect_answers FROM user_progress WHERE user_id = %s AND mode = %s', (self.user_id, mode))
                result = cursor.fetchone()
        return json.loads(result['incorrect_answers']) if result and result['incorrect_answers'] else []

    def get_review_list(self, mode):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('SELECT review_list FROM user_progress WHERE user_id = %s AND mode = %s', (self.user_id, mode))
                result = cursor.fetchone()
        return json.loads(result['review_list']) if result and result['review_list'] else []

    def update_progress(self, mode, practiced_questions, incorrect_answers, review_list):
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO user_progress 
                    (user_id, mode, practiced_questions, incorrect_answers, review_list) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, mode) DO UPDATE
                    SET practiced_questions = EXCLUDED.practiced_questions,
                        incorrect_answers = EXCLUDED.incorrect_answers,
                        review_list = EXCLUDED.review_list
                ''', (self.user_id, mode, json.dumps(practiced_questions), json.dumps(incorrect_answers), json.dumps(review_list)))

    def generate_temp_token(self):
        max_attempts = 5
        for attempt in range(max_attempts):
            token = secrets.token_urlsafe(32)
            expiration = int(time.time()) + 3600  # Token valid for 1 hour
            try:
                with get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute('INSERT INTO temp_tokens (user_id, token, expiration) VALUES (%s, %s, %s)',
                                       (self.user_id, token, expiration))
                return token
            except IntegrityError:
                if attempt == max_attempts - 1:
                    logger.error(f"Failed to generate a unique token after {max_attempts} attempts")
                    raise
                continue
        raise Exception("Failed to generate a unique token")

def get_user_by_token(token):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT user_id FROM temp_tokens WHERE token = %s AND expiration > %s',
                           (token, int(time.time())))
            result = cursor.fetchone()
    if result:
        user_id = result['user_id'] if isinstance(result, dict) else result[0]
        with conn.cursor() as cursor:
            cursor.execute('SELECT username, password FROM users WHERE id = %s', (user_id,))
            user_data = cursor.fetchone()
        if user_data:
            return User(user_data['username'] if isinstance(user_data, dict) else user_data[0],
                        user_data['password'] if isinstance(user_data, dict) else user_data[1],
                        user_id=user_id)
    return None

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = User.authenticate(username, password)
        if user:
            st.session_state.user = user
            st.success("Logged in successfully!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")
    
    if st.button("Register"):
        if username and password:
            user = User(username, password)
            user.save()
            st.session_state.user = user
            st.success("Registered successfully!")
            st.experimental_rerun()
        else:
            st.error("Please enter a username and password")