from abc import ABC
from enum import Enum, StrEnum


class Model(StrEnum):
    def __init__(self):
        self.name = ""
        super().__init__()


class ChatProvider(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = ""
        self.cost_manager = CostManager

    def chat_completion(
        self, messages: list, model: Models, api_key: str, context_length: int
    ) -> str:
        raise NotImplementedError

    def completion_title(self, messages: list, api_key: str) -> str:
        raise NotImplementedError
