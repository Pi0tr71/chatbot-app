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
                think_parts, normal_part = split_response(text_content)

                for think_part in think_parts:
                    st.markdown(
                        f"<span style='color:gray; font-style:italic'>{think_part}</span>", unsafe_allow_html=True
                    )

                if normal_part:
                    st.write(normal_part)

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
                st.markdown(
                    f"<div style='text-align: right;'><i>"
                    f"used tokens: {msg.tokens_used}, "
                    f"cost: {msg.cost:.6f}$</i></div>",
                    unsafe_allow_html=True,
                )

    # User input handling
    user_input = st.chat_input("Enter your message...")
    if user_input:
        # Create a placeholder for the user message that will be updated later
        user_msg_container = st.container()
        with user_msg_container:
            with st.chat_message("user"):
                st.write(user_input)
                # Empty placeholder for token info that will be filled later
                token_info_placeholder = st.empty()

        # Generate and display the response
        with st.spinner("Waiting for response..."):
            if streaming_enabled:
                try:
                    with st.chat_message("assistant"):

                        response = st.write_stream()

                except Exception as e:
                    st.error(f"Error occurred while retrieving the response: {e}")
            else:
                try:
                    # Send message to chat manager
                    response_data = chat_manager.generate_response(user_input, streaming_enabled)

                    # Update the token information in the placeholder
                    if "usage" in response_data and "prompt_tokens" in response_data["usage"]:
                        with token_info_placeholder:
                            st.markdown(
                                f"<div style='text-align: right;'><i>"
                                f"used tokens: {response_data['usage']['prompt_tokens']}, "
                                f"cost: {response_data["usage"]["input_cost"]:.6f}$</i></div>",
                                unsafe_allow_html=True,
                            )

                    # Display assistant response
                    with st.chat_message("assistant"):
                        think_parts, normal_part = split_response(response_data["content"])

                        for think_part in think_parts:
                            st.markdown(
                                f"<span style='color:gray; font-style:italic'>{think_part}</span>",
                                unsafe_allow_html=True,
                            )

                        if normal_part:
                            st.write(normal_part)

                        st.markdown(
                            f"<div style='text-align: right;'><i>"
                            f"model: {response_data['provider']} - {response_data['model']}: "
                            f"throughput: {response_data['throughput']:.1f} t/s, "
                            f"response time: {response_data['response_time']:.1f} s, "
                            f"used tokens: {response_data['usage']['completion_tokens']}, "
                            f"cost: {response_data['usage']['output_cost']:.6f}$</i></div>",
                            unsafe_allow_html=True,
                        )

                except Exception as e:
                    st.error(f"Error occurred while retrieving the response: {e}")


def split_response(response):
    """Split the response into thinking parts and normal parts."""
    import re

    # Find all thinking sections denoted by <thinking> tags
    thinking_pattern = r"<thinking>(.*?)</thinking>"
    thinking_parts = re.findall(thinking_pattern, response, re.DOTALL)

    # Remove thinking sections from the response to get the normal part
    normal_part = re.sub(thinking_pattern, "", response, flags=re.DOTALL).strip()

    return thinking_parts, normal_part


# def split_response(response):

#     think_parts = re.findall(r"<think>(.*?)</think>", response, flags=re.DOTALL)
#     normal_part = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()

#     return think_parts, normal_part
