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

def exam_practice_mode(quiz: Quiz, config: Config):
    if 'exam_started' not in st.session_state:
        st.session_state.exam_started = False
        st.session_state.exam_paused = False
        st.session_state.exam_end_time = None
        st.session_state.exam_finished = False

    if not st.session_state.exam_started:
        st.header("Welcome to Exam Practice Mode")
        st.write(f"Duration: {config.exam_duration} minutes")
        st.write(f"Number of questions: {config.exam_questions}")
        if st.button("Start Exam"):
            quiz.start_exam(config)
            st.session_state.exam_started = True
            st.session_state.exam_end_time = datetime.now() + timedelta(minutes=config.exam_duration)
            st.experimental_rerun()
    else:
        # Timer display
        timer_placeholder = st.empty()
        
        # Control buttons
        col1, col2 = st.columns(2)
        with col1:
            if not st.session_state.exam_paused:
                if st.button("Pause Exam"):
                    quiz.pause_exam()
                    st.session_state.exam_paused = True
                    st.session_state.pause_time = datetime.now()
                    st.experimental_rerun()
            else:
                if st.button("Resume Exam"):
                    quiz.resume_exam()
                    pause_duration = datetime.now() - st.session_state.pause_time
                    st.session_state.exam_end_time += pause_duration
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

        # Live timer implementation
        if st.session_state.exam_started and not st.session_state.exam_paused:
            end_time = st.session_state.exam_end_time.timestamp() * 1000  # Convert to milliseconds
            current_time = datetime.now().timestamp() * 1000
            initial_time_left = max(end_time - current_time, 0)  # Ensure non-negative
            
            timer_script = f"""
            <div id="timer" style="font-size: 24px; font-weight: bold; color: #FF4B4B; margin-bottom: 20px;"></div>
            <script>
                var endTime = {end_time};
                function updateTimer() {{
                    var now = new Date().getTime();
                    var timeLeft = endTime - now;
                    if (timeLeft <= 0) {{
                        document.getElementById("timer").innerHTML = "Time's up!";
                        clearInterval(timerInterval);
                        window.parent.postMessage({{action: "exam_finished"}}, "*");
                    }} else {{
                        var minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
                        var seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
                        document.getElementById("timer").innerHTML = 
                            "Time remaining: " + minutes.toString().padStart(2, '0') + ":" + seconds.toString().padStart(2, '0');
                    }}
                }}
                updateTimer();  // Initial call to avoid delay
                var timerInterval = setInterval(updateTimer, 1000);
            </script>
            """
            st.markdown(timer_script, unsafe_allow_html=True)
        else:
            remaining_time = st.session_state.exam_end_time - st.session_state.pause_time
            minutes, seconds = divmod(remaining_time.seconds, 60)
            timer_placeholder.markdown(f"<div style='font-size: 24px; font-weight: bold; color: #FF4B4B; margin-bottom: 20px;'>Time remaining (Paused): {minutes:02d}:{seconds:02d}</div>", unsafe_allow_html=True)

        if not st.session_state.exam_paused:
            display_question(quiz, config)

    # Check if exam finished
    if st.session_state.exam_finished:
        quiz.finish_exam()
        st.session_state.exam_started = False
        st.session_state.exam_paused = False
        st.session_state.exam_finished = False
        st.success("Time's up! Exam completed. Your score has been saved.")
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