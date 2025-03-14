from openai import OpenAI
import time
from models.openai_provider import OpenAIProvider


def test_openai_provider():
    """Test the OpenAIProvider class with both streaming and non-streaming modes."""
    from utils.model_config import Config, Provider, ModelConfig
    from utils.history_config import Message, MessageRole, ContentType, TextContent, Chat

    # Create a test model configuration
    test_model_config = ModelConfig(
        model_id="gpt-4o",
        display_name="GPT-4o",
        price_input_tokens=0.03,
        price_output_tokens=0.06,
        price_cached_tokens=0.0,
        max_context_tokens=8192,
        supported_file_types=["text", "image"],
    )

    # Initialize the OpenAI provider
    provider = OpenAIProvider(
        api_key="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",
        base_url="https://api.openai.com/v1",
        models={"gpt-4o": test_model_config},
    )

    # Create a simple text message
    text_content = TextContent(type=ContentType.TEXT, text="2+2.")
    user_message = Message(role=MessageRole.USER, content=[text_content])

    # Create a system message
    system_content = TextContent(
        type=ContentType.TEXT, text="You are a helpful assistant that responds with short answers."
    )
    system_message = Message(role=MessageRole.SYSTEM, content=[system_content])

    # Create a list of messages
    messages = [system_message, user_message]

    # Test streaming mode
    def test_streaming():
        print("\n=== Testing Streaming Mode ===")
        print("Sending streaming request to OpenAI API...")

        full_content = ""
        start_time = time.time()
        first_token_time = None

        # Get streaming response
        for chunk in provider.get_completion(messages, "gpt-4o", stream=True):
            if chunk is not None:
                print(chunk, end="", flush=True)

        total_time = time.time() - start_time
        delay = first_token_time - start_time if first_token_time else 0

        print(f"\n\nStreaming complete:")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Delay to first token: {delay:.2f} seconds")

        # Create chat history
        example_chat = Chat(chat_name="OpenAI API Test - Streaming", messages=messages.copy())
        assistant_content = TextContent(type=ContentType.TEXT, text=full_content)
        assistant_message = Message(role=MessageRole.ASSISTANT, content=[assistant_content], model="gpt-4o")
        example_chat.add_message(assistant_message)

        print("\nChat history example created successfully.")
        return example_chat

    streaming_chat = test_streaming()

    return {"streaming": streaming_chat}


if __name__ == "__main__":
    test_openai_provider()
