import streamlit as st
from theme import inject_theme, sidebar_brand, sidebar_footer

st.set_page_config(page_title="PlantMind AI", layout="wide", initial_sidebar_state="expanded")
inject_theme()
sidebar_brand()

pages = [
    st.Page("views/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
    st.Page("views/expert_copilot.py", title="Expert Copilot", icon=":material/forum:"),
    st.Page("views/knowledge_graph.py", title="Knowledge Graph", icon=":material/hub:"),
    st.Page("views/maintenance.py", title="Maintenance", icon=":material/build:"),
    st.Page("views/compliance.py", title="Compliance", icon=":material/verified:"),
    st.Page("views/analytics.py", title="Analytics", icon=":material/insights:"),
    st.Page("views/documents.py", title="Documents", icon=":material/folder:"),
]

nav = st.navigation(pages, position="sidebar")
sidebar_footer()
nav.run()