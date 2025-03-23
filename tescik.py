# import os
# import time
# import openai


# # SAMBA

# client = openai.OpenAI(
#     api_key="4e2a54d4-0127-4c49-8889-817d8c18fd6f",
#     base_url="https://api.sambanova.ai/v1",
# )

# response = client.chat.completions.create(
#     model="DeepSeek-R1-Distill-Llama-70B",
#     messages=[{"role": "system", "content": "You are a helpful assistant"}, {"role": "user", "content": "Hello"}],
#     temperature=0.1,
#     top_p=0.1,
# )

# print(response.choices[0].message.content)
# print(response)

# chunks = []

# completion = client.chat.completions.create(
#     model="DeepSeek-R1-Distill-Llama-70B",
#     messages=[
#         {"role": "user", "content": "Hello"},
#     ],
#     stream=True,
#     stream_options={"include_usage": True},
# )

# for chunk in completion:
#     chunks.append(chunk)
#     if chunk.choices and len(chunk.choices) > 0:
#         print(chunk.choices[0].delta.content)
#     elif hasattr(chunk, "usage") and chunk.usage is not None:
#         print(chunk)
#         print("=== Stats ===")
#         print(f"Completion tokens: {chunk.usage.completion_tokens}")
#         print(f"Prompt tokens: {chunk.usage.prompt_tokens}")
#         print(f"Total tokens: {chunk.usage.total_tokens}")
#         print(f"Tokens per second: {chunk.usage.total_tokens_per_sec}")
#         print(f"Latency: {chunk.usage.total_latency}")
#         print(f"Stop reason: {chunk.usage.stop_reason}")


# # OPENAI
# class OpenAiProvider:
#     def __init__(self):
#         self.client = openai.OpenAI(
#             api_key="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",
#         )

#     def generate_request(self):
#         start_time = time.time()
#         response = self.client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": "Count to 100, with a comma between each number and no newlines. E.g., 1, 2, 3, ...",
#                 }
#             ],
#             temperature=0,
#             stream=False,
#             stream_options={"include_usage": True},
#         )

#         is_first = True

#         for chunk in response:
#             if is_first:
#                 delay = time.time() - start_time
#                 is_first = False

#             if chunk.choices and len(chunk.choices) > 0:
#                 yield chunk.choices[0].delta.content
#             elif hasattr(chunk, "usage") and chunk.usage is not None:
#                 total_time = time.time() - start_time
#                 print(chunk)
#                 print("=== Stats ===")
#                 print(f"Completion tokens: {chunk.usage.completion_tokens}")
#                 print(f"Prompt tokens: {chunk.usage.prompt_tokens}")
#                 print(f"Total tokens: {chunk.usage.total_tokens}")
#                 print(f"Tokens per second: {chunk.usage.total_tokens/total_time:.1f}")
#                 print(f"Latency: {delay:.1f}")
#                 print(f"Total time: {total_time:.1f}")
#                 self.total_time = total_time

#     def generate_request_stream(self):
#         start_time = time.time()
#         response = self.client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {
#                     "role": "user",
#                     "content": "Count to 100, with a comma between each number and no newlines. E.g., 1, 2, 3, ...",
#                 }
#             ],
#             temperature=0,
#             stream=True,
#             stream_options={"include_usage": True},
#         )

#         is_first = True

#         for chunk in response:
#             if is_first:
#                 delay = time.time() - start_time
#                 is_first = False

#             if chunk.choices and len(chunk.choices) > 0:
#                 yield chunk.choices[0].delta.content
#             elif hasattr(chunk, "usage") and chunk.usage is not None:
#                 total_time = time.time() - start_time
#                 print(chunk)
#                 print("=== Stats ===")
#                 print(f"Completion tokens: {chunk.usage.completion_tokens}")
#                 print(f"Prompt tokens: {chunk.usage.prompt_tokens}")
#                 print(f"Total tokens: {chunk.usage.total_tokens}")
#                 print(f"Tokens per second: {chunk.usage.total_tokens/total_time:.1f}")
#                 print(f"Latency: {delay:.1f}")
#                 print(f"Total time: {total_time:.1f}")
#                 self.total_time = total_time


# if __name__ == "__main__":

#     def get_answer():
#         openai = OpenAiProvider()
#         answer = openai.generate_request_stream()
#         for chunk in answer:
#             yield chunk
#         print(f"test {openai.total_time}")

#     for chunk in get_answer():
#         print(chunk)


import anthropic

client = anthropic.Anthropic(
    api_key="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"
)

with client.messages.stream(
    max_tokens=1024,
    messages=[{"role": "user", "content": "Policz od 1 do 10"}],
    model="claude-3-5-sonnet-20241022",
) as stream:
    for text in stream:
        print(f"# {text}")


print(f"...")
print(f"...")
print(f"...")
print(f"...")
print(f"...")

with client.messages.create(
    max_tokens=1024,
    messages=[{"role": "user", "content": "Policz od 1 do 10"}],
    model="claude-3-5-sonnet-20241022",
    stream=True,
) as stream:
    for text in stream:
        print(f"# {text}")
