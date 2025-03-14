import streamlit as st


class ChatManager:
    def __init__(self):
        # Przykładowa struktura danych z dostawcami i modelami
        self.providers_models = {
            "OpenAI": ["GPT-3.5-Turbo", "GPT-4", "GPT-4-Turbo"],
            "Anthropic": ["Claude-2", "Claude-3-Opus", "Claude-3-Sonnet"],
            "Google": ["Gemini-Pro", "Gemini-Ultra", "PaLM-2"],
            "Mistral": ["Mistral-7B", "Mistral-Large", "Mixtral-8x7B"],
            "Meta": ["Llama-2", "Llama-3", "Llama-3-70B"],
        }

        # Domyślnie wybrane wartości
        self.current_provider = "OpenAI"
        self.current_model = "GPT-3.5-Turbo"

    def get_available_models_with_providers(self):
        """Zwraca listę par (provider, model) dla wszystkich dostępnych modeli"""
        result = []
        for provider, models in self.providers_models.items():
            for model in models:
                result.append((provider, model))
        return result

    def get_current_provider_and_model(self):
        """Zwraca aktualnie wybrany provider i model"""
        return self.current_provider, self.current_model

    def set_provider_and_model(self, provider, model):
        """Ustawia wybrany provider i model"""
        self.current_provider = provider
        self.current_model = model

    def get_available_providers(self):
        """Zwraca listę dostępnych providerów"""
        return list(self.providers_models.keys())

    def get_models_for_provider(self, provider):
        """Zwraca listę modeli dla danego providera"""
        return self.providers_models.get(provider, [])

    def get_current_provider(self):
        """Zwraca aktualnie wybranego providera"""
        return self.current_provider

    def get_current_model(self):
        """Zwraca aktualnie wybrany model"""
        return self.current_model


# Inicjalizacja stanu sesji
if "chat_manager" not in st.session_state:
    st.session_state.chat_manager = ChatManager()
    st.session_state.messages = []

chat_manager = st.session_state.chat_manager

# Tytuł aplikacji
st.title("Chat z wyborem dostawców i modeli")

# Metoda 1: Jednolista lista z wszystkimi opcjami (provider - model)
st.sidebar.header("Metoda 1: Wszystkie modele w jednej liście")

provider_model_options = chat_manager.get_available_models_with_providers()
display_options = [f"{provider} - {model}" for provider, model in provider_model_options]

current_provider, current_model = chat_manager.get_current_provider_and_model()
current_index = 0
for i, (provider, model) in enumerate(provider_model_options):
    if provider == current_provider and model == current_model:
        current_index = i
        break

selected_index = st.sidebar.selectbox(
    "Wybierz model",
    options=range(len(display_options)),
    format_func=lambda i: display_options[i],
    index=current_index,
    key="model_single_list",
)

# Pobieramy wybraną parę (provider, model) na podstawie indeksu
if st.sidebar.button("Ustaw model (Metoda 1)"):
    selected_provider, selected_model = provider_model_options[selected_index]
    chat_manager.set_provider_and_model(selected_provider, selected_model)
    st.sidebar.success(f"Ustawiono: {selected_provider} - {selected_model}")

# Metoda 2: Hierarchiczna struktura (najpierw provider, potem jego modele)
st.sidebar.header("Metoda 2: Hierarchiczna struktura")

providers = chat_manager.get_available_providers()
current_provider = chat_manager.get_current_provider()

# Selectbox dla dostawcy
selected_provider = st.sidebar.selectbox(
    "Wybierz dostawcę",
    providers,
    index=providers.index(current_provider) if current_provider in providers else 0,
    key="provider_hierarchical",
)

# Pobierz modele dla wybranego dostawcy
provider_models = chat_manager.get_models_for_provider(selected_provider)
current_model = chat_manager.get_current_model()

# Sprawdź, czy aktualny model jest dostępny dla wybranego dostawcy
model_index = 0
if current_model in provider_models:
    model_index = provider_models.index(current_model)

# Selectbox dla modeli wybranego dostawcy
selected_model = st.sidebar.selectbox(
    f"Wybierz model od {selected_provider}",
    provider_models,
    index=model_index,
    key="model_hierarchical",
)

if st.sidebar.button("Ustaw model (Metoda 2)"):
    chat_manager.set_provider_and_model(selected_provider, selected_model)
    st.sidebar.success(f"Ustawiono: {selected_provider} - {selected_model}")

# Wyświetl aktualnie wybrany model
st.sidebar.header("Aktualnie wybrany")
st.sidebar.info(f"Dostawca: {chat_manager.get_current_provider()}")
st.sidebar.info(f"Model: {chat_manager.get_current_model()}")

# Prosty interfejs czatu do testowania
st.header("Interfejs czatu")

# Wyświetl wcześniejsze wiadomości
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Pole do wprowadzania wiadomości
if prompt := st.chat_input("Wpisz wiadomość..."):
    # Dodaj wiadomość użytkownika do historii
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Wyświetl wiadomość użytkownika
    with st.chat_message("user"):
        st.write(prompt)

    # Zasymuluj odpowiedź od modelu
    response = f"Odpowiedź od {chat_manager.get_current_provider()} / {chat_manager.get_current_model()}: Otrzymałem twój prompt: '{prompt}'"

    # Dodaj odpowiedź bota do historii
    st.session_state.messages.append({"role": "assistant", "content": response})

    # Wyświetl odpowiedź bota
    with st.chat_message("assistant"):
        st.write(response)
