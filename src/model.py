"""Model architectures.

`ElectricityTransformer` is the proposed model. `LSTMBaseline` is a recurrent
control at comparable parameter count, used to show the attention mechanism is
doing real work rather than the extra capacity alone.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn


class PositionalEncoding(nn.Module):
    """Fixed sinusoidal position signal added to the projected inputs.

    Self-attention is permutation-invariant, so without this the model cannot
    tell hour 1 of the window from hour 24.
    """

    def __init__(self, d_model: int, max_length: int = 5000):
        super().__init__()

        position = torch.arange(max_length, dtype=torch.float32).unsqueeze(1)
        division_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float32)
            * (-math.log(10000.0) / d_model)
        )

        pe = torch.zeros(max_length, d_model)
        pe[:, 0::2] = torch.sin(position * division_term)
        pe[:, 1::2] = torch.cos(position * division_term)

        self.register_buffer("positional_encoding", pe.unsqueeze(0))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.positional_encoding[:, : x.size(1)]


class LearnablePositionalEncoding(nn.Module):
    """Trainable position embeddings — ablation alternative to the sinusoidal form."""

    def __init__(self, d_model: int, max_length: int = 5000):
        super().__init__()
        self.embedding = nn.Parameter(torch.zeros(1, max_length, d_model))
        nn.init.normal_(self.embedding, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.embedding[:, : x.size(1)]


class ElectricityTransformer(nn.Module):
    """Encoder-only Transformer for multivariate load forecasting.

    Shapes, for batch B, window L, features F, horizon H:
        input           (B, L, F)
        projection      (B, L, d_model)
        + positional    (B, L, d_model)
        encoder stack   (B, L, d_model)
        pooling         (B, d_model)
        head            (B, H)
    """

    def __init__(
        self,
        input_size: int,
        d_model: int = 64,
        num_heads: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 128,
        dropout: float = 0.1,
        horizon: int = 1,
        pooling: str = "last",
        positional: str = "sinusoidal",
    ):
        super().__init__()

        if d_model % num_heads != 0:
            raise ValueError(
                f"d_model ({d_model}) must be divisible by num_heads ({num_heads})"
            )
        if pooling not in {"last", "mean"}:
            raise ValueError(f"Unknown pooling: {pooling}")
        if positional not in {"sinusoidal", "learnable", "none"}:
            raise ValueError(f"Unknown positional encoding: {positional}")

        self.pooling = pooling
        self.horizon = horizon

        self.input_projection = nn.Linear(input_size, d_model)

        if positional == "sinusoidal":
            self.positional_encoding = PositionalEncoding(d_model)
        elif positional == "learnable":
            self.positional_encoding = LearnablePositionalEncoding(d_model)
        else:
            self.positional_encoding = nn.Identity()

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=num_heads,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            norm_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer, num_layers=num_layers
        )

        self.dropout = nn.Dropout(dropout)
        self.output_layer = nn.Linear(d_model, horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.input_projection(x)
        x = self.positional_encoding(x)
        x = self.transformer_encoder(x)

        if self.pooling == "last":
            x = x[:, -1, :]
        else:
            x = x.mean(dim=1)

        x = self.dropout(x)
        return self.output_layer(x)


class LSTMBaseline(nn.Module):
    """Recurrent control model with the same input/output contract."""

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.1,
        horizon: int = 1,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.output_layer = nn.Linear(hidden_size, horizon)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])
        return self.output_layer(out)


def count_parameters(model: nn.Module) -> int:
    """Trainable parameter count — reported in the paper for fair comparison."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def build_model(name: str, input_size: int, horizon: int, **kwargs) -> nn.Module:
    """Factory used by the training script and the ablation runner."""
    if name == "transformer":
        return ElectricityTransformer(
            input_size=input_size, horizon=horizon, **kwargs
        )
    if name == "lstm":
        return LSTMBaseline(input_size=input_size, horizon=horizon, **kwargs)
    raise ValueError(f"Unknown model: {name}")
