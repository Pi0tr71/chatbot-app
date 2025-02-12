import json
import streamlit as st
import os

COSTS_PATH = "json_files/costs.json"

input_price = {
    "DeepSeek-R1-671B": 0.80,
    "DeepSeek-R1-Distill-70B": 0.70,
    "Tulu-3-405B": 5.00,
    "gpt-4o": 2.50,
    "gpt-4o-mini": 0.15,
    "o1-preview": 15.00,
    "o1-mini": 1.10,
}
output_price = {
    "DeepSeek-R1-671B": 2.40,
    "DeepSeek-R1-Distill-70B": 1.40,
    "Tulu-3-405B": 10.00,
    "gpt-4o": 10.00,
    "gpt-4o-mini": 0.60,
    "o1-preview": 60.00,
    "o1-mini": 4.40,
}

def save_costs(costs):
    os.makedirs(os.path.dirname(COSTS_PATH), exist_ok=True)
    with open(COSTS_PATH, "w") as f:
        json.dump(costs, f)

def load_costs():
    if os.path.exists(COSTS_PATH):
        with open(COSTS_PATH, "r") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    return {}


def update_costs(model, input_tokens, output_tokens):
    costs = load_costs()  # Wczytaj aktualne koszty
    
    if model not in costs:
        costs[model] = {"input_tokens": 0, "output_tokens": 0, "total_cost": 0.0}
    
    input_cost = input_tokens * input_price[model] / 1_000_000
    output_cost = output_tokens * output_price[model] / 1_000_000
    total_cost = input_cost + output_cost

    # Aktualizacja danych w słowniku
    costs[model]["input_tokens"] += input_tokens
    costs[model]["output_tokens"] += output_tokens
    costs[model]["output_tokens"] += output_tokens
    costs[model]["total_cost"] += total_cost

    st.session_state["costs"] = costs
    save_costs(costs)

def cost_cal(model, tokens, isInput):
    if isInput:
        return tokens * input_price[model]/1000000
    else:
        return tokens * output_price[model]/1000000