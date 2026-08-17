"""Non-learned reference forecasters and shared metric definitions.

A deep model is only interesting if it beats the forecast you get for free.
These three baselines are the standard free forecasts for hourly load data.
"""

from __future__ import annotations

import numpy as np


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """MAE, MSE, RMSE, MAPE and R^2 in the original (kilowatt) units."""
    actual = np.asarray(actual, dtype=float).ravel()
    predicted = np.asarray(predicted, dtype=float).ravel()

    error = actual - predicted
    mse = float(np.mean(error**2))
    variance = float(np.var(actual))

    # Guard against division by zero on near-idle hours.
    nonzero = np.abs(actual) > 1e-6
    mape = (
        float(np.mean(np.abs(error[nonzero] / actual[nonzero])) * 100.0)
        if nonzero.any()
        else float("nan")
    )

    return {
        "MAE": float(np.mean(np.abs(error))),
        "MSE": mse,
        "RMSE": float(np.sqrt(mse)),
        "MAPE": mape,
        "R2": float(1.0 - mse / variance) if variance > 0 else float("nan"),
    }


def persistence_forecast(series: np.ndarray, lag: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Predict each hour as the value `lag` hours earlier.

    Returns (aligned_actual, prediction) so the two arrays are directly comparable.
    """
    series = np.asarray(series, dtype=float).ravel()
    return series[lag:], series[:-lag]


def mean_forecast(series: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Predict the evaluation-series mean for every hour — the R^2 = 0 reference."""
    series = np.asarray(series, dtype=float).ravel()
    return series, np.full_like(series, series.mean())


def compute_all_baselines(test_actual: np.ndarray) -> dict[str, dict]:
    """Evaluate every reference forecaster on the test series."""
    results = {}

    actual, pred = mean_forecast(test_actual)
    results["Mean predictor"] = regression_metrics(actual, pred)

    actual, pred = persistence_forecast(test_actual, lag=1)
    results["Naive persistence (t-1h)"] = regression_metrics(actual, pred)

    actual, pred = persistence_forecast(test_actual, lag=24)
    results["Seasonal naive (t-24h)"] = regression_metrics(actual, pred)

    return results


def skill_score(model_rmse: float, baseline_rmse: float) -> float:
    """Percentage RMSE reduction relative to a baseline. Higher is better."""
    return float((1.0 - model_rmse / baseline_rmse) * 100.0)
