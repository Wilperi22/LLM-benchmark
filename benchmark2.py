import json
import requests
from typing import Dict, Any, List
import datetime
# -----------------------------
# CONFIG
# -----------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek"
GIVEN_DATA = "ragpull.json"
# -----------------------------
# OLLAMA CALL
# -----------------------------
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

    # -----------------------------
    # JSON CLEANUP SAFETY
    # -----------------------------
    try:
        return json.loads(text)

    except json.JSONDecodeError:
        # attempt cleanup if model adds junk
        print(text)
        start = text.find("{")
        end = text.rfind("}") + 1

        cleaned = text[start:end]
        
        return json.loads(cleaned)


# -----------------------------
# PROMPT BUILDER
# -----------------------------
def build_prompt(
    step: Dict[str, Any],
    fundamentals: Dict[str, Any],
    history: List[Dict[str, Any]],
    portfolio: Dict[str, Any]
) -> str:
    recent_history = history[-23:]
    print(recent_history)
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
- confidence making the trade MUST be between 0 and 1.
- position_size MUST be between 0 and 1. Valuate the position size on confidence to make profit.
-You can not sell if your position is zero
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


# -----------------------------
# SIMULATION ENGINE
# -----------------------------
def apply_action(portfolio, action, price, fee=0.001):
    pos = portfolio["position"]
    cash = portfolio["cash"]

    act = action["action"]
    size = round(action["position_size"],2)

    if act == "buy":
        spend = cash * size

        if spend > 0:
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


# -----------------------------
# RUN BENCHMARK
# -----------------------------
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


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    with open(GIVEN_DATA, "r") as f:
        data = json.load(f)
    
    log, final_portfolio = run_benchmark(data)

    print("\n====================")
    print("FINAL RESULT")
    print("====================")

    print(json.dumps(final_portfolio, indent=2))

    print("\n====================")
    print("TRADE LOG")
    print("====================")

    print(json.dumps(log, indent=2))
    with open(f"{MODEL_NAME}_{GIVEN_DATA.strip(".json")}_{datetime.datetime.now()}.json","w")as f:
        json.dump(log,f,ensure_ascii=False,indent=2)
