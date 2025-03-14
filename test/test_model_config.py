import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from enum import StrEnum
from typing import Dict
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.model_config import Config, ProviderConfig, ModelConfig, Provider, FileType, CONFIG_PATH


class TestModelConfig:
    def test_model_config_initialization(self):
        """Test basic initialization of ModelConfig"""
        model = ModelConfig(
            model_id="test-model",
            display_name="Test Model",
            price_input_tokens=0.01,
            price_output_tokens=0.02,
            max_context_tokens=1000,
        )

        assert model.model_id == "test-model"
        assert model.display_name == "Test Model"
        assert model.price_input_tokens == 0.01
        assert model.price_output_tokens == 0.02
        assert model.max_context_tokens == 1000
        assert model.supported_file_types == []
        assert model.additional_params == {}

    def test_model_config_with_optional_fields(self):
        """Test initialization with optional fields"""
        model = ModelConfig(
            model_id="test-model",
            display_name="Test Model",
            price_input_tokens=0.01,
            price_output_tokens=0.02,
            max_context_tokens=1000,
            supported_file_types=[FileType.TEXT, FileType.IMAGE],
            additional_params={"temperature": 0.7},
        )

        assert model.supported_file_types == [FileType.TEXT, FileType.IMAGE]
        assert model.additional_params == {"temperature": 0.7}


class TestProviderConfig:
    def test_provider_config_initialization(self):
        """Test basic initialization of ProviderConfig"""
        provider = ProviderConfig(api_key="test-key", base_url="https://api.test.com")

        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.test.com"
        assert provider.models == {}

    def test_add_and_get_model(self):
        """Test adding and retrieving models from a provider"""
        provider = ProviderConfig(api_key="test-key", base_url="https://api.test.com")

        model = ModelConfig(
            model_id="test-model",
            display_name="Test Model",
            price_input_tokens=0.01,
            price_output_tokens=0.02,
            max_context_tokens=1000,
        )

        # Add the model
        provider.add_model("test-model", model)

        # Retrieve the model
        retrieved_model = provider.get_model("test-model")
        assert retrieved_model is not None
        assert retrieved_model.model_id == "test-model"

        # Try to retrieve a non-existent model
        assert provider.get_model("non-existent") is None


class TestConfig:
    def setup_method(self):
        """Setup test data before each test"""
        self.config = Config()

        # Create a test provider with models
        self.openai_config = ProviderConfig(api_key="openai-key", base_url="https://api.openai.com")

        # Add models to the provider
        self.openai_config.add_model(
            "gpt-4",
            ModelConfig(
                model_id="gpt-4",
                display_name="GPT-4",
                price_input_tokens=0.03,
                price_output_tokens=0.06,
                max_context_tokens=8192,
            ),
        )

        self.openai_config.add_model(
            "gpt-3.5",
            ModelConfig(
                model_id="gpt-3.5",
                display_name="GPT-3.5",
                price_input_tokens=0.01,
                price_output_tokens=0.02,
                max_context_tokens=4096,
            ),
        )

        # Add the provider to the config
        self.config.add_provider(Provider.OPENAI, self.openai_config)

        # Create another provider
        self.anthropic_config = ProviderConfig(api_key="anthropic-key", base_url="https://api.anthropic.com")

        self.anthropic_config.add_model(
            "claude-3",
            ModelConfig(
                model_id="claude-3",
                display_name="Claude 3",
                price_input_tokens=0.02,
                price_output_tokens=0.04,
                max_context_tokens=10000,
            ),
        )

        # Add the second provider
        self.config.add_provider(Provider.ANTHROPIC, self.anthropic_config)

    def test_add_and_get_provider(self):
        """Test adding and retrieving providers"""
        config = Config()

        provider_config = ProviderConfig(api_key="test-key", base_url="https://api.test.com")

        # Add the provider
        config.add_provider(Provider.SAMBONOVA, provider_config)

        # Retrieve the provider
        retrieved_provider = config.get_provider(Provider.SAMBONOVA)
        assert retrieved_provider is not None
        assert retrieved_provider.api_key == "test-key"

        # Try to retrieve a non-existent provider
        assert config.get_provider("non-existent") is None

    def test_get_model(self):
        """Test retrieving a specific model from a provider"""
        # Get an existing model
        model = self.config.get_model(Provider.OPENAI, "gpt-4")
        assert model is not None
        assert model.model_id == "gpt-4"

        # Try to get a non-existent model
        assert self.config.get_model(Provider.OPENAI, "non-existent") is None

        # Try to get a model from a non-existent provider
        assert self.config.get_model("non-existent", "gpt-4") is None

    def test_recent_model_tracking(self):
        """Test tracking of recently used models"""
        # Initially, there should be no recent models
        assert self.config.recent_model == {}
        assert self.config.recent_providers == []

        # Set a recent model
        self.config.set_recent_model(Provider.OPENAI, "gpt-4")

        # Check if it was recorded
        assert self.config.get_recent_model(Provider.OPENAI) == "gpt-4"
        assert Provider.OPENAI in self.config.recent_providers

        # Set another recent model for a different provider
        self.config.set_recent_model(Provider.ANTHROPIC, "claude-3")

        # Check if both are recorded, with ANTHROPIC being the most recent
        assert self.config.get_recent_model(Provider.ANTHROPIC) == "claude-3"
        assert self.config.recent_providers == [Provider.ANTHROPIC]

        # Update a model for an existing provider
        self.config.set_recent_model(Provider.OPENAI, "gpt-3.5")

        # Check if it was updated and moved to the front
        assert self.config.get_recent_model(Provider.OPENAI) == "gpt-3.5"
        assert self.config.recent_providers == [Provider.OPENAI]

    def test_default_model(self):
        """Test getting default models"""
        # Set default models
        self.config.default_model_by_provider = {Provider.OPENAI: "gpt-4", Provider.ANTHROPIC: "claude-3"}

        # Check if they're retrievable
        assert self.config.get_default_model(Provider.OPENAI) == "gpt-4"
        assert self.config.get_default_model(Provider.ANTHROPIC) == "claude-3"

        # Try to get a default for a provider that doesn't have one
        assert self.config.get_default_model(Provider.SAMBONOVA) is None

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_to_file(self, mock_json_dump, mock_file_open):
        """Test saving configuration to a file"""
        # Patch the open function to avoid writing to a real file
        self.config.save_to_file("test_config.json")

        # Check if the file was opened for writing
        mock_file_open.assert_called_once_with("test_config.json", "w")

        # Check if json.dump was called
        assert mock_json_dump.called

    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_load_from_file(self, mock_json_load, mock_file_open, mock_path_exists):
        """Test loading configuration from a file"""
        # Set up mocks
        mock_path_exists.return_value = True
        mock_json_load.return_value = {
            "providers": {
                Provider.OPENAI: {
                    "api_key": "test-key",
                    "base_url": "https://api.openai.com",
                    "models": {
                        "gpt-4": {
                            "model_id": "gpt-4",
                            "display_name": "GPT-4",
                            "price_input_tokens": 0.03,
                            "price_output_tokens": 0.06,
                            "max_context_tokens": 8192,
                        }
                    },
                }
            },
            "default_provider": Provider.OPENAI,
            "default_model_by_provider": {Provider.OPENAI: "gpt-4"},
        }

        # Call the method
        config = Config.load_from_file("test_config.json")

        # Check if the file was opened for reading
        mock_file_open.assert_called_once_with("test_config.json", "r")

        # Check if json.load was called
        assert mock_json_load.called

        # Check if the configuration was loaded correctly
        assert config.default_provider == Provider.OPENAI


class TestFileOperations:
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_create_example_config(self, mock_json_dump, mock_file_open, mock_makedirs):
        """Test creating and saving an example configuration"""
        # Set up a temporary path
        temp_path = Path("temp/model_config.json")

        # Patch CONFIG_PATH to avoid affecting real files
        with patch("model_config.CONFIG_PATH", temp_path):
            from utils.model_config import create_example_config

            # Create example config
            config = create_example_config()

            # Save it
            config.save_to_file(str(temp_path))

            # Check if directory was created
            mock_makedirs.assert_called_with("temp", exist_ok=True)

            # Check if file was opened for writing
            mock_file_open.assert_called_with(str(temp_path), "w")

            # Check if the config has expected providers
            assert Provider.OPENAI in config.providers
            assert Provider.ANTHROPIC in config.providers


# Integration tests that simulate real usage scenarios
class TestIntegrationScenarios:
    def test_full_workflow(self):
        """Test a complete workflow of creating, modifying, and using a configuration"""
        # Create a new configuration
        config = Config()

        # Add a provider
        provider_config = ProviderConfig(api_key="test-key", base_url="https://api.test.com")

        # Add models to the provider
        provider_config.add_model(
            "model-1",
            ModelConfig(
                model_id="model-1",
                display_name="Model 1",
                price_input_tokens=0.01,
                price_output_tokens=0.02,
                max_context_tokens=1000,
                supported_file_types=[FileType.TEXT],
            ),
        )

        provider_config.add_model(
            "model-2",
            ModelConfig(
                model_id="model-2",
                display_name="Model 2",
                price_input_tokens=0.03,
                price_output_tokens=0.06,
                max_context_tokens=2000,
                supported_file_types=[FileType.TEXT, FileType.IMAGE],
            ),
        )

        # Add the provider to the config
        config.add_provider(Provider.SAMBONOVA, provider_config)

        # Set defaults
        config.default_provider = Provider.SAMBONOVA
        config.default_model_by_provider[Provider.SAMBONOVA] = "model-1"

        # Verify the configuration
        assert Provider.SAMBONOVA in config.providers
        assert len(config.providers[Provider.SAMBONOVA].models) == 2
        assert config.default_provider == Provider.SAMBONOVA
        assert config.get_default_model(Provider.SAMBONOVA) == "model-1"

        # Simulate using a model
        config.set_recent_model(Provider.SAMBONOVA, "model-2")
        assert config.get_recent_model(Provider.SAMBONOVA) == "model-2"

        # Get the model details
        model = config.get_model(Provider.SAMBONOVA, "model-2")
        assert model is not None
        assert model.display_name == "Model 2"
        assert FileType.IMAGE in model.supported_file_types

        # Modify a model
        new_model = ModelConfig(
            model_id="model-2",
            display_name="Model 2 Enhanced",
            price_input_tokens=0.04,
            price_output_tokens=0.08,
            max_context_tokens=4000,
            supported_file_types=[FileType.TEXT, FileType.IMAGE, FileType.PDF],
        )

        config.providers[Provider.SAMBONOVA].models["model-2"] = new_model

        # Verify the modification
        updated_model = config.get_model(Provider.SAMBONOVA, "model-2")
        assert updated_model.display_name == "Model 2 Enhanced"
        assert updated_model.max_context_tokens == 4000
        assert FileType.PDF in updated_model.supported_file_types
