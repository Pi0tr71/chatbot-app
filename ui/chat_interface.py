import streamlit as st
from datetime import datetime
import json

from models.openai import openai_chat_completion, openai_chat_completion_title
from models.nebius import nebius_chat_completion
from models.sambanova import sambanova_chat_completion

from utils.helpers import split_response, get_next_chat_name, check_existing
from utils.costs import cost_cal
from utils.history import save_history
from utils.costs import update_costs


def render_chat_interface(config, enc):
     # CHAT INTERFACE
    st.title("Chatbot")
    st.write("Selected model: ", config["model"])

    # Retrieving messages from the current chat
    if st.session_state.current_chat:
        messages = st.session_state.history[st.session_state.current_chat]["messages"]
    else:
        messages = []

    # Displaying all messeges from chat
    for msg in messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":

                think_parts, normal_part = split_response(msg["content"])

                for think_part in think_parts:
                    st.markdown(f"<span style='color:gray; font-style:italic'>{think_part}</span>", unsafe_allow_html=True)

                if normal_part:
                    st.write(normal_part)

                st.markdown(f"<div style='text-align: right;'><i>Model: {msg["model"]}: Used tokens: {msg["tokens_used"]}, Price: {msg["cost"]:.6f}$</i></div>", unsafe_allow_html=True)
            else:
                st.write(msg["content"]) 
                st.markdown(f"<div style='text-align: right;'><i>Used tokens: {msg["tokens_used"]}, Price: {msg["cost"]:.6f}$</i></div>", unsafe_allow_html=True)


    # text field for the user to enter a message

    user_input = st.chat_input("Enter your message...")
    if user_input:
        input_tokens = len(enc.encode(user_input))
        input_cost = cost_cal(config['model'], input_tokens, True)

        messages.append({
            "role": "user", 
            "content": user_input,
            "tokens_used": input_tokens,
            "cost": input_cost,
            "model": config["model"]
        })
        
        
        with st.chat_message("user"):
            st.write(user_input)
            st.markdown(f"<div style='text-align: right;'><i>Used tokens: {input_tokens}, Cost: {input_cost:.6f}$</i></div>", unsafe_allow_html=True)
        
        with st.spinner("Waiting for response..."):
            try:

                context_length = st.session_state.get('context_length', 0)

                if config['model'] in ["gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini"]:
                    response, input_tokens, output_tokens  = openai_chat_completion(messages, config['model'], config["api_keys"]["openai"], context_length*2)

                elif config['model'] in ["DeepSeek-R1-671B"]:
                    response = nebius_chat_completion(messages, config['model'], config["api_keys"]["nebius"], context_length*2)
                    output_tokens = len(enc.encode(response))

                elif config['model'] in ["DeepSeek-R1-Distill-70B", "Tulu-3-405B"]:
                    response = sambanova_chat_completion(messages, config['model'], config["api_keys"]["sambanova"], context_length*2)
                    output_tokens = len(enc.encode(response))
                    
                else: 
                    response = "Jeszcze nie odsługiwany"

                input_cost = cost_cal(config['model'], input_tokens, True)
                output_cost = cost_cal(config['model'], output_tokens, False)


                messages.append({
                    "role": "assistant", 
                    "content": response,
                    "tokens_used": output_tokens,
                    "cost": output_cost,
                    "model": config["model"]
                })

                think_parts, normal_part = split_response(response) 
                with st.chat_message("assistant"):
                    for think_part in think_parts:
                        st.markdown(f"<span style='color:gray; font-style:italic'>{think_part}</span>", unsafe_allow_html=True)
                    if normal_part:
                        st.write(normal_part)

                    st.markdown(f"<div style='text-align: right;'><i>Model: {config["model"]}: Used tokens: {output_tokens}, Cost: {output_cost:.6f}$</i></div>", unsafe_allow_html=True)
            
            except Exception as e:
                st.error(f"Error occurred while retrieving the response: {e}")

        update_costs(config['model'], input_tokens, output_tokens)

        # Chat file updated with date of last activity
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        if st.session_state.current_chat:
            st.session_state.history[st.session_state.current_chat]["messages"] = messages
            st.session_state.history[st.session_state.current_chat]["last_active"] = now
        else:
            try:
                chat_name = openai_chat_completion_title(messages, config["api_keys"]["openai"])
                chat_name = check_existing(chat_name, st.session_state.history)
                    
            except: 
                chat_name = get_next_chat_name(st.session_state.history)

            st.session_state.history[chat_name] = {
                "messages": messages,
                "last_active": now
            }
            st.session_state.current_chat = chat_name
            st.rerun()
        save_history(st.session_state.history)

            