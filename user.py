import sqlite3
import streamlit as st
from database import DB_PATH

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password  # In a real app, you'd hash this password

    def save(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO users (username, password) VALUES (?, ?)', (self.username, self.password))
        return cursor.lastrowid

    @classmethod
    def authenticate(cls, username, password):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
            user_data = cursor.fetchone()
        return user_data[0] if user_data else None

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user_id = User.authenticate(username, password)
        if user_id:
            st.session_state.user_id = user_id
            st.success("Logged in successfully!")
            st.experimental_rerun()
        else:
            st.error("Invalid username or password")
    
    if st.button("Register"):
        if username and password:
            user = User(username, password)
            user_id = user.save()
            st.session_state.user_id = user_id
            st.success("Registered successfully!")
            st.experimental_rerun()
        else:
            st.error("Please enter a username and password")