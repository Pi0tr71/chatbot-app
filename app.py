import streamlit as st
import logging
import os
from pathlib import Path

from ui.css import inject_css
from ui.chat_sidebar import render_chat_sidebar
from ui.chat_interface import render_chat_interface

from ui.models_interface import render_config_models_interface
from ui.models_sidebar import render_config_models_sidebar

from chat_manager import ChatManager
from utils.model_config import CONFIG_PATH

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Apply custom CSS
    inject_css()

    # Initialize the ChatManager
    if "chat_manager" not in st.session_state:
        st.session_state.chat_manager = ChatManager()

    # Check if config file exists
    if not os.path.exists(CONFIG_PATH):
        # If config file doesn't exist, show provider config page
        st.session_state.show_provider_config = True

    # Initialize session state for provider config page
    if "show_provider_config" not in st.session_state:
        st.session_state.show_provider_config = False

    # Render the appropriate page
    if st.session_state.show_provider_config:
        render_config_models_interface(st.session_state.chat_manager)
        render_config_models_sidebar()
    else:
        render_chat_interface(st.session_state.chat_manager)
        render_chat_sidebar(st.session_state.chat_manager)
