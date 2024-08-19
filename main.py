import streamlit as st
from config import Config
from user import User, login_page, get_user_by_token
from quiz import Quiz
from database import setup_database, get_connection
from utils import load_questions_and_case_studies, generate_temp_token
from pages import configuration_page, exam_practice_mode, study_mode, study_specific_question
import os
import logging
import traceback
import json
from question import Question
from case_study import CaseStudy

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

def load_quiz_state(token):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT state FROM quiz_states WHERE token = %s', (token,))
            result = cursor.fetchone()
    
    if result:
        quiz_state = result['state'] if isinstance(result['state'], dict) else json.loads(result['state'])
        # Reconstruct the Quiz object
        all_questions = [Question.from_dict(q) for q in quiz_state['all_questions']]
        case_studies = {k: CaseStudy.from_dict(v) for k, v in quiz_state['case_studies'].items()}
        quiz = Quiz(all_questions, case_studies, quiz_state['user_id'], quiz_state['mode'])
        quiz.current_index = quiz_state['current_index']
        quiz.score = quiz_state['score']
        quiz.user_answers = quiz_state['user_answers']
        quiz.practiced_questions = quiz_state['practiced_questions']
        quiz.incorrect_answers = set(quiz_state['incorrect_answers'])
        quiz.review_list = set(quiz_state['review_list'])
        quiz.algorithm_performance = quiz_state['algorithm_performance']
        return quiz
    return None

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
    if "question_id" in query_params and "token" in query_params:
        question_id = query_params["question_id"][0]
        token = query_params["token"][0]
        quiz = load_quiz_state(token)
        if quiz:
            study_specific_question(quiz, config, question_id)
        else:
            st.error("Failed to load quiz state. Please try again.")
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