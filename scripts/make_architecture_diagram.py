"""Render the end-to-end architecture diagram used in the report and the deck.

    python scripts/make_architecture_diagram.py

Produces figures/architecture.png. The diagram deliberately covers the whole
pipeline — ingestion through evaluation — not just the network, because the
preprocessing choices are part of the contribution.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]

INK = "#0F2B46"
AMBER = "#E8871E"
TEAL = "#2A9D8F"
GRAY = "#8C9AA6"
PALE = "#EEF3F7"
PALE_AMBER = "#FDF0E1"
PALE_TEAL = "#E6F4F1"
WHITE = "#FFFFFF"


def box(ax, x, y, w, h, title, subtitle=None, face=PALE, edge=INK,
        title_size=9.5, sub_size=7.6, radius=1.2):
    """Rounded box with a bold title and optional muted subtitle."""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=1.3, edgecolor=edge, facecolor=face, zorder=2,
    ))

    if subtitle:
        ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center",
                fontsize=title_size, weight="bold", color=INK, zorder=3,
                linespacing=1.25)
        ax.text(x + w / 2, y + h * 0.27, subtitle, ha="center", va="center",
                fontsize=sub_size, color=GRAY, linespacing=1.5, zorder=3)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center",
                fontsize=title_size, weight="bold", color=INK, zorder=3,
                linespacing=1.25)


def arrow(ax, x1, y1, x2, y2, color=INK, style="-|>", lw=1.4, ls="-"):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle=style, mutation_scale=13,
        linewidth=lw, color=color, linestyle=ls,
        shrinkA=0, shrinkB=0, zorder=1,
    ))


def polyline(ax, points, color=TEAL, lw=1.6):
    """Orthogonal connector; the final segment carries the arrowhead."""
    for i in range(len(points) - 1):
        style = "-|>" if i == len(points) - 2 else "-"
        arrow(ax, points[i][0], points[i][1], points[i + 1][0], points[i + 1][1],
              color=color, style=style, lw=lw)


def shape_label(ax, x, y, text):
    """Monospace tensor-shape annotation."""
    ax.text(x, y, text, ha="center", va="center", fontsize=7.8,
            family="monospace", color=INK, weight="bold", zorder=4,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=WHITE,
                      edgecolor=TEAL, linewidth=0.9))


def band_label(ax, x, y, text):
    ax.text(x, y, text, ha="left", va="center", fontsize=10.5,
            weight="bold", color=INK)


def main() -> None:
    fig, ax = plt.subplots(figsize=(14.5, 9.4))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    ax.text(2, 97.5, "Transformer-Based Electricity Consumption Forecasting",
            fontsize=15, weight="bold", color=INK, va="center")
    ax.text(2, 94.2, "End-to-end pipeline, from raw minute-level meter readings "
                     "to an evaluated hourly forecast",
            fontsize=9.5, color=GRAY, va="center")

    # ------------------------------------------------------- 1  Data pipeline
    band_label(ax, 2, 89.5, "1   DATA PREPARATION")

    w, h, gap, y1 = 13.4, 8.8, 2.4, 78.0
    stage1 = [
        ("Raw UCI file", "2,075,259 rows\n1-minute resolution\n7 measurements", PALE, INK),
        ("Clean & index", "parse datetime\ndrop duplicates\ncoerce to numeric", PALE, INK),
        ("Hourly resample", "mean per hour\ntime interpolation\n34,589 hours", PALE, INK),
        ("Calendar features", "cyclical hour / day\nmonth / weekend\n7 physical + 7 derived", PALE, INK),
        ("Split & scale", "70 / 15 / 15 chronological\nStandardScaler\nfit on train only", PALE, INK),
        ("Sliding windows", "L = 24 hours\nstride 1\nhorizon H", PALE_TEAL, TEAL),
    ]
    for i, (title, sub, face, edge) in enumerate(stage1):
        x = 2 + i * (w + gap)
        box(ax, x, y1, w, h, title, sub, face=face, edge=edge, sub_size=7.2)
        if i:
            arrow(ax, x - gap, y1 + h / 2, x, y1 + h / 2, color=GRAY, lw=1.2)

    win_center = 2 + 5 * (w + gap) + w / 2

    # ------------------------------------------------------------- 2  Model
    band_label(ax, 2, 68.5, "2   MODEL   ·   ElectricityTransformer")

    my, mh, mx, mw = 47.0, 16.5, 2, 96
    ax.add_patch(FancyBboxPatch(
        (mx, my), mw, mh, boxstyle="round,pad=0,rounding_size=1.5",
        linewidth=1.4, edgecolor=TEAL, facecolor="#F7FBFA", zorder=0))

    inner_y, inner_h = my + 3.4, 9.8
    blocks = [
        ("Input\nprojection", "Linear\n14 to 64", PALE, INK),
        ("Positional\nencoding", "sinusoidal\nadditive", PALE, INK),
        ("Encoder\nlayer 1", "4 heads · FFN 128\npre-LN · drop 0.1", PALE_AMBER, AMBER),
        ("Encoder\nlayer 2", "4 heads · FFN 128\npre-LN · drop 0.1", PALE_AMBER, AMBER),
        ("Pooling", "take final\ntime step", PALE, INK),
        ("Dropout\n+ head", "Linear\n64 to H", PALE, INK),
    ]
    bw, bgap, start_x = 13.0, 2.6, 5.0
    positions = []
    for i, (title, sub, face, edge) in enumerate(blocks):
        bx = start_x + i * (bw + bgap)
        positions.append(bx)
        box(ax, bx, inner_y, bw, inner_h, title, sub, face=face, edge=edge,
            title_size=9, sub_size=7.2)
        if i:
            arrow(ax, bx - bgap, inner_y + inner_h / 2, bx, inner_y + inner_h / 2,
                  color=GRAY, lw=1.2)

    # Feed the windowed tensor into the model band.
    polyline(ax, [(win_center, y1), (win_center, 72.0),
                  (positions[0] + bw / 2, 72.0),
                  (positions[0] + bw / 2, my + mh)], color=TEAL)
    shape_label(ax, win_center, 74.8, "(B, 24, 14)")

    shape_label(ax, positions[0] + bw + bgap / 2, inner_y - 2.0, "(B, 24, 64)")
    shape_label(ax, positions[3] + bw + bgap / 2, inner_y - 2.0, "(B, 24, 64)")
    shape_label(ax, positions[4] + bw + bgap / 2, inner_y - 2.0, "(B, 64)")

    model_out_x = positions[-1] + bw / 2

    # ------------------------------------------- 3  Encoder layer, expanded
    band_label(ax, 6, 41.5, "3   INSIDE ONE ENCODER LAYER")

    ey, eh = 26.0, 10.0
    sub_blocks = [
        ("LayerNorm", None, WHITE),
        ("Multi-head\nself-attention", "4 heads · d_k = 16\n+ residual", PALE_AMBER),
        ("LayerNorm", None, WHITE),
        ("Feed-forward", "64 to 128 to 64\nReLU · + residual", PALE_AMBER),
    ]
    sw, sgap, sx0 = 15.0, 2.6, 32.0
    for i, (title, sub, face) in enumerate(sub_blocks):
        sx = sx0 + i * (sw + sgap)
        box(ax, sx, ey, sw, eh, title, sub, face=face, edge=AMBER,
            title_size=8.8, sub_size=7.2)
        if i:
            arrow(ax, sx - sgap, ey + eh / 2, sx, ey + eh / 2, color=GRAY, lw=1.2)

    enc_center = positions[2] + bw / 2
    arrow(ax, enc_center, inner_y, enc_center, ey + eh + 1.0,
          color=AMBER, lw=1.1, ls=(0, (3, 3)), style="-")
    ax.text(enc_center + 1.2, (inner_y + ey + eh) / 2, "expanded below",
            fontsize=7.6, color=AMBER, style="italic", ha="left", va="center")

    # ------------------------------------------------ 4  Output & evaluation
    band_label(ax, 2, 20.5, "4   OUTPUT & EVALUATION")

    oy, oh = 6.0, 11.0
    outputs = [
        ("Inverse transform", "target StandardScaler\nback to kilowatts", PALE_TEAL, TEAL),
        ("Metrics", "MAE · RMSE · R²\nper-horizon breakdown", PALE, INK),
        ("Reference forecasters", "persistence (t-1h)\nseasonal naive (t-24h)\nmean predictor", PALE, INK),
        ("Reported result", "21.8% RMSE reduction\nover persistence", PALE_AMBER, AMBER),
    ]
    ow, ogap, ox0 = 20.0, 3.0, 6.0
    for i, (title, sub, face, edge) in enumerate(outputs):
        ox = ox0 + i * (ow + ogap)
        box(ax, ox, oy, ow, oh, title, sub, face=face, edge=edge,
            title_size=9.5, sub_size=7.4)
        if i:
            arrow(ax, ox - ogap, oy + oh / 2, ox, oy + oh / 2, color=GRAY, lw=1.2)

    # Model output wraps around the right and bottom margins into stage 4.
    polyline(ax, [(model_out_x, my), (model_out_x, 43.5), (98.5, 43.5),
                  (98.5, 2.0), (ox0 + ow / 2, 2.0), (ox0 + ow / 2, oy)], color=TEAL)
    shape_label(ax, model_out_x, 43.5, "(B, H)")

    fig.tight_layout()
    out_path = ROOT / "figures" / "architecture.png"
    fig.savefig(out_path, dpi=200, facecolor="white")
    plt.close(fig)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
