import streamlit as st
from datetime import datetime

from models.openai import openai_chat_completion
from models.nebius import nebius_chat_completion
from models.sambanova import sambanova_chat_completion

from utils.helpers import split_response, get_next_chat_name
from utils.costs import cost_cal
from utils.history import save_history
from utils.costs import update_costs

def render_chat_interface(config, enc):
     # INTERFEJS CZATU
    st.title("Chatbot")
    st.write("Wybrany model: ", config["model"])

    # Pobieramy wiadomości z bieżącego czatu
    if st.session_state.current_chat:
        messages = st.session_state.history[st.session_state.current_chat]["messages"]
    else:
        messages = []

    # Wyświetlanie historii wiadomości
    for msg in messages:
        think_parts, normal_part = split_response(msg["content"])
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                # Wyświetlamy wszystkie fragmenty <think> jako szare i pochylone
                for think_part in think_parts:
                    st.markdown(f"<span style='color:gray; font-style:italic'>{think_part}</span>", unsafe_allow_html=True)

                if normal_part:
                    st.write(normal_part)
            else:
                st.write(msg["content"]) 


    # Pole tekstowe do wpisania wiadomości przez użytkownika

    user_input = st.chat_input("Wpisz wiadomość...")
    if user_input:
        messages.append({"role": "user", "content": user_input})
        input_tokens = len(enc.encode(user_input))
        with st.chat_message("user"):
            st.write(user_input)
            st.write(f"Input tokens: {input_tokens}, koszty: {cost_cal(config['model'], input_tokens, True):.6f}$")
        
        with st.spinner("Waiting for response..."):
            try:

                context_length = st.session_state.get('context_length', 0)

                if config['model'] in ["gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini"]:
                    response = openai_chat_completion(messages, config['model'], config["api_keys"]["openai"], context_length*2)

                elif config['model'] in ["DeepSeek-R1-671B"]:
                    response = nebius_chat_completion(messages, config['model'], config["api_keys"]["nebius"], context_length*2)

                elif config['model'] in ["DeepSeek-R1-Distill-70B", "Tulu-3-405B"]:
                    response = sambanova_chat_completion(messages, config['model'], config["api_keys"]["sambanova"], context_length*2)
                    
                else: 
                    response = "Jeszcze nie odsługiwany"

                output_tokens = len(enc.encode(response))

                think_parts, normal_part = split_response(response) 
                messages.append({"role": "assistant", "content": response})
                
                with st.chat_message("assistant"):
                    for think_part in think_parts:
                        st.markdown(f"<span style='color:gray; font-style:italic'>{think_part}</span>", unsafe_allow_html=True)
                    if normal_part:
                        st.write(normal_part)

                    st.write(f"Output tokens: {output_tokens}, koszty: {cost_cal(config['model'], output_tokens, False):.6f}$")

                update_costs(config['model'], input_tokens, output_tokens)

                # Aktualizacja historii czatu z datą ostatniej aktywności
                now = datetime.now().strftime("%d-%m-%Y %H:%M")
                if st.session_state.current_chat:
                    st.session_state.history[st.session_state.current_chat]["messages"] = messages
                    st.session_state.history[st.session_state.current_chat]["last_active"] = now
                else:
                    try:
                        topic = []
                        topic.append({"role": "user", "content": user_input})
                        topic.append({"role": "user", "content": "Jakiej tematyki dotyczyło poprzenie pytanie napisz w maksymalnie 5 słowach"})
                        chat_name = openai_chat_completion(topic, 'gpt-4o-mini', config["api_keys"]["openai"], 1)
                    except: 
                        chat_name = get_next_chat_name(st.session_state.history)
                    st.session_state.history[chat_name] = {"messages": messages, "last_active": now}
                    st.session_state.current_chat = chat_name
                    st.rerun()
                save_history(st.session_state.history)

            except Exception as e:
                st.error(f"Wystąpił błąd podczas uzyskiwania odpowiedzi: {e}")