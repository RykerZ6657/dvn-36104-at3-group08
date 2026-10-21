"""Group 08 data narrative: Is AI capability concentrating in fewer organisations?

Each section lives in sections/<name>.py and exposes render().
"""

import streamlit as st

from sections import concentration, geography, openness, overview

st.set_page_config(page_title="Is AI capability concentrating?", layout="wide")

st.title("Is AI capability concentrating in fewer organisations?")
st.caption("Data: Epoch AI, Notable AI Models (CC BY 4.0), 2015–2025. Last data refresh: 21 Oct 2026.")

tabs = st.tabs(["Overview", "Concentration", "Geography", "Openness"])
for tab, section in zip(tabs, [overview, concentration, geography, openness]):
    with tab:
        section.render()
