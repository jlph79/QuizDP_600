import streamlit as st
from typing import Dict, Union, List
import os
import re
import base64


class Question:
    def __init__(self, data):
        self.id = data['id'].lstrip('#')
        self.context = data.get('question_context', '')
        self.text = data['question_text']
        self.type = data['question_type']
        self.choices = data.get('choices', [])
        self.correct_answers = data['correct_answers']
        self.correct_answers_community = data.get('correct_answers_community', [])
        self.case_study_id = data.get('case_study_id')

    def display_image(self, image_filename, caption):
        if f"image_{image_filename}" in st.session_state:
            image_data = st.session_state[f"image_{image_filename}"]
            image_base64 = base64.b64encode(image_data).decode()
            st.markdown(f'<img src="data:image/png;base64,{image_base64}" alt="{caption}" style="max-width:100%;">', unsafe_allow_html=True)
            st.caption(caption)
        else:
            st.error(f"Image not found: {image_filename}")

    def display_question(self, config, case_studies):
        if self.case_study_id:
            case_study = case_studies.get(self.case_study_id)
            if case_study:
                with st.expander("View Case Study"):
                    case_study.display(config)

        st.markdown(f"<h2 style='font-size:{config.header_font_size}px;'>Question {self.id}</h2>", unsafe_allow_html=True)
        self.display_context_with_images(config)
        
        if self.type in ["hotspot", "drag-and-drop"]:
            if self.choices and isinstance(self.choices[0], str) and self.choices[0].lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                self.display_image(self.choices[0], "Question Image")
            
            if st.button("Display Answer", key=f"display_answer_{self.id}"):
                self.display_answer(config)
        elif self.type == "multiple-choice":
            options = [f"{chr(65 + i)}. {choice['text']}" for i, choice in enumerate(self.choices)]
            selected_options = st.multiselect("Select answer(s):", options, key=f"question_{self.id}")
            return selected_options
        else:
            st.markdown(f"<p style='font-size:{config.body_font_size}px;'>This question type is not yet implemented.</p>", unsafe_allow_html=True)
        return None

    def display_answer(self, config):
        st.markdown(f"<h3 style='font-size:{config.answer_font_size}px;'>Correct Answer:</h3>", unsafe_allow_html=True)
        if self.type in ["hotspot", "drag-and-drop"]:
            for answer in self.correct_answers:
                if isinstance(answer, str) and answer.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    self.display_image(answer, "Answer Image")
                else:
                    st.markdown(f"<p style='font-size:{config.answer_font_size}px;'>{answer}</p>", unsafe_allow_html=True)
        elif self.type == "multiple-choice":
            answer_texts = [f"{ans}. {self.choices[ord(ans) - ord('A')]['text']}" for ans in self.correct_answers]
            st.markdown(f"<p style='font-size:{config.answer_font_size}px;'>{', '.join(answer_texts)}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='font-size:{config.answer_font_size}px;'>{', '.join(self.correct_answers)}</p>", unsafe_allow_html=True)
        
        if self.correct_answers_community:
            st.markdown(f"<h3 style='font-size:{config.answer_font_size}px;'>Community Suggested Answer:</h3>", unsafe_allow_html=True)
            for answer in self.correct_answers_community:
                st.markdown(f"<p style='font-size:{config.answer_font_size}px;'>{answer}</p>", unsafe_allow_html=True)

    def display_context_with_images(self, config):
        image_pattern = r'!\[(.*?)\]\((.*?)\)'
        parts = re.split(image_pattern, self.context)
        for i, part in enumerate(parts):
            if i % 3 == 0:  # Text content
                st.markdown(f"<p style='font-size:{config.body_font_size}px;'>{part}</p>", unsafe_allow_html=True)
            elif i % 3 == 2:  # Image filename
                self.display_image(part, f"Context Image {i//3 + 1}")
        
        # Display question text only if it's different from the last part of the context
        if self.text.strip() != parts[-1].strip():
            st.markdown(f"<p style='font-size:{config.body_font_size}px;'>{self.text}</p>", unsafe_allow_html=True)


    def check_answer(self, user_answers):
        if self.type == "multiple-choice":
            correct_answers = set(self.correct_answers)
            user_answer_set = set(ans[0] for ans in user_answers) if user_answers else set()
            return user_answer_set == correct_answers
        return False