"""Training entry point.

Adds three things the interim implementation lacked: early stopping (the old run
kept training for 11 epochs past its best validation loss), a learning-rate
scheduler, and a persisted history/config record so every reported number can be
traced back to the run that produced it.

Example
-------
    python -m src.train --run-name transformer_h1 --epochs 60
    python -m src.train --run-name transformer_h24 --horizon 24
    python -m src.train --run-name lstm_h1 --model lstm
"""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import asdict
from pathlib import Path

import joblib
import numpy as np
import torch
import torch.nn as nn

from src.data import DataConfig, prepare_data
from src.model import build_model, count_parameters


def set_seed(seed: int) -> None:
    """Fix every RNG we touch so a rerun reproduces the reported numbers."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def select_device(preference: str = "auto") -> torch.device:
    if preference != "auto":
        return torch.device(preference)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def train_one_epoch(model, loader, criterion, optimizer, device, clip: float) -> float:
    model.train()
    total = 0.0

    for features, targets in loader:
        features = features.to(device)
        targets = targets.to(device)

        optimizer.zero_grad()
        predictions = model(features)
        loss = criterion(predictions, targets)
        loss.backward()

        if clip > 0:
            nn.utils.clip_grad_norm_(model.parameters(), clip)

        optimizer.step()
        total += loss.item()

    return total / max(1, len(loader))


@torch.no_grad()
def evaluate_loss(model, loader, criterion, device) -> float:
    model.eval()
    total = 0.0

    for features, targets in loader:
        features = features.to(device)
        targets = targets.to(device)
        total += criterion(model(features), targets).item()

    return total / max(1, len(loader))


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train an electricity forecasting model")

    parser.add_argument("--run-name", default="transformer_h1")
    parser.add_argument("--model", default="transformer", choices=["transformer", "lstm"])
    parser.add_argument("--data-path", default="data/household_power_consumption.txt")
    parser.add_argument("--output-dir", default="models")

    parser.add_argument("--sequence-length", type=int, default=24)
    parser.add_argument("--horizon", type=int, default=1)
    parser.add_argument("--no-calendar-features", action="store_true")

    parser.add_argument("--d-model", type=int, default=64)
    parser.add_argument("--num-heads", type=int, default=4)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--dim-feedforward", type=int, default=128)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--pooling", default="last", choices=["last", "mean"])
    parser.add_argument(
        "--positional", default="sinusoidal", choices=["sinusoidal", "learnable", "none"]
    )

    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=0.0)
    parser.add_argument("--patience", type=int, default=8, help="early-stopping patience")
    parser.add_argument("--lr-patience", type=int, default=3)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="auto")

    return parser.parse_args(argv)


def main(argv=None) -> dict:
    args = parse_args(argv)
    set_seed(args.seed)

    device = select_device(args.device)
    print(f"Using device: {device}")

    data_config = DataConfig(
        data_path=Path(args.data_path),
        sequence_length=args.sequence_length,
        horizon=args.horizon,
        use_calendar_features=not args.no_calendar_features,
        batch_size=args.batch_size,
        seed=args.seed,
    )
    data = prepare_data(data_config)

    print("Dataset summary:")
    for key, value in data.stats.items():
        print(f"  {key}: {value}")

    if args.model == "transformer":
        model_kwargs = dict(
            d_model=args.d_model,
            num_heads=args.num_heads,
            num_layers=args.num_layers,
            dim_feedforward=args.dim_feedforward,
            dropout=args.dropout,
            pooling=args.pooling,
            positional=args.positional,
        )
    else:
        model_kwargs = dict(
            hidden_size=args.d_model,
            num_layers=args.num_layers,
            dropout=args.dropout,
        )

    model = build_model(
        args.model,
        input_size=len(data.feature_columns),
        horizon=args.horizon,
        **model_kwargs,
    ).to(device)

    n_params = count_parameters(model)
    print(f"Trainable parameters: {n_params:,}")

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(
        model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=args.lr_patience
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / f"{args.run_name}.pt"

    train_losses: list[float] = []
    val_losses: list[float] = []
    learning_rates: list[float] = []

    best_val = float("inf")
    best_epoch = 0
    epochs_without_improvement = 0
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        train_loss = train_one_epoch(
            model, data.train_loader, criterion, optimizer, device, args.grad_clip
        )
        val_loss = evaluate_loss(model, data.val_loader, criterion, device)

        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]["lr"]

        train_losses.append(train_loss)
        val_losses.append(val_loss)
        learning_rates.append(current_lr)

        improved = val_loss < best_val - 1e-6
        if improved:
            best_val = val_loss
            best_epoch = epoch
            epochs_without_improvement = 0
            torch.save(model.state_dict(), checkpoint_path)
        else:
            epochs_without_improvement += 1

        marker = "  *" if improved else ""
        print(
            f"Epoch {epoch:3d}/{args.epochs} "
            f"- train {train_loss:.4f} - val {val_loss:.4f} - lr {current_lr:.2e}{marker}"
        )

        if epochs_without_improvement >= args.patience:
            print(f"Early stopping at epoch {epoch} (best was epoch {best_epoch}).")
            break

    elapsed = time.time() - start_time

    # Scalers are saved per run so evaluation and the demo use the exact
    # transforms this model was trained with.
    joblib.dump(data.feature_scaler, output_dir / f"{args.run_name}_feature_scaler.pkl")
    joblib.dump(data.target_scaler, output_dir / f"{args.run_name}_target_scaler.pkl")

    history = {
        "run_name": args.run_name,
        "args": vars(args),
        "data_config": {k: str(v) for k, v in asdict(data_config).items()},
        "feature_columns": data.feature_columns,
        "dataset_stats": data.stats,
        "n_parameters": n_params,
        "train_losses": train_losses,
        "val_losses": val_losses,
        "learning_rates": learning_rates,
        "best_val_loss": best_val,
        "best_epoch": best_epoch,
        "epochs_run": len(train_losses),
        "train_seconds": elapsed,
        "checkpoint": str(checkpoint_path),
    }

    history_path = output_dir / f"{args.run_name}_history.json"
    history_path.write_text(json.dumps(history, indent=2))

    print(f"\nBest validation loss {best_val:.4f} at epoch {best_epoch}")
    print(f"Checkpoint: {checkpoint_path}")
    print(f"History:    {history_path}")
    print(f"Wall clock: {elapsed / 60:.1f} min")

    return history


if __name__ == "__main__":
    main()
