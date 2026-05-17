import json
import requests
import questionary
from typing import Dict, Any, List
import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"
GIVEN_DATA = "data.json"

def call_llm(prompt: str) -> Dict[str, Any]:
    """
    Calls local Ollama model and expects STRICT JSON output.
    """

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "think": False,
            "prompt": prompt,
            "stream": False
        }
    )

    result = response.json()

    text = result["response"].strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        # attempt cleanup if model adds junk
        print(text)
        start = text.find("{")
        end = text.rfind("}") + 1

        cleaned = text[start:end]
        
        return json.loads(cleaned)



def build_prompt(
    step: Dict[str, Any],
    fundamentals: Dict[str, Any],
    history: List[Dict[str, Any]],
    portfolio: Dict[str, Any]
) -> str:
    recent_history = history[-3:]

    return f"""
You are a professional trading agent in crypto market.

You MUST output ONLY valid JSON.

Required JSON format:

{{
  "t": {step['t']},
  "action": "buy/sell/hold",
  "confidence": 0.00 - 1.00,
  "position_size": 0.00 - 1.00,
  "reasoning": "short explanation"
}}

Rules:
- action MUST be: buy, sell, or hold
- confidence making the trade Maximum value 1 minimum 0.
- position_size Maximum value 1 minimum 0.
- You can not sell if your position is zero
- NO markdown
- NO explanations outside JSON
- OUTPUT JSON ONLY
- Eaven if you hold give position size 0.00

RECENT MARKET HISTORY:
{json.dumps(recent_history, indent=2)}

CURRENT STEP:
{json.dumps(step, indent=2)}

PORTFOLIO:
{json.dumps(portfolio, indent=2)}
"""


def apply_action(portfolio, action, price, fee=0.001):
    pos = portfolio["position"]
    cash = portfolio["cash"]

    act = action["action"]

    size = action.get("position_size", 0.0)

    if size is None:
        size = 0.0

    size = round(float(size), 2)

    if act == "buy":
        spend = cash * size

        if spend > 0 and price > 0:
            coins = (spend * (1 - fee)) / price
            portfolio["cash"] -= spend
            portfolio["position"] += coins

    elif act == "sell":
        sell_amt = pos * size

        if sell_amt > 0:
            portfolio["position"] -= sell_amt
            portfolio["cash"] += (sell_amt * price) * (1 - fee)

    return portfolio


def portfolio_value(portfolio, price):
    return portfolio["cash"] + portfolio["position"] * price



def run_benchmark(data: Dict[str, Any]):
    fundamentals = data["fundamentals"]
    steps = data["market"]["steps"]

    portfolio = {
        "cash": 10000.0,
        "position": 0.0
    }

    history = []
    log = []

    for step in steps:

        print(f"\nSTEP {step['t']}")

        prompt = build_prompt(
            step,
            fundamentals,
            history,
            portfolio
        )
        
        action = call_llm(prompt)

        print("MODEL OUTPUT:")
        print(json.dumps(action, indent=2))
    
        price = step["price"]

        portfolio = apply_action(
            portfolio,
            action,
            price
        )

        value = portfolio_value(
            portfolio,
            price
        )

        if action["position_size"] is None:
            action["position_size"] = 0.0

        log_entry = {
            "t": step["t"],
            "price": price,
            "action": action["action"],
            "confidence": action["confidence"],
            "position_size": action["position_size"],
            "portfolio_value": value,
            "Cash": portfolio["cash"],
            "In Crypto":portfolio["position"] * price,
        }

        log.append(log_entry)

        history.append(step)

        print("PORTFOLIO VALUE:", round(value, 2))
        print("CASH:", portfolio["cash"])
        print("IN CRYPTO:", portfolio["position"] * price)

    return log, portfolio


if __name__ == "__main__":

    print("\n====================")
    print("LLM BENCHMARK")
    print("====================\n")

    MODEL_NAME = questionary.select(
        "Select model",
        choices=[
            "qwen2.5:7b",
            "llama3.2:3b",
            "deepseek-r1:1.5b"
        ]
    ).ask()

    GIVEN_DATA = "data/" + questionary.select(
        "Select dataset",
        choices=[
            "btc_hourly_2026_05_14_to_2026_05_16.json",
            "trump_first_48h_2025_01_17.json",
            "xrp_hourly_2026_05_14_to_2026_05_16.json",
            "fast_test.json"
        ]
    ).ask()

    print("Selected:", MODEL_NAME, GIVEN_DATA)

    with open(GIVEN_DATA, "r") as f:
        data = json.load(f)
    
    log, final_portfolio = run_benchmark(data)

    print(json.dumps(final_portfolio, indent=2))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    print(json.dumps(log, indent=2))
    with open(f"result/{MODEL_NAME}_{GIVEN_DATA.strip(".json").strip("data/")}_{timestamp}.json","w")as f:
        json.dump(log,f,ensure_ascii=False,indent=2)
