import openai
import logging
from models.chat_provider import ChatProvider

class SambaNovaChatProvider(ChatProvider):
    def __init__(self):
        super().__init__()
        self.provider_name = 'sambanova'
        self.base_url = 'https://api.sambanova.ai/v1'

    def chat_completion(self, messages: list, model: str, context_length: int) -> dict:
        if not self.api_key:
            return {"error": "Missing key"}
    
        last_messages = messages[-1-context_length:]
        formatted_messages = self.format_messages(last_messages)

        logging.info(f"Provider {self.provider_name}")
        logging.info(f"Messages sent to {model} :")

        if model == "DeepSeek-R1-Distill-70B":
            model_name = "DeepSeek-R1-Distill-Llama-70B"

        if model == "Tulu-3-405B":
            model_name = "Llama-3.1-Tulu-3-405B"
        try:
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            completion = client.chat.completions.create(
                model=model_name,
                messages=formatted_messages
            )
        except Exception as e:
            return {"error": str(e)}
        
        return completion.choices[0].message.content


    @staticmethod
    def format_messages(last_messages: list[dict]) -> list[dict]:
        formatted_messages = []
        for msg in last_messages:
            formatted_message = {
                "role": msg["role"],
                "content": msg["content"]
            }
            logging.info(formatted_message)
            formatted_messages.append(formatted_message)
        return formatted_messages