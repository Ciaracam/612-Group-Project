"""Generate notebooks/transformer_forecasting.ipynb.

The notebook is the readable walkthrough of the project. It imports from `src/`
rather than redefining the pipeline, so the notebook and the command-line
scripts can never drift apart.

    python scripts/build_notebook.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip().split("\n")}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.strip("\n").split("\n"),
    }


CELLS = [
    md("""
# Transformer-Based Electricity Consumption Forecasting

**MSML612 — Deep Learning** · William Peng, Ciara Cameron, Christopher Pedretti

This notebook walks through the full project: data preparation, model design,
training, and evaluation against reference forecasters.

The pipeline lives in `src/` so that the notebook, the command-line training
script, and the live demo all share one implementation. Run the notebook from the
repository root.

**Before running:** download the dataset from the
[UCI repository](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)
and place `household_power_consumption.txt` in `data/`.
"""),
    code("""
import sys
from pathlib import Path

# Ensure the project root is importable when running from notebooks/
ROOT = Path.cwd() if (Path.cwd() / "src").exists() else Path.cwd().parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch

print("PyTorch:", torch.__version__)
"""),
    md("""
---
## 1. The problem

Short-term load forecasting predicts electricity demand one or more hours ahead.
Utilities use it for generation scheduling and grid balancing; at the household
level it supports demand-response programmes and battery dispatch.

The difficulty is that household demand is **spiky and non-stationary**. A single
home's load is dominated by discrete appliance events, so the series has sharp
peaks against a low baseline rather than the smooth aggregate curve a
substation-level series would show.

We forecast **global active power** one hour ahead from the previous 24 hours of
multivariate measurements.
"""),
    md("""
---
## 2. Data preparation

The raw file is 2,075,259 minute-level readings taken over roughly four years.
Preparation involves five steps, all implemented in `src/data.py`:

1. **Parse and index** — combine the separate date and time columns into a
   timestamp index, coerce all measurements to numeric, and drop duplicate timestamps.
2. **Resample to hourly means** — convert the minute-level series to hourly means,
   reducing the data from 2.08 million readings to 34,589 hours.
3. **Add calendar features** — hour of day, day of week, and month encoded as
   sine/cosine pairs, plus a weekend indicator.
4. **Split chronologically, then interpolate** — divide the series 70/15/15 by
   time and fill remaining missing hours independently within each split so values
   cannot leak across split boundaries.
5. **Scale** — fit `StandardScaler` on the training split only and use those same
   statistics to transform validation and test.

The order matters: interpolation is performed separately within each split, and
the scalers are fit using training data only. This prevents information from the
validation or test periods from leaking backward into training.
"""),
    code("""
from src.data import DataConfig, prepare_data

config = DataConfig(
    data_path=ROOT / "data" / "household_power_consumption.txt",
    sequence_length=24,
    horizon=1,
    use_calendar_features=True,
    batch_size=64,
)

data = prepare_data(config)

for key, value in data.stats.items():
    print(f"{key:22s} {value}")
"""),
    code("""
# Feature set actually fed to the model
print(f"{len(data.feature_columns)} input features:")
for name in data.feature_columns:
    print("  -", name)
"""),
    md("""
### Windowing

Each training example is a 24-hour window of all input features paired with the
target for the following hour. Windows are built **within** each split, so no
input window straddles a split boundary and no future information reaches the
model.
"""),
    code("""
x_batch, y_batch = next(iter(data.train_loader))
print("Input batch :", tuple(x_batch.shape), "(batch, window, features)")
print("Target batch:", tuple(y_batch.shape), "(batch, horizon)")
"""),
    md("""
---
## 3. Model

Self-attention lets every hour in the window attend directly to every other hour,
so a 24-hour dependency is a single hop rather than 24 sequential recurrent steps.
That matters for load data, where the informative signal is often "what happened
at this hour yesterday" rather than "what happened last hour."

Because attention is permutation-invariant, sinusoidal positional encodings are
added after the input projection to restore temporal ordering.

We use **pre-norm** encoder layers (LayerNorm before the sublayer rather than
after), which trains more stably at this depth than the original post-norm
formulation.
"""),
    code("""
from src.model import ElectricityTransformer, count_parameters

model = ElectricityTransformer(
    input_size=len(data.feature_columns),
    d_model=64,
    num_heads=4,
    num_layers=2,
    dim_feedforward=128,
    dropout=0.1,
    horizon=config.horizon,
)

print(model)
print(f"\\nTrainable parameters: {count_parameters(model):,}")
"""),
    md("""
---
## 4. Training

Training uses Adam, MSE loss, gradient clipping at 1.0, `ReduceLROnPlateau`
scheduling, and early stopping on validation loss.

Early stopping is not cosmetic here. Our interim 20-epoch run reached its best
validation loss at **epoch 9** and then drifted upward for eleven more epochs
while training loss kept falling — textbook overfitting. Stopping on validation
loss removes that wasted compute and guarantees the checkpoint we evaluate is the
best one seen.

Training from the notebook is convenient for a short run; for the reported
results we use the command-line script, which records a full history file:

```bash
python -m src.train --run-name transformer_h1
```
"""),
    code("""
from src.train import main as train_main

history = train_main([
    "--run-name", "transformer_h1",
    "--epochs", "60",
    "--patience", "8",
])
"""),
    md("""
### Training and validation loss

This curve is the required diagnostic: training and validation MSE against epoch,
with the selected checkpoint marked.
"""),
    code("""
from src.plots import plot_loss_curve

plot_loss_curve(
    history["train_losses"],
    history["val_losses"],
    history["best_epoch"],
    ROOT / "figures" / "transformer_h1_loss_curve.png",
)

from IPython.display import Image
Image(str(ROOT / "figures" / "transformer_h1_loss_curve.png"))
"""),
    md("""
---
## 5. Evaluation

Metrics alone do not establish that a deep model is worth its complexity. A model
reporting RMSE of 0.46 kW sounds precise until you learn that repeating the
previous hour's reading gets 0.57 kW for free.

We therefore evaluate against three reference forecasters:

- **Naive persistence** — predict the previous hour. The standard baseline for
  hourly load, and a strong one.
- **Seasonal naive** — predict the same hour yesterday.
- **Mean predictor** — predict the test-series mean. The R² = 0 reference point.
"""),
    code("""
from src.evaluate import main as evaluate_main

results = evaluate_main(["--run-name", "transformer_h1"])
"""),
    code("""
comparison = pd.DataFrame(results["comparison_table"]).T[["MAE", "RMSE", "R2"]].round(4)
comparison
"""),
    code("""
print(f"RMSE reduction vs. naive persistence: "
      f"{results['skill_vs_persistence_pct']:.1f}%")
"""),
    md("""
---
## 6. Where the model still struggles

The residual plots show the characteristic failure mode of point forecasting on
spiky data: the model tracks the daily cycle well but **systematically
under-predicts sharp demand peaks**. MSE training makes this rational — a
confident spike prediction that misses is punished quadratically, so the optimum
is to hedge toward the mean.

This is the single most useful direction for future work: a quantile or
distributional loss would let the model express uncertainty about peaks rather
than averaging them away.
"""),
    code("""
Image(str(ROOT / "figures" / "transformer_h1_error_distribution.png"))
"""),
    md("""
---
## 7. Ablations

Each row is an independent train-and-evaluate cycle. This is what justifies the
final configuration rather than presenting it as a given.

```bash
python -m src.ablation --group all --epochs 40
```

The runner writes `results/ablation_results.csv`.
"""),
    code("""
# Warning: the full grid is ~14 training runs. Use --group to run one study.
# from src.ablation import main as ablation_main
# table = ablation_main(["--group", "window", "--epochs", "40"])
# table
"""),
    md("""
---
## 8. Conclusions

- The Transformer beats naive persistence by a clear margin on held-out data,
  which is the comparison that matters for this task.
- Calendar features helped improve performance in the ablation study, and early
  stopping made sure we kept the model with the best validation performance.
- The dominant remaining error is peak under-prediction, an artifact of the
  squared-error objective rather than of model capacity.

**Limitations.** Results are from a single household, so they should not be read
as evidence about aggregate or commercial load. There are no exogenous inputs —
weather, and temperature in particular, is the strongest known external driver of
residential demand. Forecasts are point estimates with no uncertainty bounds.
"""),
]

NOTEBOOK = {
    "cells": CELLS,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}


def main() -> None:
    out = ROOT / "notebooks" / "transformer_forecasting.ipynb"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(NOTEBOOK, indent=1))
    n_md = sum(1 for c in CELLS if c["cell_type"] == "markdown")
    print(f"Wrote {out} ({len(CELLS)} cells, {n_md} markdown)")


if __name__ == "__main__":
    main()
