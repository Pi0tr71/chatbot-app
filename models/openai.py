from enum import Enum
from openai import OpenAI, OpenAIError
import os
import logging
import json


def openai_chat_completion(messages, model, api_key, context_length) -> str:
    if not api_key:
        return "Missing key"

    last_messages = messages[-1 - context_length :]

    logging.info("Provider OpenAi")
    logging.info(f"Messages sent to {model} :")
    formatted_messages = []
    for msg in last_messages:
        formatted_message = {
            "role": msg["role"],
            "content": [{"type": "text", "text": msg["content"]}],
        }
        logging.info(formatted_message)
        formatted_messages.append(formatted_message)

    try:
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model, messages=formatted_messages
        )
        prompt_tokens = completion.usage.prompt_tokens
        completion_tokens = completion.usage.completion_tokens
        return completion.choices[0].message.content, prompt_tokens, completion_tokens
    except OpenAIError as e:
        return f"Error: {e.args}", 0, 0


def openai_chat_completion_title(messages, api_key) -> str:
    topic = []
    formatted_message = {
        "role": messages[0]["role"],
        "content": [{"type": "text", "text": messages[0]["content"]}],
    }
    topic.append(formatted_message)
    topic.append(
        {
            "role": "user",
            "content": "What was the topic of the previous question? Write in 5 words or less. In the language in which it was written before",
        }
    )

    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(model="gpt-4o-mini", messages=topic)

    return completion.choices[0].message.content


class OpenAIModels(str, Enum):
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"
    GPT35_TURBOV2 = "gpt-3.5-turbov2"


# class OpenAIChatProvider(ChatProvider):
#     def __init__(self, api_key: str):
#         self.api_key = api_key

#     def chat_completion(
#         self, messages: list, model: Models, context_length: int
#     ) -> str:
#         # TODO: implement OpenAIChat
#         pass

#     def _format_messages(self, messages: list) -> dict:
#          for msg in last_messages:
#             formatted_message = {
#                 "role": msg["role"],
#                 "content": [{"type": "text", "text": msg["content"]}]
#             }
#             logging.info(formatted_message)
#             formatted_messages.append(formatted_message)
#         pass


# class OpenAIChatGPT3_5(OpenAIChatProvider):
#     def __init__(self, api_key: str):
#         self.api_key = api_key

#     def chat_completion(
#         self, messages: list, model: Models, context_length: int
#     ) -> str:
#         self._format_messages(messages)
#         completion = openai.ChatCompletion.create(
