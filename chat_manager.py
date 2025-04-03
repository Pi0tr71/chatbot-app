import logging
from datetime import datetime
import time
from typing import List, Optional, Tuple, Dict, Any, Union, Generator

from utils.model_config import Config, Provider, ModelConfig
from utils.history_config import ChatHistory, Chat, ContentType, ImageUrlContent

from models.openai_provider import OpenAIProvider
from models.anthropic_provider import AnthropicProvider


class ChatManager:
    def __init__(self):
        self.history = ChatHistory.load_from_file()
        self.config = Config.load_from_file()
        self.current_chat_id = None
        recent_model = self.config.get_recent_model()
        if recent_model:
            self.current_provider = recent_model.provider
            self.current_model_id = recent_model.model_id
        self.context_length = 0
        self.is_reasoning = False
        self.providers = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize provider clients based on available configurations."""
        if Provider.OPENAI in self.config.providers:
            provider_config = self.config.get_provider(Provider.OPENAI)
            self.providers[Provider.OPENAI] = OpenAIProvider(
                api_key=provider_config.api_key,
                base_url=provider_config.base_url,
                models=provider_config.models,
            )
            logging.info("OpenAI provider initialized")

        if Provider.ANTHROPIC in self.config.providers:
            provider_config = self.config.get_provider(Provider.ANTHROPIC)
            self.providers[Provider.ANTHROPIC] = AnthropicProvider(
                api_key=provider_config.api_key,
                base_url=provider_config.base_url,
                models=provider_config.models,
            )
            logging.info("Anthropic provider initialized")

    def update_provider(self, provider: Provider):
        """Update or initialize a specific provider."""
        if provider in self.config.providers:
            provider_config = self.config.get_provider(provider)

            if provider == Provider.OPENAI:
                self.providers[Provider.OPENAI] = OpenAIProvider(
                    api_key=provider_config.api_key,
                    base_url=provider_config.base_url,
                    models=provider_config.models,
                )
                logging.info("OpenAI provider updated/initialized")

            elif provider == Provider.ANTHROPIC:
                self.providers[Provider.ANTHROPIC] = AnthropicProvider(
                    api_key=provider_config.api_key,
                    base_url=provider_config.base_url,
                    models=provider_config.models,
                )
                logging.info("Anthropic provider updated/initialized")

    def new_chat(self):
        if self.current_chat_id is not None:
            self.current_chat_id = None
            logging.info("Open new chat")

    def rename_chat(self, new_name: str) -> bool:
        if self.current_chat_id is not None:
            chat = self.history.get_chat(self.current_chat_id)
            if chat and chat.chat_name != new_name:
                chat.chat_name = new_name
                logging.info(f"chat_id: {self.current_chat_id} Changed chat name to {new_name}")
                return True
        return False

    def get_current_chat_name(self) -> bool:
        if self.current_chat_id is not None:
            chat = self.history.get_chat(self.current_chat_id)
            if chat:
                return chat.chat_name
        return None

    def set_current_chat(self, chat_id) -> None:
        if self.current_chat_id != chat_id:
            self.current_chat_id = chat_id
            logging.info(f"Set current chat_id to {chat_id}")

    def delete_chat(self, chat_id):
        logging.info(f"Try delete chat {chat_id}")
        if chat_id in self.history.chats:
            self.history.delete_chat(chat_id)
            logging.info(f"Deleted chat {chat_id}")

    def get_available_models_with_providers(self) -> List[Tuple[Provider, str, str]]:
        result = []
        for provider, provider_config in self.config.providers.items():
            for model_id, model_config in provider_config.models.items():
                result.append((provider, model_id, model_config.display_name))
        return result

    def get_current_provider_and_model(self) -> Tuple[Provider, str]:
        return self.current_provider, self.current_model_id

    def set_current_provider_and_model(self, provider: Provider, model_id: str) -> None:
        if self.current_provider != provider or self.current_model_id != model_id:
            self.current_provider = provider
            self.current_model_id = model_id
            logging.info(f"Set recent model to {provider.value} - {model_id}")
            self.config.set_recent_model(provider, model_id)

    def set_context_length(self, context_length):
        if 0 <= context_length <= 5 and self.context_length != context_length:
            self.context_length = context_length
            logging.info(f"Set context_length to {context_length}")

    def get_api_providers_and_keys(self) -> dict:
        result = {}
        for provider, provider_config in self.config.providers.items():
            result[provider.value] = provider_config.api_key
        return result

    def set_api_keys(self, api_keys: dict) -> None:
        changes_made = False
        updated_providers = set()
        for provider, provider_config in self.config.providers.items():
            provider_key = api_keys.get(provider.value)
            if provider_key and provider_config.api_key != provider_key:
                provider_config.api_key = provider_key
                changes_made = True
                updated_providers.add(provider)

        if changes_made:
            logging.info("API keys updated")
            for provider in updated_providers:
                self.update_provider(provider)

    def get_all_chats(self) -> List[Tuple[str, str, datetime]]:
        result = []
        for chat_id, chat in self.history.chats.items():
            result.append((chat.chat_name, chat_id, chat.last_active))
        if result:
            result.sort(key=lambda x: x[2], reverse=True)
        return result

    def get_current_chat_messages(self) -> List:
        if self.current_chat_id is None:
            return []
        chat = self.history.get_chat(self.current_chat_id)
        if chat is None:
            logging.warning(f"Attempted to get messages for non-existent chat_id: {self.current_chat_id}")
            return []
        return chat.messages

    def get_next_chat_name(self, existing_chats):
        index = 1
        while True:
            potential_name = f"Chat {index}"
            if potential_name not in existing_chats:
                return potential_name
            index += 1

    def is_error_response(self, response):
        """Check if the response is an error message."""
        if isinstance(response, str):
            return response.startswith(
                (
                    "Error:",
                    "Authentication error:",
                    "Rate limit exceeded:",
                    "Request timeout:",
                    "Connection error:",
                    "Bad request:",
                    "API error:",
                    "Unexpected error:",
                    "Błąd:",
                )
            )
        return False

    def generate_response(self, user_input: str, imgs: List):

        # Create chat if new
        if self.current_chat_id is None:
            existing_chat_names = [chat.chat_name for chat in self.history.chats.values()]
            chat_name = self.get_next_chat_name(existing_chat_names)
            new_chat = Chat(chat_name=chat_name)
            self.history.add_chat(new_chat)
            self.current_chat_id = new_chat.chat_id
            logging.info(f"Created new chat with ID: {self.current_chat_id}")

        chat = self.history.get_chat(self.current_chat_id)
        if not chat:
            logging.error(f"Could not find chat with ID: {self.current_chat_id}")
            return {"error": "Chat not found"}

        from utils.history_config import Message, MessageRole, TextContent

        try:
            # user_message = Message(
            #     role=MessageRole.USER,
            #     content=[TextContent(text=user_input)],
            # )

            image_messages = []

            for img, file_type in imgs:
                image_messages.append(
                    ImageUrlContent(
                        type=ContentType.IMAGE_URL,
                        image_url={"url": f"data:{file_type};base64,{img}", "detail": "high"},
                    )
                )

            full_message = Message(
                role=MessageRole.USER,
                content=[TextContent(text=user_input)] + image_messages,
            )

        except Exception as e:
            logging.error(f"1. {e}")
            return
        context_messages = chat.messages[-self.context_length :] if self.context_length > 0 else []
        context_messages.append(full_message)

        if self.current_provider not in self.providers:
            logging.error(f"Provider {self.current_provider} not initialized")
            return {"error": f"Provider {self.current_provider} not available"}

        provider = self.providers[self.current_provider]

        try:
            # Get completion from provider
            response = provider.get_request(messages=context_messages, model_id=self.current_model_id)

        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            return {"error": f"Failed to generate response: {str(e)}"}

        # Access the stats from the provider object after streaming is complete
        stats = provider.stats

        try:
            # Add user message with token usage from stats
            full_user_message = Message(
                role=MessageRole.USER,
                content=[TextContent(text=user_input)],
                tokens_used=stats.prompt_tokens,
                cost=stats.input_cost,
                provider=stats.provider,
                model=stats.model,
            )

            chat.add_message(full_user_message)

        except Exception as e:
            logging.error(f"Error adding user message: {e}")
            return

        # Check if the response is an error
        is_error = self.is_error_response(response)

        try:
            # Add assistant message with stats - empty stats if error
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=[TextContent(text=response)],
                tokens_used=None if is_error else stats.completion_tokens,
                reasoning_tokens=None if is_error else stats.reasoning_tokens,
                cost=None if is_error else stats.output_cost,
                provider=stats.provider,
                model=stats.model,
                throughput=None if is_error else stats.throughput,
                response_time=None if is_error else stats.response_time,
            )

            # Add to chat history
            chat.add_message(assistant_message)

        except Exception as e:
            logging.error(f"Error adding assistant message: {e}")
            return

        # Save updated history
        self.history.save_to_file()

        return response

    def generate_response_stream(self, user_input, imgs: List):

        if self.current_chat_id is None:
            existing_chat_names = [chat.chat_name for chat in self.history.chats.values()]
            chat_name = self.get_next_chat_name(existing_chat_names)
            new_chat = Chat(chat_name=chat_name)
            self.history.add_chat(new_chat)
            self.current_chat_id = new_chat.chat_id
            logging.info(f"Created new chat with ID: {self.current_chat_id}")

        chat = self.history.get_chat(self.current_chat_id)
        if not chat:
            logging.error(f"Could not find chat with ID: {self.current_chat_id}")
            yield "Błąd: Nie znaleziono czatu"
            return

        from utils.history_config import Message, MessageRole, TextContent

        try:
            # user_message = Message(
            #     role=MessageRole.USER,
            #     content=[TextContent(text=user_input)],
            # )

            image_messages = []

            for img, file_type in imgs:
                image_messages.append(
                    ImageUrlContent(
                        type=ContentType.IMAGE_URL,
                        image_url={"url": f"data:{file_type};base64,{img}", "detail": "high"},
                    )
                )

            full_message = Message(
                role=MessageRole.USER,
                content=[TextContent(text=user_input)] + image_messages,
            )

        except Exception as e:
            logging.error(f"Failed to create user message: {e}")
            yield f"Błąd: {str(e)}"
            return

        context_messages = chat.messages[-self.context_length :] if self.context_length > 0 else []
        context_messages.append(full_message)

        if self.current_provider not in self.providers:
            logging.error(f"Provider {self.current_provider} not initialized")
            yield f"Błąd: Dostawca {self.current_provider} nie jest dostępny"
            return

        provider = self.providers[self.current_provider]
        model_config = self.config.get_model(self.current_provider, self.current_model_id)

        try:
            # Collect the full response content
            response_content = []
            is_error = False

            # Stream the response to the user
            for chunk in provider.get_stream_request(messages=context_messages, model_id=self.current_model_id):
                if chunk:
                    # Check if the first chunk indicates an error
                    if not response_content and self.is_error_response(chunk):
                        is_error = True

                    response_content.append(chunk)
                    yield chunk

            # Get the complete response text
            full_response_text = "".join(response_content)
            logging.info(f"Response text: {full_response_text}")

            # Access the stats from the provider object after streaming is complete
            stats = provider.stats
            logging.info(f"Stats {stats}")

            try:
                # Add user message with token usage from stats
                full_user_message = Message(
                    role=MessageRole.USER,
                    content=[TextContent(text=user_input)],
                    tokens_used=stats.prompt_tokens if not is_error else None,
                    cost=stats.input_cost if not is_error else None,
                    provider=stats.provider,
                    model=stats.model,
                )

                chat.add_message(full_user_message)

            except Exception as e:
                logging.error(f"Error adding user message: {e}")
                return

            try:
                # Add assistant message with stats - empty stats if error
                assistant_message = Message(
                    role=MessageRole.ASSISTANT,
                    content=[TextContent(text=full_response_text)],
                    tokens_used=None if is_error else stats.completion_tokens,
                    reasoning_tokens=None if is_error else stats.reasoning_tokens,
                    cost=None if is_error else stats.output_cost,
                    provider=stats.provider,
                    model=stats.model,
                    throughput=None if is_error else stats.throughput,
                    response_time=None if is_error else stats.response_time,
                )

                # Add to chat history
                chat.add_message(assistant_message)

            except Exception as e:
                logging.error(f"Error adding assistant message: {e}")
                return

            # Save updated history
            self.history.save_to_file()

        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            yield f"Błąd: {str(e)}"

    def get_current_model_name(self) -> str:
        if self.current_model_id is not None and self.current_provider is not None:
            model = self.config.get_model(self.current_provider, self.current_model_id)
            return model.display_name
        return "No model selected"

    def reset_model_parameters(self) -> bool:
        """Reset all parameters for the current provider to default values."""
        if self.current_provider is None or self.current_provider not in self.providers:
            logging.error("Cannot reset parameters: No provider selected")
            return False

        provider = self.providers[self.current_provider]

        # Handle parameter reset based on provider type
        if self.current_provider in [Provider.OPENAI, Provider.ANTHROPIC]:
            provider.params.reset_all_params()
            logging.info(f"Reset all parameters for provider {self.current_provider}")
            return True

        # Add handlers for other providers as needed
        logging.error(f"Provider {self.current_provider} does not support parameter configuration")
        return False

    def get_current_model_parameters(self) -> Dict[str, Dict]:
        """Get parameter information for the current provider."""
        if self.current_provider is None or self.current_provider not in self.providers:
            return {"error": "No provider selected"}

        provider = self.providers[self.current_provider]

        # Return parameter ranges based on provider type
        if self.current_provider in [Provider.OPENAI, Provider.ANTHROPIC]:
            param_info = provider.params.get_param_ranges()
            # Add current values to the response
            for param_name in param_info:
                param_info[param_name]["current_value"] = provider.params.get_param(param_name)
            return param_info

        # Add handlers for other providers as needed
        return {"error": "Provider does not support parameter configuration"}

    def set_model_parameter(self, param_name: str, value: Any) -> bool:
        """Set a parameter for the current provider."""
        if self.current_provider is None or self.current_provider not in self.providers:
            logging.error("Cannot set parameter: No provider selected")
            return False

        provider = self.providers[self.current_provider]

        # Handle parameter setting based on provider type
        if self.current_provider in [Provider.OPENAI, Provider.ANTHROPIC]:
            # Convert value to appropriate type if necessary
            param_ranges = provider.params.get_param_ranges()
            if param_name not in param_ranges:
                logging.error(f"Unknown parameter: {param_name}")
                return False

            # Type conversion based on parameter type
            try:
                if param_name in ["temperature", "top_p"]:
                    value = float(value) if value is not None else None
                elif param_name in ["max_tokens", "top_k"]:
                    value = int(value) if value is not None else None
            except (ValueError, TypeError):
                logging.error(f"Invalid value type for parameter {param_name}: {value}")
                return False

            # Set parameter using provider's method
            success = provider.params.set_param(param_name, value)
            if success:
                logging.info(f"Set {param_name}={value} for provider {self.current_provider}")
            else:
                logging.error(f"Failed to set {param_name}={value} for provider {self.current_provider}")
            return success

        # Add handlers for other providers as needed
        logging.error(f"Provider {self.current_provider} does not support parameter configuration")
        return False
