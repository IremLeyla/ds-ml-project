# Fraud Detection in Electricity and Gas Consumption

**Team:** Tim Pfeiffer, Irem Baykal, Dhanya Rajendran

A machine learning project from the [neuefische](https://www.neuefische.de/) Data Science bootcamp. We built a model that helps the Tunisian electricity and gas company **STEG** find clients who manipulate their meters. We worked on the [Zindi challenge "Fraud Detection in Electricity and Gas Consumption"](https://zindi.africa/competitions/fraud-detection-in-electricity-and-gas-consumption-challenge), with real billing data from 2005 to 2019.

## Results at a glance

| | ROC-AUC |
|---|---|
| Baseline (logistic regression) | 0.757 |
| First tuned model (LightGBM, 24 features) | 0.774 |
| **Final model (LightGBM, 39 features)** | **0.881** (validation), **0.876** (5-fold CV) |
| **Zindi public leaderboard** | **0.874** |

- If STEG inspects the **10% of clients** with the highest fraud score, the final model finds **57% of all fraud cases**. Every third visit is a hit, against 1 in 18 for random visits.
- Our first tuned model found 34% in the same scenario.
- The public score is close to our cross-validation estimate (0.874 vs 0.876), so the validation was honest.
- For comparison, published solutions on the same data reach about 0.864 (top 25%) and 0.883 (4th place of the original challenge). See [model_results.md](model_results.md).

## Neural network vs. LightGBM

After the project we added one neural-network challenger (a Keras feed-forward network on the same 39 features) and compared it fairly with the final LightGBM: same clients, same test set, same metric, rules frozen before training.

| Test set (27,099 clients) | ROC-AUC | PR-AUC | Top 10% inspected: fraud caught of 1,513 |
|---|---|---|---|
| **LightGBM (final model)** | **0.881** | **0.371** | **864** |
| Neural network (mean of 3 seeds) | 0.8736 | 0.3503 | 854.3 |

**Decision: we keep LightGBM.** The network is 0.0074 ROC-AUC lower, more than our practical threshold of 0.005 and more than its seed spread, and it is not better on any other metric. It is faster at scoring and smaller, but that does not matter for a batch inspection list.

- [model-comparison-plan.md](model-comparison-plan.md): the rules, frozen before training
- [16_neural-network.ipynb](16_neural-network.ipynb): the neural network (search, final model, test scores, timing)
- [17_calibration-subgroups.ipynb](17_calibration-subgroups.ipynb): post-hoc check of calibration and client groups for both models
- [model-comparison-report.md](model-comparison-report.md): all evidence and limitations
- [decision-memo.md](decision-memo.md): the recommendation and what would change it

## The problem

- **Stakeholder:** STEG loses about 200 million Tunisian dinars because consumers tamper with their meters. It can only inspect a limited number of homes.
- **Task:** binary classification at client level (fraud yes/no), from the client table and about 4.5 million bills.
- **Output:** a fraud probability per client, used as a **priority list for inspections**.
- **Main metric: ROC-AUC.** It is the official Zindi metric and measures how well the model ranks fraud cases above honest clients. Only 5.6% of the clients are fraud, so accuracy would be misleading. We also report PR-AUC, precision, recall and F1.

## Our approach

1. **Data and EDA:** loaded and joined the tables, defined cleaning rules (the same for train and test), and checked hypotheses about what fraud looks like, separately for gas and electricity.
2. **Feature engineering:** aggregated the bills to one row per client, with an 80/20 train/validation split made early and learned steps fitted on train only, so there is no leakage.
3. **Baseline:** a logistic regression as the score to beat.
4. **Model comparison:** logistic regression, Random Forest, XGBoost and LightGBM with default settings and 5-fold stratified cross-validation. LightGBM won.
5. **Hyperparameter tuning:** a random search with cross-validation.
6. **Error analysis:** which fraud cases does the model miss, and why? This analysis led to the next steps.
7. **Feature selection:** tested groups of new features against a fixed model, fold by fold.
   - Time features and meter features: +0.08 ROC-AUC.
   - Meter-setup diversity features: another +0.02.
8. **Final model and submission:** trained on all labelled clients, predicted the Zindi test set, and submitted once (no tuning on the leaderboard).

The biggest improvements came from **features built from the error analysis**, not from model settings.

## What we learned

- Framing a business problem as an ML task and choosing a metric that fits the use: ranking for limited inspections.
- Working with imbalanced data: class weights, threshold-free metrics, and scenario-based evaluation such as "top 10% inspected".
- A clean validation setup: an early split, learned steps fitted on train only, cross-validation, and the validation split used for checks.
- Comparing and tuning models fairly: the same folds, decision rules set before seeing the results, paired fold-by-fold comparisons.
- Using error analysis to guide feature engineering.
- Spotting possible leakage. Two strong features (meter replacements, inactive accounts) may partly reflect what STEG did *after* finding fraud. We documented this as a question for STEG.
- Teamwork with GitHub issues, pull requests and a decision log ([protocol.md](protocol.md)).

## Repository structure

| File / folder | Content |
|---|---|
| [00_overview.md](00_overview.md) | **Start here:** short description of every notebook, in reading order |
| `01`–`14` notebooks | The project, from data ingestion to the final model (see the overview). `05_eda-summary.md` sums up the EDA |
| [model_results.md](model_results.md) | All models scored the same way, improvement steps, comparison with published solutions |
| [protocol.md](protocol.md) | Every team decision with date and reason |
| [problem_framing.md](problem_framing.md) | Stakeholder, value, task and metrics |
| [hypotheses.md](hypotheses.md), [day1_insights.md](day1_insights.md) | The hypotheses we checked and the first notes |
| [cleaning.py](cleaning.py), [features.py](features.py) | Cleaning rules and feature functions used by the notebooks |
| `models/` | Final model (`lightgbm_final.txt`), its settings and its feature list |
| [16_neural-network.ipynb](16_neural-network.ipynb), [nn_pipeline.py](nn_pipeline.py) | Neural-network challenger and its shared code |
| [17_calibration-subgroups.ipynb](17_calibration-subgroups.ipynb), [lightgbm_posthoc_scores.py](lightgbm_posthoc_scores.py) | Post-hoc calibration and subgroup analysis of both models |
| [model-comparison-plan.md](model-comparison-plan.md), [model-comparison-report.md](model-comparison-report.md), [decision-memo.md](decision-memo.md) | Neural network vs. LightGBM: frozen plan, evidence, decision |
| `results/` | Result files of the neural-network comparison (search trials, final config, test scores, timing, environment) |
| [build_feature_tables.py](build_feature_tables.py), [lightgbm_timing.py](lightgbm_timing.py) | Rebuild the v3 feature tables; time LightGBM (no scoring) |
| `data/` | Not included (see below) |

## Getting started

**Requirements:** Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:IremLeyla/ds-ml-project.git
cd ds-ml-project
uv sync
```

**Data:** the competition data is **not part of this repository** (Zindi rules). Download it from the [Zindi data page](https://zindi.africa/competitions/fraud-detection-in-electricity-and-gas-consumption-challenge/data) and put the files in `data/`:
- `client_train.csv`, `invoice_train.csv`,
- `client_test.csv`, `invoice_test.csv`,
- `SampleSubmission.csv`.

**Run:** open the project in VS Code (`code .`), select the `.venv` kernel and run the notebooks in the order of [00_overview.md](00_overview.md). Some notebooks write cleaned data and feature tables to `data/`, which the later notebooks read.

**Main libraries:** pandas, NumPy, scikit-learn, LightGBM, XGBoost, matplotlib, seaborn.

**Neural network:** TensorFlow needs Python 3.12, so notebook 16 runs in a second environment:

```bash
uv venv --python 3.12 .venv-nn
uv pip install --python .venv-nn/bin/python -r requirements-nn.txt
.venv/bin/python build_feature_tables.py   # v3 feature tables, needs notebooks 02 and 06 first
```

Then open `16_neural-network.ipynb` with the `.venv-nn` kernel.

## Limitations

- The labels only show **detected** fraud. Some "false alarms" may be fraud that was never inspected.
- Two strong features (`n_counters`, `days_since_last_bill`) may contain information from after a fraud was found. This does not affect the Zindi score, but it should be checked with STEG before real use.
- Part of the fraud does not show in the bills at all (small, stable, young accounts). No feature built from bills alone can find it.
- The precision, recall and F1 numbers use a threshold chosen on validation, so they are slightly optimistic. The real cut-off depends on STEG's inspection capacity.

## Acknowledgements

- Data: [STEG](https://www.steg.com.tn/) via [Zindi](https://zindi.africa/).
- Project template and course: [neuefische](https://www.neuefische.de/).
- Published solutions we compared with are linked in [model_results.md](model_results.md).

## License

[MIT](LICENSE)
