from enum import StrEnum
from models.chat import ChatProvider, Models
from openai import OpenAI
import os
import logging


class NebiusModels(StrEnum):
    DEEPSEEK_R1_671B = "DeepSeek-R1-671B"
    DEEPSEEK_R16_72B = "DeepSeek-R1-72B"


def nebius_chat_completion(messages, model, api_key, context_length) -> str:
    if not api_key:
        return "Missing key"

    last_messages = messages[-1 - context_length :]

    logging.info("Provider Nebius")
    logging.info(f"Messages sent to {model} :")
    formatted_messages = []
    for msg in last_messages:
        formatted_message = {
            "role": msg["role"],
            "content": [{"type": "text", "text": msg["content"]}],
        }
        logging.info(formatted_message)
        formatted_messages.append(formatted_message)

    if model == "DeepSeek-R1-671B":
        model_name = "deepseek-ai/DeepSeek-R1"

    client = OpenAI(base_url="https://api.studio.nebius.ai/v1/", api_key=api_key)
    completion = client.chat.completions.create(
        model=model_name, messages=formatted_messages
    )
    return completion.choices[0].message.content


class NebiusProvider(ChatProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.studio.nebius.ai/v1/"

    def chat_completion(
        self, messages: list, model: NebiusModels, context_length: int
    ) -> str:
        last_messages = messages[-1 - context_length :]

        logging.info("Provider Nebius")
        logging.info(f"Messages sent to {model} :")
        formatted_messages = []
        for msg in last_messages:
            formatted_message = {
                "role": msg["role"],
                "content": [{"type": "text", "text": msg["content"]}],
            }
            logging.info(formatted_message)
            formatted_messages.append(formatted_message)

        if model == NebiusModels.DEEPSEEK_R1_671B:
            model_name = "deepseek-ai/DeepSeek-R1"

        client = OpenAI(base_url=self.url, api_key=self.api_key)
        completion = client.chat.completions.create(
            model=model_name, messages=formatted_messages
        )
        return completion.choices[0].message.content
