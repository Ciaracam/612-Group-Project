"""Live demo: interactive hourly electricity load forecasting.

Loads a trained checkpoint and its fitted scalers, then forecasts from any point
in the held-out test period. Nothing is retrained here — the demo runs in
seconds on CPU.

    streamlit run demo/app.py

If the raw dataset is unavailable, the app falls back to the committed
predictions in models/test_predictions.csv so the demo still runs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.baselines import compute_all_baselines, regression_metrics, skill_score  # noqa: E402

DATA_PATH = ROOT / "data" / "household_power_consumption.txt"
MODELS_DIR = ROOT / "models"

# Amber matches the "Predicted" series in the report figures, so the demo and the
# slides read the same way. Both hold up against the light and dark Streamlit
# themes, which the default palette does not — the forecast blended into the
# actual series on a dark background.
ACTUAL_COLOR = "#6FA8DC"
FORECAST_COLOR = "#E8871E"

st.set_page_config(page_title="Electricity Load Forecasting", layout="wide")


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
@st.cache_resource(show_spinner="Loading model…")
def load_model(run_name: str):
    """Load checkpoint + scalers. Returns None if torch or the checkpoint is missing."""
    try:
        import joblib
        import torch

        from src.model import build_model

        history_path = MODELS_DIR / f"{run_name}_history.json"
        if not history_path.exists():
            return None

        history = json.loads(history_path.read_text())
        args = history["args"]

        if args["model"] == "transformer":
            kwargs = dict(
                d_model=args["d_model"],
                num_heads=args["num_heads"],
                num_layers=args["num_layers"],
                dim_feedforward=args["dim_feedforward"],
                dropout=args["dropout"],
                pooling=args["pooling"],
                positional=args["positional"],
            )
        else:
            kwargs = dict(
                hidden_size=args["d_model"],
                num_layers=args["num_layers"],
                dropout=args["dropout"],
            )

        model = build_model(
            args["model"],
            input_size=len(history["feature_columns"]),
            horizon=args["horizon"],
            **kwargs,
        )
        model.load_state_dict(
            torch.load(MODELS_DIR / f"{run_name}.pt", map_location="cpu")
        )
        model.eval()

        return {
            "model": model,
            "history": history,
            "feature_scaler": joblib.load(MODELS_DIR / f"{run_name}_feature_scaler.pkl"),
            "target_scaler": joblib.load(MODELS_DIR / f"{run_name}_target_scaler.pkl"),
        }
    except Exception as exc:  # noqa: BLE001 - demo should degrade, not crash
        st.session_state["load_error"] = str(exc)
        return None


@st.cache_data(show_spinner="Preparing test data…")
def load_live_test_data(run_name: str):
    """Rebuild the test split from the raw dataset so the demo forecasts live."""
    from src.data import (
        DataConfig,
        add_calendar_features,
        chronological_split,
        impute_split,
        load_raw,
        to_hourly,
    )

    history = json.loads((MODELS_DIR / f"{run_name}_history.json").read_text())
    args = history["args"]

    config = DataConfig(
        data_path=DATA_PATH,
        sequence_length=args["sequence_length"],
        horizon=args["horizon"],
        use_calendar_features=not args["no_calendar_features"],
    )

    hourly = to_hourly(load_raw(DATA_PATH))
    if config.use_calendar_features:
        hourly = add_calendar_features(hourly)

    _, _, test_df = chronological_split(
        hourly[config.feature_columns], config.train_frac, config.val_frac
    )
    # Same per-split imputation the model was trained under.
    return impute_split(test_df), config


@st.cache_data
def load_fallback_predictions():
    return pd.read_csv(MODELS_DIR / "test_predictions.csv")


@st.cache_data
def load_run_predictions(run_name: str):
    """Return (predictions, is_fallback) for the selected run.

    Never substitute another run's numbers silently. Callers must surface
    is_fallback, otherwise a mistyped run name reads as live metrics for a run
    that was never evaluated.
    """
    run_csv = ROOT / "results" / f"{run_name}_predictions.csv"
    if run_csv.exists():
        return pd.read_csv(run_csv), False
    return load_fallback_predictions(), True


def model_label(run_name: str) -> str:
    """Row label for the comparison table, from the run's own recorded model."""
    history_path = MODELS_DIR / f"{run_name}_history.json"
    if history_path.exists():
        args = json.loads(history_path.read_text()).get("args", {})
        if args.get("model") == "lstm":
            return "LSTM (ours)"
        return "Transformer (ours)"
    return "Selected run"


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
st.title("Household Electricity Load Forecasting")
st.caption(
    "Transformer-based next-hour forecasting · MSML612 · "
    "William Peng, Ciara Cameron, Christopher Pedretti"
)

with st.sidebar:
    st.header("Configuration")
    run_name = st.text_input("Run name", value="transformer_h1")
    window_hours = st.slider("Hours of context to display", 48, 336, 168, step=24)
    st.divider()
    st.caption(
        "The model was trained on the first 70% of the record and never saw the "
        "test period shown here."
    )

bundle = load_model(run_name)
live_mode = bundle is not None and DATA_PATH.exists()

tab_forecast, tab_metrics, tab_about = st.tabs(
    ["Forecast", "Performance", "About the model"]
)

# --------------------------------------------------------------------------- #
# Forecast tab
# --------------------------------------------------------------------------- #
with tab_forecast:
    if live_mode:
        import torch

        test_df, config = load_live_test_data(run_name)
        feature_columns = bundle["history"]["feature_columns"]

        max_start = len(test_df) - config.sequence_length - config.horizon
        st.markdown("**Pick a moment in the held-out test period to forecast from.**")

        idx = st.slider(
            "Forecast origin",
            0, int(max_start), int(max_start // 2),
            help="Index into the test split; the model sees the preceding 24 hours.",
        )

        origin_time = test_df.index[idx + config.sequence_length]
        st.markdown(f"Forecast origin: **{origin_time:%Y-%m-%d %H:%M}**")

        window = test_df.iloc[idx : idx + config.sequence_length][feature_columns]
        scaled = bundle["feature_scaler"].transform(window)
        tensor = torch.tensor(scaled, dtype=torch.float32).unsqueeze(0)

        with torch.no_grad():
            scaled_prediction = bundle["model"](tensor).numpy().reshape(-1, 1)

        prediction = bundle["target_scaler"].inverse_transform(scaled_prediction).ravel()

        truth = test_df["Global_active_power"].iloc[
            idx + config.sequence_length : idx + config.sequence_length + config.horizon
        ].to_numpy()

        context = test_df["Global_active_power"].iloc[
            max(0, idx + config.sequence_length - window_hours) : idx + config.sequence_length
        ]

        col1, col2, col3 = st.columns(3)
        col1.metric("Predicted (kW)", f"{prediction[0]:.3f}")
        col2.metric("Actual (kW)", f"{truth[0]:.3f}")
        col3.metric("Absolute error (kW)", f"{abs(prediction[0] - truth[0]):.3f}")

        future_index = test_df.index[
            idx + config.sequence_length : idx + config.sequence_length + config.horizon
        ]
        chart = pd.DataFrame(
            {"Actual": pd.concat([context, pd.Series(truth, index=future_index)])}
        )
        # A one-point series is invisible under a line mark, which is exactly the
        # horizon=1 case. Anchor the forecast to the last observed hour so it
        # always draws as a segment.
        forecast = pd.Series(prediction, index=future_index)
        if len(context):
            forecast = pd.concat([context.iloc[-1:], forecast])
        chart["Forecast"] = forecast
        # Colour order follows the column order: Actual, then Forecast.
        st.line_chart(chart, height=380, color=[ACTUAL_COLOR, FORECAST_COLOR])

        with st.expander("Model input (last 24 hours, original units)"):
            st.dataframe(window, use_container_width=True)

    else:
        st.warning(
            "Running in **replay mode** — either the raw dataset or a trained "
            "checkpoint is missing, so the app is showing precomputed test "
            "predictions instead of forecasting live."
        )
        if "load_error" in st.session_state:
            st.caption(f"Details: {st.session_state['load_error']}")

        predictions, is_fallback = load_run_predictions(run_name)
        if is_fallback:
            st.error(
                f"No predictions on file for **{run_name}**. Showing the "
                "superseded interim run — these are **not** this run's forecasts."
            )
        start = st.slider(
            "Test-period window",
            0, max(0, len(predictions) - window_hours), 0, step=24,
        )
        st.line_chart(
            predictions.iloc[start : start + window_hours],
            height=380,
            color=[ACTUAL_COLOR, FORECAST_COLOR],
        )

# --------------------------------------------------------------------------- #
# Performance tab
# --------------------------------------------------------------------------- #
with tab_metrics:
    predictions, is_fallback = load_run_predictions(run_name)
    if is_fallback:
        st.error(
            f"No evaluation results for **{run_name}** — the table below is the "
            "superseded interim run, **not** this run. Generate the real numbers "
            f"with `python -m src.evaluate --run-name {run_name}`."
        )
    actual = predictions["Actual"].to_numpy()
    predicted = predictions["Predicted"].to_numpy()

    label = "Interim run (superseded)" if is_fallback else model_label(run_name)
    comparison = {label: regression_metrics(actual, predicted)}
    comparison.update(compute_all_baselines(actual))

    table = pd.DataFrame(comparison).T[["MAE", "RMSE", "R2"]].round(4)
    st.subheader("Test-set performance against reference forecasters")
    st.dataframe(table, use_container_width=True)

    st.metric(
        "RMSE reduction vs. naive persistence",
        f"{skill_score(comparison[label]['RMSE'], comparison['Naive persistence (t-1h)']['RMSE']):.1f}%",
    )

    st.caption(
        f"Evaluated on {len(actual):,} held-out hourly predictions. "
        "Persistence repeats the previous hour; seasonal naive repeats the same "
        "hour yesterday."
    )

# --------------------------------------------------------------------------- #
# About tab
# --------------------------------------------------------------------------- #
with tab_about:
    if bundle is not None:
        history = bundle["history"]
        col1, col2, col3 = st.columns(3)
        col1.metric("Trainable parameters", f"{history['n_parameters']:,}")
        col2.metric("Best epoch", history["best_epoch"])
        col3.metric("Epochs run", history["epochs_run"])

        st.subheader("Training curve")
        st.line_chart(
            pd.DataFrame(
                {
                    "Training loss": history["train_losses"],
                    "Validation loss": history["val_losses"],
                },
                index=np.arange(1, len(history["train_losses"]) + 1),
            ),
            height=320,
        )

        st.subheader("Input features")
        st.write(", ".join(history["feature_columns"]))
    else:
        st.info(
            "Train a model first to populate this tab:\n\n"
            "```\npython -m src.train --run-name transformer_h1\n```"
        )

    st.subheader("Architecture")
    architecture_path = ROOT / "figures" / "architecture.png"
    if architecture_path.exists():
        st.image(str(architecture_path), use_container_width=True)
