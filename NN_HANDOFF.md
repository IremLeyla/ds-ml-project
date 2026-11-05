# Neural-network challenger: handoff

Status file for the person (and Claude session) who continues the neural-network (NN) work. Read it together with [model-comparison-plan.md](model-comparison-plan.md) (the frozen rules) and [protocol.md](protocol.md) (all team decisions, newest at the bottom, rows dated 2026-11-05).

**Goal:** compare the finished LightGBM (documented scores, validation ROC-AUC 0.881) with one Keras/TensorFlow feed-forward MLP on the same clients and the same metric, then write the report and the decision memo. Branch: `feature/neural-network`.

## What is done (by Tim, with Claude)

| Step | Result |
|---|---|
| Decisions | Logged in `protocol.md` (5 + 4 rows, 2026-11-05) |
| Comparison plan | [model-comparison-plan.md](model-comparison-plan.md), **frozen on 2026-11-05** |
| Baseline | LightGBM is **not re-scored**. Documented scores: ROC-AUC 0.881, PR-AUC 0.371, top-10% inspection 864 of 1,513 fraud caught (seed 42). Source: [model_results.md](model_results.md), notebook 13 |
| NN environment | `requirements-nn.txt` (Python 3.12, TensorFlow 2.16.2, Keras 3.15). Tested on an Intel Mac, CPU only |
| Feature tables | [build_feature_tables.py](build_feature_tables.py) rebuilds the v3 tables. Checked: the SHA-256 values match the plan |
| Notebook `16_neural-network.ipynb` | Sections 1 to 4 (setup, data check, preprocessing, model design) are written by Tim's Claude session. Run `git pull` to get them. If the file is not there yet, they are still in progress |

## What is left (you)

Work in `16_neural-network.ipynb`. Comprehensive markdown, **commented code**, English.

| # | Section | What to do | Output to commit |
|---|---|---|---|
| 5 | Random search | 30 trials, inner stratified 80/20 split of the 108,394 training clients (seed 42), max 100 epochs, early stopping patience 10, search space in the plan. Select by inner-validation ROC-AUC | `results/nn_search_trials.csv` (one row per trial with all settings and scores) |
| 6 | Final configuration | Pick the best trial. Fix the number of epochs from the inner validation. **Commit the chosen configuration before step 7** | `results/nn_final_config.json` |
| 7 | Test evaluation | Refit on all 108,394 training clients with seeds 42, 1 and 2. Score the 27,099 test clients (`X_valid_v3`) **once**. Report unrounded ROC-AUC, PR-AUC, top-10% (flagged, caught of 1,513, hit rate, false alarms) per seed, plus mean, min, max, standard deviation | `results/nn_final_runs.csv` |
| 8 | Timing | One final NN fit, total search time, inference (1 warm-up + 10 repeats on the 27,099 test clients, median and range per 1,000 clients), model file size. Same for **one** LightGBM fit and inference with `models/lightgbm_final_params.json` and `models/lightgbm_final.txt` (timing only, **no scoring**; run it in the main project environment) | `results/nn_timing.csv` |
| 9 | Record | Library versions, hardware, seeds, total runtime | `results/nn_environment.json` |

After step 9, tell Tim. The next steps (report, memo, README) use your result files:
`model-comparison-report.md`, `decision-memo.md`, updated `README.md` and `00_overview.md`.

## Rules that must not change (frozen plan)

- **Test set = the 27,099 clients of `X_valid_v3.csv` / `y_valid.csv`.** Never use them for early stopping, tuning, architecture choice, threshold choice or preprocessing. The first time they are scored is step 7.
- Fit every preprocessing step (imputation, scaling, encoding) on the training clients only.
- Same 39 features as LightGBM (`models/selected_features_v3.json`, in that order).
- Primary metric ROC-AUC, secondary PR-AUC and top-10% inspection (the 2,710 highest scores). A difference counts only if it is at least 0.005 ROC-AUC and larger than the NN seed spread.
- Seeds 42, 1, 2 for the final runs. The search uses seed 42.
- Class weights "balanced" (as for LightGBM).
- No subgroup analysis, no calibration, no extra tree challenger, no no-ML rule.
- Do not re-score LightGBM. If a rule has to change, log it as a team decision in `protocol.md` first (use the `decision-notetaker` agent, see `CLAUDE.md`) and mention it in the report.
- Keep NN model files out of git (`models/nn_*` and `*.keras` are ignored). Small result files in `results/` are committed.

## Setup on a new machine

1. Clone the repo and check out the branch: `git fetch && git switch feature/neural-network`.
2. Get the Zindi data into `data/` (not in git). Run notebooks 02 and 06 if `data/clean/` and `data/features/X_*.csv` do not exist yet (see `00_overview.md`).
3. Main environment (Python 3.13, `uv sync`) for LightGBM. On a Mac LightGBM also needs `brew install libomp`.
4. Rebuild the v3 tables: `.venv/bin/python build_feature_tables.py`. Compare the printed SHA-256 with the plan: `X_train_v3` starts with `90e52789a4c4698a`, `X_valid_v3` with `1a5ebdca6d5f2c2f` (`X_test_v3`: `c1fe546989671f15`). If they differ, stop and tell Tim.
5. NN environment: `uv venv --python 3.12 .venv-nn` then `uv pip install --python .venv-nn/bin/python -r requirements-nn.txt`. On other hardware a newer TensorFlow may work. Record whatever you use.

## Open points for Tim

- The notebook sections 1 to 4 are still being written. Pull before starting section 5.
- Nothing has been run on the NN yet. There are no NN results.
