import streamlit as st


def render_config_models_sidebar():

    if st.sidebar.button("Back to Chats"):
        st.session_state.show_provider_config = False
        st.rerun()
