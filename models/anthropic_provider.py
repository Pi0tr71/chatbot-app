import os
from typing import Dict, List, Any, Optional, Tuple, Generator, Callable
import json
import time
import anthropic
import logging

from utils.model_config import ModelConfig, Provider
from utils.history_config import Message, MessageRole, ContentType, TextContent, ImageUrlContent
from utils.usage_config import ModelUsageLogger


class AnthropicProvider:

    def __init__(self, api_key: str, base_url: str, models: Dict[str, ModelConfig]):
        self.models = models
        self.usage_logger = ModelUsageLogger()
        self.client = anthropic.Anthropic(api_key=api_key, base_url=base_url)
        self.params = Params()
        self.stats = Stats()

    def _convert_messages_to_correct_format(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert chat history messages to Anthropic-compatible format."""
        anthropic_messages = []

        for message in messages:
            content = []

            # Handle different content types
            for content_item in message.content:
                if content_item.type == ContentType.TEXT:
                    content.append({"type": "text", "text": content_item.text})
                elif content_item.type == ContentType.IMAGE_URL:
                    image_url = content_item.image_url.get("url")
                    content.append({"type": "image", "source": {"type": "url", "url": image_url}})

            # Handle single text content case (most common)
            if len(content) == 1 and content[0]["type"] == "text":
                anthropic_messages.append({"role": message.role.value, "content": content[0]["text"]})
            else:
                # Multiple content items or non-text content
                anthropic_messages.append({"role": message.role.value, "content": content})

        return anthropic_messages

    def _handle_api_error(self, e):
        """Handle different types of Anthropic API errors and return user-friendly messages."""
        if isinstance(e, anthropic.AuthenticationError):
            error_msg = "Authentication error: Invalid API key or credentials. Please check your API key configuration."
            logging.error(f"Anthropic Authentication Error: {str(e)}")
        elif isinstance(e, anthropic.RateLimitError):
            error_msg = (
                "Rate limit exceeded: Too many requests. Please try again later or reduce the frequency of requests."
            )
            logging.error(f"Anthropic Rate Limit Error: {str(e)}")
        elif isinstance(e, anthropic.APITimeoutError):
            error_msg = "Request timeout: The server took too long to respond. Please try again later."
            logging.error(f"Anthropic API Timeout: {str(e)}")
        elif isinstance(e, anthropic.APIConnectionError):
            error_msg = "Connection error: Could not connect to Anthropic services. Please check your internet connection and try again."
            logging.error(f"Anthropic API Connection Error: {str(e)}")
        elif isinstance(e, anthropic.BadRequestError):
            error_msg = f"Bad request: {str(e)}. Please check input parameters and format."
            logging.error(f"Anthropic Bad Request Error: {str(e)}")
        elif isinstance(e, anthropic.APIError):
            error_msg = f"API error: {str(e)}. Please try again later."
            logging.error(f"Anthropic API Error: {str(e)}")
        else:
            error_msg = f"Unexpected error: {str(e)}. Please try again or contact support if the issue persists."
            logging.error(f"Unexpected Anthropic Error: {str(e)}")

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

        anthropic_messages = self._convert_messages_to_correct_format(messages)

        # Extract system message if present
        system_message = None
        filtered_messages = []
        for message in anthropic_messages:
            if message["role"] == "system":
                system_message = message["content"]
            else:
                filtered_messages.append(message)

        try:
            start_time = time.time()

            request_params = {
                "model": model_id,
                "messages": filtered_messages,
                "stream": False,
                **self.params.to_dict(),
            }

            # Add system message if present
            if system_message:
                request_params["system"] = system_message

            logging.info(f"Request params: {request_params}")

            response = self.client.messages.create(**request_params)

            response_time = time.time() - start_time

            logging.info(f"Response from {model_id}: {response}")

            self.stats.update_from_response(
                response=response,
                model_config=model_config,
                response_time=response_time,
                provider=Provider.ANTHROPIC.value,
                delay=None,
            )

            # Extract text content from response
            message_content = ""
            for content_block in response.content:
                if content_block.type == "text":
                    message_content += content_block.text

            logging.info(f"Response Text: {message_content}")
            return message_content

        except Exception as e:
            return self._handle_api_error(e)

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

        anthropic_messages = self._convert_messages_to_correct_format(messages)

        # Extract system message if present
        system_message = None
        filtered_messages = []
        for message in anthropic_messages:
            if message["role"] == "system":
                system_message = message["content"]
            else:
                filtered_messages.append(message)

        try:
            start_time = time.time()

            request_params = {
                "model": model_id,
                "messages": filtered_messages,
                "stream": True,
                **self.params.to_dict(),
            }

            # Add system message if present
            if system_message:
                request_params["system"] = system_message

            logging.info(f"Request params: {request_params}")

            with self.client.messages.create(**request_params) as stream:
                is_first = True
                text_chunks = []

                for chunk in stream:
                    if is_first:
                        delay = time.time() - start_time
                        is_first = False

                    if chunk.type == "content_block_delta" and chunk.delta.type == "text":
                        text_chunks.append(chunk.delta.text)
                        logging.info(f"Chunk: {chunk.delta.text}")
                        yield chunk.delta.text

                # Calculate usage stats at the end of the stream
                response_time = time.time() - start_time

                if hasattr(stream, "usage"):
                    self.stats.update_from_response(
                        response=stream,
                        model_config=model_config,
                        response_time=response_time,
                        provider=Provider.ANTHROPIC.value,
                        delay=delay,
                    )

        except Exception as e:
            error_msg = self._handle_api_error(e)
            yield error_msg
            return


class Params:
    """Class to store and validate request parameters for Anthropic API calls."""

    # Define parameter ranges and constraints
    PARAM_RANGES = {
        "temperature": {"min": 0.0, "max": 1.0, "default": None},
        "max_tokens": {"min": 1, "max": 200000, "default": None},
        "top_p": {"min": 0.0, "max": 1.0, "default": None},
        "top_k": {"min": 0, "max": 2.0, "default": None},
    }

    def __init__(
        self,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
    ):
        # Initialize parameters with validation
        self._params = {}
        self.set_param("temperature", temperature)
        self.set_param("max_tokens", max_tokens)
        self.set_param("top_p", top_p)
        self.set_param("top_k", top_k)

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
    """Class to store response statistics from Anthropic API calls."""

    def __init__(self):
        self.provider = None
        self.model = None
        self.prompt_tokens = None
        self.completion_tokens = None
        self.total_tokens = None
        self.input_cost = None
        self.output_cost = None
        self.throughput = None
        self.response_time = None
        self.delay = None
        self.reasoning_tokens = None

    def update_from_response(
        self, response, model_config: ModelConfig, response_time: float, provider: str, delay: float = None
    ):
        """Update statistics from API response."""
        self.provider = provider
        self.model = model_config.display_name

        if hasattr(response, "usage"):
            self.prompt_tokens = response.usage.input_tokens
            self.completion_tokens = response.usage.output_tokens
            self.total_tokens = response.usage.input_tokens + response.usage.output_tokens
            self.input_cost = response.usage.input_tokens * model_config.price_input_tokens / 1_000_000
            self.output_cost = response.usage.output_tokens * model_config.price_output_tokens / 1_000_000
            self.throughput = self.total_tokens / response_time if response_time > 0 else 0

        self.response_time = response_time
        self.delay = delay
