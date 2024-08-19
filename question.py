import streamlit as st
from typing import Dict, Union, List
import os
import re
import base64


class Question:
    def __init__(self, data):
        self.id = int(str(data['id']).lstrip('#'))  # Convert to int after stripping '#' if present
        self.context = data.get('question_context', '')
        self.text = data['question_text']
        self.type = data['question_type']
        self.choices = data.get('choices', [])
        self.correct_answers = data['correct_answers']
        self.correct_answers_community = data.get('correct_answers_community', [])
        self.case_study_id = data.get('case_study_id')

    def display_image(self, image_filename, caption):
        if f"image_{image_filename}" not in st.session_state:
            image_path = os.path.join('DP-600_Resources', image_filename)
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    st.session_state[f"image_{image_filename}"] = image_file.read()
            else:
                st.error(f"Image file not found: {image_path}")
                return

        image_data = st.session_state[f"image_{image_filename}"]
        image_base64 = base64.b64encode(image_data).decode()
        st.markdown(f'<img src="data:image/png;base64,{image_base64}" alt="{caption}" style="max-width:100%;">', unsafe_allow_html=True)
        st.caption(caption)

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
            return [option[0] for option in selected_options]  # Return only the labels (A, B, C, etc.)
        elif self.type == "single-choice":
            options = [f"{chr(65 + i)}. {choice['text']}" for i, choice in enumerate(self.choices)]
            selected_option = st.radio("Select one option:", options, key=f"question_{self.id}")
            return [selected_option[0]] if selected_option else []  # Return the label as a list
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
        elif self.type in ["multiple-choice", "single-choice"]:
            answer_texts = [f"{ans}. {self.choices[ord(ans) - ord('A')]['text']}" for ans in self.correct_answers]
            st.markdown(f"<p style='font-size:{config.answer_font_size}px;'>{', '.join(answer_texts)}</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='font-size:{config.answer_font_size}px;'>{', '.join(self.correct_answers)}</p>", unsafe_allow_html=True)
        
        if self.correct_answers_community:
            st.markdown(f"<h3 style='font-size:{config.answer_font_size}px;'>Community Suggested Answer:</h3>", unsafe_allow_html=True)
            for answer in self.correct_answers_community:
                st.markdown(f"<p style='font-size:{config.answer_font_size}px;'>{answer}</p>", unsafe_allow_html=True)

    def display_context_with_images(self, config):
        def process_content(content):
            image_pattern = r'!\[(.*?)\]\((.*?)\)'
            parts = re.split(image_pattern, content)
            for i, part in enumerate(parts):
                if i % 3 == 0:  # Text content
                    st.markdown(f"<p style='font-size:{config.body_font_size}px;'>{part}</p>", unsafe_allow_html=True)
                elif i % 3 == 2:  # Image filename
                    self.display_image(part, f"Image {i//3 + 1}")

        # Process context
        process_content(self.context)
        
        # Process question text
        if self.text.strip() != self.context.strip():
            process_content(self.text)

    def check_answer(self, user_answers):
        if self.type in ["multiple-choice", "single-choice"]:
            correct_answers = set(self.correct_answers)
            user_answer_set = set(user_answers)
            return user_answer_set == correct_answers
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'question_context': self.context,
            'question_text': self.text,
            'question_type': self.type,
            'choices': self.choices,
            'correct_answers': self.correct_answers,
            'correct_answers_community': self.correct_answers_community,
            'case_study_id': self.case_study_id
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data)