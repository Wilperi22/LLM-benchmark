#!/usr/bin/env python3
import json
import glob
import argparse
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator


ASSET_CONFIG = {
    "xrp": {
        "market_file": "XRP.json",
        "signal_patterns": {
            "deepseek": ["deepseek_XRP*.json"],
            "lobotomite2.0": ["Lobotomite2.0_XRP*.json"],
        },
        "title": "XRP",
        "out": "xrp_plot.png",
    },
    "btc": {
        "market_file": "BTC.json",
        "signal_patterns": {
            "deepseek": ["deepseek_BTC*.json"],
            "lobotomite2.0": ["Lobotomite2.0_BTC*.json"],
        },
        "title": "BTC",
        "out": "btc_plot.png",
    },
    "trumpcoin": {
        "market_file": "Trumpcoin.json",
        "signal_patterns": {
            "deepseek": ["deepseek_Trumpcoi*.json", "deepseek_Trumpcoin*.json"],
            "lobotomite2.0": ["Lobotomite2.0_Trumpcoi*.json", "Lobotomite2.0_Trumpcoin*.json"],
        },
        "title": "Trumpcoin",
        "out": "trumpcoin_plot.png",
    },
    "rocket": {
        "market_file": "Rocket.json",
        "signal_patterns": {
            "deepseek": ["deepseek_Rocket*.json", "deepseek_BOME*.json"],
            "lobotomite2.0": ["Lobotomite2.0_Rocket*.json", "Lobotomite2.0_BOME*.json"],
        },
        "title": "Rocket",
        "out": "rocket_plot.png",
    },
    "ragpull": {
        "market_file": "ragpull.json",
        "signal_patterns": {
            "deepseek": ["deepseek_ragpull*.json"],
            "lobotomite2.0": ["Lobotomite2.0_ragpull*.json"],
        },
        "title": "Ragpull",
        "out": "ragpull_plot.png",
    },
}


def load_market(path):
    with open(path, "r") as f:
        data = json.load(f)
    steps = data.get("market", {}).get("steps", [])
    ts = [s.get("t") for s in steps]
    prices = [s.get("price") for s in steps]
    return ts, prices


def load_signals(patterns, path=None, all_files=False):
    if path:
        files = [path]
    else:
        files = []
        for pattern in patterns:
            files.extend(glob.glob(pattern))
        files = sorted(set(files))
    if not files:
        raise FileNotFoundError(f"No signal files found for patterns: {patterns}")
    if all_files:
        results = []
        for chosen in files:
            with open(chosen, "r") as f:
                data = json.load(f)
            results.append((data, chosen))
        return results
    # pick the last (usually the most recent)
    chosen = files[-1]
    with open(chosen, "r") as f:
        data = json.load(f)
    return data, chosen


def scale_marker_sizes(values, min_size=35, max_size=180):
    if not values:
        return []
    vmin, vmax = min(values), max(values)
    if vmin == vmax:
        return [0.5 * (min_size + max_size)] * len(values)
    return [min_size + (v - vmin) / (vmax - vmin) * (max_size - min_size) for v in values]


def format_amount(usd, coins, mode):
    def short_usd(value):
        if value >= 1_000_000:
            return f"${value/1_000_000:.2f}M"
        if value >= 1_000:
            return f"${value/1_000:.2f}k"
        return f"${value:.2f}"

    if mode == "usd":
        return short_usd(usd)
    if mode == "coins":
        return f"{coins:.6f}"
    return f"{short_usd(usd)} / {coins:.6f}"


def compute_trade_sizes(signals):
    trade_info = {}
    for i in range(1, len(signals)):
        prev = signals[i - 1]
        curr = signals[i]
        act = curr.get("action")
        if act not in ("buy", "sell"):
            continue
        price_prev = prev.get("price")
        price_curr = curr.get("price")
        cash_prev = prev.get("Cash")
        cash_curr = curr.get("Cash")
        in_prev = prev.get("In Crypto")
        in_curr = curr.get("In Crypto")
        t_curr = curr.get("t")

        if None in (price_prev, price_curr, cash_prev, cash_curr, in_prev, in_curr, t_curr):
            continue
        if price_prev == 0 or price_curr == 0:
            continue

        pos_prev = in_prev / price_prev
        pos_curr = in_curr / price_curr
        delta_coins = pos_curr - pos_prev

        if act == "buy":
            usd = cash_prev - cash_curr
            coins = delta_coins
        else:
            usd = cash_curr - cash_prev
            coins = -delta_coins

        usd = max(0.0, usd)
        coins = max(0.0, coins)
        if usd == 0.0 and coins == 0.0:
            continue

        trade_info[t_curr] = {"usd": usd, "coins": coins}

    return trade_info


def plot_prices(ts, prices, signals, title_name, model_name, out, annotate_sizes=True, size_units="usd"):
    buy_t = [s["t"] for s in signals if s.get("action") == "buy"]
    buy_p = [s["price"] for s in signals if s.get("action") == "buy"]
    sell_t = [s["t"] for s in signals if s.get("action") == "sell"]
    sell_p = [s["price"] for s in signals if s.get("action") == "sell"]
    hold_t = [s["t"] for s in signals if s.get("action") == "hold"]
    hold_p = [s["price"] for s in signals if s.get("action") == "hold"]

    trade_info = compute_trade_sizes(signals)

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(ts, prices, color="tab:blue", label="price")
    if buy_t:
        buy_info = [trade_info.get(t) for t in buy_t]
        buy_t2 = [t for t, info in zip(buy_t, buy_info) if info]
        buy_p2 = [p for p, info in zip(buy_p, buy_info) if info]
        buy_usd = [info["usd"] for info in buy_info if info]
        sizes = scale_marker_sizes(buy_usd) if buy_usd else 60
        ax1.scatter(buy_t2, buy_p2, color="red", label="buy", zorder=5, s=sizes)
        if annotate_sizes:
            for t, p, info in zip(buy_t2, buy_p2, [trade_info.get(t) for t in buy_t2]):
                label = format_amount(info["usd"], info["coins"], size_units)
                ax1.annotate(label, (t, p), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
    if sell_t:
        sell_info = [trade_info.get(t) for t in sell_t]
        sell_t2 = [t for t, info in zip(sell_t, sell_info) if info]
        sell_p2 = [p for p, info in zip(sell_p, sell_info) if info]
        sell_usd = [info["usd"] for info in sell_info if info]
        sizes = scale_marker_sizes(sell_usd) if sell_usd else 60
        ax1.scatter(sell_t2, sell_p2, color="green", label="sell", zorder=5, s=sizes)
        if annotate_sizes:
            for t, p, info in zip(sell_t2, sell_p2, [trade_info.get(t) for t in sell_t2]):
                label = format_amount(info["usd"], info["coins"], size_units)
                ax1.annotate(label, (t, p), textcoords="offset points", xytext=(0, -10), ha="center", fontsize=8)
    if hold_t:
        ax1.scatter(hold_t, hold_p, color="gray", label="hold", zorder=4, s=28, marker="s")
    ax1.set_xlabel("time (t)")
    ax1.set_ylabel("price", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    # set x ticks every 2 hours
    try:
        min_t = int(min(ts + [s.get("t") for s in signals if s.get("t") is not None]))
        max_t = int(max(ts + [s.get("t") for s in signals if s.get("t") is not None]))
    except ValueError:
        min_t, max_t = 0, max(ts) if ts else 0
    ax1.xaxis.set_major_locator(MultipleLocator(2))
    ax1.set_xticks(range(min_t, max_t + 1, 2))
    ax1.grid(axis="x", linestyle="--", alpha=0.4)

    # plot portfolio value on secondary axis if present
    pv_ts = [s["t"] for s in signals if s.get("portfolio_value") is not None]
    pv_vals = [s["portfolio_value"] for s in signals if s.get("portfolio_value") is not None]
    if pv_ts and pv_vals:
        ax2 = ax1.twinx()
        ax2.plot(pv_ts, pv_vals, color="orange", label="portfolio value", linewidth=2, alpha=0.9)
        ax2.set_ylabel("portfolio value", color="orange")
        ax2.tick_params(axis="y", labelcolor="orange")
        # combine legends
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
    ax.set_title(f"{model_name} {title_name}: value in crypto over 48 hours")
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.set_xticks(range(int(min(bar_t)), int(max(bar_t)) + 1, 2))
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved bar chart to {out}")


def plot_model_compare(ts, prices, deepseek_signals, lobotomite_signals, title_name, out):
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.plot(ts, prices, color="tab:blue", label="price")
    ax1.set_xlabel("time (t)")
    ax1.set_ylabel("price", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ds_t = [s.get("t") for s in deepseek_signals if s.get("portfolio_value") is not None]
    ds_v = [s.get("portfolio_value") for s in deepseek_signals if s.get("portfolio_value") is not None]
    lb_t = [s.get("t") for s in lobotomite_signals if s.get("portfolio_value") is not None]
    lb_v = [s.get("portfolio_value") for s in lobotomite_signals if s.get("portfolio_value") is not None]

    if ds_t and ds_v:
        ax2.plot(ds_t, ds_v, color="orange", label="deepseek portfolio", linewidth=2, alpha=0.9)
    if lb_t and lb_v:
        ax2.plot(lb_t, lb_v, color="purple", label="lobotomite2.0 portfolio", linewidth=2, alpha=0.9)

    ax2.set_ylabel("portfolio value", color="black")
    ax2.tick_params(axis="y", labelcolor="black")

    ax1.xaxis.set_major_locator(MultipleLocator(2))
    ax1.set_xticks(range(int(min(ts)), int(max(ts)) + 1, 2))
    ax1.grid(axis="x", linestyle="--", alpha=0.4)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.title(f"{title_name}: price vs portfolio performance")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    print(f"Saved model comparison chart to {out}")


def main():
    p = argparse.ArgumentParser(
        description="Plot buy/sell/hold signals and portfolio value for supported assets"
    )
    p.add_argument(
        "--asset",
        default="all",
        choices=["all", "xrp", "btc", "trumpcoin", "rocket", "ragpull"],
        help="which asset to plot",
    )
    p.add_argument(
        "--model",
        default="deepseek",
        choices=["deepseek", "lobotomite2.0", "all"],
        help="which model output files to use",
    )
    p.add_argument(
        "--deepseek",
        default=None,
        help="optional explicit signals json path (only used when --asset is not all and --model is not all)",
    )
    p.add_argument(
        "--out",
        default=None,
        help="optional output image name (only used when --asset is not all)",
    )
    p.add_argument(
        "--bar-in-crypto",
        action="store_true",
        help="generate a bar chart for value currently in crypto",
    )
    p.add_argument(
        "--compare-models",
        action="store_true",
        help="generate price + portfolio comparison chart for deepseek vs lobotomite2.0",
    )
    p.add_argument(
        "--all-files",
        action="store_true",
        help="plot every matching signals file instead of only the latest",
    )
    p.add_argument(
        "--size-units",
        default="usd",
        choices=["usd", "coins", "both"],
        help="label units for buy/sell sizes",
    )
    p.add_argument(
        "--annotate-sizes",
        dest="annotate_sizes",
        action="store_true",
        help="show buy/sell size labels",
    )
    p.add_argument(
        "--no-annotate-sizes",
        dest="annotate_sizes",
        action="store_false",
        help="disable buy/sell size labels",
    )
    p.set_defaults(annotate_sizes=False)
    args = p.parse_args()

    if args.asset != "all":
        assets = [args.asset]
    else:
        assets = ["btc", "xrp", "trumpcoin", "ragpull"]
    models = [args.model] if args.model != "all" else ["deepseek", "lobotomite2.0"]

    for model in models:
        model_slug = model.replace(".", "")
        for asset in assets:
            cfg = ASSET_CONFIG[asset]
            ts, prices = load_market(cfg["market_file"])
            patterns = cfg["signal_patterns"].get(model, [])
            if not patterns:
                if args.asset == "all" or args.model == "all":
                    print(f"Warning: no patterns configured for model '{model}' and asset '{asset}'")
                    continue
                raise FileNotFoundError(f"No patterns configured for model '{model}' and asset '{asset}'")

            try:
                override_file = args.deepseek if (args.asset != "all" and args.model != "all") else None
                if args.all_files and not override_file:
                    results = load_signals(patterns, all_files=True)
                else:
                    results = [load_signals(patterns, override_file)]
                title_name = cfg["title"]
            except FileNotFoundError as err:
                if args.asset == "all" or args.model == "all":
                    results = []
                    title_name = f"{cfg['title']} (no {model} signals file found)"
                    print(f"Warning: {err}")
                else:
                    raise

            for signals, chosen in results:
                if chosen:
                    print(f"Using {model} file for {asset.upper()}: {chosen}")
                default_out = f"{model_slug}_{cfg['out']}"
                if chosen and args.all_files:
                    base = chosen.replace(" ", "_").replace(".", "_")
                    base = base.replace("/", "_")
                    default_out = f"{model_slug}_{base}_plot.png"
                out_name = args.out if (args.asset != "all" and args.out) else default_out
                plot_prices(
                    ts,
                    prices,
                    signals,
                    title_name=title_name,
                    model_name=model,
                    out=out_name,
                    annotate_sizes=args.annotate_sizes,
                    size_units=args.size_units,
                )
                if args.bar_in_crypto:
                    bar_out = out_name.replace(".png", "_in_crypto_bar.png")
                    plot_in_crypto_bars(signals, title_name=title_name, model_name=model, out=bar_out)

            if args.compare_models:
                cfg = ASSET_CONFIG[asset]
                ts, prices = load_market(cfg["market_file"])
                ds_patterns = cfg["signal_patterns"].get("deepseek", [])
                lb_patterns = cfg["signal_patterns"].get("lobotomite2.0", [])
                if not ds_patterns or not lb_patterns:
                    print(f"Warning: compare-models requires deepseek and lobotomite2.0 patterns for {asset}")
                    continue

                try:
                    ds_signals, ds_file = load_signals(ds_patterns)
                    lb_signals, lb_file = load_signals(lb_patterns)
                except FileNotFoundError as err:
                    print(f"Warning: {err}")
                    continue

                compare_out = f"compare_{asset}_price_portfolio.png"
                if args.all_files:
                    ds_base = ds_file.replace(" ", "_").replace(".", "_").replace("/", "_")
                    lb_base = lb_file.replace(" ", "_").replace(".", "_").replace("/", "_")
                    compare_out = f"compare_{asset}_{ds_base}__{lb_base}.png"
                plot_model_compare(
                    ts,
                    prices,
                    ds_signals,
                    lb_signals,
                    title_name=cfg["title"],
                    out=compare_out,
                )


if __name__ == "__main__":
    main()
