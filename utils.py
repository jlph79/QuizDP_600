import streamlit as st
from typing import Tuple, List, Dict
from question import Question
from case_study import CaseStudy
import secrets
from database import get_connection
import psycopg2
import json

@st.cache_data
def load_questions_and_case_studies(image_dir: str) -> Tuple[List[Question], Dict[str, CaseStudy]]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                # Load questions
                cursor.execute("SELECT * FROM questions")
                questions_data = cursor.fetchall()
               #  st.write(f"Loaded {len(questions_data)} questions from the database.")
               # st.write("Raw questions data (first 5 rows):")
               #  st.write(json.dumps(questions_data[:5], indent=2, default=str))
                
                if not questions_data:
                    st.warning("No questions found in the database.")
                
                questions = []
                for q in questions_data:
                    try:
                        questions.append(Question(q))
                    except Exception as e:
                        st.error(f"Error creating Question object: {str(e)}")
                        st.write(f"Problematic question data: {json.dumps(q, default=str)}")

                # Load case studies
                cursor.execute("SELECT * FROM case_studies")
                case_studies_data = cursor.fetchall()
                #st.write(f"Loaded {len(case_studies_data)} case studies from the database.")
                #st.write("Raw case studies data (first 5 rows):")
                #st.write(json.dumps(case_studies_data[:5], indent=2, default=str))
                
                if not case_studies_data:
                    st.warning("No case studies found in the database.")
                
                case_studies = {}
                for cs in case_studies_data:
                    try:
                        case_studies[cs['id']] = CaseStudy(cs, image_dir)
                    except Exception as e:
                        st.error(f"Error creating CaseStudy object: {str(e)}")
                        st.write(f"Problematic case study data: {json.dumps(cs, default=str)}")

        return questions, case_studies
    except psycopg2.Error as e:
        st.error(f"Database error: {e}")
        return [], {}
    except Exception as e:
        st.error(f"Error loading questions and case studies: {str(e)}")
        return [], {}

def generate_temp_token():
    return secrets.token_urlsafe(32)