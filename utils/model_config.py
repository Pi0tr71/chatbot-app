from enum import StrEnum
import json
import os
from pathlib import Path
from typing import List, Optional, Union, Dict
from pydantic import BaseModel, Field
import logging

CONFIG_PATH = Path("json_files/model_config.json")


class Provider(StrEnum):
    """Enum representing available AI providers."""

    OPENAI = "openai"
    SAMBONOVA = "sambanova"
    ANTHROPIC = "anthropic"


class FileType(StrEnum):
    """Enum for file types supported by models."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PDF = "pdf"


class ModelConfig(BaseModel):
    """Configuration for an AI model."""

    model_id: str
    display_name: str
    price_input_tokens: float
    price_output_tokens: float
    max_context_tokens: int
    supported_file_types: List[FileType] = []
    additional_params: Dict[str, Union[str, int, float, bool, list, dict]] = Field(default_factory=dict)


class ProviderConfig(BaseModel):
    api_key: str
    base_url: str
    models: Dict[str, ModelConfig] = Field(default_factory=dict)

    def add_model(self, model_id: str, model_config: ModelConfig) -> None:
        """Add a new model to this provider."""
        self.models[model_id] = model_config

    def get_model(self, model_id: str) -> Optional[ModelConfig]:
        """Get a model by its ID."""
        return self.models.get(model_id)


class RecentModel(BaseModel):
    """Structure to hold information about the most recently used model."""

    provider: Provider
    model_id: str


class Config(BaseModel):
    """Main application configuration."""

    providers: Dict[Provider, ProviderConfig] = Field(default_factory=dict)
    recent_model: Optional[RecentModel] = None

    def add_provider(self, provider: Provider, config: ProviderConfig) -> None:
        """Add a new provider with its configuration."""
        self.providers[provider] = config

    def get_provider(self, provider: Provider) -> Optional[ProviderConfig]:
        """Get a provider configuration."""
        return self.providers.get(provider)

    def get_model(self, provider: Provider, model_id: str) -> Optional[ModelConfig]:
        """Get a specific model from a provider."""
        provider_config = self.get_provider(provider)
        if provider_config:
            return provider_config.get_model(model_id)
        return None

    def set_recent_model(self, provider: Provider, model_id: str) -> None:
        """Set the most recently used model."""
        self.recent_model = RecentModel(provider=provider, model_id=model_id)

    def get_recent_model(self) -> Optional[RecentModel]:
        """Get the provider of the most recently used model."""
        if self.recent_model:
            return self.recent_model
        return None

    def save_to_file(self, path: str = None) -> None:
        """Save configuration to a JSON file only if it changed."""
        file_path = path if path is not None else CONFIG_PATH

        # Check if the file exists
        if os.path.exists(file_path):
            try:
                # Read current file content
                with open(file_path, "r") as f:
                    current_content = f.read()

                # Generate new content
                new_content = self.model_dump_json(indent=2)

                # Compare contents
                if current_content == new_content:
                    # logging.info(f"Config: No changes detected, skipping save")
                    return
            except Exception as e:
                # If there's any error reading the file, proceed with saving
                logging.warning(f"Config: Error comparing files, proceeding with save: {e}")
            with open(file_path, "w") as f:
                f.write(self.model_dump_json(indent=2))
                logging.info(f"Config: Changes detected, saved")

    @classmethod
    def load_from_file(cls, path: Optional[str] = CONFIG_PATH) -> "Config":
        """Load configuration from a JSON file."""
        if path is None or not os.path.exists(path):
            logging.info(f"Config: No data to load")
            return cls()

        with open(path, "r") as f:
            data = json.load(f)
            logging.info(f"Config: Data loaded")
            return cls.model_validate(data)


# # Example usage
# def create_example_config() -> Config:
#     """Create an example configuration with sample providers and models."""
#     config = Config()

#     # OpenAI configuration
#     openai_config = ProviderConfig(api_key="YOUR_OPENAI_KEY", base_url="https://api.openai.com/v1")

#     # Add OpenAI models
#     openai_config.add_model(
#         "gpt-4o",
#         ModelConfig(
#             model_id="gpt-4o",
#             display_name="GPT-4o",
#             price_input_tokens=0.03,
#             price_output_tokens=0.06,
#             max_context_tokens=8192,
#             supported_file_types=[FileType.TEXT, FileType.IMAGE],
#             description="OpenAI's most capable model",
#         ),
#     )

#     openai_config.add_model(
#         "gpt-3.5-turbo",
#         ModelConfig(
#             model_id="gpt-3.5-turbo",
#             display_name="GPT-3.5 Turbo",
#             price_input_tokens=0.045,
#             price_output_tokens=0.2342,
#             max_context_tokens=4096,
#             supported_file_types=[FileType.TEXT],
#         ),
#     )

#     # Add OpenAI provider
#     config.add_provider(Provider.OPENAI, openai_config)

#     # Anthropic configuration
#     anthropic_config = ProviderConfig(api_key="YOUR_ANTHROPIC_KEY", base_url="https://api.anthropic.com")

#     # Add Anthropic models
#     anthropic_config.add_model(
#         "claude-3-opus",
#         ModelConfig(
#             model_id="claude-3-opus",
#             display_name="Claude 3 Opus",
#             price_input_tokens=0.045,
#             price_output_tokens=0.2342,
#             max_context_tokens=4096,
#             supported_file_types=[FileType.TEXT, FileType.IMAGE, FileType.PDF],
#             description="Anthropic's most powerful model",
#         ),
#     )

#     anthropic_config.add_model(
#         "claude-3-sonnet",
#         ModelConfig(
#             model_id="claude-3-sonnet",
#             display_name="Claude 3 Sonnet",
#             price_input_tokens=0.045,
#             price_output_tokens=0.2342,
#             max_context_tokens=4096,
#             supported_file_types=[FileType.TEXT, FileType.IMAGE],
#         ),
#     )

#     # Add Anthropic provider
#     config.add_provider(Provider.ANTHROPIC, anthropic_config)

#     return config


# if __name__ == "__main__":
#     CONFIG_PATH = Path("json_files/model_config.json")
#     config = create_example_config()
#     config.save_to_file()

# # ==========================================
# # PRZYKŁADY UŻYCIA FUNKCJI Z KLAS
# # ==========================================

# # 1. Tworzenie własnej konfiguracji od podstaw
# def przyklad_tworzenia_konfiguracji():
#     print("=== Przykład 1: Tworzenie konfiguracji ===")
#     # Utwórz nową konfigurację
#     app_config = Config()

#     # Dodaj nowego dostawcę (SambaNova)
#     sambanova_config = ProviderConfig(api_key="YOUR_SAMBANOVA_KEY", base_url="https://api.sambanova.ai")

#     # Dodaj model do dostawcy SambaNova
#     sambanova_config.add_model(
#         "sambanova-1",
#         ModelConfig(
#             model_id="sambanova-1",
#             display_name="SambaNova Base",
#             price_input_tokens=0.01,
#             price_output_tokens=0.02,
#             max_context_tokens=8192,
#             supported_file_types=[FileType.TEXT],
#             additional_params={"temperature": 0.7},
#         ),
#     )

#     # Dodaj dostawcę do konfiguracji aplikacji
#     app_config.add_provider(Provider.SAMBONOVA, sambanova_config)

#     # Ustaw model domyślny dla SambaNova
#     app_config.default_model_by_provider[Provider.SAMBONOVA] = "sambanova-1"

#     # Zapisz konfigurację do pliku
#     os.makedirs("json_files", exist_ok=True)
#     app_config.save_to_file("json_files/nowa_konfiguracja.json")
#     print(f"Konfiguracja zapisana do pliku: json_files/nowa_konfiguracja.json")

# # 2. Pobieranie informacji o modelu
# def przyklad_pobierania_informacji():
#     print("\n=== Przykład 2: Pobieranie informacji ===")
#     # Utwórz przykładową konfigurację
#     config = create_example_config()

#     # Pobierz informacje o dostawcy
#     openai_provider = config.get_provider(Provider.OPENAI)
#     print(f"Adres API OpenAI: {openai_provider.base_url}")

#     # Pobierz informacje o modelu
#     gpt4_model = config.get_model(Provider.OPENAI, "gpt-4o")
#     print(f"Model: {gpt4_model.display_name}")
#     print(f"Maksymalna liczba tokenów: {gpt4_model.max_context_tokens}")
#     print(f"Cena za tokeny wejściowe: ${gpt4_model.price_input_tokens}")
#     print(f"Obsługiwane typy plików: {', '.join(gpt4_model.supported_file_types)}")

#     # Pobierz domyślny model dla dostawcy
#     default_model_id = config.get_default_model(Provider.ANTHROPIC)
#     print(f"Domyślny model Anthropic: {default_model_id}")

#     # Pobierz szczegóły domyślnego modelu
#     default_model = config.get_model(Provider.ANTHROPIC, default_model_id)
#     print(f"Nazwa domyślnego modelu: {default_model.display_name}")

# # 3. Śledzenie ostatnio używanych modeli
# def przyklad_sledzenia_uzywanych_modeli():
#     print("\n=== Przykład 3: Śledzenie używanych modeli ===")
#     # Utwórz przykładową konfigurację
#     config = create_example_config()

#     print("Początkowa lista używanych dostawców:", config.recent_providers)

#     # Ustaw ostatnio używane modele
#     config.set_recent_model(Provider.ANTHROPIC, "claude-3-opus")
#     config.set_recent_model(Provider.OPENAI, "gpt-4o")
#     config.set_recent_model(Provider.ANTHROPIC, "claude-3-sonnet")  # Nadpisuje poprzedni model Anthropic

#     print("Ostatnio używani dostawcy (w kolejności):", config.recent_providers)
#     print("Ostatnio używane modele:")
#     for provider in config.recent_providers:
#         model_id = config.get_recent_model(provider)
#         print(f"  - {provider}: {model_id}")

# # 4. Wczytywanie i modyfikacja konfiguracji z pliku
# def przyklad_wczytywania_i_modyfikacji():
#     print("\n=== Przykład 4: Wczytywanie i modyfikacja konfiguracji ===")
#     # Najpierw zapisz przykładową konfigurację
#     config = create_example_config()
#     os.makedirs("json_files", exist_ok=True)
#     config.save_to_file("json_files/config_do_modyfikacji.json")

#     # Wczytaj konfigurację z pliku
#     loaded_config = Config.load_from_file("json_files/config_do_modyfikacji.json")
#     print("Wczytano konfigurację z pliku")

#     # Dodaj nowy model do istniejącego dostawcy
#     anthropic_config = loaded_config.get_provider(Provider.ANTHROPIC)
#     anthropic_config.add_model(
#         "claude-3-haiku",
#         ModelConfig(
#             model_id="claude-3-haiku",
#             display_name="Claude 3 Haiku",
#             price_input_tokens=0.01,
#             price_output_tokens=0.03,
#             max_context_tokens=200000,
#             supported_file_types=[FileType.TEXT, FileType.IMAGE],
#         ),
#     )

#     # Zapisz zmodyfikowaną konfigurację
#     loaded_config.save_to_file("json_files/zmodyfikowana_konfiguracja.json")
#     print("Dodano model 'claude-3-haiku' i zapisano zmodyfikowaną konfigurację")

#     # Pokaż listę wszystkich modeli Anthropic po modyfikacji
#     anthropic_config = loaded_config.get_provider(Provider.ANTHROPIC)
#     print("Modele Anthropic po modyfikacji:")
#     for model_id, model in anthropic_config.models.items():
#         print(f"  - {model.display_name} (ID: {model_id})")

# # Uruchom wszystkie przykłady
# przyklad_tworzenia_konfiguracji()
# przyklad_pobierania_informacji()
# przyklad_sledzenia_uzywanych_modeli()
# przyklad_wczytywania_i_modyfikacji()

# CONFIG_PATH = Path("json_files/model_config.json")
# config = create_example_config()
# # Upewnij się, że katalog istnieje
# os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
# # Zapisz konfigurację do pliku
# config.save_to_file(str(CONFIG_PATH))
# print(f"Konfiguracja zapisana do: {CONFIG_PATH}")
# # Wydrukuj konfigurację
# print(config)


# # Example usage
# def create_example_config() -> Config:
#     """Create an example configuration with sample providers and models."""
#     config = Config()

#     # OpenAI configuration
#     openai_config = ProviderConfig(api_key="YOUR_OPENAI_KEY", base_url="https://api.openai.com/v1")

#     # Add OpenAI models
#     openai_config.add_model(
#         "gpt-4o",
#         ModelConfig(
#             model_id="gpt-4o",
#             display_name="GPT-4o",
#             price_input_tokens=0.03,
#             price_output_tokens=0.06,
#             max_context_tokens=8192,
#             supported_file_types=[FileType.TEXT, FileType.IMAGE],
#             description="OpenAI's most capable model",
#         ),
#     )

#     openai_config.add_model(
#         "gpt-3.5-turbo",
#         ModelConfig(
#             model_id="gpt-3.5-turbo",
#             display_name="GPT-3.5 Turbo",
#             price_input_tokens=0.045,
#             price_output_tokens=0.2342,
#             max_context_tokens=4096,
#             supported_file_types=[FileType.TEXT],
#         ),
#     )

#     # Add OpenAI provider
#     config.add_provider(Provider.OPENAI, openai_config)

#     # Anthropic configuration
#     anthropic_config = ProviderConfig(api_key="YOUR_ANTHROPIC_KEY", base_url="https://api.anthropic.com")

#     # Add Anthropic models
#     anthropic_config.add_model(
#         "claude-3-opus",
#         ModelConfig(
#             model_id="claude-3-opus",
#             display_name="Claude 3 Opus",
#             price_input_tokens=0.045,
#             price_output_tokens=0.2342,
#             max_context_tokens=4096,
#             supported_file_types=[FileType.TEXT, FileType.IMAGE, FileType.PDF],
#             description="Anthropic's most powerful model",
#         ),
#     )

#     anthropic_config.add_model(
#         "claude-3-sonnet",
#         ModelConfig(
#             model_id="claude-3-sonnet",
#             display_name="Claude 3 Sonnet",
#             price_input_tokens=0.045,
#             price_output_tokens=0.2342,
#             max_context_tokens=4096,
#             supported_file_types=[FileType.TEXT, FileType.IMAGE],
#         ),
#     )

#     # Add Anthropic provider
#     config.add_provider(Provider.ANTHROPIC, anthropic_config)

#     return config


# if __name__ == "__main__":
#     CONFIG_PATH = Path("json_files/model_config.json")
#     config = create_example_config()
#     config.save_to_file()

# # ==========================================
# # PRZYKŁADY UŻYCIA FUNKCJI Z KLAS
# # ==========================================

# # 1. Tworzenie własnej konfiguracji od podstaw
# def przyklad_tworzenia_konfiguracji():
#     print("=== Przykład 1: Tworzenie konfiguracji ===")
#     # Utwórz nową konfigurację
#     app_config = Config()

#     # Dodaj nowego dostawcę (SambaNova)
#     sambanova_config = ProviderConfig(api_key="YOUR_SAMBANOVA_KEY", base_url="https://api.sambanova.ai")

#     # Dodaj model do dostawcy SambaNova
#     sambanova_config.add_model(
#         "sambanova-1",
#         ModelConfig(
#             model_id="sambanova-1",
#             display_name="SambaNova Base",
#             price_input_tokens=0.01,
#             price_output_tokens=0.02,
#             max_context_tokens=8192,
#             supported_file_types=[FileType.TEXT],
#             additional_params={"temperature": 0.7},
#         ),
#     )

#     # Dodaj dostawcę do konfiguracji aplikacji
#     app_config.add_provider(Provider.SAMBONOVA, sambanova_config)

#     # Ustaw model domyślny dla SambaNova
#     app_config.default_model_by_provider[Provider.SAMBONOVA] = "sambanova-1"

#     # Zapisz konfigurację do pliku
#     os.makedirs("json_files", exist_ok=True)
#     app_config.save_to_file("json_files/nowa_konfiguracja.json")
#     print(f"Konfiguracja zapisana do pliku: json_files/nowa_konfiguracja.json")

# # 2. Pobieranie informacji o modelu
# def przyklad_pobierania_informacji():
#     print("\n=== Przykład 2: Pobieranie informacji ===")
#     # Utwórz przykładową konfigurację
#     config = create_example_config()

#     # Pobierz informacje o dostawcy
#     openai_provider = config.get_provider(Provider.OPENAI)
#     print(f"Adres API OpenAI: {openai_provider.base_url}")

#     # Pobierz informacje o modelu
#     gpt4_model = config.get_model(Provider.OPENAI, "gpt-4o")
#     print(f"Model: {gpt4_model.display_name}")
#     print(f"Maksymalna liczba tokenów: {gpt4_model.max_context_tokens}")
#     print(f"Cena za tokeny wejściowe: ${gpt4_model.price_input_tokens}")
#     print(f"Obsługiwane typy plików: {', '.join(gpt4_model.supported_file_types)}")

#     # Pobierz domyślny model dla dostawcy
#     default_model_id = config.get_default_model(Provider.ANTHROPIC)
#     print(f"Domyślny model Anthropic: {default_model_id}")

#     # Pobierz szczegóły domyślnego modelu
#     default_model = config.get_model(Provider.ANTHROPIC, default_model_id)
#     print(f"Nazwa domyślnego modelu: {default_model.display_name}")

# # 3. Śledzenie ostatnio używanych modeli
# def przyklad_sledzenia_uzywanych_modeli():
#     print("\n=== Przykład 3: Śledzenie używanych modeli ===")
#     # Utwórz przykładową konfigurację
#     config = create_example_config()

#     print("Początkowa lista używanych dostawców:", config.recent_providers)

#     # Ustaw ostatnio używane modele
#     config.set_recent_model(Provider.ANTHROPIC, "claude-3-opus")
#     config.set_recent_model(Provider.OPENAI, "gpt-4o")
#     config.set_recent_model(Provider.ANTHROPIC, "claude-3-sonnet")  # Nadpisuje poprzedni model Anthropic

#     print("Ostatnio używani dostawcy (w kolejności):", config.recent_providers)
#     print("Ostatnio używane modele:")
#     for provider in config.recent_providers:
#         model_id = config.get_recent_model(provider)
#         print(f"  - {provider}: {model_id}")

# # 4. Wczytywanie i modyfikacja konfiguracji z pliku
# def przyklad_wczytywania_i_modyfikacji():
#     print("\n=== Przykład 4: Wczytywanie i modyfikacja konfiguracji ===")
#     # Najpierw zapisz przykładową konfigurację
#     config = create_example_config()
#     os.makedirs("json_files", exist_ok=True)
#     config.save_to_file("json_files/config_do_modyfikacji.json")

#     # Wczytaj konfigurację z pliku
#     loaded_config = Config.load_from_file("json_files/config_do_modyfikacji.json")
#     print("Wczytano konfigurację z pliku")

#     # Dodaj nowy model do istniejącego dostawcy
#     anthropic_config = loaded_config.get_provider(Provider.ANTHROPIC)
#     anthropic_config.add_model(
#         "claude-3-haiku",
#         ModelConfig(
#             model_id="claude-3-haiku",
#             display_name="Claude 3 Haiku",
#             price_input_tokens=0.01,
#             price_output_tokens=0.03,
#             max_context_tokens=200000,
#             supported_file_types=[FileType.TEXT, FileType.IMAGE],
#         ),
#     )

#     # Zapisz zmodyfikowaną konfigurację
#     loaded_config.save_to_file("json_files/zmodyfikowana_konfiguracja.json")
#     print("Dodano model 'claude-3-haiku' i zapisano zmodyfikowaną konfigurację")

#     # Pokaż listę wszystkich modeli Anthropic po modyfikacji
#     anthropic_config = loaded_config.get_provider(Provider.ANTHROPIC)
#     print("Modele Anthropic po modyfikacji:")
#     for model_id, model in anthropic_config.models.items():
#         print(f"  - {model.display_name} (ID: {model_id})")

# # Uruchom wszystkie przykłady
# przyklad_tworzenia_konfiguracji()
# przyklad_pobierania_informacji()
# przyklad_sledzenia_uzywanych_modeli()
# przyklad_wczytywania_i_modyfikacji()

# CONFIG_PATH = Path("json_files/model_config.json")
# config = create_example_config()
# # Upewnij się, że katalog istnieje
# os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
# # Zapisz konfigurację do pliku
# config.save_to_file(str(CONFIG_PATH))
# print(f"Konfiguracja zapisana do: {CONFIG_PATH}")
# # Wydrukuj konfigurację
# print(config)
