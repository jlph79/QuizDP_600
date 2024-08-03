import streamlit as st
from config import Config
from user import User, login_page
from quiz import Quiz
from database import setup_database
from utils import load_questions_and_case_studies
from pages import configuration_page, exam_practice_mode, study_mode
import os

#IMAGE_DIR = os.path.abspath(r"C:\Users\YourUsername\Path\To\DP-600_Resources")
IMAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "DP-600_Resources"))
def serve_image(image_path):
    with open(image_path, "rb") as f:
        return f.read()

def main():
    setup_database()

    # Set up image serving
    if 'image_dir' not in st.session_state:
        st.session_state.image_dir = IMAGE_DIR
    
    # Serve images
    for filename in os.listdir(IMAGE_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            image_path = os.path.join(IMAGE_DIR, filename)
            st.session_state[f"image_{filename}"] = serve_image(image_path)
            
    st.sidebar.title("DP-600 Quiz App")
    
    if 'user_id' not in st.session_state:
        login_page()
        return

    user_id = st.session_state.user_id
    config = Config.load(user_id)

    app_mode = st.sidebar.selectbox("Choose the app mode", ["Study", "Exam Practice", "Configuration"])

    if app_mode == "Configuration":
        configuration_page(config, user_id)
    else:
        questions, case_studies = load_questions_and_case_studies(st.session_state.image_dir)
        if not questions:
            st.error("No questions loaded. Please check the JSON file path and format.")
            return

        if 'quiz' not in st.session_state or st.session_state.quiz.mode != app_mode.lower():
            st.session_state.quiz = Quiz.load_progress(questions, case_studies, user_id, app_mode.lower())
        
        quiz = st.session_state.quiz

        if app_mode == "Exam Practice":
            exam_practice_mode(quiz, config)
        else:  # Study mode
            study_mode(quiz, config)

if __name__ == "__main__":
    main()