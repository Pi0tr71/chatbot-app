import time


class StreamingResponse:
    def __init__(self, client, model_id, messages):
        self.client = client
        self.model_id = model_id
        self.messages = messages
        self.stats = {}

    def __iter__(self):
        try:
            start_time = time.time()
            stream_response = self.client.chat.completions.create(
                model=self.model_id,
                messages=self.messages,
                # ...pozostałe parametry...
                stream=True,
                stream_options={"include_usage": True},
            )
            first_token_received = False
            delay = 0
            chunks_list = []

            for chunk in stream_response:
                if not first_token_received:
                    delay = time.time() - start_time
                    first_token_received = True
                chunks_list.append(chunk)
                yield chunk.choices[0].delta.content

            # Po zakończeniu zapisz statystyki jako atrybut klasy
            self.stats = {
                "prompt_tokens": chunks_list[-1].usage.prompt_tokens,
                "completion_tokens": chunks_list[-1].usage.completion_tokens,
                "reasoning_tokens": (
                    chunks_list[-1].usage.completion_tokens_details.reasoning_tokens
                    if hasattr(chunks_list[-1].usage, "completion_tokens_details")
                    else None
                ),
                "response_time": time.time() - start_time,
                "delay": delay,
            }
        except Exception as e:
            self.stats = {"Error": f"Error calling OpenAI API: {str(e)}"}
