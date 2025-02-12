import streamlit as st
import logging
import tiktoken

from ui.css import inject_css
from ui.sidebar import render_side
from ui.chat_interface import render_chat_interface

from utils.history import load_history
from utils.config import load_config

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    enc = tiktoken.encoding_for_model("gpt-4")

    inject_css()

    # Inicjalizacja historii oraz bieżącego czatu w sesji
    if "history" not in st.session_state:
        st.session_state.history = load_history()
    if "current_chat" not in st.session_state:
        st.session_state.current_chat = None

    # Wczytanie konfiguracji
    config = load_config()

    #PASEK BOCZNY
    render_side(config)
    render_chat_interface(config, enc)


