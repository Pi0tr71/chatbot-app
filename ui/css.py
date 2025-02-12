import streamlit as st

def inject_css():
    st.markdown(
        """
        <style>
        div.stButton > button {
            width: 100%;
            text-align: left;
            justify-content: left;
        }
        </style>
        """,
        unsafe_allow_html=True
    )