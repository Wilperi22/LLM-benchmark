import json
import requests
import questionary
from typing import Dict, Any, List
import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

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
- Even if you hold, give position size 0.00

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


def load_market_from_dataset(path: str):
    with open(path, "r") as f:
        data = json.load(f)
    steps = data.get("market", {}).get("steps", [])
    ts = [s.get("t") for s in steps]
    prices = [s.get("price") for s in steps]
    asset_name = data.get("asset", {}).get("name", "Asset")
    return ts, prices, asset_name


def plot_prices_and_signals(ts, prices, signals, title_name, model_name, out):
    buy_t = [s["t"] for s in signals if s.get("action") == "buy"]
    buy_p = [s["price"] for s in signals if s.get("action") == "buy"]
    sell_t = [s["t"] for s in signals if s.get("action") == "sell"]
    sell_p = [s["price"] for s in signals if s.get("action") == "sell"]
    hold_t = [s["t"] for s in signals if s.get("action") == "hold"]
    hold_p = [s["price"] for s in signals if s.get("action") == "hold"]

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(ts, prices, color="tab:blue", label="price")

    if buy_t:
        ax1.scatter(buy_t, buy_p, color="red", label="buy", zorder=5, s=60)
    if sell_t:
        ax1.scatter(sell_t, sell_p, color="green", label="sell", zorder=5, s=60)
    if hold_t:
        ax1.scatter(hold_t, hold_p, color="gray", label="hold", zorder=4, s=28, marker="s")

    ax1.set_xlabel("time (t)")
    ax1.set_ylabel("price", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    try:
        min_t = int(min(ts + [s.get("t") for s in signals if s.get("t") is not None]))
        max_t = int(max(ts + [s.get("t") for s in signals if s.get("t") is not None]))
    except ValueError:
        min_t, max_t = 0, max(ts) if ts else 0

    ax1.xaxis.set_major_locator(MultipleLocator(2))
    ax1.set_xticks(range(min_t, max_t + 1, 2))
    ax1.grid(axis="x", linestyle="--", alpha=0.4)

    pv_ts = [s["t"] for s in signals if s.get("portfolio_value") is not None]
    pv_vals = [s["portfolio_value"] for s in signals if s.get("portfolio_value") is not None]
    if pv_ts and pv_vals:
        ax2 = ax1.twinx()
        ax2.plot(pv_ts, pv_vals, color="orange", label="portfolio value", linewidth=2, alpha=0.9)
        ax2.set_ylabel("portfolio value", color="orange")
        ax2.tick_params(axis="y", labelcolor="orange")
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    else:
        ax1.legend(loc="upper left")

    plt.title(f"{model_name} {title_name}: buy (red), sell (green), hold (gray), portfolio (orange)")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved plot to {out}")


def plot_in_crypto_bars(signals, title_name, model_name, out):
    bar_t = [s.get("t") for s in signals if s.get("In Crypto") is not None]
    bar_vals = [s.get("In Crypto") for s in signals if s.get("In Crypto") is not None]
    pv_t = [s.get("t") for s in signals if s.get("portfolio_value") is not None]
    pv_vals = [s.get("portfolio_value") for s in signals if s.get("portfolio_value") is not None]

    if not bar_t or not bar_vals:
        print("No In Crypto data available to plot.")
        return

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(bar_t, bar_vals, color="orange", alpha=0.75, width=0.8, label="In Crypto")
    if pv_t and pv_vals:
        ax.plot(pv_t, pv_vals, color="tab:blue", linewidth=2, label="Portfolio Value")
    ax.set_xlabel("time (t)")
    ax.set_ylabel("value in crypto")
    ax.set_title(f"{model_name} {title_name}: value in crypto over time")
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.set_xticks(range(int(min(bar_t)), int(max(bar_t)) + 1, 2))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved bar chart to {out}")


def generate_graphs(given_data_path: str, results_path: str, model_name: str):
    ts, prices, asset_name = load_market_from_dataset(given_data_path)
    with open(results_path, "r") as f:
        signals = json.load(f)

    os.makedirs("Final graphs", exist_ok=True)
    model_slug = model_name.replace(".", "")
    asset_slug = asset_name.lower().replace(" ", "_")

    out_main = f"Final graphs/{model_slug}_{asset_slug}_plot.png"
    out_bar = f"Final graphs/{model_slug}_{asset_slug}_plot_in_crypto_bar.png"

    plot_prices_and_signals(ts, prices, signals, asset_name, model_name, out_main)
    plot_in_crypto_bars(signals, asset_name, model_name, out_bar)



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

    os.makedirs("result", exist_ok=True)
    dataset_name = os.path.splitext(os.path.basename(GIVEN_DATA))[0]
    RESULTS = f"result/{MODEL_NAME}_{dataset_name}_{timestamp}.json"

    with open(RESULTS, "w") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    generate_graphs(GIVEN_DATA, RESULTS, MODEL_NAME)
