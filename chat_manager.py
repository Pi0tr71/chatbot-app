from typing import List, Optional, Tuple, Dict
import logging
from datetime import datetime
from utils.model_config import Config, Provider, ModelConfig
from utils.history_config import ChatHistory, Chat, ContentType
from models.openai_provider import OpenAIProvider


class ChatManager:
    def __init__(self):
        self.history = ChatHistory.load_from_file()
        self.config = Config.load_from_file()
        self.current_chat_id = None
        self.current_provider = None
        self.current_model_id = None
        self.context_length = 0
        self.is_reasoning = False
        self.providers = {}
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize provider clients based on available configurations."""
        if Provider.OPENAI in self.config.providers:
            provider_config = self.config.get_provider(Provider.OPENAI)
            self.providers[Provider.OPENAI] = OpenAIProvider(
                api_key=provider_config.api_key, base_url=provider_config.base_url, models=provider_config.models
            )
            logging.info("OpenAI provider initialized")

    def update_provider(self, provider: Provider):
        """Update or initialize a specific provider."""
        if provider in self.config.providers:
            provider_config = self.config.get_provider(provider)

            if provider == Provider.OPENAI:
                self.providers[Provider.OPENAI] = OpenAIProvider(
                    api_key=provider_config.api_key, base_url=provider_config.base_url, models=provider_config.models
                )
                logging.info("OpenAI provider updated/initialized")

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

    def generate_response(self, user_input, stream):

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
            user_message = Message(
                role=MessageRole.USER,
                content=[TextContent(text=user_input)],
            )

        except Exception as e:
            logging.error(f"1. {e}")
            return
        context_messages = chat.messages[-self.context_length :] if self.context_length > 0 else []
        context_messages.append(user_message)

        if self.current_provider not in self.providers:
            logging.error(f"Provider {self.current_provider} not initialized")
            return {"error": f"Provider {self.current_provider} not available"}

        provider = self.providers[self.current_provider]

        if not stream:
            try:
                # Get completion from provider
                response = provider.get_completion(
                    messages=context_messages, model_id=self.current_model_id, stream=stream
                )

                try:
                    full_user_message = Message(
                        role=MessageRole.USER,
                        content=[TextContent(text=user_input)],
                        tokens_used=response["usage"]["prompt_tokens"],
                        cost=response["usage"]["input_cost"],
                        provider=response["provider"],
                        model=response["model"],
                    )

                    chat.add_message(full_user_message)

                except Exception as e:
                    logging.error(f"1.1 {e}")
                    return

                try:
                    assistant_message = Message(
                        role=MessageRole.ASSISTANT,
                        content=[TextContent(type=ContentType.TEXT, text=response["content"])],
                        tokens_used=response["usage"]["completion_tokens"],
                        reasoning_tokens=response["usage"]["reasoning_tokens"],
                        cost=response["usage"]["output_cost"],
                        provider=response["provider"],
                        model=response["model"],
                        throughput=response["throughput"],
                        response_time=response["response_time"],
                    )

                    # Add to chat history
                    chat.add_message(assistant_message)
                except Exception as e:
                    logging.error(f"2. {e}")
                    return

                # Save updated history
                self.history.save_to_file()

                return response

            except Exception as e:
                logging.error(f"Error generating response: {str(e)}")
                return {"error": f"Failed to generate response: {str(e)}"}
        else:
            pass

    def get_current_model_name(self) -> str:
        if self.current_model_id is not None and self.current_provider is not None:
            model = self.config.get_model(self.current_provider, self.current_model_id)
            return model.display_name
        return "No model selected"
