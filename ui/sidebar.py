import streamlit as st
from datetime import datetime
import logging


def render_sidebar(chat_manager):
    st.sidebar.title("Settings")

    # New chat button
    if st.sidebar.button("New Chat", key="new_chat"):
        chat_manager.new_chat()
        st.rerun()

    # Chat name modification section
    current_chat = chat_manager.get_current_chat_name()

    if current_chat:
        new_chat_name = st.sidebar.text_input("Chat name", current_chat)
        if new_chat_name and new_chat_name != current_chat:
            success = chat_manager.rename_chat(new_chat_name)
            if success:
                st.sidebar.success("Chat name changed")
                st.rerun()
            else:
                st.sidebar.error("You're already using that name!")

    # Select box with models
    provider_model_options = chat_manager.get_available_models_with_providers()
    display_options = [
        f"{provider.value.capitalize()} - {display_name}" for provider, model_id, display_name in provider_model_options
    ]

    current_provider, current_model_id = chat_manager.get_current_provider_and_model()
    current_index = 0
    for i, (provider, model_id, _) in enumerate(provider_model_options):
        if provider == current_provider and model_id == current_model_id:
            current_index = i
            break

    def on_model_change():
        selected_index = st.session_state.model_selectbox
        selected_provider, selected_model_id, _ = provider_model_options[selected_index]
        st.session_state.selected_model_index = selected_index
        chat_manager.set_current_provider_and_model(selected_provider, selected_model_id)

    selected_index = st.sidebar.selectbox(
        "Select model",
        options=range(len(display_options)),
        format_func=lambda i: display_options[i],
        index=current_index,
        key="model_selectbox",
        on_change=on_model_change,
    )

    # Context settings
    with st.sidebar.expander("Context settings"):
        context_length = st.slider("How many past messages to include", min_value=0, max_value=5, value=0)
        chat_manager.set_context_length(context_length)

    # API keys management
    with st.sidebar.expander("API keys"):
        api_providers_and_keys = chat_manager.get_api_providers_and_keys()
        updated_api_keys = {}
        # Dynamically create text inputs for each provider
        for provider, api_key in api_providers_and_keys.items():
            updated_key = st.text_input(
                f"{provider.capitalize()} API Key",
                value=api_key,
                type="password",
                key=f"{provider.upper()}_API_KEY",
            )
            updated_api_keys[provider] = updated_key

        # Update all API keys at once
        chat_manager.set_api_keys(updated_api_keys)

    # Chat history management
    st.sidebar.subheader("History of chats")
    chats = chat_manager.get_all_chats()

    if chats:
        for chat_name, chat_id, last_active in chats:
            container = st.sidebar.container()
            col1, col2 = container.columns([4, 1])

            if isinstance(last_active, str):
                last_active_dt = datetime.strptime(last_active, "%d-%m-%Y %H:%M:%S")
                display_time = last_active_dt.strftime("%d-%m-%Y %H:%M")
            elif isinstance(last_active, datetime):
                display_time = last_active.strftime("%d-%m-%Y %H:%M")
            else:
                display_time = ""

            with col1:
                if st.button(f"{chat_name} ({display_time})", key=f"chat_{chat_name}"):
                    chat_manager.set_current_chat(chat_id)
                    st.rerun()

            with col2:
                if st.button("X", key=f"delete_{chat_name}"):
                    chat_manager.delete_chat(chat_name)
                    st.rerun()
    else:
        st.sidebar.write("Empty chat history")

    # Save all changes
    chat_manager.config.save_to_file()
