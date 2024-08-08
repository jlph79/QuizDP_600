import sqlite3
import json
import streamlit as st
from database import DB_PATH
import secrets
import time

class User:
    def __init__(self, username, password, user_id=None):
        self.username = username
        self.password = password  # In a real app, you'd hash this password
        self.user_id = user_id

    def save(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO users (username, password) VALUES (?, ?)', (self.username, self.password))
            self.user_id = cursor.lastrowid
        return self.user_id

    @classmethod
    def authenticate(cls, username, password):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
            user_data = cursor.fetchone()
        if user_data:
            return cls(username, password, user_id=user_data[0])
        return None

    def get_practiced_questions(self, mode):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT practiced_questions FROM user_progress WHERE user_id = ? AND mode = ?', (self.user_id, mode))
            result = cursor.fetchone()
        return json.loads(result[0]) if result and result[0] else []

    def get_incorrect_answers(self, mode):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT incorrect_answers FROM user_progress WHERE user_id = ? AND mode = ?', (self.user_id, mode))
            result = cursor.fetchone()
        return json.loads(result[0]) if result and result[0] else []

    def get_review_list(self, mode):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT review_list FROM user_progress WHERE user_id = ? AND mode = ?', (self.user_id, mode))
            result = cursor.fetchone()
        return json.loads(result[0]) if result and result[0] else []

    def update_progress(self, mode, practiced_questions, incorrect_answers, review_list):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_progress 
                (user_id, mode, practiced_questions, incorrect_answers, review_list) 
                VALUES (?, ?, ?, ?, ?)
            ''', (self.user_id, mode, json.dumps(practiced_questions), json.dumps(incorrect_answers), json.dumps(review_list)))

    def generate_temp_token(self):
        token = secrets.token_urlsafe(32)
        expiration = int(time.time()) + 3600  # Token valid for 1 hour
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO temp_tokens (user_id, token, expiration) VALUES (?, ?, ?)',
                           (self.user_id, token, expiration))
        return token

def get_user_by_token(token):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM temp_tokens WHERE token = ? AND expiration > ?',
                       (token, int(time.time())))
        result = cursor.fetchone()
    if result:
        user_id = result[0]
        cursor.execute('SELECT username, password FROM users WHERE id = ?', (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return User(user_data[0], user_data[1], user_id=user_id)
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