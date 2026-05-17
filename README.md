# LLM-Benchmark

LLM-Benchmark is a crypto trading backtest playground for local LLMs (via Ollama).
It runs a step-by-step market simulation, logs decisions, saves a result JSON, and now automatically creates graphs at the end of each benchmark run.

## What It Does

- Prompts an LLM to output `buy` / `sell` / `hold` decisions in strict JSON.
- Simulates portfolio changes with trading fees.
- Tracks portfolio value over time.
- Saves a full run log in `result/`.
- Generates charts in `Final graphs/` directly from:
  - selected dataset (`GIVEN_DATA`)
  - saved run output (`RESULTS`)

## Project Layout

```text
benchmark.py             # main benchmark runner (also auto-generates graphs)
requirements.txt
data/                    # benchmark datasets
result/                  # saved run logs
Final graphs/            # generated PNG charts
```

## Requirements

- Python 3.8+
- Ollama running locally
- One installed model (for example `qwen2.5:7b`)

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Run Benchmark (Recommended)

```bash
python benchmark.py
```

You will select:
1. Model
2. Dataset

At the end of the run, `benchmark.py` will:
1. Save run output as `RESULTS` in `result/`
2. Read market data from `GIVEN_DATA`
3. Generate charts in `Final graphs/`

### Files Created Per Run

- Result log:
  - `result/<model>_<dataset>_<timestamp>.json`
- Main chart:
  - `Final graphs/<model_slug>_<asset_slug>_plot.png`
- In-crypto bar chart:
  - `Final graphs/<model_slug>_<asset_slug>_plot_in_crypto_bar.png`

## Output Format (Result JSON)

Each run writes a list of entries like:

```json
{
  "t": 12,
  "price": 1.52,
  "action": "buy",
  "confidence": 0.81,
  "position_size": 0.40,
  "portfolio_value": 10321.77,
  "Cash": 6000.0,
  "In Crypto": 4321.77
}
```

## Auto-Generated Graphs in `benchmark.py`

After the benchmark completes, graph generation uses:

- `GIVEN_DATA`: for timeline (`t`) and asset prices
- `RESULTS`: for actions and portfolio metrics

Two graphs are produced:

1. Price + action markers + portfolio line
   - Blue line: price
   - Red points: buy
   - Green points: sell
   - Gray points: hold
   - Orange line: portfolio value

2. In-crypto value bar chart
   - Orange bars: `In Crypto`
   - Blue line: portfolio value

## Configuration Notes

In `benchmark.py`, these constants control runtime defaults:

- `OLLAMA_URL`
- `MODEL_NAME`
- `GIVEN_DATA`

The interactive prompts in `benchmark.py` select the actual model and dataset per run.

## Troubleshooting

### Ollama connection errors

- Ensure Ollama is running:

```bash
ollama serve
```

- Ensure the selected model exists:

```bash
ollama pull qwen2.5:7b
```

### Missing Python modules

Re-activate the virtual environment and reinstall dependencies:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Graphs not created

Check:
- Run completed successfully.
- `result/` contains the latest `RESULTS` file.
- `Final graphs/` is writable.

## Current Workflow Summary

- Run `benchmark.py`
- Get `RESULTS` JSON in `result/`
- Get charts in `Final graphs/`
