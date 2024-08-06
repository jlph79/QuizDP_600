import streamlit as st
from datetime import datetime, timedelta
from quiz import Quiz
from config import Config

def configuration_page(config: Config, user_id: int):
    st.title("Configuration")
    config.header_font_size = st.slider("Header Font Size", 16, 36, int(config.header_font_size))
    config.body_font_size = st.slider("Body Font Size", 12, 24, int(config.body_font_size))
    config.answer_font_size = st.slider("Answer Font Size", 12, 24, int(config.answer_font_size))
    config.exam_duration = st.slider("Exam Duration (minutes)", 60, 180, int(config.exam_duration))
    config.exam_questions = st.slider("Number of Exam Questions", 20, 100, int(config.exam_questions))
    
    if st.button("Save Configuration"):
        config.save(user_id)
        st.success("Configuration saved successfully!")
        st.experimental_rerun()

# Add this import at the top if not already present
from datetime import datetime, timedelta

def exam_practice_mode(quiz: Quiz, config: Config):
    if 'exam_started' not in st.session_state:
        reset_exam_state()

    if not st.session_state.exam_started and not st.session_state.exam_finished:
        st.header("Welcome to Exam Practice Mode")
        st.write(f"Duration: {config.exam_duration} minutes")
        st.write(f"Number of questions: {config.exam_questions}")
        if st.button("Start Exam"):
            quiz.start_exam(config)
            st.session_state.exam_started = True
            st.session_state.exam_start_time = datetime.now()
            st.session_state.exam_end_time = datetime.now() + timedelta(minutes=config.exam_duration)
            # Reset quiz state when starting a new exam
            quiz.current_index = 0
            quiz.score = 0
            quiz.user_answers = {}
            st.experimental_rerun()
    elif st.session_state.exam_started:
        # Timer display
        timer_placeholder = st.empty()

        # Control buttons
        col1, col2 = st.columns(2)
        with col1:
            if not st.session_state.exam_paused:
                if st.button("Pause Exam"):
                    st.session_state.exam_paused = True
                    st.session_state.pause_time = datetime.now()
                    st.experimental_rerun()
            else:
                if st.button("Resume Exam"):
                    pause_duration = datetime.now() - st.session_state.pause_time
                    st.session_state.total_pause_time += pause_duration
                    st.session_state.exam_paused = False
                    st.experimental_rerun()

        with col2:
            if st.button("Stop Exam"):
                finish_exam(quiz)
                return

        # Live timer implementation
        current_time = datetime.now()
        if st.session_state.exam_paused:
            time_left = (st.session_state.exam_end_time - st.session_state.pause_time).total_seconds()
        else:
            time_left = (st.session_state.exam_end_time - current_time + st.session_state.total_pause_time).total_seconds()

        if time_left <= 0:
            timer_placeholder.markdown("Time's up!", unsafe_allow_html=True)
            finish_exam(quiz)
            return
        else:
            minutes, seconds = divmod(int(time_left), 60)
            timer_placeholder.markdown(f"<div style='font-size: 24px; font-weight: bold; color: #FF4B4B;'>Time remaining: {minutes:02d}:{seconds:02d}</div>", unsafe_allow_html=True)

        if not st.session_state.exam_paused:
            # Display current question
            display_question(quiz, config)
        else:
            st.info("Exam is paused. Click 'Resume Exam' to continue.")

    if st.session_state.exam_finished:
        st.success("Exam session done!")
        total_time = (st.session_state.exam_end_time - st.session_state.exam_start_time - st.session_state.total_pause_time).total_seconds()
        st.write(f"Total time elapsed: {total_time // 60:.0f} minutes {total_time % 60:.0f} seconds")
        st.write(f"Total questions: {len(quiz.questions)}")
        st.write(f"Correct answers: {quiz.score}")
        
        if st.button("Start New Exam"):
            reset_exam_state()
            # Reset quiz state when starting a new exam
            quiz.current_index = 0
            quiz.score = 0
            quiz.user_answers = {}
            st.experimental_rerun()     

def study_mode(quiz: Quiz, config: Config):
    st.markdown(f"<h1 style='font-size:{config.header_font_size + 4}px;'>DP-600 Certificate Quiz App - Study Mode</h1>", unsafe_allow_html=True)
    display_question(quiz, config)

def display_question(quiz: Quiz, config: Config):
    current_question = quiz.get_current_question()
 #   st.markdown(f"<h2 style='font-size:{config.header_font_size}px;'>Question #{current_question.id}</h2>", unsafe_allow_html=True)
    
    user_answers = current_question.display_question(config, quiz.case_studies)
    
    if current_question.type == "multiple-choice":
        if st.button("Submit", key=f"submit_{current_question.id}"):
            if user_answers is not None:
                is_correct = quiz.check_answer(user_answers)
                if is_correct:
                    st.success("Correct!")
                else:
                    st.error("Incorrect.")
                current_question.display_answer(config)
            else:
                st.warning("Please select an answer before submitting.")
    
    st.markdown(f"<p style='font-size:{config.body_font_size}px;'>Current Score: {quiz.score}/{len(quiz.questions)}</p>", unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Previous", key=f"prev_{current_question.id}", disabled=quiz.current_index == 0):
            quiz.go_to_question(quiz.current_index - 1)
            st.experimental_rerun()
    with col2:
        go_to_page = st.number_input("Go to question", min_value=1, max_value=len(quiz.questions), value=quiz.current_index + 1, key=f"goto_{current_question.id}")
        if st.button("Go", key=f"go_{current_question.id}"):
            quiz.go_to_question(go_to_page - 1)
            st.experimental_rerun()
    with col3:
        if st.button("Next", key=f"next_{current_question.id}", disabled=quiz.current_index == len(quiz.questions) - 1):
            quiz.go_to_question(quiz.current_index + 1)
            st.experimental_rerun()

def finish_exam(quiz):
    quiz.finish_exam()
    st.session_state.exam_started = False
    st.session_state.exam_paused = False
    st.session_state.exam_finished = True
    st.success("Exam completed! Your score has been saved.")
    st.experimental_rerun()

def reset_exam_state():
    st.session_state.exam_started = False
    st.session_state.exam_paused = False
    st.session_state.exam_end_time = None
    st.session_state.exam_finished = False
    st.session_state.exam_start_time = None
    st.session_state.pause_time = None
    st.session_state.total_pause_time = timedelta()
    # Reset the quiz state
    if 'quiz' in st.session_state:
        st.session_state.quiz.current_index = 0
        st.session_state.quiz.score = 0
        st.session_state.quiz.user_answers = {}