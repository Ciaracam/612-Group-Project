"""Regenerate the report and deck figures from committed run artifacts.

Reads `results/<run>_predictions.csv` and `models/<run>_history.json`, both of
which are committed, so this works on a fresh clone with no raw dataset and no
GPU. Figures are written under the run-prefixed names the report and deck embed.

    python scripts/make_figures.py                              # transformer_h1
    python scripts/make_figures.py --run-name transformer_h1_tuned

After retraining, prefer `python -m src.evaluate --run-name <name>`, which
produces the same figures directly from the new checkpoint. This script exists
for the case where the dataset is unavailable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.baselines import compute_all_baselines, regression_metrics, skill_score  # noqa: E402
from src.plots import (  # noqa: E402
    plot_actual_vs_predicted,
    plot_baseline_comparison,
    plot_error_distribution,
    plot_loss_curve,
)


def model_label(history: dict) -> str:
    """Match the row label src.evaluate uses, from the run's recorded model."""
    if history.get("args", {}).get("model") == "lstm":
        return "LSTM (ours)"
    return "Transformer (ours)"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-name",
        default="transformer_h1",
        help="Run whose committed predictions and history to plot.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> dict:
    args = parse_args(argv)
    run = args.run_name

    predictions_path = ROOT / "results" / f"{run}_predictions.csv"
    history_path = ROOT / "models" / f"{run}_history.json"

    missing = [p for p in (predictions_path, history_path) if not p.exists()]
    if missing:
        names = ", ".join(str(p.relative_to(ROOT)) for p in missing)
        raise SystemExit(
            f"No committed artifacts for run '{run}': missing {names}.\n"
            f"Run `python -m src.evaluate --run-name {run}` first, or pick a run "
            f"that has committed results."
        )

    figures_dir = ROOT / "figures"
    figures_dir.mkdir(exist_ok=True)

    history = json.loads(history_path.read_text())
    predictions = pd.read_csv(predictions_path)
    actual = predictions["Actual"].to_numpy()
    predicted = predictions["Predicted"].to_numpy()

    label = model_label(history)
    comparison = {label: regression_metrics(actual, predicted)}
    comparison.update(compute_all_baselines(actual))

    plot_loss_curve(
        history["train_losses"],
        history["val_losses"],
        history["best_epoch"],
        figures_dir / f"{run}_loss_curve.png",
    )
    plot_actual_vs_predicted(actual, predicted, figures_dir / f"{run}_actual_vs_predicted.png")
    plot_baseline_comparison(comparison, figures_dir / f"{run}_baseline_comparison.png")
    plot_error_distribution(actual, predicted, figures_dir / f"{run}_error_distribution.png")

    skill = skill_score(
        comparison[label]["RMSE"],
        comparison["Naive persistence (t-1h)"]["RMSE"],
    )

    print(f"Run: {run}  ({len(actual):,} test predictions, best epoch "
          f"{history['best_epoch']} of {history['epochs_run']})")
    print(f"{'Model':28s} {'MAE':>8s} {'RMSE':>8s} {'R2':>8s}")
    for name, metrics in comparison.items():
        print(f"{name:28s} {metrics['MAE']:8.4f} {metrics['RMSE']:8.4f} {metrics['R2']:8.4f}")
    print(f"\nRMSE reduction vs persistence: {skill:.1f}%")
    print(f"Figures written to {figures_dir} as {run}_*.png")

    return comparison


if __name__ == "__main__":
    main()
