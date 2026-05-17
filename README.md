# LLM-Benchmark: Cryptocurrency Trading Bot Evaluation Framework

A comprehensive benchmarking system for evaluating Large Language Models (LLMs) on cryptocurrency trading decisions. This project tests different LLMs (via Ollama) on historical market data and visualizes their trading performance against actual price movements.

## 📋 Overview

**LLM-Benchmark** allows you to:
- Run multiple LLM models on cryptocurrency trading scenarios
- Generate buy/sell/hold trading signals from LLM reasoning
- Track portfolio performance in simulated trading environments
- Visualize trading signals and portfolio value over time
- Compare performance across different models and assets
- Analyze model confidence levels and position sizing decisions

## 🏗️ Project Structure

```
├── benchmark.py              # Main trading simulation engine
├── plot_deepseek_xrp.py     # Visualization and analysis toolkit
├── requirements.txt          # Python dependencies
├── data/                     # Historical market data (JSON format)
│   ├── btc_hourly_*.json
│   ├── xrp_hourly_*.json
│   ├── trump_first_48h_*.json
│   └── fast_test.json       # Quick test dataset
├── result/                   # Benchmark results (auto-generated)
│   └── [model_name]_[asset]_[timestamp].json
└── Final graphs/             # Generated visualization plots
```

## 📊 Data Format

Market data files contain:
```json
{
  "id": "asset_period_identifier",
  "asset": {
    "name": "Asset Name",
    "symbol": "SYMBOL",
    "chain": "blockchain"
  },
  "fundamentals": {
    "token_age_days": 0,
    "liquidity_locked": true,
    "liquidity_usd": 0,
    "owner_percent": 0,
    "top10_holders_percent": 0,
    "mintable": false,
    "contract_renounced": true,
    "audit_exists": true
  },
  "market": {
    "initial_price": 0.00,
    "steps": [
      { "t": 0, "price": 0.00, "volume": 0, "liquidity": 0 },
      { "t": 1, "price": 0.01, "volume": 100, "liquidity": 1000 }
    ]
  },
  "ground_truth": {
    "final_price": 0.05,
    "rug_occurred": false,
    "risk_level": "low",
    "optimal_strategy": "mixed",
    "max_return": 0.50,
    "max_drawdown": 0.20,
    "key_risk_factors": []
  }
}
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai/) running locally with at least one model installed
  - Default: `qwen2.5:7b` (supports: `llama3.2:3b`, `deepseek-r1:1.5b`)
  - Ollama server must be accessible at `http://localhost:11434`

### Installation

```bash
# Clone repository
git clone <repository-url>
cd LLM-benchmark

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Run Trading Benchmark

```bash
python3 benchmark.py
```

You'll be prompted to:
1. **Select a model** - Choose which LLM to test
2. **Select a dataset** - Choose market data (BTC, XRP, Trump, Fast test, etc.)

The system will:
- Run the LLM through each market step
- Generate trading signals for each step
- Track portfolio value changes
- Save results to `result/` directory

**Output:** `result/{MODEL}_{ASSET}_{TIMESTAMP}.json`

#### Example Output Format
```json
[
  {
    "t": 0,
    "price": 1.4271,
    "action": "buy",
    "confidence": 0.85,
    "position_size": 0.50,
    "portfolio_value": 10000.0,
    "Cash": 10000.0,
    "In Crypto": 0.0
  },
  {
    "t": 1,
    "price": 1.4310,
    "action": "hold",
    "confidence": 0.72,
    "position_size": 0.0,
    "portfolio_value": 10272.13,
    "Cash": 5000.0,
    "In Crypto": 5272.13
  }
]
```

### Visualize Results

```bash
# Plot latest results for all assets
python3 plot_deepseek_xrp.py

# Plot specific asset
python3 plot_deepseek_xrp.py --asset xrp

# Plot specific asset with specific model results
python3 plot_deepseek_xrp.py --asset btc --model deepseek

# Compare models
python3 plot_deepseek_xrp.py --compare-models

# Show buy/sell size annotations
python3 plot_deepseek_xrp.py --annotate-sizes

# Export as bars chart
python3 plot_deepseek_xrp.py --bar-in-crypto
```

#### Plotting Options
- `--asset {all|xrp|btc|trumpcoin|rocket|ragpull}` - Which asset to plot
- `--model {deepseek|lobotomite2.0|all}` - Which model signals to use
- `--deepseek PATH` - Use specific signal file
- `--out NAME` - Output image filename
- `--compare-models` - Plot model comparison charts
- `--bar-in-crypto` - Generate bar charts for crypto holdings
- `--all-files` - Plot every matching signal file
- `--size-units {usd|coins|both}` - How to label trade sizes
- `--annotate-sizes` - Show size labels on plot
- `--no-annotate-sizes` - Hide size labels

## 📈 Understanding the Plots

The visualization generates several chart types:

1. **Price + Trading Signals**
   - Blue line: Asset price over time
   - Red dots: Buy signals (sized by amount)
   - Green dots: Sell signals (sized by amount)
   - Gray squares: Hold signals
   - Orange line: Portfolio value (secondary axis)

2. **Model Comparison**
   - Blue line: Asset price
   - Orange line: Deepseek portfolio value
   - Purple line: Lobotomite2.0 portfolio value

3. **Crypto Holdings Bar Chart**
   - Bars: USD value held in crypto
   - Blue line: Total portfolio value

## 🤖 How It Works

### Trading Loop (benchmark.py)

1. **Initialize**: Start with $10,000 portfolio
2. **For each market step**:
   - Collect recent market history (last 3 steps)
   - Build comprehensive prompt with:
     - Current price, volume, liquidity
     - Fundamentals (token age, holders, audit status)
     - Portfolio state (cash, position, value)
     - Recent trade history
   - Call LLM to generate decision
   - Parse JSON response: `action`, `confidence`, `position_size`, `reasoning`
   - Execute trade:
     - **Buy**: Use `position_size` % of cash to purchase at current price (0.1% fee)
     - **Sell**: Close `position_size` % of holdings (0.1% fee)
     - **Hold**: Keep current position
   - Record: Price, action, portfolio state, portfolio value
3. **Output**: Save full trading log and final portfolio value

### LLM Prompting

The LLM is asked to output **valid JSON only** with:
```json
{
  "t": <timestamp>,
  "action": "buy|sell|hold",
  "confidence": 0.0-1.0,
  "position_size": 0.0-1.0,
  "reasoning": "brief explanation"
}
```

**Key constraints enforced:**
- Cannot sell if position is zero
- Position size cannot exceed 100%
- Fee charged on all trades (buy/sell)

## ⚙️ Configuration

Edit these constants in `benchmark.py` or `plot_deepseek_xrp.py`:

```python
# benchmark.py
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"  # Change to your model
GIVEN_DATA = "data.json"   # Change to your data file
```

### Adding Custom Models

1. Ensure model is installed in Ollama: `ollama pull model-name`
2. Add to choices in benchmark.py:
   ```python
   choices=[
       "qwen2.5:7b",
       "your-model-name"
   ]
   ```

### Adding Custom Datasets

1. Create data file in `data/` directory following the JSON format above
2. Add to choices in benchmark.py:
   ```python
   choices=[
       "your_dataset.json",
       "another_dataset.json"
   ]
   ```

## 📋 Results Analysis

Benchmark results are saved as JSON with complete trading history. Use these metrics to evaluate model performance:

| Metric | Calculation | Interpretation |
|--------|-------------|-----------------|
| **Final Portfolio Value** | Cash + (Crypto Position × Final Price) | Total value after trading |
| **Return %** | (Final Value - Initial) / Initial × 100 | Overall profit/loss |
| **Win Rate** | (Profitable Trades) / (Total Trades) × 100 | % of trades that made money |
| **Max Drawdown** | (Peak Value - Lowest Value) / Peak Value × 100 | Worst portfolio decline |
| **Trade Count** | Sum of buy + sell actions | Activity level |
| **Avg Confidence** | Mean of confidence scores | Model certainty |

## 🐛 Known Issues & Limitations

### Current Limitations
1. **Single-threaded**: Processes models sequentially
2. **Static starting balance**: Always starts with $10,000
3. **Fixed trading fee**: 0.1% on all trades
4. **Local Ollama only**: No support for API-based LLMs (yet)
5. **Historical data only**: No real-time trading capability
6. **Deterministic models**: Results vary; LLMs are not deterministic

### Workarounds
- Run benchmarks multiple times to understand variance
- Modify starting balance in `apply_action()` function
- Adjust fee rate in `apply_action()` function
- Integrate other LLM providers (OpenAI, Anthropic, etc.)

## 🔧 Troubleshooting

### "Connection refused" error
```
Error: Failed to connect to http://localhost:11434
```
**Solution**: Start Ollama server
```bash
ollama serve
```

### "Model not found" error
```
Error: Model 'model-name' not found
```
**Solution**: Pull the model first
```bash
ollama pull qwen2.5:7b
```

### JSON decode error in benchmark output
```
json.JSONDecodeError: Invalid JSON from model
```
**Solution**: 
- Model may not follow instructions; try different model
- Add cleanup logic in `call_llm()` - currently attempts basic parsing
- Verify model prompt is clear (check print output)

### Missing market files for plotting
```
FileNotFoundError: No market files found
```
**Solution**: Market files (XRP.json, BTC.json) expected in root directory. Adjust paths in `plot_deepseek_xrp.py` ASSET_CONFIG or copy data files appropriately.

## 📝 File Reference

| File | Purpose |
|------|---------|
| `benchmark.py` | Main trading simulation + LLM integration |
| `plot_deepseek_xrp.py` | Comprehensive visualization toolkit |
| `requirements.txt` | Python package dependencies |
| `data/*.json` | Historical market data for backtesting |
| `result/*.json` | Trading simulation results (auto-generated) |
| `Final graphs/*.png` | Visualization outputs (auto-generated) |

## 🚀 Performance Tips

1. **Faster testing**: Use `fast_test.json` during development
2. **Parallel benchmarks**: Run multiple instances with different `--deepseek` files
3. **Memory efficient**: Delete old results before running many simulations
4. **Plot generation**: Use `--no-annotate-sizes` for faster plot generation

## 📚 Example Workflow

```bash
# 1. Ensure Ollama is running
ollama serve &

# 2. Run benchmark with qwen2.5:7b on BTC data
python3 benchmark.py
# Select: qwen2.5:7b → btc_hourly_2026_05_14_to_2026_05_16.json

# 3. Visualize results
python3 plot_deepseek_xrp.py --asset btc --model deepseek

# 4. Compare multiple models
python3 plot_deepseek_xrp.py --compare-models --asset btc

# 5. Analyze results
# Check: result/qwen2.5:7b_btc_hourly_2026_05_14_to_2026_05_16_TIMESTAMP.json
```

## 🔬 Advanced Usage

### Modify LLM Prompt

Edit `build_prompt()` in `benchmark.py` to customize:
- What information the LLM sees
- How positions are scaled
- Risk parameters
- Decision constraints

### Add Custom Metrics

Extend the logging in `run_benchmark()`:
```python
# Add to log_entry dict
"sharpe_ratio": calculate_sharpe(...),
"max_position": current_max_position,
"fee_paid": total_fees,
```

### Batch Testing

Create a script to run multiple benchmarks:
```bash
for model in "qwen2.5:7b" "llama3.2:3b"; do
  for dataset in data/*.json; do
    echo "Testing $model on $dataset"
    # Automate questionary selection
  done
done
```

## 📄 License

[Add your license information here]

## 👨‍💼 Contributing

[Add contribution guidelines here]

## 📧 Support

For issues, questions, or suggestions, please open an issue in the repository.