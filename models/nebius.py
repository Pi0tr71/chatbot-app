from openai import OpenAI
import os
import logging

def nebius_chat_completion(messages, model, api_key, context_length) -> str:
    if not api_key:
        return "Brak klucza"
    
    last_messages = messages[-1-context_length:]
    
    logging.info("Dostawca Nebius")
    logging.info(f"Wiadomości wysyłane do modeli {model} :")
    formatted_messages = []
    for msg in last_messages:
        formatted_message = {
            "role": msg["role"],
            "content": [{"type": "text", "text": msg["content"]}]
        }
        logging.info(formatted_message)
        formatted_messages.append(formatted_message)


    if model == "DeepSeek-R1-671B":
        model_name = "deepseek-ai/DeepSeek-R1"

    client = OpenAI(
        base_url="https://api.studio.nebius.ai/v1/",
        api_key = api_key
        )
    completion = client.chat.completions.create(
        model=model_name,
        messages=formatted_messages
    )
    return completion.choices[0].message.content
