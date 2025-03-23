import streamlit as st

from utils.history_config import ContentType


def render_chat_interface(chat_manager):
    st.title("Chatbot")

    current_provider, current_model_id = chat_manager.get_current_provider_and_model()
    current_model = chat_manager.get_current_model_name()
    st.write(f"Selected model: {current_provider} - {current_model}")

    reasoning_enabled = st.toggle("Enable enhanced reasoning", value=False)
    chat_manager.is_reasoning = reasoning_enabled

    streaming_enabled = st.toggle("Enable streaming responses", value=True)

    messages = chat_manager.get_current_chat_messages()

    # Displaying all messeges from chat
    for msg in messages:
        with st.chat_message(msg.role):
            if msg.role == "assistant":
                text_content = ""
                for item in msg.content:
                    if item.type == ContentType.TEXT:
                        text_content += item.text

                # Check if the response is an error message
                is_error = text_content.startswith(
                    (
                        "Error:",
                        "Authentication error:",
                        "Rate limit exceeded:",
                        "Request timeout:",
                        "Connection error:",
                        "Bad request:",
                        "API error:",
                        "Unexpected error:",
                        "Błąd:",
                    )
                )

                if is_error:
                    st.error(text_content)
                else:
                    think_parts, normal_part = split_response(text_content)

                    for think_part in think_parts:
                        st.markdown(
                            f"<span style='color:gray; font-style:italic'>{think_part}</span>", unsafe_allow_html=True
                        )

                    if normal_part:
                        st.write(normal_part)

                # Display statistics if available and not an error message
                if not is_error and hasattr(msg, "throughput") and msg.throughput is not None:
                    st.markdown(
                        f"<div style='text-align: right;'><i>"
                        f"model: {msg.provider} - {msg.model}: "
                        f"throughput: {msg.throughput:.1f} t/s, "
                        f"response time: {msg.response_time:.1f} s, "
                        f"used tokens: {msg.tokens_used}, "
                        f"cost: {msg.cost:.6f}$</i></div>",
                        unsafe_allow_html=True,
                    )
            else:
                text_content = ""
                for item in msg.content:
                    if item.type == ContentType.TEXT:
                        text_content += item.text
                st.write(text_content)

                # Check if the previous assistant message was an error
                is_previous_error = False
                if len(messages) > 1:
                    msg_index = messages.index(msg)
                    if msg_index > 0 and msg_index < len(messages) - 1:
                        next_msg = messages[msg_index + 1]
                        if next_msg.role == "assistant":
                            next_text = "".join(
                                [item.text for item in next_msg.content if item.type == ContentType.TEXT]
                            )
                            is_previous_error = next_text.startswith(
                                (
                                    "Error:",
                                    "Authentication error:",
                                    "Rate limit exceeded:",
                                    "Request timeout:",
                                    "Connection error:",
                                    "Bad request:",
                                    "API error:",
                                    "Unexpected error:",
                                    "Błąd:",
                                )
                            )

                # Display user message statistics only if not related to error
                if not is_previous_error and hasattr(msg, "tokens_used") and msg.tokens_used is not None:
                    st.markdown(
                        f"<div style='text-align: right;'><i>"
                        f"used tokens: {msg.tokens_used}, "
                        f"cost: {msg.cost:.6f}$</i></div>",
                        unsafe_allow_html=True,
                    )

    # User input handling
    user_input = st.chat_input("Enter your message...")
    if user_input:
        with st.chat_message("user"):
            st.write(user_input)

        # Generate and display the response
        with st.spinner("Waiting for response..."):
            if streaming_enabled:
                try:
                    with st.chat_message("assistant"):
                        response_stream = chat_manager.generate_response_stream(user_input)
                        response_content = ""
                        placeholder = st.empty()
                        is_error = False

                        for chunk in response_stream:
                            if chunk:
                                if response_content == "" and chunk.startswith(
                                    (
                                        "Error:",
                                        "Authentication error:",
                                        "Rate limit exceeded:",
                                        "Request timeout:",
                                        "Connection error:",
                                        "Bad request:",
                                        "API error:",
                                        "Unexpected error:",
                                        "Błąd:",
                                    )
                                ):
                                    # If the first chunk indicates an error, display it as an error
                                    placeholder.error(chunk)
                                    response_content = chunk
                                    is_error = True
                                else:
                                    response_content += chunk if chunk else ""
                                    if is_error:
                                        placeholder.error(response_content)
                                    else:
                                        placeholder.write(response_content)

                        st.rerun()
                except Exception as e:
                    st.error(f"Client error: {e}")
            else:
                try:
                    response_data = chat_manager.generate_response(user_input)

                    # Check if the response is an error
                    if isinstance(response_data, str) and response_data.startswith(
                        (
                            "Error:",
                            "Authentication error:",
                            "Rate limit exceeded:",
                            "Request timeout:",
                            "Connection error:",
                            "Bad request:",
                            "API error:",
                            "Unexpected error:",
                            "Błąd:",
                        )
                    ):
                        with st.chat_message("assistant"):
                            st.error(response_data)
                    elif isinstance(response_data, dict) and "error" in response_data:
                        with st.chat_message("assistant"):
                            st.error(response_data["error"])
                    else:
                        st.rerun()

                except Exception as e:
                    st.error(f"Client error: {e}")


def split_response(response):
    """Split the response into thinking parts and normal parts."""
    import re

    # Find all thinking sections denoted by <thinking> tags
    thinking_pattern = r"<thinking>(.*?)</thinking>"
    thinking_parts = re.findall(thinking_pattern, response, re.DOTALL)

    # Remove thinking sections from the response to get the normal part
    normal_part = re.sub(thinking_pattern, "", response, flags=re.DOTALL).strip()

    return thinking_parts, normal_part
