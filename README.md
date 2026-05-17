# Deepseek XRP plot

This repository includes a small script `plot_deepseek_xrp.py` that plots price data from `XRP.json` and overlays buy (red) and sell (green) signals from a `deepseek_XRP*.json` file.

Setup and run (Linux/macOS):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python plot_deepseek_xrp.py
```

The script will auto-detect the latest `deepseek_XRP*.json` in the current directory. Use `--deepseek` to specify a particular file and `--out` to change the output image name.
# LLM-benchmark