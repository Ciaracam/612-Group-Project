"""Run the ablation grid and emit the table that justifies the final architecture.

This is what turns "we used a Transformer" into "we chose these hyperparameters
for this measured reason." Every row is a full train + evaluate cycle.

Example
-------
    python -m src.ablation --group all --epochs 40
    python -m src.ablation --group window          # only the window-length study
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src import evaluate as evaluate_module
from src import train as train_module

# Each entry is (run_name, extra CLI flags appended to the shared base).
ABLATION_GROUPS: dict[str, list[tuple[str, list[str]]]] = {
    "window": [
        ("abl_win24", ["--sequence-length", "24"]),
        ("abl_win48", ["--sequence-length", "48"]),
        ("abl_win168", ["--sequence-length", "168"]),
    ],
    "capacity": [
        ("abl_d64_l2", ["--d-model", "64", "--num-layers", "2"]),
        ("abl_d64_l4", ["--d-model", "64", "--num-layers", "4"]),
        ("abl_d128_l2", ["--d-model", "128", "--num-layers", "2", "--dim-feedforward", "256"]),
    ],
    "positional": [
        ("abl_pos_sin", ["--positional", "sinusoidal"]),
        ("abl_pos_learn", ["--positional", "learnable"]),
        ("abl_pos_none", ["--positional", "none"]),
    ],
    "features": [
        ("abl_feat_full", []),
        ("abl_feat_nocal", ["--no-calendar-features"]),
    ],
    "architecture": [
        ("abl_arch_transformer", ["--model", "transformer"]),
        ("abl_arch_lstm", ["--model", "lstm"]),
    ],
}


def run_one(run_name: str, extra: list[str], base: list[str]) -> dict:
    """Train one configuration, then evaluate it without regenerating figures."""
    print(f"\n{'=' * 70}\n  {run_name}\n{'=' * 70}")

    train_module.main(["--run-name", run_name] + base + extra)
    return evaluate_module.main(["--run-name", run_name, "--no-figures"])


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run architecture ablations")
    parser.add_argument(
        "--group",
        default="all",
        choices=list(ABLATION_GROUPS) + ["all"],
        help="Which ablation study to run",
    )
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--patience", type=int, default=6)
    parser.add_argument("--horizon", type=int, default=1)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--results-dir", default="results")
    return parser.parse_args(argv)


def main(argv=None) -> pd.DataFrame:
    args = parse_args(argv)

    base = [
        "--epochs", str(args.epochs),
        "--patience", str(args.patience),
        "--horizon", str(args.horizon),
        "--seed", str(args.seed),
    ]

    groups = list(ABLATION_GROUPS) if args.group == "all" else [args.group]

    rows = []
    for group in groups:
        for run_name, extra in ABLATION_GROUPS[group]:
            result = run_one(run_name, extra, base)
            pooled = result["test_metrics_pooled"]
            rows.append(
                {
                    "Study": group,
                    "Configuration": run_name.replace("abl_", ""),
                    "Params": result["n_parameters"],
                    "Best epoch": result["best_epoch"],
                    "MAE": round(pooled["MAE"], 4),
                    "RMSE": round(pooled["RMSE"], 4),
                    "R2": round(pooled["R2"], 4),
                    "Skill vs persistence (%)": round(
                        result["skill_vs_persistence_pct"], 1
                    ),
                }
            )

    table = pd.DataFrame(rows)

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    csv_path = results_dir / "ablation_results.csv"
    md_path = results_dir / "ablation_results.md"

    table.to_csv(csv_path, index=False)
    md_path.write_text(table.to_markdown(index=False))
    (results_dir / "ablation_results.json").write_text(
        json.dumps(rows, indent=2)
    )

    print("\n" + table.to_string(index=False))
    print(f"\nSaved: {csv_path}\n       {md_path}")

    return table


if __name__ == "__main__":
    main()
