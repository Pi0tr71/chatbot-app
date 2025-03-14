import os
from typing import Dict, List, Any, Optional, Tuple, Generator, Callable
import json
import time
from openai import OpenAI
import base64
import logging

from utils.model_config import ModelConfig, Provider
from utils.history_config import Message, MessageRole, ContentType, TextContent, ImageUrlContent
from utils.usage_config import ModelUsageLogger


class OpenAIProvider:

    def __init__(self, api_key: str, base_url: str, models: Dict[str, ModelConfig]):
        self.models = models
        self.usage_logger = ModelUsageLogger()
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def _encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def _convert_messages_to_correct_format(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert chat history messages to OpenAI-compatible format."""
        openai_messages = []

        for message in messages:
            content = []

            # Handle different content types
            for content_item in message.content:
                if content_item.type == ContentType.TEXT:
                    content.append({"type": "text", "text": content_item.text})
                elif content_item.type == ContentType.IMAGE_URL:
                    image_url = content_item.image_url.get("url")
                    detail = content_item.image_url.get("detail", "auto")
                    content.append({"type": "image_url", "image_url": {"url": image_url, "detail": detail}})

            # Handle single text content case (most common)
            if len(content) == 1 and content[0]["type"] == "text":
                openai_messages.append({"role": message.role, "content": content[0]["text"]})
            else:
                # Multiple content items or non-text content
                openai_messages.append({"role": message.role, "content": content})

        return openai_messages

    def get_completion(
        self, messages: List[Message], model_id: str, stream: bool = False, callback: Optional[Callable] = None
    ):
        """
        Get completion from OpenAI API.

        Args:
            messages: List of Message objects
            model_id: Model identifier
            stream: Whether to stream the response
            callback: Callback function to process streaming chunks (if stream=True)

        Returns:
            If stream=False: The complete response object
            If stream=True: A generator yielding response chunks
        """
        model_config = self.models.get(model_id)
        if not model_config:
            error_dict = {"Error": f"Model {model_id} not configured"}
            return error_dict

        openai_messages = self._convert_messages_to_correct_format(messages)

        try:
            start_time = time.time()

            if not stream:
                # Non-streaming response
                response = self.client.chat.completions.create(
                    model=model_id,
                    messages=openai_messages,
                    temperature=0.7,
                    max_tokens=None,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    stream=False,
                )
                response_time = time.time() - start_time
                logging.info(f"Response from {model_id}: {response}")

                formatted_response = {
                    "provider": Provider.OPENAI.value,
                    "model": model_config.display_name,
                    "content": response.choices[0].message.content,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "reasoning_tokens": (
                            response.usage.completion_tokens_details.reasoning_tokens
                            if hasattr(response.usage, "completion_tokens_details")
                            else 0
                        ),
                        "input_cost": response.usage.prompt_tokens * model_config.price_input_tokens / 1_000_000,
                        "output_cost": response.usage.completion_tokens * model_config.price_output_tokens / 1_000_000,
                    },
                    "throughput": response.usage.total_tokens / response_time,
                    "response_time": response_time,
                }

                logging.info(f"Formatted response: {formatted_response}")

                return formatted_response

            else:
                # Streaming response
                stream_response = self.client.chat.completions.create(
                    model=model_id,
                    messages=openai_messages,
                    temperature=0.7,
                    max_tokens=None,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                    stream=True,
                    stream_options={"include_usage": True},
                )
                first_token_received = False
                delay = 0
                chunks_list = []

                for chunk in stream_response:

                    if not first_token_received:
                        delay = time.time() - start_time
                        first_token_received = True

                    chunks_list.append(chunk)
                    yield chunk.choices[0].delta.content

                prompt_tokens = chunks_list[-1].usage.prompt_tokens
                completion_tokens = chunks_list[-1].usage.completion_tokens
                reasoning_tokens = (
                    chunks_list[-1].usage.completion_tokens_details.reasoning_tokens
                    if hasattr(chunks_list[-1].usage, "completion_tokens_details")
                    else None
                )

                response_time = time.time() - start_time

                print(prompt_tokens)
                print(completion_tokens)
                print(reasoning_tokens)
                print(response_time)
                print(delay)

        except Exception as e:
            error_dict = {"Error": f"Error calling OpenAI API: {str(e)}"}
            return error_dict
