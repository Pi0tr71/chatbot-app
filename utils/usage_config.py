import csv
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, List

CSV_PATH = Path("logs/model_usage.csv")


class TokenType(Enum):
    INPUT = "Input"
    THINKING = "Thinking"
    OUTPUT = "Output"


class ModelUsageLogger:
    """Class for logging AI model usage to a CSV file."""

    CSV_HEADERS = [
        "Datetime",
        "Provider",
        "Model Name",
        "Input Tokens",
        "Thinking Tokens",
        "Output Tokens",
        "Input Price",
        "Cached Price",
        "Thinking Price",
        "Output Price",
        "Delay",
        "Time to response",
        "Tokens per second",
    ]

    def __init__(self, csv_path: Path = CSV_PATH):
        self.csv_path = csv_path
        self._ensure_csv_exists()

    def _ensure_csv_exists(self):
        """Ensures that the CSV file exists and has the appropriate headers."""
        if not self.csv_path.exists():
            # Make sure the folder exists
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)

            # Create a new CSV file with headers
            with open(self.csv_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(self.CSV_HEADERS)

    def log_model_usage(
        self,
        provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        time_to_response: float,
        thinking_tokens: int = 0,
        delay: float = 0.0,
        input_price: Optional[float] = None,
        cached_price: Optional[float] = None,
        thinking_price: Optional[float] = None,
        output_price: Optional[float] = None,
    ):

        # Calculate prices if not provided
        if input_price is None and input_tokens > 0:
            input_price = self._calculate_price(provider, model_name, input_tokens, token_type=TokenType.INPUT)

        if output_price is None and output_tokens > 0:
            output_price = self._calculate_price(provider, model_name, output_tokens, token_type=TokenType.OUTPUT)

        if thinking_price is None and thinking_tokens > 0:
            thinking_price = self._calculate_price(provider, model_name, thinking_tokens, token_type=TokenType.THINKING)

        # Calculate response time per token
        tokens_per_second = output_tokens / time_to_response if time_to_response > 0 else 0

        # Create current timestamp
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Data to save
        row_data = [
            current_datetime,
            provider,
            model_name,
            input_tokens,
            thinking_tokens,
            output_tokens,
            input_price or 0.0,
            cached_price or 0.0,
            thinking_price or 0.0,
            output_price or 0.0,
            delay or 0.0,
            time_to_response,
            tokens_per_second,
        ]

        # Save to CSV file
        with open(self.csv_path, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(row_data)

    def _calculate_price(self, provider: str, model_name: str, tokens: int, token_type: TokenType) -> float:
        """
        Helper method to calculate price based on token count.
        This method should be extended to retrieve current prices from model configuration.

        Args:
            provider: Model provider
            model_name: Model name
            tokens: Number of tokens
            token_type: Type of tokens (INPUT, OUTPUT, etc.)

        Returns:
            float: Calculated price
        """
        # Here you can add logic to retrieve prices from model configuration
        # Example implementation:
        from utils.model_config import Config, Provider

        config = Config.load_from_file()
        provider_enum = Provider(provider)
        provider_config = config.get_provider(provider_enum)

        if provider_config:
            model_config = provider_config.get_model(model_name)
            if model_config:
                if token_type == TokenType.INPUT:
                    price_per_token = model_config.price_input_tokens
                elif token_type == TokenType.OUTPUT or token_type == TokenType.THINKING:
                    price_per_token = model_config.price_output_tokens
                else:
                    raise ValueError(f"Unsupported token type: {token_type}")
                return price_per_token * tokens / 1_000_000

        # Default value if configuration cannot be found
        return 0.0


# Usage example:
if __name__ == "__main__":
    logger = ModelUsageLogger()

    # Example logging
    logger.log_model_usage(
        provider="anthropic",
        model_name="claude-3-opus-20240229",
        input_tokens=1500,
        output_tokens=350,
        time_to_response=3.5,
        thinking_tokens=200,
        input_price=0.015,
        output_price=0.075,
    )

    print(f"Data has been saved to {logger.csv_path}")
