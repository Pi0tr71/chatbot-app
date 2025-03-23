import streamlit as st
from enum import StrEnum
from typing import Dict, List
import os
from pathlib import Path

from utils.model_config import Config, Provider, ProviderConfig, ModelConfig, FileType


def render_config_models_interface(chat_manager):
    st.title("Providers Configuration")

    config = chat_manager.config

    # Add a new provider section
    st.header("Add New Provider")
    new_provider_col1, new_provider_col2 = st.columns([3, 1])

    with new_provider_col1:
        provider_options = [provider.value for provider in Provider]
        selected_provider = st.selectbox("Select Provider", provider_options)

    with new_provider_col2:
        if st.button("Add Provider"):
            if selected_provider:
                provider_enum = Provider(selected_provider)
                if config.get_provider(provider_enum) is None:
                    # Create a new provider config
                    api_key = ""
                    base_url = f"https://api.{selected_provider.lower()}.com"
                    if selected_provider == "openai":
                        base_url = "https://api.openai.com/v1"
                    elif selected_provider == "anthropic":
                        base_url = "https://api.anthropic.com"

                    provider_config = ProviderConfig(api_key=api_key, base_url=base_url)
                    config.add_provider(provider_enum, provider_config)
                    st.success(f"Added {selected_provider} provider")
                    st.rerun()
                else:
                    st.error(f"Provider {selected_provider} already exists")

    # Display existing providers
    st.header("Existing Providers")

    for provider in Provider:
        provider_config = config.get_provider(provider)
        if provider_config:
            with st.expander(f"{provider.value.capitalize()} Provider"):

                # Api Key
                new_api_key = st.text_input(
                    "API Key", value=provider_config.api_key, type="password", key=f"api_key_{provider}"
                )
                if new_api_key != provider_config.api_key:
                    provider_config.api_key = new_api_key
                    config.save_to_file()
                    # Update the provider with the new API key
                    chat_manager.update_provider(provider)
                    st.success(f"Updated API key for {provider.value}")

                # Base URL
                new_base_url = st.text_input("Base URL", value=provider_config.base_url, key=f"base_url_{provider}")
                if new_base_url != provider_config.base_url:
                    provider_config.base_url = new_base_url
                    config.save_to_file()

                # Display models for this provider
                st.subheader("Models")

                # Display existing models in a table
                if provider_config.models:
                    model_data = []
                    for model_id, model_config in provider_config.models.items():
                        model_data.append(
                            {
                                "ID": model_id,
                                "Display Name": model_config.display_name,
                                "Input Price": f"${model_config.price_input_tokens}",
                                "Output Price": f"${model_config.price_output_tokens}",
                                "Max Tokens": model_config.max_context_tokens,
                                "File Types": ", ".join(model_config.supported_file_types),
                            }
                        )

                    st.dataframe(model_data)
                else:
                    st.info(f"No models configured for {provider.value}")

                # Add new model section
                st.subheader("Add New Model")
                with st.form(key=f"add_model_{provider.value}"):
                    model_id = st.text_input("Model ID", key=f"model_id_{provider.value}")
                    display_name = st.text_input("Display Name", key=f"display_name_{provider.value}")
                    price_input = st.number_input(
                        "Price per Input Token ($)",
                        min_value=0.0,
                        format="%.3f",
                        step=0.1,
                        key=f"price_input_{provider.value}",
                    )
                    price_output = st.number_input(
                        "Price per Output Token ($)",
                        min_value=0.0,
                        format="%.3f",
                        step=0.1,
                        key=f"price_output_{provider.value}",
                    )
                    max_tokens = st.number_input(
                        "Max Context Tokens", min_value=1, step=4096, value=4096 * 4, key=f"max_tokens_{provider.value}"
                    )

                    # File types selection
                    file_types = st.multiselect(
                        "Supported File Types",
                        options=[ft.value for ft in FileType],
                        default=["text"],
                        key=f"file_types_{provider.value}",
                    )

                    submit_button = st.form_submit_button("Add Model")

                    if submit_button:
                        if not model_id or not display_name:
                            st.error("Model ID and Display Name are required")
                        elif model_id in provider_config.models:
                            st.error(f"Model ID {model_id} already exists")
                        else:
                            new_model = ModelConfig(
                                model_id=model_id,
                                display_name=display_name,
                                price_input_tokens=price_input,
                                price_output_tokens=price_output,
                                max_context_tokens=max_tokens,
                                supported_file_types=[FileType(ft) for ft in file_types],
                            )
                            provider_config.add_model(model_id, new_model)
                            config.save_to_file()
                            st.success(f"Added model {model_id}")
                            st.rerun()

                # Delete model section
                if provider_config.models:
                    st.subheader("Delete Model")
                    model_to_delete = st.selectbox(
                        "Select Model to Delete",
                        options=list(provider_config.models.keys()),
                        key=f"model_delete_{provider.value}",
                    )

                    if st.button("Delete Selected Model", key=f"delete_model_{provider.value}"):
                        if model_to_delete in provider_config.models:
                            del provider_config.models[model_to_delete]
                            config.save_to_file()
                            st.success(f"Deleted model {model_to_delete}")
                            st.rerun()

                # Delete provider section
                st.subheader("Delete Provider")
                if st.button(f"Delete {provider.value} Provider", key=f"delete_provider_{provider.value}"):
                    if provider in config.providers:
                        del config.providers[provider]
                        config.save_to_file()
                        st.success(f"Deleted provider {provider.value}")
                        st.rerun()

    # Save configuration
    if st.button("Save Configuration"):
        config.save_to_file()
        st.success("Configuration saved successfully")
