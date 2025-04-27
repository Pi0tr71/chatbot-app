import os
from typing import Dict, List, Any, Optional, Tuple, Generator, Callable
import json
import time
from openai import OpenAI
from openai import APIError, APIConnectionError, RateLimitError, APITimeoutError, BadRequestError, AuthenticationError
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
        self.params = Params()
        self.stats = Stats()

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
                elif content_item.type == ContentType.FILE:
                    file_data = content_item.file_url
                    content.append(
                        {
                            "type": "file",
                            "file": {
                                "name": file_data.get("name"),
                                "mime_type": file_data.get("mime_type"),
                                "content": file_data.get("content"),
                            },
                        }
                    )

            # Handle single text content case (most common)
            if len(content) == 1 and content[0]["type"] == "text":
                openai_messages.append({"role": message.role.value, "content": content[0]["text"]})
            else:
                # Multiple content items or non-text content
                openai_messages.append({"role": message.role.value, "content": content})

        return openai_messages

    def _handle_api_error(self, e):
        """Handle different types of OpenAI API errors and return user-friendly messages."""
        if isinstance(e, AuthenticationError):
            error_msg = "Authentication error: Invalid API key or credentials. Please check your API key configuration."
            logging.error(f"OpenAI Authentication Error: {str(e)}")
        elif isinstance(e, RateLimitError):
            error_msg = (
                "Rate limit exceeded: Too many requests. Please try again later or reduce the frequency of requests."
            )
            logging.error(f"OpenAI Rate Limit Error: {str(e)}")
        elif isinstance(e, APITimeoutError):
            error_msg = "Request timeout: The server took too long to respond. Please try again later."
            logging.error(f"OpenAI API Timeout: {str(e)}")
        elif isinstance(e, APIConnectionError):
            error_msg = "Connection error: Could not connect to OpenAI services. Please check your internet connection and try again."
            logging.error(f"OpenAI API Connection Error: {str(e)}")
        elif isinstance(e, BadRequestError):
            error_msg = f"Bad request: {str(e)}. Please check input parameters and format."
            logging.error(f"OpenAI Bad Request Error: {str(e)}")
        elif isinstance(e, APIError):
            error_msg = f"API error: {str(e)}. Please try again later."
            logging.error(f"OpenAI API Error: {str(e)}")
        else:
            error_msg = f"Unexpected error: {str(e)}. Please try again or contact support if the issue persists."
            logging.error(f"Unexpected OpenAI Error: {str(e)}")

        return error_msg

    def get_request(
        self,
        messages: List[Message],
        model_id: str,
    ) -> str:

        model_config = self.models.get(model_id)
        if not model_config:
            error_msg = f"Model {model_id} not configured"
            logging.error(error_msg)
            return error_msg

        openai_messages = self._convert_messages_to_correct_format(messages)

        try:
            start_time = time.time()

            request_params = {
                "model": model_id,
                "messages": openai_messages,
                "stream": False,
                **self.params.to_dict(),
            }

            logging.info(f"Request params: {request_params}")

            response = self.client.chat.completions.create(**request_params)

            response_time = time.time() - start_time

            logging.info(f"Response from {model_id}: {response}")

            self.stats.update_from_response(
                response=response,
                model_config=model_config,
                response_time=response_time,
                provider=Provider.OPENAI.value,
                delay=None,
            )

            logging.info(f"Response Text: {response.choices[0].message.content}")
            return response.choices[0].message.content

        except (
            APIError,
            APIConnectionError,
            RateLimitError,
            APITimeoutError,
            BadRequestError,
            AuthenticationError,
        ) as e:
            return self._handle_api_error(e)
        except Exception as e:
            error_msg = f"Error calling OpenAI API: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def get_stream_request(
        self,
        messages: List[Message],
        model_id: str,
    ):
        model_config = self.models.get(model_id)

        if not model_config:
            error_msg = f"Model {model_id} not configured"
            logging.error(error_msg)
            yield error_msg
            return

        openai_messages = self._convert_messages_to_correct_format(messages)

        try:
            start_time = time.time()

            request_params = {
                "model": model_id,
                "messages": openai_messages,
                "stream": True,
                "stream_options": {"include_usage": True},
                **self.params.to_dict(),
            }

            logging.info(f"Request params: {request_params}")

            response = self.client.chat.completions.create(**request_params)

            is_first = True

            for chunk in response:
                if is_first:
                    delay = time.time() - start_time
                    is_first = False

                if chunk.choices and len(chunk.choices) > 0:
                    yield chunk.choices[0].delta.content

                elif hasattr(chunk, "usage") and chunk.usage is not None:
                    logging.info(f"Chunk with stats: {chunk}")
                    response_time = time.time() - start_time

                    self.stats.update_from_response(
                        response=chunk,
                        model_config=model_config,
                        response_time=response_time,
                        provider=Provider.OPENAI.value,
                        delay=delay,
                    )

        except (
            APIError,
            APIConnectionError,
            RateLimitError,
            APITimeoutError,
            BadRequestError,
            AuthenticationError,
        ) as e:
            error_msg = self._handle_api_error(e)
            yield error_msg
            return
        except Exception as e:
            error_msg = f"Error calling OpenAI API: {str(e)}"
            logging.error(error_msg)
            yield error_msg
            return


class Params:
    """Class to store and validate request parameters for OpenAI API calls."""

    # Define parameter ranges and constraints
    PARAM_RANGES = {
        "temperature": {"min": 0.0, "max": 2.0, "default": None},
        "max_tokens": {"min": 1, "max": 32000, "default": None},
        "max_completion_tokens": {"min": 1, "max": 32000, "default": None},
        "top_p": {"min": 0.0, "max": 1.0, "default": None},
        "frequency_penalty": {"min": -2.0, "max": 2.0, "default": None},
        "presence_penalty": {"min": -2.0, "max": 2.0, "default": None},
        "reasoning_effort": {"values": ["low", "medium", "high"], "default": None},
    }

    def __init__(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        reasoning_effort: Optional[str] = None,
    ):
        # Initialize parameters with validation
        self._params = {}
        self.set_param("temperature", temperature)
        self.set_param("max_tokens", max_tokens)
        self.set_param("max_completion_tokens", max_completion_tokens)
        self.set_param("top_p", top_p)
        self.set_param("frequency_penalty", frequency_penalty)
        self.set_param("presence_penalty", presence_penalty)
        self.set_param("reasoning_effort", reasoning_effort)

    def set_param(self, param_name: str, value: Any) -> bool:
        """Set parameter with validation against defined ranges.

        Args:
            param_name: Name of the parameter to set
            value: Value to set for the parameter

        Returns:
            bool: True if parameter was set successfully, False otherwise
        """
        if param_name not in self.PARAM_RANGES:
            return False

        # If value is None, set to default (which might also be None)
        if value is None:
            self._params[param_name] = self.PARAM_RANGES[param_name]["default"]
            return True

        # For enum-type parameters (like reasoning_effort)
        if "values" in self.PARAM_RANGES[param_name]:
            if value in self.PARAM_RANGES[param_name]["values"]:
                self._params[param_name] = value
                return True
            return False

        # For range-based parameters
        param_min = self.PARAM_RANGES[param_name].get("min")
        param_max = self.PARAM_RANGES[param_name].get("max")

        if (param_min is not None and value < param_min) or (param_max is not None and value > param_max):
            return False

        self._params[param_name] = value
        return True

    def get_param(self, param_name: str) -> Any:
        """Get the current value of a parameter."""
        return self._params.get(param_name)

    def get_param_ranges(self) -> Dict[str, Dict]:
        """Get the valid ranges for all parameters."""
        return self.PARAM_RANGES

    def reset_all_params(self) -> None:
        """Reset all parameters to their default values."""
        for param_name, param_config in self.PARAM_RANGES.items():
            self._params[param_name] = param_config["default"]

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary for API request, excluding None values."""
        return {k: v for k, v in self._params.items() if v is not None}


class Stats:
    """Class to store response statistics from OpenAI API calls."""

    def __init__(self):
        self.provider = None
        self.model = None
        self.prompt_tokens = None
        self.completion_tokens = None
        self.total_tokens = None
        self.reasoning_tokens = None
        self.input_cost = None
        self.output_cost = None
        self.throughput = None
        self.response_time = None
        self.delay = None

    def update_from_response(
        self, response, model_config: ModelConfig, response_time: float, provider: str, delay: float = None
    ):
        """Update statistics from API response."""
        self.provider = provider
        self.model = model_config.display_name
        self.prompt_tokens = response.usage.prompt_tokens
        self.completion_tokens = response.usage.completion_tokens
        self.total_tokens = response.usage.total_tokens
        self.reasoning_tokens = (
            response.usage.completion_tokens_details.reasoning_tokens
            if hasattr(response.usage, "completion_tokens_details")
            else 0
        )
        self.input_cost = response.usage.prompt_tokens * model_config.price_input_tokens / 1_000_000
        self.output_cost = response.usage.completion_tokens * model_config.price_output_tokens / 1_000_000
        self.throughput = response.usage.total_tokens / response_time
        self.response_time = response_time
        self.delay = delay
