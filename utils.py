import json
import streamlit as st
from typing import Tuple, List, Dict
from question import Question
from case_study import CaseStudy
import os

# Use os.path.join to create a path that works in both environments
JSON_PATH = os.path.join("DP-600_Resources", "DP600_QuestionsAnswersV2.json")

@st.cache_data
def load_questions_and_case_studies(image_dir: str) -> Tuple[List[Question], Dict[str, CaseStudy]]:
    try:
        with open(JSON_PATH, 'r') as file:
            data = json.load(file)
        questions = [Question(q) for q in data['questions']]
        case_studies = {cs['id']: CaseStudy(cs, image_dir) for cs in data['case_studies']}
        return questions, case_studies
    except FileNotFoundError:
        st.error(f"JSON file not found at path: {JSON_PATH}")
        return [], {}
    except json.JSONDecodeError:
        st.error(f"Invalid JSON format in file: {JSON_PATH}")
        return [], {}