import re
import streamlit as st
from datetime import datetime
import json
from models.openai import OpenAiChatProvider

def get_next_chat_name(existing_chats):
    index = 1
    while True:
        potential_name = f"Chat {index}"
        if potential_name not in existing_chats:
            return potential_name
        index += 1

def split_response(response):

    think_parts = re.findall(r"<think>(.*?)</think>", response, flags=re.DOTALL)
    normal_part = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    
    return think_parts, normal_part

def check_existing(chat_name, existing_chats):
    index = 1
    if chat_name in existing_chats:
        while True:
            potential_name = f"{chat_name} {index}"
            if potential_name not in existing_chats:
                return potential_name
            index += 1
    return chat_name


def update_chat_history(messages, config):
        # Chat file updated with date of last activity
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        if st.session_state.current_chat:
            st.session_state.history[st.session_state.current_chat]["messages"] = messages
            st.session_state.history[st.session_state.current_chat]["last_active"] = now
        else:
            try:
                chat_name = OpenAiChatProvider.openai_chat_completion_title(messages, config["api_keys"]["openai"])
                chat_name = check_existing(chat_name, st.session_state.history)

            except:
                chat_name = get_next_chat_name(st.session_state.history)

            st.session_state.history[chat_name] = {
                "messages": messages,
                "last_active": now
            }
            st.session_state.current_chat = chat_name
            st.rerun()













































