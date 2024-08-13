import streamlit as st
from datetime import datetime, timedelta
from quiz import Quiz
from config import Config

def reset_exam_state():
    st.session_state.exam_started = False
    st.session_state.exam_finished = False
    st.session_state.exam_paused = False
    st.session_state.exam_start_time = None
    st.session_state.exam_end_time = None
    st.session_state.pause_time = None
    st.session_state.total_pause_time = timedelta()

def configuration_page(config: Config, user_id: int):
    st.title("Configuration")
    config.header_font_size = st.slider("Header Font Size", 16, 36, int(config.header_font_size))
    config.body_font_size = st.slider("Body Font Size", 12, 24, int(config.body_font_size))
    config.answer_font_size = st.slider("Answer Font Size", 12, 24, int(config.answer_font_size))
    config.choice_font_size = st.slider("Choice Font Size", 12, 24, int(config.choice_font_size))
    config.exam_duration = st.slider("Exam Duration (minutes)", 1, 180, int(config.exam_duration))
    config.exam_questions = st.slider("Number of Exam Questions", 20, 100, int(config.exam_questions))
    
    if st.button("Save Configuration"):
        config.save(user_id)
        st.success("Configuration saved successfully!")
        st.experimental_rerun()

def exam_practice_mode(quiz: Quiz, config: Config):
    if 'exam_started' not in st.session_state:
        reset_exam_state()

    if not st.session_state.exam_started and not st.session_state.exam_finished:
        display_exam_start_page(quiz, config)
    elif st.session_state.exam_started:
        display_exam_in_progress(quiz, config)
    else:
        display_exam_finished(quiz, config)

def display_exam_start_page(quiz: Quiz, config: Config):
    st.header("Welcome to Exam Practice Mode")
    st.write(f"Duration: {config.exam_duration} minutes")
    st.write(f"Number of questions: {config.exam_questions}")
    if st.button("Start Exam"):
        quiz.start_exam(config)
        st.session_state.exam_started = True
        st.session_state.exam_start_time = datetime.now()
        st.session_state.exam_end_time = datetime.now() + timedelta(minutes=config.exam_duration)
        st.experimental_rerun()

def display_exam_in_progress(quiz: Quiz, config: Config):
    # Timer display
    timer_placeholder = st.empty()

    # Control buttons
    col1, col2, col3, col4 = st.columns(4)
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
            quiz.finish_exam()
            st.session_state.exam_started = False
            st.session_state.exam_paused = False
            st.session_state.exam_finished = True
            st.success("Exam completed! Your score has been saved.")
            st.experimental_rerun()
    
    with col3:
        current_question = quiz.get_current_question()
        if st.button("Mark for Review", key=f"review_{current_question.id}"):
            quiz.mark_for_review(current_question.id)
            st.success(f"Question {current_question.id} marked for review.")
            st.experimental_rerun()

    with col4:
        if st.button("Show Review List"):
            st.session_state.showing_review_list = True
            st.experimental_rerun()

    # Live timer implementation
    current_time = datetime.now()
    if st.session_state.exam_paused:
        time_left = (st.session_state.exam_end_time - st.session_state.pause_time).total_seconds()
    else:
        time_left = (st.session_state.exam_end_time - current_time + st.session_state.total_pause_time).total_seconds()

    if time_left <= 0:
        timer_placeholder.markdown("Time's up!", unsafe_allow_html=True)
        quiz.finish_exam()
        st.session_state.exam_started = False
        st.session_state.exam_paused = False
        st.session_state.exam_finished = True
        st.success("Time's up! Exam completed. Your score has been saved.")
        st.experimental_rerun()
    else:
        minutes, seconds = divmod(int(time_left), 60)
        timer_placeholder.markdown(f"<div style='font-size: 24px; font-weight: bold; color: #FF4B4B;'>Time remaining: {minutes:02d}:{seconds:02d}</div>", unsafe_allow_html=True)

    if not st.session_state.exam_paused:
        if 'showing_review_list' in st.session_state and st.session_state.showing_review_list:
            display_review_list(quiz, config)
            if st.button("Back to Exam"):
                st.session_state.showing_review_list = False
                st.experimental_rerun()
        else:
            # Display current question
            display_question(quiz, config)
    else:
        st.info("Exam is paused. Click 'Resume Exam' to continue.")

def display_exam_finished(quiz: Quiz, config: Config):
    st.header("Exam Finished")
    st.write(f"Your score: {quiz.score}/{len(quiz.questions)}")
    
    if st.button("Start New Exam"):
        reset_exam_state()
        st.experimental_rerun()
    
    st.subheader("Review List")
    display_review_list(quiz, config)

def study_mode(quiz: Quiz, config: Config):
    st.markdown(f"<h1 style='font-size:{config.header_font_size + 4}px;'>DP-600 Certificate Quiz App - Study Mode</h1>", unsafe_allow_html=True)
    display_question(quiz, config)

def display_question(quiz: Quiz, config: Config):
    current_question = quiz.get_current_question()
    
    # Display question number
    st.markdown(f"<h2 style='font-size:{config.header_font_size}px;'>Question {current_question.id}</h2>", unsafe_allow_html=True)
    
    # Display case study if available
    if current_question.case_study_id:
        case_study = quiz.case_studies.get(current_question.case_study_id)
        if case_study:
            with st.expander("View Case Study"):
                case_study.display(config)
    
    # Display question context and text with images
    current_question.display_context_with_images(config)
    
    user_answers = []
    if current_question.type == "multiple-choice":
        for idx, choice in enumerate(current_question.choices):
            label = chr(65 + idx)  # Convert 0, 1, 2, ... to A, B, C, ...
            checked = st.checkbox(f"{label} - {choice['text']}", key=f"option_{current_question.id}_{idx}")
            if checked:
                user_answers.append(label)
    elif current_question.type == "single-choice":
        options = [f"{chr(65 + idx)} - {choice['text']}" for idx, choice in enumerate(current_question.choices)]
        selected = st.radio("Select one option:", options, key=f"option_{current_question.id}")
        if selected:
            user_answers = [selected[0]]  # Extract the label (A, B, C, ...)
    elif current_question.type in ["hotspot", "drag-and-drop"]:
        st.write("This is a hotspot or drag-and-drop question. Please refer to the image below.")
        if current_question.choices and isinstance(current_question.choices[0], str) and current_question.choices[0].lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            current_question.display_image(current_question.choices[0], "Question Image")
        
        if st.button("Display Answer", key=f"display_answer_{current_question.id}"):
            current_question.display_answer(config)
    else:
        st.write("This question type is not yet implemented.")
    
    if current_question.type not in ["hotspot", "drag-and-drop"]:
        if st.button("Submit", key=f"submit_{current_question.id}"):
            if user_answers:
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

def remove_question(quiz: Quiz, question_id: str):
    quiz.remove_from_review(question_id)
    st.success(f"Question {question_id} removed from review list.")
    st.experimental_rerun()

def display_review_list(quiz: Quiz, config: Config):
    st.markdown(f"<h2 style='font-size:{config.header_font_size}px;'>Questions Marked for Review</h2>", unsafe_allow_html=True)
    
    review_list = list(quiz.review_list)
    if review_list:
        for question_id in review_list:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"Question {question_id}", key=f"open_{question_id}"):
                    token = st.session_state.user.generate_temp_token()
                    js_code = f"""
                    <script>
                    window.open('/?question_id={question_id}&token={token}', '_blank');
                    </script>
                    """
                    st.components.v1.html(js_code, height=0)
            with col2:
                if st.button("🗑️", key=f"remove_{question_id}", on_click=remove_question, args=(quiz, question_id)):
                    pass
    else:
        st.markdown(f"<p style='font-size:{config.body_font_size}px;'>No questions marked for review.</p>", unsafe_allow_html=True)

def study_specific_question(quiz: Quiz, config: Config, question_id: str):
    question = quiz.get_question_by_id(question_id)
    if question:
        st.markdown(f"<h2 style='font-size:{config.header_font_size}px;'>Studying Question {question_id}</h2>", unsafe_allow_html=True)
        
        # Display case study if available
        if question.case_study_id:
            case_study = quiz.case_studies.get(question.case_study_id)
            if case_study:
                with st.expander("View Case Study"):
                    case_study.display(config)
        
        # Display question context and text with images
        question.display_context_with_images(config)
        
        user_answers = []
        if question.type == "multiple-choice":
            for idx, choice in enumerate(question.choices):
                label = chr(65 + idx)  # Convert 0, 1, 2, ... to A, B, C, ...
                checked = st.checkbox(f"{label} - {choice['text']}", key=f"option_{question_id}_{idx}")
                if checked:
                    user_answers.append(label)
        elif question.type == "single-choice":
            options = [f"{chr(65 + idx)} - {choice['text']}" for idx, choice in enumerate(question.choices)]
            selected = st.radio("Select one option:", options, key=f"option_{question_id}")
            if selected:
                user_answers = [selected[0]]  # Extract the label (A, B, C, ...)
        elif question.type in ["hotspot", "drag-and-drop"]:
            st.write("This is a hotspot or drag-and-drop question. Please refer to the image below.")
            if question.choices and isinstance(question.choices[0], str) and question.choices[0].lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                question.display_image(question.choices[0], "Question Image")
            
            if st.button("Display Answer", key=f"display_answer_{question_id}"):
                question.display_answer(config)
        else:
            st.write("This question type is not yet implemented.")
        
        if question.type not in ["hotspot", "drag-and-drop"]:
            if st.button("Submit", key=f"submit_{question_id}"):
                if user_answers:
                    is_correct = quiz.check_answer(user_answers)
                    if is_correct:
                        st.success("Correct!")
                    else:
                        st.error("Incorrect.")
                    question.display_answer(config)
                else:
                    st.warning("Please select an answer before submitting.")
        
        if st.button("Close"):
            js_code = """
            <script>
            window.close();
            </script>
            """
            st.components.v1.html(js_code, height=0)
    else:
        st.error("Question not found.")
        if st.button("Close"):
            js_code = """
            <script>
            window.close();
            </script>
            """
            st.components.v1.html(js_code, height=0)