import streamlit as st
from datetime import datetime
from utils.history import save_history
from utils.helpers import get_next_chat_name
from utils.costs import load_costs
from utils.config import save_config

def render_side(config):
    
    st.sidebar.title("Settings")

    #New chat button
    if st.sidebar.button("New Chat", key="new_chat"):
        st.session_state.current_chat = None

    #Changing chat name
    if st.session_state.current_chat:
        new_chat_name = st.sidebar.text_input("Chat name", st.session_state.current_chat)
        if new_chat_name and new_chat_name != st.session_state.current_chat:
            if new_chat_name in st.session_state.history:
                st.sidebar.error("You're already using that name!")
            else:
                st.session_state.history[new_chat_name] = st.session_state.history.pop(st.session_state.current_chat)
                st.session_state.current_chat = new_chat_name
                save_history(st.session_state.history)
                st.sidebar.success("Chat name changed")
                st.rerun()

    # Models to select
    model_options = [
        "gpt-4o",
        "gpt-4o-mini",
        "o1-preview",
        "o1-mini",
        "DeepSeek-R1-671B",
        "DeepSeek-R1-Distill-70B",
        "Tulu-3-405B",
    ]

    # Select box with models
    selected_model = st.sidebar.selectbox("Select model", model_options)
    config["model"] = selected_model

    #Context settings
    with st.sidebar.expander("Context settings"):
        st.session_state.context_length = st.slider("How many past messages to include (past user messages)", min_value=0, max_value=5, value=0)
        
    # Inputs for API keys
    with st.sidebar.expander("API keys"):
        openai_key = st.text_input("OpenAI API Key", value=config["api_keys"]["openai"], type="password")
        nebius_key = st.text_input("Nebius API Key", value=config["api_keys"]["nebius"], type="password")
        sambanova_key = st.text_input("Sambanova API Key", value=config["api_keys"]["sambanova"], type="password")

        # Save config
        if st.button("Save settings"):
            config["api_keys"]["openai"] = openai_key
            config["api_keys"]["nebius"] = nebius_key
            config["api_keys"]["sambanova"] = sambanova_key
            save_config(config)
            st.success("Settings saved!")
            
    # Cost displaying
    costs = load_costs()

    with st.sidebar.expander("Costs of using models"):
        if not costs:
            st.write("No cost data.")
        else:
            total_cost = 0
            for model, data in costs.items():
                st.write(f"### {model}")
                st.write(f"- Prompt tokens: {data['input_tokens']}")
                st.write(f"- Completion tokens: {data['output_tokens']}")
                st.write(f"- Total cost: **{data['total_cost']:.4f}$**")
                st.write("---")
                total_cost += data['total_cost']

            st.write(f"### Total cost of all models: **{total_cost:.4f}$**")
            

    # Chat history displaying
    def render_chat_list():
        st.sidebar.subheader("History of chats")
        chat_names = list(st.session_state.history.keys())

        if chat_names:
            chat_last_active = []
            chat_last_active_without_date = []
            for chat in chat_names:

                last_active = st.session_state.history[chat].get("last_active", "No data")
                if last_active == "No data" or last_active == None:
                    chat_last_active_without_date.append((chat, last_active))
                else:
                    last_active_dt = datetime.strptime(last_active, "%d-%m-%Y %H:%M:%S")
                    chat_last_active.append((chat, last_active_dt))

            if chat_last_active:
                chat_last_active.sort(key=lambda x: x[1], reverse=True)
                                  
            chat_last_active.extend(chat_last_active_without_date)

            for chat, last_active in chat_last_active:
                container = st.sidebar.container()
                col1, col2 = container.columns([4, 1]) 
                
                with col1:
                    if st.button(f"{chat} ({last_active.strftime("%d-%m-%Y %H:%M")})", key=f"chat_{chat}"):
                        st.session_state.current_chat = chat
                        st.rerun()

                with col2:
                    if st.button("X", key=f"delete_{chat}"):
                        del st.session_state.history[chat]
                        if st.session_state.current_chat == chat:
                            st.session_state.current_chat = None
                        save_history(st.session_state.history)
                        st.rerun()
        else:
            st.sidebar.write("Empty chat history")

    render_chat_list()