"""Regenerate every figure in the report from the committed interim artifacts.

This exists so the figures are reproducible without the 2 GB raw dataset or a
GPU: it reads `models/test_predictions.csv` and the recorded loss history from
the interim 20-epoch run and rewrites `figures/`.

    python scripts/make_interim_figures.py

Once you have retrained with `python -m src.train`, prefer
`python -m src.evaluate --run-name <name>`, which produces the same figures from
the new checkpoint.
"""

from __future__ import annotations

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

# Loss history recorded from the interim notebook run (20 epochs, no early stopping).
INTERIM_TRAIN_LOSSES = [
    0.4234, 0.3785, 0.3665, 0.3546, 0.3517, 0.3454, 0.3426, 0.3398, 0.3356,
    0.3348, 0.3271, 0.3252, 0.3239, 0.3193, 0.3185, 0.3165, 0.3135, 0.3042,
    0.3064, 0.3052,
]
INTERIM_VAL_LOSSES = [
    0.3962, 0.3733, 0.3578, 0.3599, 0.3459, 0.3435, 0.3657, 0.3684, 0.3404,
    0.3478, 0.3485, 0.3567, 0.3560, 0.3578, 0.3572, 0.3671, 0.3739, 0.3517,
    0.3642, 0.3618,
]
INTERIM_BEST_EPOCH = 9


def main() -> None:
    figures_dir = ROOT / "figures"
    results_dir = ROOT / "results"
    figures_dir.mkdir(exist_ok=True)
    results_dir.mkdir(exist_ok=True)

    predictions = pd.read_csv(ROOT / "models" / "test_predictions.csv")
    actual = predictions["Actual"].to_numpy()
    predicted = predictions["Predicted"].to_numpy()

    comparison = {"Transformer (ours)": regression_metrics(actual, predicted)}
    comparison.update(compute_all_baselines(actual))

    plot_loss_curve(
        INTERIM_TRAIN_LOSSES,
        INTERIM_VAL_LOSSES,
        INTERIM_BEST_EPOCH,
        figures_dir / "loss_curve.png",
    )
    plot_actual_vs_predicted(actual, predicted, figures_dir / "actual_vs_predicted.png")
    plot_baseline_comparison(comparison, figures_dir / "baseline_comparison.png")
    plot_error_distribution(actual, predicted, figures_dir / "error_distribution.png")

    summary = {
        "source": "interim 20-epoch run",
        "n_test_predictions": int(len(actual)),
        "comparison_table": comparison,
        "skill_vs_persistence_pct": skill_score(
            comparison["Transformer (ours)"]["RMSE"],
            comparison["Naive persistence (t-1h)"]["RMSE"],
        ),
    }
    (results_dir / "interim_metrics.json").write_text(json.dumps(summary, indent=2))

    print(f"{'Model':28s} {'MAE':>8s} {'RMSE':>8s} {'R2':>8s}")
    for name, metrics in comparison.items():
        print(f"{name:28s} {metrics['MAE']:8.4f} {metrics['RMSE']:8.4f} {metrics['R2']:8.4f}")
    print(f"\nRMSE reduction vs persistence: {summary['skill_vs_persistence_pct']:.1f}%")
    print(f"Figures written to {figures_dir}")


if __name__ == "__main__":
    main()
