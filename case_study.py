import streamlit as st
import os
import markdown
from bs4 import BeautifulSoup
from typing import Dict, Union, List

class CaseStudy:
    def __init__(self, data: Dict[str, Union[str, Dict[str, str], Dict[str, List[str]]]], image_dir: str):
        self.id = data['id']
        self.overview = data.get('overview', '')
        self.existing_environment = data.get('existing_environment', {})
        self.requirements = data.get('requirements', {})
        self.image_dir = image_dir

    def _render_markdown(self, text: str) -> str:
        html = markdown.markdown(text)
        soup = BeautifulSoup(html, 'html.parser')
        for img in soup.find_all('img'):
            img_path = os.path.join(self.image_dir, img['src'])
            if os.path.exists(img_path):
                st.image(img_path, use_column_width=True)
            else:
                st.warning(f"Image not found: {img['src']}")
            img.decompose()
        return str(soup)

    def display(self, config):
        st.markdown(f"<h2 style='font-size:{config.header_font_size}px;'>Case Study: {self.id}</h2>", unsafe_allow_html=True)
        
        if self.overview:
            st.markdown(f"<h3 style='font-size:{config.header_font_size - 2}px;'>Overview</h3>", unsafe_allow_html=True)
            st.markdown(self._render_markdown(self.overview), unsafe_allow_html=True)
        
        if self.existing_environment:
            st.markdown(f"<h3 style='font-size:{config.header_font_size - 2}px;'>Existing Environment</h3>", unsafe_allow_html=True)
            for key, value in self.existing_environment.items():
                st.markdown(f"<h4 style='font-size:{config.header_font_size - 4}px;'>{key.replace('_', ' ').title()}</h4>", unsafe_allow_html=True)
                st.markdown(self._render_markdown(value), unsafe_allow_html=True)
        
        if self.requirements:
            st.markdown(f"<h3 style='font-size:{config.header_font_size - 2}px;'>Requirements</h3>", unsafe_allow_html=True)
            for key, value in self.requirements.items():
                st.markdown(f"<h4 style='font-size:{config.header_font_size - 4}px;'>{key.replace('_', ' ').title()}</h4>", unsafe_allow_html=True)
                if isinstance(value, list):
                    for item in value:
                        st.markdown(self._render_markdown(f"- {item}"), unsafe_allow_html=True)
                else:
                    st.markdown(self._render_markdown(value), unsafe_allow_html=True)