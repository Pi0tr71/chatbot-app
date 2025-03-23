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
        """
        Get the most recently used model.
        If no recent model exists, return the first available model.
        """
        if self.recent_model:
            return self.recent_model

        # If no recent model, find the first available provider and model
        for provider, provider_config in self.providers.items():
            if provider_config.models:
                # Get the first model ID from this provider
                first_model_id = next(iter(provider_config.models.keys()))
                return RecentModel(provider=provider, model_id=first_model_id)

        return None

    def save_to_file(self, path: str = None) -> None:
        """Save configuration to a JSON file only if it changed or if file doesn't exist."""
        file_path = path if path is not None else CONFIG_PATH

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

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
        else:
            # File doesn't exist, create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            logging.info(f"Config: Creating new config file at {file_path}")

        # Save the file (happens if: file doesn't exist OR content changed OR error occurred)
        with open(file_path, "w") as f:
            f.write(self.model_dump_json(indent=2))
            logging.info(f"Config: File saved")

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
