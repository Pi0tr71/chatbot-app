import abc
from typing import Dict, List, Optional, Any, Union

from utils.model_config import Provider, ModelConfig, Config, ProviderConfig


class ChatProvider(abc.ABC):
    """
    Abstract base class for chat providers.
    This class defines the interface that all provider implementations must follow.
    """

    def __init__(self, provider_type: Provider, config: Config):
        """
        Initialize the chat provider with its type and configuration.

        Args:
            provider_type: The type of this provider (from Provider enum)
            config: The application configuration
        """
        self.provider_type = provider_type
        self.config = config
        self.provider_config = config.get_provider(provider_type)

        if not self.provider_config:
            raise ValueError(f"No configuration found for provider {provider_type}")

        # Set default model if available
        self.current_model_id = config.get_default_model(provider_type)

    @abc.abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Send a chat completion request to the provider.

        Args:
            messages: List of message dictionaries (usually with 'role' and 'content' keys)
            **kwargs: Additional provider-specific parameters

        Returns:
            Response from the provider
        """
        pass

    @abc.abstractmethod
    async def stream_chat_completion(self, messages: List[Dict[str, str]], **kwargs):
        """
        Stream a chat completion from the provider.

        Args:
            messages: List of message dictionaries (usually with 'role' and 'content' keys)
            **kwargs: Additional provider-specific parameters

        Returns:
            An async generator that yields chunks of the response
        """
        pass

    def set_model(self, model_id: str) -> None:
        """
        Set the model to use for this provider.

        Args:
            model_id: The ID of the model to use

        Raises:
            ValueError: If the model ID is not valid for this provider
        """
        model_config = self.get_model_config(model_id)
        if not model_config:
            raise ValueError(f"Model {model_id} not configured for provider {self.provider_type}")

        self.current_model_id = model_id
        # Update recent model in the config
        self.config.set_recent_model(self.provider_type, model_id)

    def get_model_config(self, model_id: Optional[str] = None) -> Optional[ModelConfig]:
        """
        Get the configuration for a specific model.

        Args:
            model_id: The ID of the model (uses current model if None)

        Returns:
            The model configuration or None if not found
        """
        model_id = model_id or self.current_model_id
        if not model_id:
            return None

        return self.provider_config.get_model(model_id)

    def get_available_models(self) -> Dict[str, ModelConfig]:
        """
        Get all available models for this provider.

        Returns:
            Dictionary of model IDs to model configurations
        """
        return self.provider_config.models

    @property
    def api_key(self) -> str:
        """Get the API key for this provider."""
        return self.provider_config.api_key

    @property
    def base_url(self) -> str:
        """Get the base URL for API requests."""
        return self.provider_config.base_url

    @abc.abstractmethod
    async def handle_file_upload(self, file_path: str, file_type: str) -> Union[str, Dict[str, Any]]:
        """
        Handle a file upload for this provider.

        Args:
            file_path: Path to the file
            file_type: Type of the file (should match FileType enum)

        Returns:
            Provider-specific file reference or content
        """
        pass
