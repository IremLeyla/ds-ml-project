# Project Overview: Fraud Detection in Electricity and Gas Consumption

**Goal:** help STEG, the Tunisian electricity and gas company, find fraudulent clients. The model ranks clients by fraud risk, so that STEG can send its limited inspections where fraud is most likely. Data and leaderboard: [Zindi challenge](https://zindi.africa/competitions/fraud-detection-in-electricity-and-gas-consumption-challenge).

**Result:** LightGBM with 39 features. Validation ROC-AUC **0.881**, Zindi public score **0.874** (baseline: 0.757).

**Main metric:** ROC-AUC. It is the official Zindi metric and it measures how well the model ranks fraud cases above honest clients. See [problem_framing.md](problem_framing.md) and [protocol.md](protocol.md).

## The notebooks in order

| # | Notebook | What it does | Key result |
|---|---|---|---|
| 01 | [Data ingestion](01_data-ingestion.ipynb) | Loads the 4 Zindi tables (clients and invoices, train and test) and shows how they join | 135,493 train clients, 4.5 million bills |
| 02 | [EDA and cleaning](02_eda.ipynb) | Checks data quality and defines the cleaning rules (in [cleaning.py](cleaning.py)), the same for train and test | Cleaned tables in `data/clean/` |
| 03 | [EDA analysis](03_eda-analysis.ipynb) | What do fraud clients look like? | Only 5.6% fraud; client category 51, many bills and backward meter readings are signals |
| 04 | [Gas vs electricity](04_hypotheses-gas-vs-elec.ipynb) | Re-checks every hypothesis separately per meter type | Some signals exist only on electricity |
| 05 | [EDA summary](05_eda-summary.md) | Short summary of all EDA findings and the features they suggest | The feature list for notebook 06 |
| 06 | [Feature engineering](06_feature-engineering.ipynb) | One row per client: aggregates the bills ([features.py](features.py)) and makes an 80/20 train/validation split | 24 features (feature set v1) |
| 07 | [Baseline](07_baseline-model.ipynb) | Logistic regression as the score to beat | ROC-AUC 0.757 |
| 08 | [Model comparison](08_model-comparison.ipynb) | Logistic regression, Random Forest, XGBoost and LightGBM with default settings, 5-fold CV | LightGBM wins (0.766) |
| 09 | [Tuning](09_hyperparameter-tuning.ipynb) | Random search for LightGBM | 0.774 |
| 10 | [Error analysis](10_error-analysis.ipynb) | Who does the model miss? (top-10% inspection scenario) | Misses low-consumption fraud, long histories and young clients |
| 11 | [Feature selection](11_feature-selection.ipynb) | Adds and removes feature groups with a fixed model | + time and meter features: **0.859** (feature set v2, 30 features) |
| 12 | [Re-tuning](12_retuning-new-features.ipynb) | Tunes again on the 30 features | Only a small gain; kept as a record, not part of the presentation |
| 13 | [Diversity features](13_diversity-features.ipynb) | 12 new features (meter setup diversity, consumption shape, time activity), tuning, confusion matrices | **0.881** (feature set v3, 39 features) |
| 14 | [Final model and submission](14_final-model-submission.ipynb) | Trains the final model on all labelled clients and writes the Zindi submission | CV 0.876, Zindi **0.874** |

## Other files

| File | Content |
|---|---|
| [model_results.md](model_results.md) | All models scored the same way, the steps of improvement, and a comparison with published solutions |
| [protocol.md](protocol.md) | Every team decision with date and reason |
| [problem_framing.md](problem_framing.md) | Stakeholder, value, prediction task and metrics |
| [hypotheses.md](hypotheses.md), [day1_insights.md](day1_insights.md) | The hypotheses we checked and the first notes from day 1 |
| [cleaning.py](cleaning.py), [features.py](features.py) | Cleaning rules and feature functions, used by the notebooks |
| `models/` | The final model (`lightgbm_final.txt`), its settings and its feature list |

## How to run it

1. Download the Zindi data into `data/`. It is not in git (competition rules).
2. Run the notebooks in the order of the table. Notebooks 02, 06, 11 and 13 write the cleaned data and the feature tables to `data/`, which the later notebooks read.
