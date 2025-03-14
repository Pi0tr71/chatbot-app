from models.chat_provider import ChatProvider


class OpenAiChatProvider(ChatProvider):
    def __init__(self):
        super().__init__()
        self.provider_name = "nebius"
        self.base_url = "https://api.studio.nebius.ai/v1/"

    def chat_completion(self, messages: list, model: str, context_length: int) -> dict:
        return super().chat_completion(messages, model, context_length)

    @staticmethod
    def format_messages(last_messages: list[dict]) -> list[dict]:
        return super().format_messages(last_messages)
