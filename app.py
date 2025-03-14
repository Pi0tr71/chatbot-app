import streamlit as st
import logging
import tiktoken

from ui.css import inject_css
from ui.sidebar import render_sidebar
from ui.chat_interface import render_chat_interface


from chat_manager import ChatManager

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Apply custom CSS
    inject_css()

    # Initialize the ChatManager
    if "chat_manager" not in st.session_state:
        st.session_state.chat_manager = ChatManager()

    # Render the sidebar
    render_sidebar(st.session_state.chat_manager)

    # Render the chat interface
    render_chat_interface(st.session_state.chat_manager)
