# Podejście nr 1
# Odpowiedzenie na pytanie w stosunku do pytania
# Sprawdzenie ważności odpowiedzi w stosunku do pytania
# Wrzucenie ważnych odpowiedzi wraz z pytaniem

# Podejście nr 2 
# Sprawdzenie ważnosći pytania w stosunku do pytania
# Odpowiedzenie na pytanie
# Sprawdzenie ważności odpowiedzi dla pytania
# Wrzucenie ważnych odpowiedzi wraz z pytaniem

# Podejście nr 3
# Odpowiedzenie na pytanie w stosunku do pytania w max 200 słowach
# Sprawdzenie ważności odpowiedzi w stosunku do pytania
# Rozszerzenie odpowiedzi
# Wrzucenie ważnych odpowiedzi wraz z pytaniem

import pandas as pd
import re
from models.openai_provider import OpenAiChatProvider

def better_response(messages, model, api_key):
    file_path = 'csv_files/questions.csv' 
    questions = pd.read_csv(file_path, delimiter=';')

    input_tokens = 0
    output_tokens = 0

    knowledge = []
    thinking = ""

    for question in questions['question']:
        prompt = []
        
        prompt.append(messages[-1])
        prompt.append({"role": "user", "content": f"Odpowiedź na pytanie: {question} Nie odpowiadając na zapytanie. W kontekście poprzedniego zapytania"})

        thinking += f"<think>Odpowiedź na pytanie: {question} w kontekście poprzedniego zapytania</think>"

        response, i_tokens, o_tokens  = OpenAiChatProvider.openai_chat_completion(prompt, "gpt-4o-mini", api_key, 1)
        input_tokens += i_tokens
        output_tokens += o_tokens

        thinking += f"<think>{response}</think>"

        prompt_checker = []
        prompt_checker.append(messages[-1])
        prompt_checker.append({"role": "user", "content": f"Czy wiedza o : {response}. Czy ta wiedza w kontekście poprzedniego zapytania pomoże w znacznym stopniu w odpowiedzi na poprzednie zapytanie. Jeśli jest mało przydatna odrzuć. Odpowiedź tylko i wyłącznie: TAK lub NIE"})
        
        boolean, i_tokens, o_tokens  = OpenAiChatProvider.openai_chat_completion(prompt_checker, "gpt-4o-mini", api_key, 1)
        
        input_tokens += i_tokens
        output_tokens += o_tokens

        thinking += f"<think>Czy wiedza ta będzie przydatna: {boolean}</think>"

        if re.match(r"^\s*tak\s*[.!?]?\s*$", boolean, re.IGNORECASE):
            knowledge.append({"role": "assistant", "content": f"{response}"})
    
    
    knowledge.append({"role": "assistant", "content": f"Na podstawie wcześniejszych odpowiedzi i swojej wiedzy odpowiedz na zapytanie: {messages[-1]["content"]}"})
    final_response, i_tokens, o_tokens = OpenAiChatProvider.openai_chat_completion(knowledge, model, api_key, -1)
    input_tokens += i_tokens
    output_tokens += o_tokens

    thinking += final_response

    return thinking, input_tokens, output_tokens


    # The function better_response processes a set of questions from a CSV file, generates answers
    # using an OpenAI language model, and checks the relevance of those answers in relation to a previous query.
    # It builds a conversation flow where for each question, it first retrieves an answer, then evaluates
    # if that answer is useful. Relevant answers are stored, and eventually, a final response is generated
    # based on the accumulated knowledge.    # The function better_response processes a set of questions from a CSV file, generates answers
    # using an OpenAI language model, and checks the relevance of those answers in relation to a previous query.
    # It builds a conversation flow where for each question, it first retrieves an answer, then evaluates
    # if that answer is useful. Relevant answers are stored, and eventually, a final response is generated
    # based on the accumulated knowledge.