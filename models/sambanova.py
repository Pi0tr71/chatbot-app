import openai
import os
import logging

def sambanova_chat_completion(messages, model, api_key, context_length) -> str:
    if not api_key:
        return "Missing key"
    
    last_messages = messages[-1-context_length:]

    logging.info("Provider SambaNova")
    logging.info(f"Messages sent to {model} :")

    formatted_messages = []
    for msg in last_messages:
        formatted_message = {
            "role": msg["role"],
            "content": msg["content"]
        }
        logging.info(formatted_message)
        formatted_messages.append(formatted_message)

    if model == "DeepSeek-R1-Distill-70B":
        model_name = "DeepSeek-R1-Distill-Llama-70B"

    if model == "Tulu-3-405B":
        model_name = "Llama-3.1-Tulu-3-405B"

    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.sambanova.ai/v1"
    )
    
    completion = client.chat.completions.create(
        model=model_name,
        messages=formatted_messages
    )
    return completion.choices[0].message.content
