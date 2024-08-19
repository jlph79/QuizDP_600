import streamlit as st
from config import Config
from user import User, login_page, get_user_by_token
from quiz import Quiz
from database import setup_database
from utils import load_questions_and_case_studies, generate_temp_token
from pages import configuration_page, exam_practice_mode, study_mode, study_specific_question
import os
import logging
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use os.path.join to create a path that works in both environments
IMAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "DP-600_Resources"))
def serve_image(image_path):
    with open(image_path, "rb") as f:
        return f.read()

def algorithm_performance_page(quiz):
    st.title("Algorithm Performance")
    
    performance = quiz.get_algorithm_performance()
    
    st.write("Current Algorithm Performance:")
    st.write(f"Total questions presented: {performance['total_questions_presented']}")
    st.write(f"Unique questions presented: {performance['unique_questions_presented']}")
    st.write(f"Questions until full coverage: {performance['questions_until_full_coverage']}")
    
    if st.button("Reset Algorithm"):
        quiz.reset_tracking()
        st.success("Algorithm has been reset to zero.")
        st.experimental_rerun()

def main():
    logger.info("Starting main application...")
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
    
    # Handle auto-login with token
    query_params = st.experimental_get_query_params()
    if "token" in query_params:
        token = query_params["token"][0]
        user = get_user_by_token(token)
        if user:
            st.session_state.user = user
    
    if 'user' not in st.session_state:
        login_page()
        return

    user = st.session_state.user
    config = Config.load(user.user_id)

    logger.info("Loading questions and case studies...")
    questions, case_studies = load_questions_and_case_studies(st.session_state.image_dir)
    logger.info(f"Loaded {len(questions)} questions and {len(case_studies)} case studies.")

    if not questions:
        st.error("No questions loaded. Please check the error messages above for more details.")
        logger.error("No questions loaded.")
        return

    logger.info(f"Question IDs: {[q.id for q in questions]}")
    logger.info(f"Case Study IDs: {list(case_studies.keys())}")

    # Handle the study_question route
    if "question_id" in query_params:
        question_id = query_params["question_id"][0]
        if 'quiz' not in st.session_state:
            try:
                st.session_state.quiz = Quiz(questions, case_studies, user.user_id, "study")
                st.session_state.quiz.load_progress()
                logger.info("Quiz created and progress loaded successfully for study_question route.")
            except Exception as e:
                logger.error(f"Error creating quiz or loading progress: {str(e)}")
                logger.error(traceback.format_exc())
                st.error(f"An error occurred while creating the quiz or loading progress: {str(e)}")
                st.error("Please check the logs for more details.")
                return
        study_specific_question(st.session_state.quiz, config, question_id)
        return

    app_mode = st.sidebar.selectbox("Choose the app mode", ["Study", "Exam Practice", "Configuration", "Algorithm Performance"])

    if app_mode == "Configuration":
        configuration_page(config, user.user_id)
    elif app_mode == "Algorithm Performance":
        if 'quiz' not in st.session_state:
            try:
                st.session_state.quiz = Quiz(questions, case_studies, user.user_id, "study")
                st.session_state.quiz.load_progress()
                logger.info("Quiz created and progress loaded successfully for Algorithm Performance mode.")
            except Exception as e:
                logger.error(f"Error creating quiz or loading progress: {str(e)}")
                logger.error(traceback.format_exc())
                st.error(f"An error occurred while creating the quiz or loading progress: {str(e)}")
                st.error("Please check the logs for more details.")
                return
        algorithm_performance_page(st.session_state.quiz)
    else:
        if 'quiz' not in st.session_state or st.session_state.quiz.mode != app_mode.lower():
            try:
                st.session_state.quiz = Quiz(questions, case_studies, user.user_id, app_mode.lower())
                st.session_state.quiz.load_progress()
                logger.info(f"Quiz created and progress loaded successfully for {app_mode} mode.")
                logger.info(f"Number of questions in quiz: {len(st.session_state.quiz.all_questions)}")
            except Exception as e:
                logger.error(f"Error creating quiz or loading progress: {str(e)}")
                logger.error(traceback.format_exc())
                st.error(f"An error occurred while creating the quiz or loading progress: {str(e)}")
                st.error("Please check the logs for more details.")
                return
        
        quiz = st.session_state.quiz

        if app_mode == "Exam Practice":
            exam_practice_mode(quiz, config)
        elif app_mode == "Study":
            study_mode(quiz, config)

    logger.info("Application execution completed.")

if __name__ == "__main__":
    main()