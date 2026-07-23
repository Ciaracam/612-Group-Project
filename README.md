## Overview

This project develops a Transformer-based deep learning model to forecast household electricity consumption using multivariate time-series data. The model is implemented in PyTorch and predicts future electricity usage based on historical power consumption measurements from the UCI Individual Household Electric Power Consumption dataset.

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


Install the required packages:

pip install -r requirements.txt


Launch Jupyter Notebook and open the notebook located in the `notebooks/` folder.



## Model

The current implementation uses a custom Transformer architecture built with PyTorch for multivariate time-series forecasting. The model is trained using historical electricity consumption data and evaluated using:

- Mean Absolute Error (MAE)
- Mean Squared Error (MSE)
- Root Mean Squared Error (RMSE)



## Current Status

- Dataset preprocessing completed
- Transformer model implemented
- Model training pipeline completed
- Evaluation metrics implemented
- Interim report draft added