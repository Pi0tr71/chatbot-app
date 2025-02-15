import re

def get_next_chat_name(existing_chats):
    index = 1
    while True:
        potential_name = f"Chat {index}"
        if potential_name not in existing_chats:
            return potential_name
        index += 1

def split_response(response):

    think_parts = re.findall(r"<think>(.*?)</think>", response, flags=re.DOTALL)
    normal_part = re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()
    
    return think_parts, normal_part

def check_existing(chat_name, existing_chats):
    index = 1
    if chat_name in existing_chats:
        while True:
            potential_name = f"{chat_name} {index}"
            if potential_name not in existing_chats:
                return potential_name
            index += 1
    return chat_name