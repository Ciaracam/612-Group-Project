"""Data loading, cleaning, feature engineering, and sequence construction.

The raw UCI "Individual Household Electric Power Consumption" file is
minute-level and contains missing values marked with '?'. This module turns it
into the hourly, standardized, windowed tensors the model consumes.

All scalers are fit on the training split only, and gaps are interpolated
independently within each split, so no test-set information ever leaks backwards
into training.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset

# The seven physical measurements present in the raw file.
BASE_FEATURES = [
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3",
]

# Cyclical calendar features derived from the timestamp index.
CALENDAR_FEATURES = [
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "month_sin",
    "month_cos",
    "is_weekend",
]

TARGET = "Global_active_power"


@dataclass
class DataConfig:
    """Everything that controls how the dataset is built."""

    data_path: Path = Path("data/household_power_consumption.txt")
    sequence_length: int = 24
    horizon: int = 1
    use_calendar_features: bool = True
    train_frac: float = 0.70
    val_frac: float = 0.15
    batch_size: int = 64
    seed: int = 42
    num_workers: int = 0

    @property
    def feature_columns(self) -> list[str]:
        if self.use_calendar_features:
            return BASE_FEATURES + CALENDAR_FEATURES
        return list(BASE_FEATURES)


@dataclass
class PreparedData:
    """Container for everything downstream code needs."""

    train_loader: DataLoader
    val_loader: DataLoader
    test_loader: DataLoader
    feature_scaler: StandardScaler
    target_scaler: StandardScaler
    feature_columns: list[str]
    stats: dict = field(default_factory=dict)


def load_raw(data_path: Path) -> pd.DataFrame:
    """Read the semicolon-delimited raw file and index it by timestamp."""
    data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {data_path}. Download it from "
            "https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption "
            "and place household_power_consumption.txt in the data/ folder."
        )

    df = pd.read_csv(data_path, sep=";", na_values="?", low_memory=False)

    df["Datetime"] = pd.to_datetime(
        df["Date"] + " " + df["Time"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
    )

    df = df.drop(columns=["Date", "Time"])
    df = df.dropna(subset=["Datetime"]).sort_values("Datetime").set_index("Datetime")
    df = df.apply(pd.to_numeric, errors="coerce")

    # Keep the first record for any duplicated timestamp (daylight-saving artifacts).
    df = df[~df.index.duplicated(keep="first")]
    return df


def to_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Downsample minute-level readings to hourly means.

    Gap filling deliberately does *not* happen here. Interpolating before the
    chronological split lets readings either side of a split boundary inform each
    other, which is leakage: a test hour next to the boundary would be filled
    using training values, and vice versa. Call `impute_split` per split instead.
    """
    return df.resample("h").mean()


def impute_split(df: pd.DataFrame) -> pd.DataFrame:
    """Time-interpolate gaps within one split, using only that split's values."""
    return df.interpolate(method="time", limit_direction="both")


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add cyclical time-of-day / day-of-week / seasonality encodings.

    Sine-cosine pairs are used so that hour 23 and hour 0 are adjacent in
    feature space, which a raw integer encoding would not capture.
    """
    out = df.copy()
    idx = out.index

    hour = idx.hour.to_numpy()
    dow = idx.dayofweek.to_numpy()
    month = idx.month.to_numpy()

    out["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
    out["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
    out["dow_sin"] = np.sin(2 * np.pi * dow / 7.0)
    out["dow_cos"] = np.cos(2 * np.pi * dow / 7.0)
    out["month_sin"] = np.sin(2 * np.pi * (month - 1) / 12.0)
    out["month_cos"] = np.cos(2 * np.pi * (month - 1) / 12.0)
    out["is_weekend"] = (dow >= 5).astype(float)

    return out


def chronological_split(
    df: pd.DataFrame, train_frac: float, val_frac: float
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split in time order. Never shuffle a forecasting dataset before splitting."""
    n = len(df)
    train_end = int(n * train_frac)
    val_end = int(n * (train_frac + val_frac))
    return df.iloc[:train_end], df.iloc[train_end:val_end], df.iloc[val_end:]


class SequenceDataset(Dataset):
    """Sliding windows over a contiguous block of hours.

    Each item is (window of `sequence_length` past hours, next `horizon` targets).
    Windows never span a split boundary because each split gets its own instance.
    """

    def __init__(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        sequence_length: int,
        horizon: int = 1,
    ):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.targets = torch.tensor(targets, dtype=torch.float32)
        self.sequence_length = sequence_length
        self.horizon = horizon

    def __len__(self) -> int:
        return max(0, len(self.features) - self.sequence_length - self.horizon + 1)

    def __getitem__(self, index: int):
        start = index
        end = index + self.sequence_length
        x = self.features[start:end]
        y = self.targets[end : end + self.horizon]
        return x, y


def prepare_data(config: DataConfig) -> PreparedData:
    """Run the full pipeline and return ready-to-use dataloaders."""
    raw = load_raw(config.data_path)
    raw_rows = len(raw)
    rows_with_missing = int(raw.isna().any(axis=1).sum())

    hourly = to_hourly(raw)
    if config.use_calendar_features:
        hourly = add_calendar_features(hourly)

    feature_columns = config.feature_columns
    model_df = hourly[feature_columns].copy()

    train_df, val_df, test_df = chronological_split(
        model_df, config.train_frac, config.val_frac
    )

    # Impute after splitting so no split borrows values from another.
    train_df = impute_split(train_df)
    val_df = impute_split(val_df)
    test_df = impute_split(test_df)

    feature_scaler = StandardScaler()
    target_scaler = StandardScaler()

    train_x = feature_scaler.fit_transform(train_df[feature_columns])
    val_x = feature_scaler.transform(val_df[feature_columns])
    test_x = feature_scaler.transform(test_df[feature_columns])

    train_y = target_scaler.fit_transform(train_df[[TARGET]]).flatten()
    val_y = target_scaler.transform(val_df[[TARGET]]).flatten()
    test_y = target_scaler.transform(test_df[[TARGET]]).flatten()

    splits = [
        (train_x, train_y),
        (val_x, val_y),
        (test_x, test_y),
    ]
    datasets = [
        SequenceDataset(x, y, config.sequence_length, config.horizon)
        for x, y in splits
    ]

    generator = torch.Generator()
    generator.manual_seed(config.seed)

    train_loader = DataLoader(
        datasets[0],
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=config.num_workers,
        generator=generator,
        drop_last=False,
    )
    val_loader = DataLoader(
        datasets[1],
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
    )
    test_loader = DataLoader(
        datasets[2],
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
    )

    stats = {
        "raw_rows": raw_rows,
        "raw_rows_with_missing": rows_with_missing,
        "hourly_rows": len(hourly),
        "start": str(hourly.index.min()),
        "end": str(hourly.index.max()),
        "n_features": len(feature_columns),
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
        "train_sequences": len(datasets[0]),
        "val_sequences": len(datasets[1]),
        "test_sequences": len(datasets[2]),
    }

    return PreparedData(
        train_loader=train_loader,
        val_loader=val_loader,
        test_loader=test_loader,
        feature_scaler=feature_scaler,
        target_scaler=target_scaler,
        feature_columns=feature_columns,
        stats=stats,
    )
