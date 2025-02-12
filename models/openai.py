from openai import OpenAI
import os
import logging

def openai_chat_completion(messages, model, api_key, context_length) -> str:
    if not api_key:
        return "Brak klucza"

    # logging.info("messages")
    # logging.info(messages)
    
    last_messages = messages[-1-context_length:]
    
    logging.info("Dostawca OpenAi")
    logging.info(f"Wiadomości wysyłane do modelu {model} :")
    formatted_messages = []
    for msg in last_messages:
        formatted_message = {
            "role": msg["role"],
            "content": [{"type": "text", "text": msg["content"]}]
        }
        logging.info(formatted_message)
        formatted_messages.append(formatted_message)

    client = OpenAI(api_key = api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=formatted_messages
    )
    return completion.choices[0].message.content
