"""Evaluate a trained checkpoint and emit every number and figure the report needs.

Example
-------
    python -m src.evaluate --run-name transformer_h1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from src.baselines import compute_all_baselines, regression_metrics, skill_score
from src.data import DataConfig, prepare_data
from src.model import build_model
from src.plots import (
    plot_actual_vs_predicted,
    plot_baseline_comparison,
    plot_error_distribution,
    plot_horizon_curve,
    plot_loss_curve,
)
from src.train import select_device, set_seed


@torch.no_grad()
def collect_predictions(model, loader, device) -> tuple[np.ndarray, np.ndarray]:
    """Run the model over a loader and return (actuals, predictions) in scaled units."""
    model.eval()
    preds, actuals = [], []

    for features, targets in loader:
        output = model(features.to(device))
        preds.append(output.cpu().numpy())
        actuals.append(targets.numpy())

    return np.concatenate(actuals, axis=0), np.concatenate(preds, axis=0)


def inverse_transform(array: np.ndarray, target_scaler) -> np.ndarray:
    """Undo standardization column-by-column, preserving the (N, horizon) shape."""
    shape = array.shape
    flat = array.reshape(-1, 1)
    return target_scaler.inverse_transform(flat).reshape(shape)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained model")
    parser.add_argument("--run-name", default="transformer_h1")
    parser.add_argument("--models-dir", default="models")
    parser.add_argument("--figures-dir", default="figures")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--no-figures", action="store_true")
    return parser.parse_args(argv)


def main(argv=None) -> dict:
    args = parse_args(argv)

    models_dir = Path(args.models_dir)
    figures_dir = Path(args.figures_dir)
    results_dir = Path(args.results_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    history_path = models_dir / f"{args.run_name}_history.json"
    if not history_path.exists():
        raise FileNotFoundError(
            f"No history at {history_path}. Train the run first: "
            f"python -m src.train --run-name {args.run_name}"
        )
    history = json.loads(history_path.read_text())
    train_args = history["args"]

    set_seed(train_args["seed"])
    device = select_device(args.device)

    data_config = DataConfig(
        data_path=Path(train_args["data_path"]),
        sequence_length=train_args["sequence_length"],
        horizon=train_args["horizon"],
        use_calendar_features=not train_args["no_calendar_features"],
        batch_size=train_args["batch_size"],
        seed=train_args["seed"],
    )
    data = prepare_data(data_config)

    target_scaler = joblib.load(models_dir / f"{args.run_name}_target_scaler.pkl")

    if train_args["model"] == "transformer":
        model_kwargs = dict(
            d_model=train_args["d_model"],
            num_heads=train_args["num_heads"],
            num_layers=train_args["num_layers"],
            dim_feedforward=train_args["dim_feedforward"],
            dropout=train_args["dropout"],
            pooling=train_args["pooling"],
            positional=train_args["positional"],
        )
    else:
        model_kwargs = dict(
            hidden_size=train_args["d_model"],
            num_layers=train_args["num_layers"],
            dropout=train_args["dropout"],
        )

    model = build_model(
        train_args["model"],
        input_size=len(data.feature_columns),
        horizon=train_args["horizon"],
        **model_kwargs,
    ).to(device)
    model.load_state_dict(
        torch.load(models_dir / f"{args.run_name}.pt", map_location=device)
    )

    actual_scaled, pred_scaled = collect_predictions(model, data.test_loader, device)
    actual = inverse_transform(actual_scaled, target_scaler)
    predicted = inverse_transform(pred_scaled, target_scaler)

    horizon = actual.shape[1]

    # Overall metrics, pooled across every horizon step.
    model_metrics = regression_metrics(actual, predicted)

    # Per-step metrics show how forecast quality decays with lead time.
    per_horizon = [
        regression_metrics(actual[:, h], predicted[:, h]) for h in range(horizon)
    ]

    # Baselines are computed on the h=1 target series, which is the contiguous
    # hourly sequence the naive forecasters need.
    test_series = actual[:, 0]
    baselines = compute_all_baselines(test_series)

    comparison = {"Transformer (ours)" if train_args["model"] == "transformer"
                  else "LSTM (ours)": regression_metrics(actual[:, 0], predicted[:, 0])}
    comparison.update(baselines)

    persistence_rmse = baselines["Naive persistence (t-1h)"]["RMSE"]
    model_rmse_h1 = list(comparison.values())[0]["RMSE"]

    results = {
        "run_name": args.run_name,
        "n_parameters": history["n_parameters"],
        "best_epoch": history["best_epoch"],
        "epochs_run": history["epochs_run"],
        "horizon": horizon,
        "test_metrics_pooled": model_metrics,
        "test_metrics_per_horizon": per_horizon,
        "comparison_table": comparison,
        "skill_vs_persistence_pct": skill_score(model_rmse_h1, persistence_rmse),
    }

    (results_dir / f"{args.run_name}_metrics.json").write_text(json.dumps(results, indent=2))

    predictions_df = pd.DataFrame(
        {"Actual": actual[:, 0], "Predicted": predicted[:, 0]}
    )
    predictions_df.to_csv(results_dir / f"{args.run_name}_predictions.csv", index=False)

    if not args.no_figures:
        plot_loss_curve(
            history["train_losses"],
            history["val_losses"],
            history["best_epoch"],
            figures_dir / f"{args.run_name}_loss_curve.png",
        )
        plot_actual_vs_predicted(
            actual[:, 0], predicted[:, 0], figures_dir / f"{args.run_name}_actual_vs_predicted.png"
        )
        plot_baseline_comparison(
            comparison, figures_dir / f"{args.run_name}_baseline_comparison.png"
        )
        plot_error_distribution(
            actual[:, 0], predicted[:, 0], figures_dir / f"{args.run_name}_error_distribution.png"
        )
        if horizon > 1:
            plot_horizon_curve(
                per_horizon, figures_dir / f"{args.run_name}_horizon_curve.png"
            )

    print(f"\n=== {args.run_name} ===")
    print(f"Parameters: {history['n_parameters']:,}  |  best epoch: {history['best_epoch']}")
    print(f"\n{'Model':28s} {'MAE':>8s} {'RMSE':>8s} {'R2':>8s}")
    for name, metrics in comparison.items():
        print(f"{name:28s} {metrics['MAE']:8.4f} {metrics['RMSE']:8.4f} {metrics['R2']:8.4f}")
    print(f"\nRMSE reduction vs persistence: {results['skill_vs_persistence_pct']:.1f}%")

    return results


if __name__ == "__main__":
    main()
