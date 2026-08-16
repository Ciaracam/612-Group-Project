"""Figure generation, kept in one place so every plot in the paper and the deck
shares a palette, a font size, and an export resolution.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

INK = "#0F2B46"
AMBER = "#E8871E"
TEAL = "#2A9D8F"
GRAY = "#8C9AA6"
LIGHT = "#E9EEF2"

DPI = 200


def _style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRAY)
    ax.spines["bottom"].set_color(GRAY)
    ax.tick_params(colors=INK, labelsize=9)
    ax.grid(True, axis="y", color=LIGHT, linewidth=0.8)
    ax.set_axisbelow(True)
    return ax


def plot_loss_curve(train_losses, val_losses, best_epoch, path: Path):
    """Training/validation MSE against epoch — required in both deliverables."""
    epochs = np.arange(1, len(train_losses) + 1)

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(epochs, train_losses, color=INK, linewidth=2, label="Training loss")
    ax.plot(epochs, val_losses, color=AMBER, linewidth=2, label="Validation loss")

    if best_epoch:
        best_value = val_losses[best_epoch - 1]
        ax.scatter([best_epoch], [best_value], color=AMBER, s=70, zorder=5,
                   edgecolor="white", linewidth=1.5)
        ax.annotate(
            f"best epoch {best_epoch}\nval MSE {best_value:.4f}",
            xy=(best_epoch, best_value),
            xytext=(-18, 78),
            textcoords="offset points",
            fontsize=9,
            color=INK,
            arrowprops=dict(arrowstyle="-", color=GRAY, linewidth=0.9),
            ha="left",
        )

    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
    ax.set_xlabel("Epoch", color=INK, fontsize=10)
    ax.set_ylabel("Mean squared error (standardized)", color=INK, fontsize=10)
    ax.set_title("Training and validation loss", color=INK, fontsize=12, weight="bold",
                 loc="left")
    ax.legend(frameon=False, fontsize=9)
    _style(ax)

    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def plot_actual_vs_predicted(actual, predicted, path: Path, window: int = 336):
    """Two weeks of hourly test predictions overlaid on ground truth."""
    n = min(window, len(actual))

    fig, ax = plt.subplots(figsize=(9.5, 4.2))
    ax.plot(np.arange(n), actual[:n], color=INK, linewidth=1.8, label="Actual")
    ax.plot(np.arange(n), predicted[:n], color=AMBER, linewidth=1.6,
            label="Predicted", alpha=0.9)

    ax.set_xlabel("Hour of test period", color=INK, fontsize=10)
    ax.set_ylabel("Global active power (kW)", color=INK, fontsize=10)
    ax.set_title(f"Actual vs. predicted consumption (first {n} test hours)",
                 color=INK, fontsize=12, weight="bold", loc="left")
    ax.legend(frameon=False, fontsize=9, ncol=2)
    _style(ax)

    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def plot_baseline_comparison(comparison: dict, path: Path):
    """Grouped bars: our model against every free forecast."""
    names = list(comparison.keys())
    rmse = [comparison[n]["RMSE"] for n in names]
    mae = [comparison[n]["MAE"] for n in names]

    y = np.arange(len(names))
    height = 0.38

    fig, ax = plt.subplots(figsize=(8.5, 0.85 * len(names) + 1.8))
    bars_rmse = ax.barh(y - height / 2, rmse, height, label="RMSE", color=INK)
    bars_mae = ax.barh(y + height / 2, mae, height, label="MAE", color=AMBER)

    for bars in (bars_rmse, bars_mae):
        for bar in bars:
            ax.text(bar.get_width() + 0.012, bar.get_y() + bar.get_height() / 2,
                    f"{bar.get_width():.3f}", va="center", fontsize=8.5, color=INK)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9.5, color=INK)
    # The proposed model is the first row; make it visually unmistakable.
    ax.get_yticklabels()[0].set_fontweight("bold")
    ax.get_yticklabels()[0].set_color(TEAL)
    ax.invert_yaxis()
    ax.set_xlabel("Error (kW) — lower is better", color=INK, fontsize=10)
    ax.set_title("Model vs. reference forecasters on the test set",
                 color=INK, fontsize=12, weight="bold", loc="left")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(True, axis="x", color=LIGHT, linewidth=0.8)
    ax.grid(False, axis="y")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRAY)
    ax.spines["bottom"].set_color(GRAY)
    ax.tick_params(colors=INK, labelsize=9)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(rmse + mae) * 1.18)

    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def plot_error_distribution(actual, predicted, path: Path):
    """Residual histogram plus a predicted-vs-actual scatter."""
    residuals = np.asarray(actual).ravel() - np.asarray(predicted).ravel()

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    axes[0].hist(residuals, bins=60, color=INK, alpha=0.85)
    axes[0].axvline(0, color=AMBER, linewidth=1.6)
    axes[0].set_xlabel("Residual (actual − predicted, kW)", color=INK, fontsize=10)
    axes[0].set_ylabel("Count", color=INK, fontsize=10)
    axes[0].set_title(
        f"Residuals (mean {residuals.mean():.3f}, sd {residuals.std():.3f})",
        color=INK, fontsize=11, weight="bold", loc="left")
    _style(axes[0])

    axes[1].scatter(actual, predicted, s=4, color=TEAL, alpha=0.25, edgecolors="none")
    lim = [0, float(np.max(actual)) * 1.02]
    axes[1].plot(lim, lim, color=AMBER, linewidth=1.4, linestyle="--")
    axes[1].set_xlim(lim)
    axes[1].set_ylim(lim)
    axes[1].set_xlabel("Actual (kW)", color=INK, fontsize=10)
    axes[1].set_ylabel("Predicted (kW)", color=INK, fontsize=10)
    axes[1].set_title("Predicted vs. actual", color=INK, fontsize=11,
                      weight="bold", loc="left")
    _style(axes[1])

    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def plot_horizon_curve(per_horizon: list[dict], path: Path):
    """RMSE as a function of forecast lead time, for multi-step runs."""
    steps = np.arange(1, len(per_horizon) + 1)
    rmse = [m["RMSE"] for m in per_horizon]

    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.plot(steps, rmse, color=INK, linewidth=2, marker="o", markersize=4)
    ax.fill_between(steps, 0, rmse, color=INK, alpha=0.07)

    ax.set_xlabel("Forecast lead time (hours ahead)", color=INK, fontsize=10)
    ax.set_ylabel("RMSE (kW)", color=INK, fontsize=10)
    ax.set_title("Forecast error grows with lead time", color=INK, fontsize=12,
                 weight="bold", loc="left")
    ax.set_ylim(bottom=0)
    _style(ax)

    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path
