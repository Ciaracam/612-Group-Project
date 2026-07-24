## Overview

This project develops a Transformer-based deep learning model to forecast household electricity consumption using multivariate time-series data. The model is implemented in PyTorch and predicts future electricity usage based on historical power consumption measurements from the UCI Individual Household Electric Power Consumption dataset. Hyperparameters (architecture and training) are selected via a Hyperopt search rather than chosen by hand.

**Team Members**
- William Peng
- Ciara Cameron
- Christopher Pedretti



## Dataset

Due to GitHub's 100 MB file size limit, the dataset is **not included** in this repository.

Download the **Individual Household Electric Power Consumption** dataset from the UCI Machine Learning Repository:

https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption

After downloading, place the file:


household_power_consumption.txt


inside the `data/` folder:


612-Group-Project/
└── data/
    └── household_power_consumption.txt


The notebook assumes the dataset is located in this directory.


## Repository Structure


612-Group-Project/
│
├── data/
├── figures/
├── models/
├── notebooks/
├── report/
├── README.md
├── requirements.txt
└── .gitignore



## Installation

Clone the repository:


git clone https://github.com/Ciaracam/612-Group-Project.git


Install the required packages (pinned versions, from a working environment):

pip install -r requirements.txt


Launch Jupyter Notebook and open the notebook located in the `notebooks/` folder. Running it top-to-bottom will download nothing on its own — the dataset must already be in `data/` per the section above.


## Model

The notebook builds a custom encoder-only Transformer (PyTorch `TransformerEncoder`) with a sinusoidal positional encoding, trained to predict the next hour's `Global_active_power` from a lookback window of prior hours.

Pipeline, in order:

- Missing values are imputed **after** the chronological train/validation/test split (each split filled independently) to avoid leakage across split boundaries.
- Architecture and training hyperparameters (`d_model`, `num_heads`, `num_layers`, `dim_feedforward`, `dropout`, `learning_rate`, `sequence_length`, `batch_size`) are selected via a Hyperopt (TPE) search over 15 trials, each a short capped-epoch training run. All trial results are logged to `models/hyperopt_trials.csv`.
- The final model is trained with the selected hyperparameters using early stopping on validation loss, repeated across 3 seeds to check that results are stable and not just noise from one lucky run.
- Evaluated on the held-out test set using MAE, MSE, and RMSE, and compared against a persistence (naive "next hour = last hour") baseline.

## Results

Most recent run (see the notebook for full details and plots):

| | MAE | MSE | RMSE |
|---|---|---|---|
| Transformer (mean over 3 seeds) | 0.3204 ± 0.0041 | 0.2151 ± 0.0031 | 0.4638 ± 0.0034 |
| Persistence baseline | 0.3730 | 0.3308 | 0.5752 |

The Transformer beats the persistence baseline by roughly **14% on MAE**, consistently across seeds.

Best hyperparameters found by the Hyperopt search: `d_model=64`, `num_heads=8`, `num_layers=1`, `dim_feedforward=256`, `dropout≈0.027`, `learning_rate≈0.00062`, `sequence_length=48`, `batch_size=128`.

Saved artifacts: `models/best_transformer_model.pt` (best checkpoint), `models/test_predictions.csv` (timestamped actual vs. predicted values), `models/feature_scaler.pkl` / `target_scaler.pkl`, `models/hyperopt_trials.csv` (full search log), and plots in `figures/`.


## Current Status

- Dataset preprocessing completed, with missing-value imputation fixed to avoid train/val/test leakage
- Transformer model implemented
- Hyperparameter search (Hyperopt) implemented and wired into training
- Model training pipeline completed, with early stopping and multi-seed evaluation
- Evaluation metrics implemented, including a persistence baseline for comparison
- Interim report draft added (metrics in the report predate the leakage fix and hyperparameter search above, and will need updating to match)
