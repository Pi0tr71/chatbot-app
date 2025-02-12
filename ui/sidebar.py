import streamlit as st
from datetime import datetime
from utils.history import save_history
from utils.helpers import get_next_chat_name
from utils.costs import load_costs
from utils.config import save_config

def render_side(config):
    
    # USTAWIENIA W PASKU BOCZNYM
    st.sidebar.title("Ustawienia")

    # Dodanie przycisku "Nowy Chat" na górze
    if st.sidebar.button("Nowy Chat", key="new_chat"):
        st.session_state.current_chat = None

    # Możliwość zmiany nazwy czatu
    if st.session_state.current_chat:
        new_chat_name = st.sidebar.text_input("Nazwa czatu", st.session_state.current_chat)
        if new_chat_name and new_chat_name != st.session_state.current_chat:
            if new_chat_name in st.session_state.history:
                st.sidebar.error("Już używasz takiej nazwy!")
            else:
                st.session_state.history[new_chat_name] = st.session_state.history.pop(st.session_state.current_chat)
                st.session_state.current_chat = new_chat_name
                save_history(st.session_state.history)
                st.sidebar.success("Zmieniono nazwę czatu!")
                st.rerun()

    # Wybór modelu
    model_options = [
        "gpt-4o",
        "gpt-4o-mini",
        "o1-preview",
        "o1-mini",
        "DeepSeek-R1-671B",
        "DeepSeek-R1-Distill-70B",
        "Tulu-3-405B",
    ]

    # Tworzymy selectbox (usuwamy pogrubione nagłówki z wartości)
    selected_model = st.sidebar.selectbox("Wybierz model", model_options)
    config["model"] = selected_model

    #Ustawienia kontekstu
    with st.sidebar.expander("Ustawienia kontekstu"):
        st.session_state.context_length = st.slider("Ile wiadomości wstecz uwzględnić", min_value=0, max_value=5, value=0)

    # Wprowadzenie kluczy API
    with st.sidebar.expander("Klucze API"):
        openai_key = st.text_input("OpenAI API Key", value=config["api_keys"]["openai"], type="password")
        nebius_key = st.text_input("Nebius API Key", value=config["api_keys"]["nebius"], type="password")
        sambanova_key = st.text_input("Sambanova API Key", value=config["api_keys"]["sambanova"], type="password")
        
        # Zapis konfiguracji
        if st.button("Zapisz ustawienia"):
            config["api_keys"]["openai"] = openai_key
            config["api_keys"]["nebius"] = nebius_key
            config["api_keys"]["sambanova"] = sambanova_key
            save_config(config)
            st.success("Ustawienia zapisane!")

    #WYŚWIETLANIE KOSZTÓW
    costs = load_costs()

    with st.sidebar.expander("Koszty użycia modeli"):
        if not costs:
            st.write("Brak danych o kosztach.")
        else:
            total_cost = 0
            for model, data in costs.items():
                st.write(f"### {model}")
                st.write(f"- Tokeny wejściowe: {data['input_tokens']}")
                st.write(f"- Tokeny wyjściowe: {data['output_tokens']}")
                st.write(f"- Łączny koszt: **{data['total_cost']:.4f}$**")
                st.write("---")
                total_cost += data['total_cost']

            st.write(f"### Łączny koszt wszystkich modeli: **{total_cost:.4f}$**")
            

    # WYŚWIETLANIE HISTORII CZATÓW
    def render_chat_list():
        st.sidebar.subheader("Historia czatów")
        chat_names = list(st.session_state.history.keys())

        if chat_names:
            chat_last_active = []
            chat_last_active_without_date = []
            for chat in chat_names:

                last_active = st.session_state.history[chat].get("last_active", "Brak danych")
                if last_active == "Brak danych" or last_active == None:
                    chat_last_active_without_date.append((chat, last_active))
                else:
                    last_active_dt = datetime.strptime(last_active, "%d-%m-%Y %H:%M")
                    last_active_dt = last_active_dt.strftime("%d-%m-%Y %H:%M")
                    chat_last_active.append((chat, last_active_dt))

            if chat_last_active:
                chat_last_active.sort(key=lambda x: x[1], reverse=True)
                                  
            chat_last_active.extend(chat_last_active_without_date)

            for chat, last_active in chat_last_active:
                # Tworzymy kontener z dwiema kolumnami
                container = st.sidebar.container()
                col1, col2 = container.columns([4, 1])  # dostosuj szerokości kolumn wg uznania
                
                with col1:
                    if st.button(f"{chat} ({last_active})", key=f"chat_{chat}"):
                        st.session_state.current_chat = chat
                        st.rerun()

                with col2:
                    if st.button("X", key=f"delete_{chat}"):
                        # Usuwamy czat z historii
                        del st.session_state.history[chat]
                        # Jeśli usuwany czat był aktualnie wybrany, resetujemy current_chat
                        if st.session_state.current_chat == chat:
                            st.session_state.current_chat = None
                        save_history(st.session_state.history)
                        # Wymuszenie przeładowania aplikacji, aby odświeżyć widok
                        st.rerun()
        else:
            st.sidebar.write("Brak historii czatów")

    render_chat_list()